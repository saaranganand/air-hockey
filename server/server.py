import json
import socket
from _thread import *
import uuid
import time
from collections import deque

from server.sim import Simulator 

'''
Server Class

The server class handles all communication between clients.
It maintains an internal state of the current game, including 
the position of objects on the playing surface and the current score.
'''
class Server:
    def __init__(self, num_players, host="0.0.0.0", port=0):
        self.host = host
        self.port = port
        self.num_players = num_players
        self.server_socket = None
        self.active_clients = 0
        self.running = False

        # Game state
        self.players = {}
        self.paddles = {}
        self.lock = allocate_lock()
        self.game_state = {
            "paddles": {},
            "puck": {"position": [1280//2,720//2], "velocity": [0,0]},
            "score": {"left": 0, "right": 0}
        }

        # Simulation
        self.sim = Simulator()
        self.simDelta = 1000 / 60 # How often we should simulate the game state
        self.broadcastDelta = 1000 / 60 # How often we should broadcast game state to players
        self.lastSim = -float('inf')
        self.lastBroadcast = -float('inf')
        self.actionQueue = [] # The game state updates received from clients since last simulation
        self.paddleInfo = {} # Internal state of paddles
        self.puckInfo = {} # Internal state of the puck

        start_new_thread(self.tick, ())

    '''
    tick function

    The tick function incrementally updates the internal game state, updating
    it based on the updates received from each client.
    It also handles incrementally sending game state updates to clients.
    '''
    def tick(self):
        while True:
            curTime = time.clock_gettime(time.CLOCK_MONOTONIC)

            simDelta = (curTime - self.lastSim) * 1000
            if (simDelta > self.simDelta):
                with self.lock:
                    # Update game state with simulator
                    self.game_state = self.sim.simulate(self.actionQueue, simDelta)
                    self.actionQueue = [] # Reset action queue
                    self.lastSim = curTime
            if ((curTime - self.lastBroadcast) * 1000 > self.broadcastDelta):
                with self.lock:
                    # Sends current game state to each player
                    self.broadcast_game_state()
                    self.lastBroadcast = curTime

    '''
    handle_client function

    The handle_client function handles establishing and maintaining connections
    between each client.
    Based on the received packet, it will parse it for necessary information to 
    update the action queue or add new players to the game.
    '''
    def handle_client(self, client_socket, client_addr):
        print(f"[+] {client_addr} connected") # validate connection
        self.active_clients += 1
        player_id = None

        try:
            while True:
                # size of information we're trying to receive
                # TODO: increase if insufficient (!takes longer!)
                data = client_socket.recv(2048).decode('utf-8')
                if not data:
                    print("No data")
                    break

                message = json.loads(data)
                action = message.get('action')

                # GAME ACTION CASES

                # ---
                # PLAYER JOINS
                # ---

                if action == 'disconnect':
                    player_id = message.get('player_id')
                    break
                elif action == "join":
                    player_id = str(uuid.uuid4()) # unique

                    # register player and assign paddle
                    with self.lock:
                        if player_id not in self.players:
                            # paddle id is same as player id
                            paddle_id = player_id
                            self.players[player_id] = {"paddle_id": paddle_id, "position": None, "client_socket": client_socket}
                            self.paddles[paddle_id] = {"locked_by": None, "position": None}
                            self.paddleInfo[paddle_id] = {
                                'position': [1280 // 4, 720 // 2],
                                'velocity': [0, 0]
                            }
                            # Add a new paddle to the simulator
                            self.actionQueue.append({'join': {
                                'paddle_id': paddle_id,
                                'position': [1280 // 4, 720 // 2],
                                'velocity': [0, 0]
                            }})
                            print(f"Player {player_id} joined with paddle {paddle_id}")
                        else:
                            # player rejoins/already exists
                            paddle_id = self.players[player_id]["paddle_id"]

                    # acknowledge
                    ack = json.dumps({"action": "join_ack", "player_id": player_id, "paddle_id": paddle_id, "game_state": self.game_state})
                    client_socket.sendall((ack + "\n").encode('utf-8'))

                # ---
                # Other actions (besides "join")
                # ---
                else:
                    # requires player_id
                    player_id = message.get("player_id")
                    if not player_id or player_id not in self.players:
                        # reject requests without valid player_id
                        error_msg = json.dumps({
                            "action": "error",
                            "message": "Invalid or missing player_id"
                        })
                        client_socket.sendall((error_msg + "\n").encode('utf-8'))
                        # self.broadcast_game_state()
                        continue

                    # ---
                    # UPDATE POSITION
                    # ---
                    if action == "update_position":
                        # client sends position for its player's paddle
                        player_id = message.get("player_id")
                        position = message.get("position")
                        velocity = message.get("velocity")

                        with self.lock:
                            paddle_id = message.get("id")
                            # If the paddle is not reflected in internal game state, add an entry for it
                            if paddle_id not in self.paddleInfo.keys():
                                self.paddleInfo[paddle_id] = {}

                            # Update position and velocity based on client's packet
                            self.players[player_id]["position"] = position
                            self.paddles[paddle_id]["position"] = position
                            self.paddleInfo[paddle_id]["position"] = position
                            self.paddleInfo[paddle_id]["velocity"] = velocity
                            self.paddles[paddle_id]["velocity"] = velocity
                            
                            self.actionQueue.append({
                                "update_position": {
                                    "paddle_id": paddle_id,
                                    "position": position,
                                    "velocity": velocity
                                }
                            })


                        #acknowledge
                        ack = json.dumps({"action": "update_ack", "player_id": player_id})
                        client_socket.sendall((ack + "\n").encode('utf-8'))

                    # ---
                    # GRAB PADDLE
                    # ---
                    elif action == "grab_paddle":
                        # client wants to lock this paddle
                        player_id = message.get("player_id")
                        requested_paddle = message.get("paddle_id")

                        with self.lock:
                            if requested_paddle in self.paddles: # paddle exists
                                if self.paddles[requested_paddle]["locked_by"] is None: # paddle not alr claimed
                                    self.paddles[requested_paddle]["locked_by"] = player_id
                                    self.players[player_id]["paddle_id"] = requested_paddle

                                    ack = json.dumps({
                                        "action": "grab_ack",
                                        "status": "success",
                                        "player": player_id,
                                        "paddle_id": requested_paddle
                                    })
                                    self.actionQueue.append({"grab": {'success': True, 'paddle': requested_paddle, 'player': player_id}})
                                else: # paddle alr claimed
                                    ack = json.dumps({
                                        "action": "grab_ack",
                                        "status": "failed",
                                        "paddle_id": requested_paddle,
                                        "player": player_id,
                                        "reason": "paddle already locked"
                                    })
                                    self.actionQueue.append({'grab': {'success': False, 'paddle': requested_paddle, 'player_id': player_id}})
                            else: # paddle doesnt exist
                                ack = json.dumps({
                                    "action": "grab_ack",
                                    "status": "failed",
                                    "paddle_id": requested_paddle,
                                    "player": player_id,
                                    "reason": "invalid paddle"
                                })
                                self.actionQueue.append({'grab': {'success': False, 'paddle': requested_paddle, 'player_id': player_id}})
                        client_socket.sendall((ack + "\n").encode('utf-8'))

                    # ---
                    # RELEASE PADDLE
                    # ---
                    elif action == "release_paddle":
                        # client wants to release this paddle
                        player_id = message.get("player_id")
                        released_paddle = message.get("paddle_id")

                        with self.lock:
                            if released_paddle in self.paddles: # paddle exists
                                if self.paddles[released_paddle]["locked_by"] == player_id: # ensure paddle alr claimed (by this player)
                                    self.paddles[released_paddle]["locked_by"] = None

                                    ack = json.dumps({
                                        "action": "release_ack",
                                        "status": "success",
                                        "paddle_id": released_paddle
                                    })

                                    self.actionQueue.append({"release": released_paddle})
                                # TODO: server needs to retry releasing until it works (no fail case possible)
                                else:# paddle alr claimed (by other player)
                                    print(f"Player {player_id} failed to release paddle {released_paddle} (already locked)")
                                    ack = json.dumps({
                                        "action": "release_ack",
                                        "status": "failed",
                                        "paddle_id": released_paddle,
                                        "reason": "you do not own this paddle"
                                    })
                            else: # paddle doesnt exist
                                print(f"Player {player_id} requested to release invalid paddle")
                                ack = json.dumps({
                                    "action": "release_ack",
                                    "status": "failed",
                                    "reason": "invalid paddle"
                                })
                        client_socket.sendall((ack + "\n").encode('utf-8'))
                        # self.broadcast_game_state()

        except Exception as e:
            print(f"[-] Error: {e}")

        finally:
            # Runs on client disconnection
            if player_id:
                with self.lock:
                    if player_id in self.players:
                        paddle_id = self.players[player_id]['paddle_id']
                        # remove player and corresponding paddle
                        del self.players[player_id]
                print(f"[-] {client_addr} disconnected")
                # Close the connection to the client
                client_socket.close()
                self.active_clients -= 1

            # shutdown if no clients
            if self.active_clients == 0:
                print("[*] No active clients. Shutting down server.")
                self.stop_server()
                return


    '''
    start_server function

    Handles setting up the socket used by the server
    '''
    def start_server(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((self.host, self.port))
            self.running = True
            # see if anything on port
            self.server_socket.listen()
            print(f"Server started, listening on {self.host}:{self.get_port_num()}")

            # continuously look for connections
            while self.running:
                try:
                    # accept new connection
                    client_socket, client_addr = self.server_socket.accept()
                    print("Connection from: ", client_addr)

                    start_new_thread(self.handle_client, (client_socket, client_addr))
                except Exception as e:
                    if not self.running:
                        break
        except KeyboardInterrupt:
            print("\nServer shutting down...")

    '''
    broadcast_game_state function

    Sends the latest updated game state to each client currently connected
    '''
    def broadcast_game_state(self):
        try:
            # The game state contains information about the position of each object
            # on the playing surface, and the current score
            game_state_message = json.dumps({
                "action": "state_update",
                "game_state": self.game_state
            })

            # Send the game state to all players that are currently connected
            for player in self.players.values():
                player["client_socket"].sendall((game_state_message + "\n").encode('utf-8'))
        except Exception as e:
            print("Something went wrong broadcasting:", e)

    # Utility functions ---------------------------------------------------------------------------
    # ---
    # scoring
    # ---
    def handle_goal(self, scoring_side):
        with self.lock:
            if scoring_side == "left":
                self.game_state["score"]["left"] += 1
            elif scoring_side == "right":
                self.game_state["score"]["right"] += 1
            self.reset_puck()
            # self.broadcast_game_state()

    def reset_puck(self):
        self.game_state["puck"]["position"] = [1280 // 2, 720 // 2]
        self.game_state["puck"]["velocity"] = [0, 0]


    def stop_server(self):
        """Stops the server."""
        if self.server_socket:
            self.running = False
            self.server_socket.close()
            self.server_socket = None
        print("Server stopped.")

    def get_port_num(self):
        """returns dynamicly assigned port number after bind"""
        if self.server_socket is not None:
            return self.server_socket.getsockname()[1]
        return None
    # ----------------------------------------------------------------------------------------------

if __name__ == "__main__":
    server = Server(num_players=4) 
    server.start_server()

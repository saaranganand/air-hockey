import json
import socket
from _thread import *

host = "0.0.0.0"
port = 12345
# TODO: have server loop and try multiple ports if default in use

# game state
players = {}
paddles = {}

lock = allocate_lock()

active_clients = 0

def handle_client(client_socket, client_addr):
    print(f"[+] {client_addr} connected") # validate connection
    global active_clients
    active_clients += 1

    while True:
        try:
            # size of information we're trying to receive
            # TODO: increase if insufficient (!takes longer!)
            data = client_socket.recv(2048).decode('utf-8')
            if not data:
                print("No data")
                break

            message = json.loads(data)
            action = message.get('action')
            player_id = message.get('player_id') # unique

            # ----
            # TODO: handle game action cases
            # ex. join, update position, grab/lock paddle, release paddle, etc.
            # ----

        except Exception as e:
            print(f"[-] Error: {e}")
            break

    # remove player
    with lock:
        if player_id in players:
            paddle_id = players[player_id]['paddle_id']
            # remove player and corresponding paddle
            del players[player_id]
            del paddles[paddle_id]
    print(f"[-] {client_addr} disconnected")
    client_socket.close()
    active_clients -=1

    # shutdown if no clients
    if active_clients == 0:
        print("[*] No active clients. Shutting down server.")
        interrupt_main()


def start_server():
    global active_clients

    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            server_socket.bind((host, port))
        except socket.error as e: # port in use
            str(e)

        # see if anything on port
        server_socket.listen()
        print(f"Server started, listening on {host}:{port}")

        # continuously look for connections
        while True:
            # accept new connection
            client_socket, client_addr = server_socket.accept()
            print("Connection from: ", client_addr)

            start_new_thread(handle_client, (client_socket, client_addr))

    except KeyboardInterrupt:
        print("\nServer shutting down...")

if __name__ == "__main__":
    start_server()
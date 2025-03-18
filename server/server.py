import socket
import threading
import pickle

class Server:
    def __init__(self, num_players, host="0.0.0.0", port=5555):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen(num_players) 
        self.clients = {}

    def start(self):
        print("Server started. Waiting for players...")
        player_id = 1
        while True:
            conn, addr = self.server.accept()
            print(f"Player {player_id} connected from {addr}")
            self.clients[player_id] = conn
            threading.Thread(target=self.handle_client, args=(conn, player_id)).start()
            player_id += 1

#if __name__ == "__main__":
#    server = Server()
#    server.start()

""" 
usage:
    from Server import Server 
    server = Server() 
    server.start()
    #this will start the server, start listening for connections, up to 


"""


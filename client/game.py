import socket
import threading
import time
import sys
import os
from collections import deque
from _thread import *

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
client_dir = os.path.dirname(os.path.abspath(__file__))

from server import server
import pygame
import math
import json
import pygame_menu

# Initialize Pygame
pygame.init()

def get_local_ip():
    # Connect to an external IP and get the socket's own address
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            # Doesn't have to be reachable — just to figure out the local IP
            s.connect(('8.8.8.8', 80))
            return s.getsockname()[0]
        except Exception:
            return '127.0.0.1'  # fallback

def send_to_server(server_socket, msg):
    try:
        server_socket.send(msg)
    except OSError: # try to reconnect
        print("Broken pipe happens here")
        print(OSError)
        return False
    return True


# Constants
WIDTH, HEIGHT = 1280, 720
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SERVER_PORT = 55000
SERVER_IP = '127.0.0.1'
pause_menu_active = False
is_paused = False
game_running = False
player_name = ""
player_id = ""
# paddle_id = ""
server_socket = None
game_session = None
main_menu = None
pause_menu = None
join_match_menu = None
buffer_lock = allocate_lock()

# Create game window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Air Hockey")


def wait_for_server():
    global SERVER_PORT, game_session

    # Extract the port number from the server, if it fails after 5 attempts, time out
    for i in range(5):

        SERVER_PORT = game_session.get_port_num()

        if SERVER_PORT is not None:
            print(f"The port is {SERVER_PORT}")
            return True

        else:

            time.sleep(0.3)

    return False


def wait_and_connect():
    global SERVER_PORT, SERVER_IP, server_socket
    print(f"wait and connect trying to connect to {SERVER_IP}:{SERVER_PORT}")

    # Connect to the server. If it fails after 5 attempts, time out
    for i in range(5):

        try:

            if server_socket:

                get_player_id()

                return True
            else:
                print("Server socket uninitialized")
                return False

        except Exception as e:
            print(e)
            time.sleep(0.3)

    return False


# Quit the current match
def leave_match():
    global game_session, server_socket

    # TODO: Implement graceful disconnection with the host user
    try:
        msg = json.dumps({
            "action": "disconnect",
            "player_id": player_id
        })
        server_socket.sendall(msg.encode('utf-8'))
        server_socket.close()

    except Exception as e:
        print(f"Leave Match Error: {e}")


def get_player_id():
    global server_socket, player_id

    join_msg = json.dumps({
        "action": "join",
        "player_id": 0
    })

    host = socket.gethostbyname(SERVER_IP)
    server_socket.connect((host, SERVER_PORT))

    # Send a request to join the server
    server_socket.sendall(join_msg.encode('utf-8'))

    # Retrieve the player's ID
    response = json.loads(server_socket.recv(2048).decode('utf-8'))

    player_id = response['player_id']


# Classes for game menus
class PauseMenu:

    def __init__(self):
        self.menu = pygame_menu.Menu('Paused', 600, 400, theme=pygame_menu.themes.THEME_BLUE)
        self.menu.add.button('Back to Main Menu', self.return_to_main_menu)
        self.menu.add.button('Resume', self.resume_game)

    def return_to_main_menu(self):
        global game_running, pause_menu_active, main_menu
        game_running = False
        leave_match()
        pause_menu_active = False
        self.menu.disable()
        main_menu.show()

    def resume_game(self):
        global is_paused, pause_menu_active
        pause_menu_active = False
        is_paused = False
        self.menu.disable()

    def show(self):
        self.menu.enable()
        self.menu.mainloop(screen)


class MainMenu:

    def __init__(self):
        self.menu = pygame_menu.Menu('2v2 Air Hockey', WIDTH, HEIGHT,
                                     theme=pygame_menu.themes.THEME_BLUE)
        self.name_box = self.menu.add.text_input('Player Name :', '')
        self.menu.add.button('Start Match', self.start_the_game)
        self.menu.add.button('Join A Server', self.main_menu_to_join_match_menu)
        self.menu.add.button('Quit', pygame_menu.events.EXIT)

    def get_name(self):
        return self.name_box.value()

    def start_the_game(self):
        global game_running, game_session, server_socket, SERVER_PORT, SERVER_IP
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        SERVER_IP = get_local_ip()
        game_session = server.Server(4, SERVER_IP)

        # Run the server in a different thread
        threading.Thread(target=game_session.start_server, daemon=False).start()

        if wait_for_server() and wait_and_connect():

            game_running = True
            self.menu.disable()

        else:
            game_session.stop_server()
            print("Could not connect to server")

    def main_menu_to_join_match_menu(self):
        global join_match_menu

        self.menu.disable()
        join_match_menu.show()

    def show(self):
        self.menu.enable()
        self.menu.mainloop(screen)

class JoinGameMenu:

    def __init__(self):

        self.menu = pygame_menu.Menu('Join Match', WIDTH, HEIGHT,)
        self.server_ip = self.menu.add.text_input('Server IP :', '')
        self.server_port = self.menu.add.text_input('Server Port :', '')
        self.menu.add.button('Join Match', self.join_the_game)
        self.menu.add.button('Return to Main Menu', self.return_to_main_menu)
        self.error_label = self.menu.add.label("")

    def join_the_game(self):

        global game_running, SERVER_IP, SERVER_PORT, server_socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        SERVER_IP = self.server_ip.get_value()
        SERVER_PORT = int(self.server_port.get_value())

        print(f"trying to connect to {SERVER_IP}:{SERVER_PORT}")
        if wait_and_connect():
            game_running = True
            self.menu.disable()
        else:
            print("Couldn't connect")

    def return_to_main_menu(self):

        global main_menu
        self.server_port.reset_value()
        self.server_ip.reset_value()
        self.menu.disable()
        main_menu.show()

    def show(self):

        self.menu.enable()
        self.menu.mainloop(screen)


class Paddle:
    def __init__(self, x, y, color, paddle_id):
        self.x = x
        self.y = y
        self.radius = 40
        self.color = color
        self.maxSpeed = 22 
        self.vx = 0
        self.vy = 0
        self.curSpeed = 0 
        self.friction = 0.97
        self.isGrabbed = False
        self.paddleID = paddle_id

    def move(self):
        if not self.isGrabbed:
            self.x += self.vx
            self.y += self.vy
            self.vx *= self.friction
            self.vy *= self.friction

            # Bounce off walls
            if self.y - self.radius <= 0 or self.y + self.radius >= HEIGHT:
                self.vy = -self.vy
            if self.x - self.radius <= 0 or self.x + self.radius >= WIDTH:
                self.vx = -self.vx

            # Prevent clipping into walls
            self.x = max(self.radius, min(self.x, WIDTH - self.radius))
            self.y = max(self.radius, min(self.y, HEIGHT - self.radius))
        else:
            mouseX, mouseY = pygame.mouse.get_pos()
            dist = -math.hypot(self.x - mouseX, self.y - mouseY)
            angle = math.atan2(self.y - mouseY, self.x - mouseX)

            self.vx =  dist * math.cos(angle)
            self.vy = dist * math.sin(angle)
            velocity = math.sqrt(self.vx**2 + self.vy**2)

            if velocity > self.maxSpeed:
                self.vx = (self.vx / velocity) * self.maxSpeed
                self.vy = (self.vy / velocity) * self.maxSpeed

            self.x += self.vx
            self.y += self.vy

            self.curSpeed = math.sqrt(self.vx ** 2 + self.vy ** 2)

    # returns True if the mouse is inside the paddle's radius
    def mouseInRadius(self, paddle):
        mouseX, mouseY = pygame.mouse.get_pos()
        if mouseX < self.x + self.radius and mouseX > self.x - self.radius and mouseY < paddle.y + self.radius and mouseY > self.y - paddle.radius:
            return True
        else:
            return False


    def draw(self, screen):
        if self.isGrabbed:
            # Make the color darker to indicate to all players that the paddle has been grabbed
            tempColor = []
            tempColor.append(self.color[0] * 0.5)
            tempColor.append(self.color[1] * 0.5)
            tempColor.append(self.color[2] * 0.5)
            pygame.draw.circle(screen, tuple(tempColor), (self.x, self.y), self.radius)
        else:
            pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)

class Puck:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.radius = 30
        self.color = tuple([0, 220, 50])
        self.vx = 0
        self.vy = 0
        self.friction = 0.99
        self.maxSpeed = 25

    def move(self):
        self.x += self.vx
        self.y += self.vy
        

        # Bounce off walls
        if self.y - self.radius <= 0 or self.y + self.radius >= HEIGHT:
            self.vy = -self.vy

        if self.x - self.radius <= 0 or self.x + self.radius >= WIDTH:
            self.vx = -self.vx

        # Prevent clipping with walls
        self.x = max(self.radius, min(self.x, WIDTH - self.radius))
        self.y = max(self.radius, min(self.y, HEIGHT - self.radius))

        # Friction
        self.vx *= self.friction
        self.vy *= self.friction

        velocity = math.sqrt(self.vx**2 + self.vy**2)
        if velocity > self.maxSpeed:
            self.vx = (self.vx / velocity) * self.maxSpeed
            self.vy = (self.vy / velocity) * self.maxSpeed


    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)

class Goal:
    def __init__(self, side):
        self.width = 10 
        self.height = HEIGHT // 3 
        self.y = HEIGHT // 3
        if side == "left":
            self.x = 0 
        elif side == "right":
            self.x = WIDTH - self.width

    def draw(self):
        goal = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen, WHITE, goal)

    def goal(self):
        goalHornSoundEffect.play()
        goalHornSoundEffect.fadeout(2500)

    def checkCollisionWithPuck(self, puck):
        puckDistanceX = abs(puck.x - self.x)
        return puckDistanceX - puck.radius <= 0 and puck.y - puck.radius > self.y and puck.y + puck.radius < 2 * self.y
            

def checkCollisionPuckAndPaddle(paddle, puck):
    dist = math.hypot(paddle.x - puck.x, paddle.y - puck.y)
    if dist < paddle.radius + puck.radius:
        if dist == 0:
            dist = 10e-6 # prevent division by 0
        if puckCollisionSound.get_num_channels() == 0:
            puckCollisionSound.play(maxtime=500)

        angle = math.atan2(puck.y - paddle.y, puck.x - paddle.x)

        # distances between paddles
        dx = paddle.x - puck.x
        dy = paddle.y - puck.y

        # normal vector
        nx = dx / dist
        ny = dy / dist

        # tangent vector
        tx = -ny
        ty = nx

        # dot product tangent
        dpTan1 = paddle.vx * tx + paddle.vy * ty
        dpTan2 = puck.vx * tx + puck.vy * ty

        # dot product normal
        dpNorm1 = paddle.vx * nx + paddle.vy * ny
        dpNorm2 = puck.vx * nx + puck.vy * ny
        if paddle.isGrabbed:
            puck.vx += paddle.curSpeed * math.cos(angle)
            puck.vy += paddle.curSpeed * math.sin(angle)
        else:
            # Swap normal velocities
            paddle.vx = tx * dpTan1 + nx * dpNorm2
            paddle.vy = ty * dpTan1 + ny * dpNorm2
            puck.vx = tx * dpTan2 + nx * dpNorm1
            puck.vy = ty * dpTan2 + ny * dpNorm1

        # prevent sticking together
        overlap = (paddle.radius + puck.radius) - dist
        if overlap < 0:
            separation = (overlap / 2) + 0.5
            paddle.x += nx * separation 
            paddle.y += ny * separation 
            puck.x -= nx * separation 
            puck.y -= ny * separation 

def checkCollisionPaddleAndPaddle(paddle1, paddle2):
    dist = math.hypot(paddle1.x - paddle2.x, paddle1.y - paddle2.y)
    if dist <= paddle1.radius * 2:
        if paddleCollisionSound.get_num_channels() == 0:
            paddleCollisionSound.play(maxtime=500)

        # distances between paddles
        dx = paddle1.x - paddle2.x
        dy = paddle1.y - paddle2.y
        
        # avoid division by 0
        if dx == 0 or dy == 0:
            return

        # normal vector
        nx = dx / dist
        ny = dy / dist

        # tangent vector
        tx = -ny
        ty = nx

        # dot product tangent
        dpTan1 = paddle1.vx * tx + paddle1.vy * ty
        dpTan2 = paddle2.vx * tx + paddle2.vy * ty

        # dot product normal
        dpNorm1 = paddle1.vx * nx + paddle1.vy * ny
        dpNorm2 = paddle2.vx * nx + paddle2.vy * ny

        angle = math.atan2(paddle1.y - paddle2.y, paddle1.x - paddle2.x)
        if (paddle1.isGrabbed and paddle2.isGrabbed) or (not paddle1.isGrabbed and not paddle2.isGrabbed):
            # Swap normal velocities
            paddle1.vx = tx * dpTan1 + nx * dpNorm2
            paddle1.vy = ty * dpTan1 + ny * dpNorm2
            paddle2.vx = tx * dpTan2 + nx * dpNorm1
            paddle2.vy = ty * dpTan2 + ny * dpNorm1
            
            # make both players drop their paddle if they collide
            paddle1.isGrabbed = False
            paddle2.isGrabbed = False
        elif paddle1.isGrabbed and not paddle2.isGrabbed:
            paddle2.vx += paddle1.curSpeed * -math.cos(angle) * 0.9
            paddle2.vy += paddle1.curSpeed * -math.sin(angle) * 0.9
        elif paddle2.isGrabbed and not paddle1.isGrabbed:
            paddle1.vx += paddle2.curSpeed * math.cos(angle) * 0.9
            paddle1.vy += paddle2.curSpeed * math.sin(angle) * 0.9

        # prevent sticking together
        overlap = paddle1.radius * 2 - dist
        if overlap < 0:
            separation = (overlap / 2) + 0.5
            paddle1.x -= nx * separation 
            paddle1.y -= ny * separation 
            paddle2.x += nx * separation 
            paddle2.y += ny * separation 
        return paddle1, paddle2
    return None


puckCollisionSound = pygame.mixer.Sound(os.path.join(client_dir, "./sounds/puck-sound.wav"))
paddleCollisionSound = pygame.mixer.Sound(os.path.join(client_dir, "./sounds/paddle-sound.wav"))
goalHornSoundEffect = pygame.mixer.Sound(os.path.join(client_dir, "./sounds/goalhorn.mp3"))

font = pygame.font.SysFont(pygame.font.get_default_font(), 40)
txtsurface = font.render("0:0", True, (255, 255, 255))


class Game:
    def __init__(self):
        self.paddles = []
        self.paddle_ids = {}
        self.puck = Puck()

        self.mousedown = False
        self.curPaddle = None
        self.running = True

        self.rightScore = 0
        self.rightGoal = Goal("right")
        self.leftScore = 0
        self.leftGoal = Goal("left")
        self.gameStateBuffer = deque(maxlen=1000)
        self.isListeningForGameState = False

        self.lastPacketSent = -float('inf')
        self.packetDelta = 1000 / 30

    def listenForGameState(self):

        while game_running:

            try:

                if server_socket is None:
                    break

                game_states = server_socket.recv(2048).decode("utf-8").split('}{')
                
                # If more than 1 JSON object was received
                if len(game_states) > 1:
                    for i in range(len(game_states)-1):
                        game_states[i] += '}'

                    game_states[-1] = '{' + game_states[-1]


                # Only the most current state of the game is saved
                # game_state = json.loads(game_state)
                for game_state in game_states:
                    # print(game_state)
                    game_state = json.loads(game_state)
                    action = game_state.get('action')
                    if action == "state_update" or action == 'grab_ack':

                        with buffer_lock:

                            if len(self.gameStateBuffer) > 0:

                                self.gameStateBuffer.popleft()

                            self.gameStateBuffer.append(game_state)

                        

            except (BrokenPipeError, OSError):
                return
            except Exception as e:
                if not game_running:
                    break

        pygame.font.init()
        pygame.mixer.init()

    def run(self):
        global pause_menu_active, game_running, main_menu, pause_menu, join_match_menu, server_socket

        # Init Menus
        pause_menu = PauseMenu()
        main_menu = MainMenu()
        join_match_menu = JoinGameMenu()

        while self.running:

            if game_running:

                if not self.isListeningForGameState:
                    #self.paddles.append(Paddle(100, HEIGHT // 2, (0, 0, 255), paddle_id))

                    threading.Thread(target=self.listenForGameState, daemon=False).start()
                    self.isListeningForGameState = True

                if pause_menu_active:

                    pause_menu.show()

                with buffer_lock:

                    if len(self.gameStateBuffer) > 0:

                        new_state = self.gameStateBuffer.popleft()
                        game_state = new_state.get('game_state')
        
                        if game_state:
                            for paddle_id in game_state['paddles']:
                                if self.paddle_ids.get(paddle_id) is None:
                                    self.paddles.append(Paddle(100, HEIGHT // 2, (0, 0, 255), paddle_id))
                                    self.paddle_ids[paddle_id] = True
                                else:
                                    for paddle in self.paddles:
                                        # Update position on client side if they are not holding the paddle
                                        if paddle.paddleID == paddle_id:
                                            paddle_info = game_state['paddles'][paddle_id]
                                            if not (self.curPaddle and self.curPaddle.paddleID == paddle_id):
                                                paddle.x, paddle.y = tuple(paddle_info.get('position'))
                                                paddle.vx, paddle.vy = tuple(paddle_info.get('velocity'))
                                                paddle.isGrabbed = paddle_info.get('isGrabbed')

                            puck_info = game_state.get('puck')
                            if puck_info:
                                self.puck.x, self.puck.y = tuple(puck_info['position'])
                                self.puck.vx, self.puck.vy = tuple(puck_info['velocity'])

                            score_info = game_state.get('score')
                            if score_info:
                                self.leftScore = score_info['left']
                                self.rightScore = score_info['right']

                        if new_state.get('action') == 'grab_ack':
                            if self.curPaddle and self.curPaddle.paddleID == new_state.get('paddle_id'):
                                if player_id != new_state.get('player'):
                                    self.curPaddle = None

                pygame.time.delay(30)  # Control game speed
                screen.fill(BLACK)
                txtsurface = font.render(f"{self.leftScore}:{self.rightScore}", False, (255, 255, 255))
                screen.blit(txtsurface, (WIDTH // 2 - txtsurface.get_width() // 2, 20 - txtsurface.get_height() // 2))
                txtsurface2 = font.render(f"Connected to {SERVER_IP}:{SERVER_PORT}", False, (255, 255, 255))
                screen.blit(txtsurface2, (WIDTH // 4 - txtsurface2.get_width() // 2, 20 - txtsurface2.get_height() // 2))

                collisions = []

                if self.mousedown and self.curPaddle:
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_CROSSHAIR)
                else:
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

                self.puck.move()
                for paddle in self.paddles:
                    checkCollisionPuckAndPaddle(paddle, self.puck)
                    paddle.draw(screen)
                    paddle.move()
                    if not self.curPaddle and paddle.mouseInRadius(paddle):
                        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                    if paddle not in collisions:
                        for paddle2 in self.paddles:
                            if paddle2 != paddle:
                                collisions.append(checkCollisionPaddleAndPaddle(paddle, paddle2))

                self.puck.draw(screen)
                self.leftGoal.draw()
                self.rightGoal.draw()

                if self.curPaddle:
                    # Send paddle information to server
                    packet = json.dumps({
                        "player_id": player_id,
                        "type": "Paddle",
                        "action": "update_position",
                        "id": self.curPaddle.paddleID,
                        "position": [self.curPaddle.x, self.curPaddle.y],
                        "velocity": [self.curPaddle.vx, self.curPaddle.vy]
                    })

                    curTime = time.clock_gettime(time.CLOCK_MONOTONIC)
                    delta = (curTime - self.lastPacketSent) * 1000
                    if delta > self.packetDelta:
                        send_to_server(server_socket, str.encode(packet))
                        self.lastPacketSent = curTime

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        leave_match()
                        self.running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:
                            for paddle in self.paddles:
                                if paddle.mouseInRadius(paddle) and not paddle.isGrabbed:
                                    packet = json.dumps({
                                        "action": "grab_paddle",
                                        "player_id": player_id,
                                        "paddle_id": paddle.paddleID
                                    })
                                    
                                    send_to_server(server_socket, str.encode(packet))
                                    self.curPaddle = paddle
                                    self.curPaddle.isGrabbed = True
                                    break
                            self.mousedown = True
                    elif event.type == pygame.MOUSEBUTTONUP:
                        if event.button == 1:
                            if self.curPaddle:
                                packet = json.dumps({
                                    "action": "release_paddle",
                                    "player_id": player_id,
                                    "paddle_id": self.curPaddle.paddleID
                                })

                                send_to_server(server_socket, str.encode(packet))
                                self.curPaddle.isGrabbed = False
                                self.curPaddle = None
                            self.mousedown = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        pause_menu_active = True
            else:
                main_menu.show()

            pygame.display.update()

        pygame.quit()


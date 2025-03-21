# Example file showing a basic pygame "game loop"
import socket
import time
from time import sleep

import pygame
import pygame_menu
import threading
from server import server

HEIGHT = 720
WIDTH = 1280

SERVER_PORT = 55000
SERVER_IP = '127.0.0.1'

# pygame setup
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
running = True
pygame.font.init()
my_font = pygame.font.SysFont('Comic Sans MS', 30)

pause_menu_active = False
is_paused = False
game_running = False
player_name = ""
server_socket = None
game_session = None

def end_session():

    global game_session, server_socket

    # TODO: Implement graceful disconnection with the host user

    server_socket.close()

    if game_session:
        game_session.stop_server()


def resume_game():
    global is_paused, pause_menu_active
    pause_menu_active = False
    is_paused = False
    ingame_menu.disable()


def pause_menu_to_main_menu():
    global game_running, pause_menu_active
    game_running = False
    end_session()
    pause_menu_active = False
    ingame_menu.disable()
    main_menu.enable()


def join_menu_to_main_menu():
    server_port.reset_value()
    server_ip.reset_value()
    join_match_menu.disable()
    main_menu.enable()


def get_game_session():
    global game_session, server_socket
    # TODO: This function should return an instance of the game session

    try:
        if server_socket:

            server_socket.connect((SERVER_IP, SERVER_PORT))

    except ConnectionRefusedError:

        print("Connection refused")


def join_game():
    main_menu.disable()
    join_match_menu.enable()
    join_match_menu.mainloop(screen)


def join_the_game():
    global game_running, SERVER_IP, SERVER_PORT, server_socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    game_running = True
    SERVER_IP = server_ip.get_value()
    SERVER_PORT = server_port.get_value()
    get_game_session()
    join_match_menu.disable()


def start_the_game():
    global game_running, game_session, server_socket, SERVER_PORT, SERVER_IP

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    game_session = server.Server(2, SERVER_IP)

    # Run the server in a different thread
    threading.Thread(target=game_session.start_server, daemon=True).start()

    SERVER_PORT = game_session.get_port_num()

    if SERVER_PORT is None:

        print("Server port not available")
        game_session.stop_server()
        return

    player_connected = False

    # Loop until the server becomes active and ready to accept players or timeout
    for i in range(10):

        try:

            server_socket.connect((SERVER_IP, SERVER_PORT))
            player_connected = True
            break

        except (ConnectionRefusedError, BrokenPipeError):
            time.sleep(0.5)

    if player_connected:
        game_running = True
        main_menu.disable()
    else:
        print("Failed to connect to server (timeout)")
        game_session.stop_server()


def pause_menu():
    ingame_menu.enable()
    ingame_menu.mainloop(screen)


# Pause menu
ingame_menu = pygame_menu.Menu('Paused', 600, 400, theme=pygame_menu.themes.THEME_BLUE)
ingame_menu.add.button('Back to Main Menu', pause_menu_to_main_menu)
ingame_menu.add.button('Resume', resume_game)

#Main menu
main_menu = pygame_menu.Menu('2v2 Air Hockey', WIDTH, HEIGHT,
                             theme=pygame_menu.themes.THEME_BLUE)
name_box = main_menu.add.text_input('Player Name :', '')
main_menu.add.button('Start Match', start_the_game)
main_menu.add.button('Join A Server', join_game)
main_menu.add.button('Quit', pygame_menu.events.EXIT)

#Match join menu
join_match_menu = pygame_menu.Menu('Join Match', WIDTH, HEIGHT, )
server_port = join_match_menu.add.text_input('Server IP :', '')
server_ip = join_match_menu.add.text_input('Server Port :', '')
join_match_menu.add.button('Join Match', join_the_game)
join_match_menu.add.button('Return to Main Menu', join_menu_to_main_menu)
error_label = join_match_menu.add.label("")

while running:

    if game_running:

        if pause_menu_active:
            pause_menu()

        player_name = name_box.get_value()

        # TODO: Add game logic here

        screen.fill("purple")

        # Display player's name
        text_surface = my_font.render(player_name, False, (0, 0, 0))
        screen.blit(text_surface, (10, 10))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                end_session()
                running = False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pause_menu_active = True

        pygame.display.flip()

        clock.tick(60)  # limits FPS to 60

    else:

        main_menu.mainloop(screen)

pygame.quit()

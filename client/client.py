# Example file showing a basic pygame "game loop"
import pygame
import pygame_menu
import threading

HEIGHT = 720
WIDTH = 1280

SERVER_PORT = 0
SERVER_IP = ''

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


def resume_game():
    global is_paused, pause_menu_active
    pause_menu_active = False
    is_paused = False
    ingame_menu.disable()


def pause_menu_to_main_menu():
    global game_running, pause_menu_active
    game_running = False

    pause_menu_active = False
    ingame_menu.disable()
    main_menu.enable()


def join_menu_to_main_menu():
    server_port.reset_value()
    server_ip.reset_value()
    join_match_menu.disable()
    main_menu.enable()


def get_game_session(port, IP):
    # TODO: This function should return an instance of the game session
    # TODO: The player is either joining a current game session or starting a new one
    # TODO: If the player is starting a new session, then this should return the new session
    pass


def join_game():
    main_menu.disable()
    join_match_menu.enable()
    join_match_menu.mainloop(screen)

    SERVER_IP = server_ip.get_value()
    SERVER_PORT = server_port.get_value()

    print(SERVER_IP)
    print(SERVER_PORT)
    print("Joining game")


def start_the_game():
    global game_running
    game_running = True
    main_menu.disable()


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
join_match_menu.add.button('Join Match', start_the_game)
join_match_menu.add.button('Return to Main Menu', join_menu_to_main_menu)
error_label = join_match_menu.add.label("")

while running:

    if game_running:

        if pause_menu_active:
            pause_menu()

        player_name = name_box.get_value()

        screen.fill("purple")

        # TODO: Add game logic here

        # Display player's name
        text_surface = my_font.render(player_name, False, (0, 0, 0))
        screen.blit(text_surface, (10, 10))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pause_menu_active = True

        pygame.display.flip()

        clock.tick(60)  # limits FPS to 60

    else:

        main_menu.mainloop(screen)

pygame.quit()

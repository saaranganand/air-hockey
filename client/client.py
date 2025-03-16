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
game_running = False
player_name = ""


def resume_game():
    global pause_menu_active
    pause_menu_active = False
    ingame_menu.disable()


def quit_to_main_menu():
    global game_running, pause_menu_active
    game_running = False
    pause_menu_active = False  # Return to main menu
    ingame_menu.disable()
    main_menu.enable()


def get_game_session(port, host):
    # TODO: This function should return an instance of the game session
    pass


def join_game():
    # TODO: Add prompt for server code
    print("Joining game")


def start_the_game():
    global game_running
    global pause_menu_active
    game_running = True
    pause_menu_active = False
    main_menu.disable()


# Pause menu
ingame_menu = pygame_menu.Menu('Game', 600, 400, theme=pygame_menu.themes.THEME_BLUE)
ingame_menu.add.button('Back to Main Menu', quit_to_main_menu)
ingame_menu.add.button('Resume', resume_game)

#Main menu
main_menu = pygame_menu.Menu('2v2 Air Hockey', WIDTH, HEIGHT,
                             theme=pygame_menu.themes.THEME_BLUE)
name_box = main_menu.add.text_input('Player Name :', '')
main_menu.add.button('Start Match', start_the_game)
main_menu.add.button('Join Game', join_game)
main_menu.add.button('Quit', pygame_menu.events.EXIT)

while running:

    if game_running:

        if pause_menu_active:
            # TODO: Since this is a multiplayer game, this should be placed in a new thread such that the entire game can run async
            ingame_menu.enable()
            ingame_menu.mainloop(screen)

        else:

            player_name = name_box.get_value()

            screen.fill("purple")

            # TODO: Add game logic here

            # Displays player's name
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
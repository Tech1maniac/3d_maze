import getopt
import sys

import glm
import pygame
import pygame.display
from world import World

# Screen resolution and fixed FPS
RESOLUTION = 1024, 720
FPS = 60
LEVEL = 1


def game_loop(world):
    clock = pygame.time.Clock()
    world.sound.play_sound('start')
    world.sound.play_music()

    while True:
        # Cap the frame rate and get milliseconds since last frame
        ms = clock.tick(FPS)
        # Convert to seconds for your delta
        world.delta = ms / 1000.0

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYDOWN and event.key == pygame.locals.K_ESCAPE:
                return

        # Update all systems and render
        world.process()


def main():
    pygame.init()
    pygame.display.init()
    pygame.display.set_mode(RESOLUTION, pygame.DOUBLEBUF | pygame.OPENGL)
    pygame.display.set_caption("3DMaze-Packman")
    pygame.mouse.set_visible(False)

    # Create and run the world
    world = World(glm.vec2(RESOLUTION), LEVEL)
    game_loop(world)
    world.cleanup()


def get_level_from_cmd(argv):
    level = 0
    try:
        opts, args = getopt.getopt(argv, "l:", ["level="])
    except getopt.GetoptError:
        print('main.py --level <level>\nor \nmain.py -l <level>')
        sys.exit(2)
    for opt, arg in opts:
        if opt not in ("-l", "--level"):
            print('main.py --level <level>\nor \nmain.py -l <level>')
            sys.exit()
        elif opt in ("-l", "--level"):
            try:
                level = int(arg)
            except ValueError:
                print('Level argument must be an integer!')
                sys.exit()
    return level


def choose_level(argv):
    global LEVEL
    got_arg = False
    level = get_level_from_cmd(argv)
    if 3 >= level > 0:
        LEVEL = level
        got_arg = True
    elif not got_arg and (level < 0 or level > 3):
        print('The --level argument should be either 1, 2 or 3')
        sys.exit()
    if not got_arg:
        print('Please choose a level!')
        print('Choose:\n\t1 for Beginner (Noob)\n\t2 for Intermediate\n\t3 for Pro\n\n')
        while True:
            show = False
            val = 0
            try:
                val = int(input('Enter your choice: '))
            except ValueError:
                print('You should choose a number between 1, 2 or 3 inclusive!')
                show = False
            if 3 >= val > 0:
                LEVEL = val
                if val == 3:
                    print('Excellent choice!')
                break
            if val < 0 or val > 3:
                show = True
            if show:
                print('You should choose either 1, 2 or 3!')


if __name__ == '__main__':
    choose_level(sys.argv[1:])
    print('\nPress Escape to quit!\n')
    main()
    pygame.quit()
    print('You quit the game!')
1
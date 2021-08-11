import pygame
from pygame import display, event, time
from pygame.constants import QUIT

from wad.reader import read_wad_info_table

from bsp.bsp_map import init_bsp_map

WAD_PATH = 'wads/DOOM.WAD'
WINDOW_DIMS = WINDOW_WIDTH, WINDOW_HEIGHT = 640, 480

def main():
    pygame.init()
    screen = display.set_mode(WINDOW_DIMS)
    clock = time.Clock()

    info_table = read_wad_info_table(WAD_PATH)
    init_bsp_map(WAD_PATH, info_table, 'E1M1')

    running = True
    while running:
        for e in event.get():
            if e.type == QUIT:
                running = False
    
        screen.fill('white')
        display.update()
        clock.tick(60)
        display.set_caption('doom-py %0.1f fps' % clock.get_fps())

    pygame.quit()

if __name__ == '__main__':
    main()
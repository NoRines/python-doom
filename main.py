import pygame
from pygame import display, event, time, key, transform
from pygame.constants import KEYDOWN, K_ESCAPE, K_SPACE, QUIT

from wad.reader import read_things, read_wad_info_table

from bsp.bsp_map import init_bsp_map, render_player_view

import math

from entities.player import Player


WAD_PATH = 'wads/DOOM.WAD'
WINDOW_DIMS = RES_WIDTH, HEIGHT_RES = 640, 480

def main():
    pygame.init()
    screen = display.set_mode(WINDOW_DIMS)
    clock = time.Clock()

    info_table = read_wad_info_table(WAD_PATH)
    init_bsp_map(WAD_PATH, info_table, 'E1M1')

    things = read_things(WAD_PATH, *info_table['E1M1']['THINGS'])
    player_thing = list(filter(lambda x: x.thing_type == 1, things))[0]

    player = Player(player_thing.position, math.radians(player_thing.angle), 90, 20)

    one_seg_mode = False

    seg_index = 375
    running = True
    while running:
        for e in event.get():
            if e.type == QUIT:
                running = False
            if e.type == KEYDOWN:
                if e.key == K_SPACE:
                    seg_index += 1
                    print(seg_index)
                if e.key == K_ESCAPE:
                    one_seg_mode = True

        player.update(key.get_pressed())
    
        screen.fill('white', (0,0,640,400))
        render_list = render_player_view(player)
        for pos, ss in render_list:
            screen.blit(transform.scale2x(ss), (pos[0]*2, pos[1]*2))
        display.update()
        clock.tick(60)
        display.set_caption('doom-py %0.1f fps' % clock.get_fps())

    pygame.quit()

if __name__ == '__main__':
    main()
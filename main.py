import pygame
from pygame import display, event, time, transform
from pygame.constants import QUIT

from wad.reader import read_patch_names, read_wad_info_table, read_playpal, read_patch, read_textures

from bsp.bsp_map import init_bsp_map

WAD_PATH = 'wads/DOOM.WAD'
WINDOW_DIMS = WINDOW_WIDTH, WINDOW_HEIGHT = 640, 480



def main():
    pygame.init()
    screen = display.set_mode(WINDOW_DIMS)
    clock = time.Clock()

    info_table = read_wad_info_table(WAD_PATH)
    playpal = read_playpal(WAD_PATH, *info_table['PLAYPAL'])

    init_bsp_map(WAD_PATH, info_table, 'E1M1')

    current_color_palette = playpal[0]

    weapon_patch = read_patch(WAD_PATH, *info_table['SPRITE']['PISGA0'])

    #weapon_surf = patch_to_surface(weapon_patch, current_color_palette)
    #weapon_surf = transform.scale2x(weapon_surf)
    #weapon_rect = weapon_surf.get_rect(
    #    bottom=WINDOW_HEIGHT,
    #    centerx=WINDOW_WIDTH//2)

    running = True
    while running:
        for e in event.get():
            if e.type == QUIT:
                running = False
    
        screen.fill('white')
        #screen.blit(weapon_surf, weapon_rect)
        display.update()
        clock.tick(60)
        display.set_caption('doom-py %0.1f fps' % clock.get_fps())

    pygame.quit()

if __name__ == '__main__':
    main()
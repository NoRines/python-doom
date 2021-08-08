from os import read
from typing import List, Tuple
import pygame
from pygame import PixelArray, Surface, display, event, time, transform
from pygame.constants import QUIT

from wad.d_types import Patch
from wad.reader import read_wad_info_table, read_playpal, read_patch, Palette

def patch_to_surface(patch : Patch, palette : Palette) -> Surface:
    surf = Surface((patch.width, patch.height)).convert_alpha()
    surf.fill((0, 0, 0, 0))
    pixarr = PixelArray(surf)
    x_index = 0
    for column in patch.columns:
        if column.top_delta == 0xff:
            x_index += 1
            continue
        for y_index in range(column.length):
            pixarr[x_index, y_index + column.top_delta] = palette[column.data[y_index]]
    return surf

def main():
    w, h = 640, 480

    pygame.init()
    screen = display.set_mode((w,h))
    clock = time.Clock()

    wad_path = 'wads/DOOM.WAD'
    info_table = read_wad_info_table(wad_path)
    playpal = read_playpal(wad_path, *info_table['PLAYPAL'])

    current_color_palette = playpal[0]

    weapon_patch = read_patch(wad_path, *info_table['SPRITE']['PISGA0'])

    weapon_surf = patch_to_surface(weapon_patch, current_color_palette)
    weapon_surf = transform.scale2x(weapon_surf)
    weapon_rect = weapon_surf.get_rect(bottom=h, centerx=w//2)

    running = True
    while running:
        for e in event.get():
            if e.type == QUIT:
                running = False
    
        screen.fill('white')
        screen.blit(weapon_surf, weapon_rect)
        display.update()
        clock.tick(60)
        display.set_caption('doom-py %0.1f fps' % clock.get_fps())

    pygame.quit()

if __name__ == '__main__':
    main()
from typing import Dict, List, Optional, Tuple

import pygame
from pygame import PixelArray, Surface, display, event, time, transform
from pygame.constants import QUIT

from wad.d_types import Patch, WadTexture
from wad.reader import read_patch_names, read_wad_info_table, read_playpal, read_patch, read_textures, Palette


WAD_PATH = 'wads/DOOM.WAD'
WINDOW_DIMS = WINDOW_WIDTH, WINDOW_HEIGHT = 640, 480

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

def compose_texture(wad_tex : WadTexture, patch_surfaces : List[Surface]):
    texture_surface = Surface((wad_tex.width, wad_tex.height)).convert_alpha()
    texture_surface.fill((0, 0, 0, 0))
    for layout in wad_tex.layouts:
        texture_surface.blit(patch_surfaces[layout.p_number], (layout.orginx, layout.orginy))
    return texture_surface

def main():
    pygame.init()
    screen = display.set_mode(WINDOW_DIMS)
    clock = time.Clock()

    info_table = read_wad_info_table(WAD_PATH)
    playpal = read_playpal(WAD_PATH, *info_table['PLAYPAL'])
    tex_dict = read_textures(WAD_PATH, *info_table['TEXTURE1'])
    patch_names = read_patch_names(WAD_PATH, *info_table['PNAMES'])

    current_color_palette = playpal[0]

    weapon_patch = read_patch(WAD_PATH, *info_table['SPRITE']['PISGA0'])

    weapon_surf = patch_to_surface(weapon_patch, current_color_palette)
    weapon_surf = transform.scale2x(weapon_surf)
    weapon_rect = weapon_surf.get_rect(
        bottom=WINDOW_HEIGHT,
        centerx=WINDOW_WIDTH//2)

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
from typing import Dict, List, Optional, Tuple

import pygame
from pygame import PixelArray, Surface, display, event, time, transform
from pygame.constants import QUIT

from wad.d_types import Patch, WadTexture
from wad.reader import read_patch_names, read_wad_info_table, read_playpal, read_patch, read_textures, Palette


WAD_PATH = 'wads/DOOM.WAD'


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

class WallTextureManager:
    _patch_names : List[str]
    _patch_list : List[Surface]
    _tex_dict : Dict[str, Surface]

    def __init__(self, patch_names : List[str]):
        self._patch_names = patch_names
        self._patch_list = []
        self._tex_dict = {}

    def read_patches(self, patch_table : Dict[str, Tuple[int, int]], palette : Palette):
        self._patch_list = [patch_to_surface(
            read_patch(WAD_PATH, *patch_table[name]), palette)
            for name in self._patch_names]
    
    def read_textures(self, tex_dict : Dict[str, WadTexture]):
        self._tex_dict = {
            name : compose_texture(wad_tex, self._patch_list)
            for name, wad_tex in tex_dict.items() }

    def __getitem__(self, name : str) -> Optional[Surface]:
        if name in self._tex_dict:
            return self._tex_dict[name]
        return None

def main():
    w, h = 640, 480

    pygame.init()
    screen = display.set_mode((w,h))
    clock = time.Clock()

    info_table = read_wad_info_table(WAD_PATH)
    playpal = read_playpal(WAD_PATH, *info_table['PLAYPAL'])
    tex_dict = read_textures(WAD_PATH, *info_table['TEXTURE1'])
    patch_names = read_patch_names(WAD_PATH, *info_table['PNAMES'])

    current_color_palette = playpal[0]

    am = WallTextureManager(patch_names)
    am.read_patches(info_table['PATCH'], current_color_palette)
    am.read_textures(tex_dict)

    weapon_patch = read_patch(WAD_PATH, *info_table['SPRITE']['PISGA0'])

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
        screen.blit(am['SW1DIRT'], (0,0))
        display.update()
        clock.tick(60)
        display.set_caption('doom-py %0.1f fps' % clock.get_fps())

    pygame.quit()

if __name__ == '__main__':
    main()
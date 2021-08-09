from typing import List

import pygame
from pygame import PixelArray, Surface, display, event, time, transform
from pygame.constants import QUIT

from wad.d_types import Patch, WadTexture
from wad.reader import read_patch_names, read_wad_info_table, read_playpal, read_patch, read_textures, Palette

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
    print(wad_tex.n_patches)
    for layout in wad_tex.layouts:
        texture_surface.blit(patch_surfaces[layout.p_number], (layout.orginx, layout.orginy))
    return texture_surface

def main():
    w, h = 640, 480

    pygame.init()
    screen = display.set_mode((w,h))
    clock = time.Clock()

    wad_path = 'wads/DOOM.WAD'
    info_table = read_wad_info_table(wad_path)
    playpal = read_playpal(wad_path, *info_table['PLAYPAL'])
    tex_dict = read_textures(wad_path, *info_table['TEXTURE1'])
    patch_names = read_patch_names(wad_path, *info_table['PNAMES'])

    current_color_palette = playpal[0]

    patch_surfaces = [patch_to_surface(read_patch(wad_path, *info_table['PATCH'][name.upper()]), current_color_palette) for name in patch_names]


    #test_texture = compose_texture(tex_dict['AASTINKY'], patch_surfaces)
    #test_texture = compose_texture(tex_dict['BROWN1'], patch_surfaces)
    #test_texture = compose_texture(tex_dict['BROWNPIP'], patch_surfaces)
    #test_texture = compose_texture(tex_dict['BROWN144'], patch_surfaces)
    #test_texture = compose_texture(tex_dict['BIGDOOR1'], patch_surfaces)
    #test_texture = compose_texture(tex_dict['BIGDOOR2'], patch_surfaces)
    #test_texture = compose_texture(tex_dict['BIGDOOR4'], patch_surfaces)
    #test_texture = compose_texture(tex_dict['COMP2'], patch_surfaces)
    test_texture = compose_texture(tex_dict['BRNSMAL1'], patch_surfaces)
    #test_texture = compose_texture(tex_dict['BRNBIGC'], patch_surfaces)
    #test_texture = compose_texture(tex_dict['BRNPOIS'], patch_surfaces)
    #test_texture = compose_texture(tex_dict['BRNPOIS2'], patch_surfaces)
    #test_texture = compose_texture(tex_dict['EXITDOOR'], patch_surfaces)
    #test_texture = compose_texture(tex_dict['SKY1'], patch_surfaces)
    #test_texture = compose_texture(tex_dict['TEKWALL5'], patch_surfaces)
    #test_texture = compose_texture(tex_dict['SW1DIRT'], patch_surfaces)

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
        screen.blit(test_texture, (0,0))
        display.update()
        clock.tick(60)
        display.set_caption('doom-py %0.1f fps' % clock.get_fps())

    pygame.quit()

if __name__ == '__main__':
    main()
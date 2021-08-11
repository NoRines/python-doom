from typing import Dict, List

from pygame import Vector2, Surface

from wad.d_types import ColorPalette, LineDef, SideDef, Seg, SubSector, \
    Node, Sector, WadTexture

from wad.reader import read_patch, \
    read_patch_names, read_playpal, read_textures
from wad.reader import read_linedefs, read_vertexes, \
    read_sidedefs, read_segs, read_ssectors, read_nodes, \
    read_sectors

from utils.pic_utils import patch_to_surface

linedefs : List[LineDef]   = []
vertexes : List[Vector2]   = []
sidedefs : List[SideDef]   = []
segs     : List[Seg]       = []
ssectors : List[SubSector] = []
nodes    : List[Node]      = []
sectors  : List[Sector]    = []

wall_textures : Dict[str, Surface] = {}


def _add_linedefs_to_sector(sector : Sector, sector_id : int):
    for i, linedef in enumerate(linedefs):
        front_sidedef = linedef.front_sidedef
        back_sidedef = linedef.back_sidedef
        if (front_sidedef != -1 and sidedefs[front_sidedef].sector == sector_id) or \
           (back_sidedef != -1 and sidedefs[back_sidedef].sector == sector_id):
           sector.lines.append(i)

def _load_map_data(wad_path : str, info_table : Dict, map_name : str):
    global linedefs, vertexes, sidedefs, segs, ssectors, nodes, sectors

    linedefs = read_linedefs(wad_path, *info_table[map_name]['LINEDEFS'])
    vertexes = read_vertexes(wad_path, *info_table[map_name]['VERTEXES'])
    sidedefs = read_sidedefs(wad_path, *info_table[map_name]['SIDEDEFS'])
    segs     =     read_segs(wad_path, *info_table[map_name]['SEGS'])
    ssectors = read_ssectors(wad_path, *info_table[map_name]['SSECTORS'])
    nodes    =    read_nodes(wad_path, *info_table[map_name]['NODES'])
    sectors  =  read_sectors(wad_path, *info_table[map_name]['SECTORS'])

    for i, sector in enumerate(sectors):
        _add_linedefs_to_sector(sector, i)

def _create_texture_from_patches(
        wad_path : str,
        info_table : Dict,
        wad_tex : WadTexture,
        p_names : List[str],
        p_dict : Dict[str, Surface],
        color_palette : ColorPalette) -> Surface:

    surface = Surface((wad_tex.width, wad_tex.height)).convert_alpha()
    surface.fill((0, 0, 0, 0))

    for layout in wad_tex.layouts:
        p_name = p_names[layout.p_number]
        if p_name not in p_dict:
            p_dict[p_name] = patch_to_surface(
                read_patch(wad_path, *info_table['PATCH'][p_name]),
                color_palette)
        surface.blit(p_dict[p_name], (layout.orginx, layout.orginy))

    return surface

def _load_texture_data(wad_path : str, info_table : Dict, map_name : str):
    global wall_textures

    color_palette = read_playpal(wad_path, *info_table['PLAYPAL'])[0]
    p_names = read_patch_names(wad_path, *info_table['PNAMES'])
    p_dict : Dict[str, Surface] = {}

    wtex_dict = read_textures(wad_path, *info_table['TEXTURE1'])
    wtex_dict.update(read_textures(wad_path, *info_table['TEXTURE2']))

    def add_texture(t_name):
        if t_name not in wall_textures:
            wall_textures[t_name] = _create_texture_from_patches(
                wad_path, info_table, wtex_dict[t_name], p_names, p_dict,
                color_palette)

    for sidedef in sidedefs:
        if sidedef.lower_texture_name != '-':
            add_texture(sidedef.lower_texture_name)
        if sidedef.middle_texture_name != '-':
            add_texture(sidedef.middle_texture_name)
        if sidedef.upper_texture_name != '-':
            add_texture(sidedef.upper_texture_name)

def init_bsp_map(wad_path : str, info_table : Dict, map_name : str):
    _load_map_data(wad_path, info_table, map_name)
    _load_texture_data(wad_path, info_table, map_name)
import re
import math
from typing import Dict, List, Tuple
import os

from pygame import Rect
from pygame.math import Vector2

from wad.d_types import Thing, LineDef, SideDef, Seg, SubSector, Node, Sector, PatchColumn, Patch

def _bytes_to_int(b : bytes, signed=False) -> int:
    return int.from_bytes(b, 'little', signed=signed)

def _bytes_to_str(b : bytes) -> str:
    return b.decode('utf-8').rstrip('\x00')

def read_wad_info_table(wad_path : str):
    map_name_re = re.compile(r'E\dM\d')

    lump_info : Dict = {}
    with open(wad_path, 'rb') as f:
        id = _bytes_to_str(f.read(4))
        n_lumps = _bytes_to_int(f.read(4))
        info_table_ptr = _bytes_to_int(f.read(4))
        f.seek(info_table_ptr)

        current_map = ''
        map_component_names = ('THINGS', 'LINEDEFS', 'SIDEDEFS', 'VERTEXES', 'SEGS',
                               'SSECTORS', 'NODES', 'SECTORS', 'REJECT', 'BLOCKMAP',
                               'BEHAVIOUR')
        resource_type = None

        for _ in range(n_lumps):
            file_pos = _bytes_to_int(f.read(4))
            size = _bytes_to_int(f.read(4))
            name = _bytes_to_str(f.read(8))

            if name in ('F_END', 'S_END', 'P_END'):
                resource_type = None
                continue

            if resource_type is not None:
                lump_info[resource_type][name] = (file_pos, size)
            else:
                if map_name_re.match(name):
                    current_map = name
                    lump_info[name] = {}
                elif name in map_component_names:
                    lump_info[current_map][name] = (file_pos, size)
                elif name == 'F_START':
                    resource_type = 'FLAT'
                    lump_info[resource_type] = {}
                elif name == 'S_START':
                    resource_type = 'SPRITE'
                    lump_info[resource_type] = {}
                elif name == 'P_START':
                    resource_type = 'PATCH'
                    lump_info[resource_type] = {}
                else:
                    lump_info[name] = (file_pos, size)

    return lump_info

def read_things(wad_path : str, file_pos : int, size : int) -> List[Thing]:
    things : List[Thing] = []
    with open(wad_path, 'rb') as f:
        f.seek(file_pos)
        while size > 0:
            thing_bytes = f.read(10)
            size -= 10

            thing = Thing(
                position= Vector2(
                    float(_bytes_to_int(thing_bytes[0:2], signed=True)),
                    float(_bytes_to_int(thing_bytes[2:4], signed=True)),
                ),
                angle= _bytes_to_int(thing_bytes[4:6], signed=True),
                thing_type= _bytes_to_int(thing_bytes[6:8], signed=True),
                flags= _bytes_to_int(thing_bytes[8:10], signed=True),
            )
            things.append(thing)
    return things

def read_linedefs(wad_path : str, file_pos : int, size : int) -> List[LineDef]:
    linedefs : List[LineDef] = []
    with open(wad_path, 'rb') as f:
        f.seek(file_pos)
        while size > 0:
            linedef_bytes = f.read(14)
            size -= 14

            linedef = LineDef(
                start_vert =    _bytes_to_int(linedef_bytes[0:2],   signed=True),
                end_vert =      _bytes_to_int(linedef_bytes[2:4],   signed=True),
                flags =         _bytes_to_int(linedef_bytes[4:6],   signed=True),
                special_type =  _bytes_to_int(linedef_bytes[6:8],   signed=True),
                sector_tag =    _bytes_to_int(linedef_bytes[8:10],  signed=True),
                front_sidedef = _bytes_to_int(linedef_bytes[10:12], signed=True),
                back_sidedef =  _bytes_to_int(linedef_bytes[12:14], signed=True)
            )
            linedefs.append(linedef)
    return linedefs

def read_sidedefs(wad_path : str, file_pos : int, size : int) -> List[SideDef]:
    sidedefs : List[SideDef] = []
    with open(wad_path, 'rb') as f:
        f.seek(file_pos)
        while size > 0:
            sidedef_bytes = f.read(30)
            size -= 30

            sidedef = SideDef(
                x_offset=            _bytes_to_int(sidedef_bytes[0:2], signed=True),
                y_offset=            _bytes_to_int(sidedef_bytes[2:4], signed=True),
                upper_texture_name=  _bytes_to_str(sidedef_bytes[4:12]),
                lower_texture_name=  _bytes_to_str(sidedef_bytes[12:20]),
                middle_texture_name= _bytes_to_str(sidedef_bytes[20:28]),
                sector=              _bytes_to_int(sidedef_bytes[28:30], signed=True)
            )
            sidedefs.append(sidedef)
    return sidedefs

def read_vertexes(wad_path : str, file_pos : int, size : int) -> List[Vector2]:
    vertices : List[Vector2] = []
    with open(wad_path, 'rb') as f:
        f.seek(file_pos)
        while size > 0:
            vertex_bytes = f.read(4)
            size -= 2

            vertex = Vector2(
                float(_bytes_to_int(vertex_bytes[0:2], signed=True)),
                float(_bytes_to_int(vertex_bytes[2:4], signed=True))
            )
            vertices.append(vertex)
    return vertices


def read_segs(wad_path : str, file_pos : int, size : int) -> List[Seg]:
    int_to_angle = lambda i: (i / 65535) * 2 * math.pi
    segs : List[Seg] = []
    with open(wad_path, 'rb') as f:
        f.seek(file_pos)
        while size > 0:
            seg_bytes = f.read(12)
            size -= 12

            seg = Seg(
                start_vert= _bytes_to_int(seg_bytes[0:2],   signed=True),
                end_vert=   _bytes_to_int(seg_bytes[2:4],   signed=True),
                angle=      int_to_angle(_bytes_to_int(seg_bytes[4:6], signed=True)),
                linedef=    _bytes_to_int(seg_bytes[6:8],   signed=True),
                direction=  _bytes_to_int(seg_bytes[8:10],  signed=True),
                offset=     _bytes_to_int(seg_bytes[10:12], signed=True),
            )
            segs.append(seg)
    return segs

def read_ssectors(wad_path : str, file_pos : int, size : int) -> List[SubSector]:
    ssectors : List[SubSector] = []
    with open(wad_path, 'rb') as f:
        f.seek(file_pos)
        while size > 0:
            ssector_bytes = f.read(4)
            size -= 4

            ssector = SubSector(
                n_segs=    _bytes_to_int(ssector_bytes[0:2]),
                start_seg= _bytes_to_int(ssector_bytes[2:4])
            )
            ssectors.append(ssector)
    return ssectors

def read_nodes(wad_path : str, file_pos : int, size : int) -> List[Node]:
    nodes : List[Node] = []
    with open(wad_path, 'rb') as f:
        f.seek(file_pos)
        while size > 0:
            node_bytes = f.read(28)
            size -= 28

            right_top =    float(_bytes_to_int(node_bytes[8:10], signed=True))
            right_bottom = float(_bytes_to_int(node_bytes[10:12], signed=True))
            right_left =   float(_bytes_to_int(node_bytes[12:14], signed=True))
            right_right =  float(_bytes_to_int(node_bytes[14:16], signed=True))

            left_top =    float(_bytes_to_int(node_bytes[16:18], signed=True))
            left_bottom = float(_bytes_to_int(node_bytes[18:20], signed=True))
            left_left =   float(_bytes_to_int(node_bytes[20:22], signed=True))
            left_right =  float(_bytes_to_int(node_bytes[22:24], signed=True))

            node = Node(
                part_line_start= Vector2(
                    float(_bytes_to_int(node_bytes[0:2], signed=True)),
                    float(_bytes_to_int(node_bytes[2:4], signed=True))
                ),
                part_line_dir= Vector2(
                    float(_bytes_to_int(node_bytes[4:6], signed=True)),
                    float(_bytes_to_int(node_bytes[6:8], signed=True))
                ),
                right_bbox= Rect(
                    right_left, right_bottom, right_right - right_left, right_top - right_bottom
                ),
                left_bbox= Rect(
                    left_left, left_bottom, left_right - left_left, left_top - left_bottom
                ),
                right_child= _bytes_to_int(node_bytes[24:26]),
                left_child=  _bytes_to_int(node_bytes[26:28])
            )
            nodes.append(node)
    return nodes

def read_sectors(wad_path : str, file_pos : int, size : int) -> List[Sector]:
    sectors : List[Sector] = []
    with open(wad_path, 'rb') as f:
        f.seek(file_pos)
        while size > 0:
            sector_bytes = f.read(26)
            size -= 26

            sector = Sector(
                floor_height=         _bytes_to_int(sector_bytes[0:2], signed=True),
                ceiling_height=       _bytes_to_int(sector_bytes[2:4], signed=True),
                floor_texture_name=   _bytes_to_str(sector_bytes[4:12]),
                ceiling_texture_name= _bytes_to_str(sector_bytes[12:20]),
                light_level=          _bytes_to_int(sector_bytes[20:22], signed=True),
                special_type=         _bytes_to_int(sector_bytes[22:24], signed=True),
                tag_number=           _bytes_to_int(sector_bytes[24:26], signed=True),
                lines=                []
            )
            sectors.append(sector)
    return sectors

def add_linedefs_to_sector(sector : Sector, sector_id : int, linedefs : List[LineDef], sidedefs : List[SideDef]):
    for i, linedef in enumerate(linedefs):
        front_sidedef = linedef.front_sidedef
        back_sidedef = linedef.back_sidedef
        if (front_sidedef != -1 and sidedefs[front_sidedef].sector == sector_id) or \
           (back_sidedef != -1 and sidedefs[back_sidedef].sector == sector_id):
           sector.lines.append(i)

Color = Tuple[int, int, int, int]
Palette = List[Color]
def read_playpal(wad_path : str, file_pos : int, size : int) -> List[Palette]:
    n_bytes = 256 * 3
    palettes = []
    with open(wad_path, 'rb') as f:
        f.seek(file_pos)
        while size > 0:
            palette_bytes = f.read(n_bytes)
            size -= n_bytes

            palettes.append([])
            for i in range(0, n_bytes, 3):
                palettes[-1].append((int(palette_bytes[i + 0]), int(palette_bytes[i + 1]), int(palette_bytes[i + 2]), 255))
    return palettes

def read_patch(wad_path : str, file_pos : int, size : int) -> Patch:
    with open(wad_path, 'rb') as f:
        f.seek(file_pos)
        start_pos = f.tell()

        width = _bytes_to_int(f.read(2))
        height = _bytes_to_int(f.read(2))
        left_offset = _bytes_to_int(f.read(2), signed=True)
        top_offset = _bytes_to_int(f.read(2), signed=True)

        columnofs = [_bytes_to_int(f.read(4)) for _ in range(width)]

        patch = Patch(width, height, left_offset, top_offset, [])
        for offset in columnofs:
            f.seek(start_pos + offset)
            top_delta = 0
            while top_delta != 0xFF:
                top_delta = _bytes_to_int(f.read(1))
                length = _bytes_to_int(f.read(1))
                f.read(1)
                data = f.read(length)
                f.read(1)
                patch_col = PatchColumn(top_delta, length, data)
                patch.columns.append(patch_col)

        return patch
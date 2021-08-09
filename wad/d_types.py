from typing import NamedTuple, List
from pygame import Rect, Vector2

class Thing(NamedTuple):
    position : Vector2
    angle : int
    thing_type : int
    flags : int

class LineDef(NamedTuple):
    start_vert : int
    end_vert : int
    flags : int
    special_type : int
    sector_tag : int
    front_sidedef : int
    back_sidedef : int

class SideDef(NamedTuple):
    x_offset : int
    y_offset : int
    upper_texture_name : str
    lower_texture_name : str
    middle_texture_name : str
    sector : int

class Seg(NamedTuple):
    start_vert : int
    end_vert : int
    angle : float
    linedef : int
    direction : int
    offset : int

class SubSector(NamedTuple):
    n_segs : int
    start_seg : int

class Node(NamedTuple):
    part_line_start : Vector2
    part_line_dir : Vector2
    right_bbox : Rect
    left_bbox : Rect
    right_child : int
    left_child : int

class Sector(NamedTuple):
    floor_height : int
    ceiling_height : int
    floor_texture_name : str
    ceiling_texture_name : str
    light_level : int
    special_type : int
    tag_number : int
    lines : List[int]

    @property
    def linecount(self):
        return len(self.lines)


class PatchPost(NamedTuple):
    top_delta : int
    length : int
    data : bytes
    
class Patch(NamedTuple):
    width : int
    height : int
    left_offset : int
    top_offset : int
    columns : List[PatchPost]

class PatchLayout(NamedTuple):
    orginx : int
    orginy : int
    p_number : int

class WadTexture(NamedTuple):
    name : str
    width : int
    height : int
    n_patches : int
    layouts : List[PatchLayout]
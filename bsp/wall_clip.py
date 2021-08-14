import copy
from typing import NamedTuple, List, Optional
from dataclasses import dataclass
from pygame import Vector2

from utils.defs import RES_WIDTH

@dataclass
class ClipRange:
    first : int = 0
    last : int = 0

MAXSEGS = int((RES_WIDTH / 2) + 1)
n_solid_segs = 0
solid_segs : List[ClipRange] = [ClipRange() for _ in range(MAXSEGS)]

class ScreenCoords(NamedTuple):
    first_col : int
    last_col : int
    h_top_start : int
    h_top_end : int
    y_step_top : float
    h_bottom_start : int
    h_bottom_end : int
    y_step_bottom : float
    u_left : float
    u_right : float
    u_step : float
    one_over_z0 : float
    one_over_z1 : float
    one_over_z_step : float
    wall_height : int

def clear_clip_range():
    global n_solid_segs, solid_segs
    solid_segs[0] = ClipRange(-0x7fffffff, -1)
    solid_segs[1] = ClipRange(RES_WIDTH, 0x7fffffff)
    n_solid_segs = 2

def _update_screen_coords(sc:ScreenCoords, new_first_col:int, new_last_col:int) -> ScreenCoords:
    first_diff = new_first_col - sc.first_col
    last_diff = new_last_col - sc.last_col

    h_top_start = sc.h_top_start + first_diff * sc.y_step_top
    h_top_end = sc.h_top_end + last_diff * sc.y_step_top

    h_bottom_start = sc.h_bottom_start + first_diff * sc.y_step_bottom
    h_bottom_end = sc.h_bottom_end + last_diff * sc.y_step_bottom

    u_left = sc.u_left + first_diff * sc.u_step
    u_right = sc.u_right + last_diff * sc.u_step

    one_over_z0 = sc.one_over_z0 + first_diff * sc.one_over_z_step
    one_over_z1 = sc.one_over_z1 + last_diff * sc.one_over_z_step

    first_col = new_first_col
    last_col = new_last_col

    return ScreenCoords(
        first_col, last_col,
        h_top_start, h_top_end, sc.y_step_top,
        h_bottom_start, h_bottom_end, sc.y_step_bottom,
        u_left, u_right, sc.u_step,
        one_over_z0, one_over_z1, sc.one_over_z_step,
        sc.wall_height)

def clip_solid_wall(sc:ScreenCoords) -> List[ScreenCoords]:
    global n_solid_segs, solid_segs
    first, last = sc.first_col, sc.last_col
    res : List[ScreenCoords] = []

    i = 0
    while first-1 > solid_segs[i].last:
        i += 1

    if first < solid_segs[i].first:
        if last < solid_segs[i].first-1: # Entire Seg is visible
            res.append(_update_screen_coords(sc, first, last))
            next = n_solid_segs
            while next != i:
                solid_segs[next] = copy.deepcopy(solid_segs[next-1])
                next -= 1
            solid_segs[next].first = first
            solid_segs[next].last = last
            n_solid_segs += 1
            return res
        res.append(_update_screen_coords(sc, first, solid_segs[i].first))
        solid_segs[i].first = first
    
    if last <= solid_segs[i].last:
        return res
    
    next = i
    while last >= solid_segs[next+1].first-1:
        next += 1
        res.append(_update_screen_coords(sc, solid_segs[next-1].last, solid_segs[next].first))
        if last <= solid_segs[next].last:
            solid_segs[i].last = solid_segs[next].last
            while next != n_solid_segs:
                next += 1
                i += 1
                solid_segs[i] = copy.deepcopy(solid_segs[next])
            n_solid_segs = i + 1
            return res

    res.append(_update_screen_coords(sc, solid_segs[next].last, last))
    solid_segs[i].last = last

    if i == next:
        return res

    while next != n_solid_segs:
        next += 1
        i += 1
        solid_segs[i] = copy.deepcopy(solid_segs[next])
    n_solid_segs = i + 1 
    return res
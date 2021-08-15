import math
from typing import Dict, List, NamedTuple, Optional, Tuple

from pygame import Vector2, Surface, transform, Rect

from wad.d_types import ColorPalette, LineDef, SideDef, Seg, SubSector, \
    Node, Sector, WadTexture

from wad.reader import read_patch, \
    read_patch_names, read_playpal, read_textures
from wad.reader import read_linedefs, read_vertexes, \
    read_sidedefs, read_segs, read_ssectors, read_nodes, \
    read_sectors

from bsp.wall_clip import ScreenCoords, clear_clip_range, clip_solid_wall, clip_window_wall

from utils.pic_utils import patch_to_surface
from utils.math_utils import line_intersection

from entities.player import Player
from utils.defs import RES_WIDTH, RES_HEIGHT

WALL_HEIGHT_SCALE = 1.0

FOV : float = math.radians(90)
TAN_HALF_FOV = math.tan(FOV / 2)

VIEW_POS = Vector2(0,0)
VIEW_DIR = Vector2(1,0)
VIEW_LEFT_FRUST = VIEW_DIR.rotate_rad(-FOV / 2)
VIEW_RIGHT_FRUST = VIEW_DIR.rotate_rad(FOV / 2)
VIEW_LEFT_FRUST_NORM = Vector2(-VIEW_LEFT_FRUST.y, VIEW_LEFT_FRUST.x)
VIEW_RIGHT_FRUST_NORM = Vector2(VIEW_RIGHT_FRUST.y, -VIEW_RIGHT_FRUST.x)


linedefs : List[LineDef]   = []
vertexes : List[Vector2]   = []
sidedefs : List[SideDef]   = []
segs     : List[Seg]       = []
ssectors : List[SubSector] = []
nodes    : List[Node]      = []
sectors  : List[Sector]    = []

wall_textures : Dict[str, Surface] = {}

top_bound : List[int] = [0] * RES_WIDTH
bottom_bound : List[int] = [RES_HEIGHT] * RES_WIDTH

def _clear_floor_ceiling_bounds():
    global top_bound, bottom_bound
    top_bound = [0] * RES_WIDTH
    bottom_bound = [RES_HEIGHT] * RES_WIDTH

def _classify_point_to_view(pos : Vector2, dir : Vector2, left_norm : Vector2, right_norm : Vector2, p : Vector2) -> int:
    a = int((pos - p).dot(left_norm) < 0)
    b = int((pos - p).dot(right_norm) < 0) << 1
    c = int((pos - p).dot(dir) < 0) << 2
    return a | b | c

def _classify_edge_to_view(pos : Vector2, dir : Vector2, left_norm : Vector2, right_norm : Vector2, p0 : Vector2, p1 : Vector2) -> Tuple[int, int]:
    c0 = _classify_point_to_view(pos, dir, left_norm, right_norm, p0)
    c1 = _classify_point_to_view(pos, dir, left_norm, right_norm, p1)
    return c0, c1

def _test_edge_classification(pos : Vector2, dir : Vector2, p0 : Vector2, p1 : Vector2, c0 : int, c1 : int) -> bool:
    if c0 == 7 or c1 == 7:
        return True
    x_or = c0 ^ c1
    if x_or == 0:
        return False
    if x_or == 3 and c0 & 0b100:
        return True
    if x_or == 7:
        p = line_intersection(p0, p1, pos, pos + dir)
        dist = (p - pos).dot(dir)
        if dist > 0:
            return True
    return False


def _test_edge_to_view(pos : Vector2, dir : Vector2, left_norm : Vector2, right_norm : Vector2, p0 : Vector2, p1 : Vector2) -> bool:
    return _test_edge_classification(pos, dir, p0, p1, *_classify_edge_to_view(pos, dir, left_norm, right_norm, p0, p1))

def _boundingbox_intersects_view(pos : Vector2, dir : Vector2, left_norm : Vector2, right_norm : Vector2, bbox : Rect):
    if bbox.collidepoint(pos.x, pos.y):
        return True
    if _test_edge_to_view(pos, dir, left_norm, right_norm, Vector2(bbox.topleft), Vector2(bbox.topright)):
        return True
    if _test_edge_to_view(pos, dir, left_norm, right_norm, Vector2(bbox.topleft), Vector2(bbox.bottomleft)):
        return True
    if _test_edge_to_view(pos, dir, left_norm, right_norm, Vector2(bbox.bottomleft), Vector2(bbox.bottomright)):
        return True
    if _test_edge_to_view(pos, dir, left_norm, right_norm, Vector2(bbox.topright), Vector2(bbox.bottomright)):
        return True
    return False

def _on_right_side(pos : Vector2, node : Node) -> bool:
    normal = node.part_line_dir.rotate_rad(math.pi / 2).normalize()
    dist_to_line = (pos - node.part_line_start).dot(normal)
    if dist_to_line > 0:
        return False
    return True

def _clip_to_view(v0 : Vector2, v1 : Vector2, pos : Vector2, dir : Vector2, frust_left : Vector2, frust_right : Vector2, c0 : int, c1 : int) -> Tuple[Vector2, Vector2]:
    vs = Vector2(v0), Vector2(v1)
    cs = c0, c1
    if c0 == 7 or c1 == 7:
        in_p = 1 if c1 == 7 else 0
        if cs[in_p ^ 1] & 0b010:
            vs[in_p ^ 1].update(line_intersection(pos, pos + frust_left, *vs))
        elif cs[in_p ^ 1] & 0b001:
            vs[in_p ^ 1].update(line_intersection(pos, pos + frust_right, *vs))
        else:
            pl = line_intersection(pos, pos + frust_left, *vs)
            if (pos - pl).dot(dir) < 0:
                vs[in_p ^ 1].update(pl)
            else:
                vs[in_p ^ 1].update(line_intersection(pos, pos + frust_right, *vs))
    else:
        vs[0].update(line_intersection(pos, pos + frust_right, *vs))
        vs[1].update(line_intersection(pos, pos + frust_left, *vs))
    return vs

def _is_backface(p : Vector2, angle : float, pos : Vector2) -> bool:
    angle = angle + math.pi / 2
    seg_normal = Vector2(math.cos(angle), math.sin(angle))
    dist_vec = p - pos
    if dist_vec.length_squared() < 0.01:
        return True
    return (dist_vec.normalize()).dot(seg_normal) < 0


ScreenColumn = Tuple[Tuple[int, int], Surface]
SOLID_WALL = 0
UPPER_WALL = 1
LOWER_WALL = 2
MIDDLE_WALL = 3

def _screen_coord_to_screen_cols(sc:ScreenCoords, tex_name:str, sidedef_x:int, sidedef_y:int, wall_type:int) -> List[ScreenColumn]:
    global top_bound, bottom_bound

    texture = wall_textures.get(tex_name, None)
    render_list : List[ScreenColumn] = []

    y_top = sc.h_top_start
    y_bottom = sc.h_bottom_start
    u = sc.u_left
    one_over_z = sc.one_over_z0

    for i in range(sc.first_col, sc.last_col):
        top = max(int(y_top), top_bound[i])
        bottom = min(int(y_bottom), bottom_bound[i])
        col_height = int(y_bottom - y_top)

        if texture is not None and y_top < RES_HEIGHT and y_bottom >= 0 and col_height != 0 and bottom > top:
            y_offset = int(((top - int(y_top)) / col_height) * sc.wall_height)
            off_screen = int(((int(y_bottom) - bottom) / col_height) * sc.wall_height)
            tex_x = sidedef_x + int(u / one_over_z)

            if (texture.get_height() - sidedef_y) >= sc.wall_height:
                ss = texture.subsurface((tex_x % texture.get_width(), y_offset + sidedef_y, 1, sc.wall_height - (y_offset + off_screen)))
                ss = transform.scale(ss, (1, bottom - top))
                render_list.append(((i, top), ss))
            else:
                surf = Surface((1, sc.wall_height - (y_offset + off_screen))).convert_alpha()
                rect = (tex_x % texture.get_width(), (sidedef_y + y_offset), 1, texture.get_height() - (sidedef_y + y_offset))
                surf.blit(texture, (0,0), rect)
                y = (texture.get_height() - (sidedef_y + y_offset))
                pix_left = sc.wall_height - (texture.get_height() - (sidedef_y + y_offset))
                while pix_left > texture.get_height():
                    rect = (tex_x % texture.get_width(), 0, 1, texture.get_height())
                    surf.blit(texture, (0,y), rect)
                    y += texture.get_height()
                    pix_left -= texture.get_height()
                rect = (tex_x % texture.get_width(), 0, 1, pix_left - off_screen)
                surf.blit(texture, (0,y), rect)
                surf = transform.scale(surf, (1, bottom - top))
                render_list.append(((i, top), surf))
        if wall_type == SOLID_WALL:
            top_bound[i] = top
            bottom_bound[i] = bottom
        elif wall_type == UPPER_WALL:
            top_bound[i] = max(top, bottom)
        elif wall_type == LOWER_WALL:
            bottom_bound[i] = min(top, bottom)

        y_top += sc.y_step_top
        y_bottom += sc.y_step_bottom
        u += sc.u_step
        one_over_z += sc.one_over_z_step
    return render_list

def _seg_to_screen_coord(seg:Seg, linedef:LineDef, ceiling_h:int, floor_h:int, pos:Vector2, angle:float, eye_pos:int) -> Optional[ScreenCoords]:
    v0 = vertexes[seg.start_vert]
    v1 = vertexes[seg.end_vert]

    if _is_backface(v0, seg.angle, pos):
        return None

    linedef_len = (vertexes[linedef.end_vert] - vertexes[linedef.start_vert]).length()
    v0 = (v0 - pos).rotate_rad(-angle)
    v1 = (v1 - pos).rotate_rad(-angle)

    c0, c1 = _classify_edge_to_view(VIEW_POS, VIEW_DIR,
        VIEW_LEFT_FRUST_NORM, VIEW_RIGHT_FRUST_NORM, v0, v1)
    seg_in_view = _test_edge_classification(VIEW_POS, VIEW_DIR,
        v0, v1, c0, c1)

    if seg_in_view:
        u_left, u_right = 0.0, linedef_len
        if not (c0 == 7 and c1 == 7):
            tmp_v0, tmp_v1 = v0, v1
            v0, v1 = _clip_to_view(v0, v1, VIEW_POS, VIEW_DIR,
                VIEW_LEFT_FRUST, VIEW_RIGHT_FRUST, c0, c1)
            u_left = (tmp_v0 - v0).length()
            u_right = linedef_len - (tmp_v1 - v1).length()

        x_scale0 = v0.y / (TAN_HALF_FOV * -v0.x)
        x_scale1 = v1.y / (TAN_HALF_FOV * -v1.x)

        x_scale0, x_scale1 = min(x_scale0, x_scale1), max(x_scale0, x_scale1)
        first_col = int((max(-1.0, min(x_scale0, 1.0)) + 1.0) * (RES_WIDTH / 2))
        last_col = int((max(-1.0, min(x_scale1, 1.0)) + 1.0) * (RES_WIDTH / 2))

        if last_col == first_col:
            return None

        if x_scale0 > x_scale1:
            v0, v1 = v1, v0

        vfov = WALL_HEIGHT_SCALE * RES_HEIGHT
        y_scale0 = vfov / v0.x
        y_scale1 = vfov / v1.x

        half_height = RES_HEIGHT / 2
        h_top_start = int(half_height - y_scale0 * (ceiling_h - eye_pos))
        h_bottom_start = int(half_height - y_scale0 * (floor_h - eye_pos))
        h_top_end = int(half_height - y_scale1 * (ceiling_h - eye_pos))
        h_bottom_end = int(half_height - y_scale1 * (floor_h - eye_pos))

        u_left += (vertexes[linedef.start_vert] - vertexes[seg.start_vert]).length()
        u_right -= (vertexes[linedef.end_vert] - vertexes[seg.end_vert]).length()

        n_columns = last_col - first_col

        y_step_top = (h_top_end - h_top_start) / n_columns
        y_step_bottom = (h_bottom_end - h_bottom_start) / n_columns

        one_over_z0 = 1 / v0.x
        one_over_z1 = 1 / v1.x
        one_over_z_step = (one_over_z1 - one_over_z0) / n_columns
        u_left *= one_over_z0
        u_right *= one_over_z1
        u_step = (u_right - u_left) / n_columns

        return ScreenCoords(
            first_col, last_col,
            h_top_start, h_top_end, y_step_top,
            h_bottom_start, h_bottom_end, y_step_bottom,
            u_left, u_right, u_step,
            one_over_z0, one_over_z1, one_over_z_step,
            ceiling_h - floor_h)
    return None

def _render_subsector(subsector_index:int, player:Player):
    render_list : List[ScreenColumn] = []
    subsector = ssectors[subsector_index]

    for i in range(subsector.n_segs):
        seg_index = subsector.start_seg + i
        seg = segs[seg_index]
        linedef = linedefs[seg.linedef]

        if linedef.back_sidedef == -1:
            sidedef = sidedefs[linedef.front_sidedef]
            sector = sectors[sidedef.sector]

            if sc := _seg_to_screen_coord(seg, linedef, sector.ceiling_height, sector.floor_height, player.pos, player.angle, player.get_eye_pos()):
                for clipped_sc in clip_solid_wall(sc):
                    if clipped_sc.last_col != clipped_sc.first_col:
                        render_list += _screen_coord_to_screen_cols(clipped_sc, sidedef.middle_texture_name, sidedef.x_offset, sidedef.y_offset, SOLID_WALL)
        else:
            front_sidedef = sidedefs[linedef.front_sidedef]
            back_sidedef = sidedefs[linedef.back_sidedef]

            if seg.direction == 1:
                front_sidedef, back_sidedef = back_sidedef, front_sidedef

            front_sector = sectors[front_sidedef.sector]
            back_sector = sectors[back_sidedef.sector]

            if sc := _seg_to_screen_coord(seg, linedef, front_sector.ceiling_height, back_sector.ceiling_height, player.pos, player.angle, player.get_eye_pos()):
                for clipped_sc in clip_window_wall(sc):
                    render_list += _screen_coord_to_screen_cols(clipped_sc, front_sidedef.upper_texture_name, front_sidedef.x_offset, front_sidedef.y_offset, UPPER_WALL)
            if sc := _seg_to_screen_coord(seg, linedef, back_sector.floor_height, front_sector.floor_height, player.pos, player.angle, player.get_eye_pos()):
                for clipped_sc in clip_window_wall(sc):
                    render_list += _screen_coord_to_screen_cols(clipped_sc, front_sidedef.lower_texture_name, front_sidedef.x_offset, front_sidedef.y_offset, LOWER_WALL)
    return render_list

def _render_bsp_node(player:Player, node_index:Optional[int]=None):
    if node_index is None:
        node_index = len(nodes) - 1

    if node_index >> 15:
        return _render_subsector(node_index ^ (1 << 15), player)

    node = nodes[node_index]
    render_list : List[ScreenColumn] = []

    if _on_right_side(player.pos, node):
        render_list += _render_bsp_node(player, node.right_child)
        if _boundingbox_intersects_view(player.pos, player.dir, player.frust_norm_left, player.frust_norm_right, node.left_bbox):
            render_list += _render_bsp_node(player, node.left_child)
    else:
        render_list += _render_bsp_node(player, node.left_child)
        if _boundingbox_intersects_view(player.pos, player.dir, player.frust_norm_left, player.frust_norm_right, node.right_bbox):
            render_list += _render_bsp_node(player, node.right_child)
    return render_list

def sector_search(pos:Vector2, node_index:Optional[int]=None) -> Sector:
    if node_index is None:
        node_index = len(nodes) - 1

    if node_index >> 15:
        subsector = ssectors[node_index ^ (1 << 15)]
        seg = segs[subsector.start_seg]
        linedef = linedefs[seg.linedef]
        if seg.direction == 0:
            return sectors[sidedefs[linedef.front_sidedef].sector]
        return sectors[sidedefs[linedef.back_sidedef].sector]
    
    node = nodes[node_index]
    if _on_right_side(pos, node):
        return sector_search(pos, node.right_child)
    return sector_search(pos, node.left_child)

def render_player_view(player:Player):
    clear_clip_range()
    _clear_floor_ceiling_bounds()
    return _render_bsp_node(player)























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
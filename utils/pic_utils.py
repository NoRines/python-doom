from pygame import Surface, PixelArray
from wad.d_types import Patch, ColorPalette


def patch_to_surface(patch : Patch, palette : ColorPalette) -> Surface:
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

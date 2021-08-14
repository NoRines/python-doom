import pygame
from pygame import Vector2, display, event, time, key, transform
from pygame.constants import KEYDOWN, K_ESCAPE, K_SPACE, QUIT
from pygame.version import ver

from wad.reader import read_things, read_wad_info_table

from bsp.bsp_map import init_bsp_map, test_render_seg, temp_bla_func

import math

class Player:
    def __init__(self, pos : Vector2, angle : float, fov : float, head_height : int) -> None:
        self.pos = pos
        self.angle = angle
        self.fov = fov
        self.head_height = head_height
        self._update_dir()

    def _update_dir(self):
        self.dir = Vector2(math.cos(self.angle), math.sin(self.angle))
        self.frust_left = self.dir.rotate_rad(-self.fov/2)
        self.frust_right = self.dir.rotate_rad(self.fov/2)
        self.frust_norm_left = Vector2(-self.frust_left.y, self.frust_left.x)
        self.frust_norm_right = Vector2(self.frust_right.y, -self.frust_right.x)

    def update(self, keys):
        if keys[pygame.K_LEFT]:
            self.angle += 0.025
        if keys[pygame.K_RIGHT]:
            self.angle -= 0.025
        self._update_dir()
        if keys[pygame.K_UP]:
            self.pos += self.dir * 2.5
        if keys[pygame.K_DOWN]:
            self.pos -= self.dir * 2.5

WAD_PATH = 'wads/DOOM.WAD'
WINDOW_DIMS = RES_WIDTH, HEIGHT_RES = 640, 480

def main():
    pygame.init()
    screen = display.set_mode(WINDOW_DIMS)
    clock = time.Clock()

    info_table = read_wad_info_table(WAD_PATH)
    init_bsp_map(WAD_PATH, info_table, 'E1M1')

    things = read_things(WAD_PATH, *info_table['E1M1']['THINGS'])
    player_thing = list(filter(lambda x: x.thing_type == 1, things))[0]

    player = Player(player_thing.position, math.radians(player_thing.angle), 90, 20)

    one_seg_mode = False

    seg_index = 375
    running = True
    while running:
        for e in event.get():
            if e.type == QUIT:
                running = False
            if e.type == KEYDOWN:
                if e.key == K_SPACE:
                    seg_index += 1
                    print(seg_index)
                if e.key == K_ESCAPE:
                    one_seg_mode = True

        player.update(key.get_pressed())
    
        screen.fill('white', (0,0,640,400))
        #screen.blit(wall_textures['STARTAN3'], (0,0))
        if not one_seg_mode:
            render_list = []
            for i in range(747):
                render_list += test_render_seg(i, player.pos, player.angle)
        else:
            render_list = test_render_seg(seg_index, player.pos, player.angle, True)
            #temp_bla_func(seg_index)
        for pos, ss in render_list:
            #screen.blit(ss, pos)
            screen.blit(transform.scale2x(ss), (pos[0]*2, pos[1]*2))
        display.update()
        clock.tick(60)
        display.set_caption('doom-py %0.1f fps' % clock.get_fps())

    pygame.quit()

if __name__ == '__main__':
    main()
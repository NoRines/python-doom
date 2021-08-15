import math
import pygame
from pygame import Vector2

class Player:
    def __init__(self, pos : Vector2, angle : float, fov : float, head_height : int) -> None:
        self.pos = pos
        self.angle = angle
        self.fov = fov
        self.head_height = head_height
        self.eye_height = head_height - 15
        self.foot_pos = 0
        self._update_dir()

    def _update_dir(self):
        self.dir = Vector2(math.cos(self.angle), math.sin(self.angle))
        self.frust_left = self.dir.rotate_rad(-self.fov/2)
        self.frust_right = self.dir.rotate_rad(self.fov/2)
        self.frust_norm_left = Vector2(-self.frust_left.y, self.frust_left.x)
        self.frust_norm_right = Vector2(self.frust_right.y, -self.frust_right.x)
    
    def update_foot_pos(self, foot_pos):
        self.foot_pos = foot_pos
    
    def get_eye_pos(self):
        return self.foot_pos + self.eye_height

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
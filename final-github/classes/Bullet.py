import pygame
from constants.global_var import *
from constants.global_var import PLAY_AREA, BULLET_SPEED, RED

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # generate bullet under enemy
        # self.rect = pygame.Rect(x - 2, y, 4, 10)
        # self.alive = True
        self.image = pygame.Surface((4, 10))
        self.image.fill((200, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        
        self.speed = -8

    def update(self):
        # bullet go up
        self.rect.y -= BULLET_SPEED
        # out of area then delete
        if self.rect.top > PLAY_AREA.bottom:
            self.alive = False
        if self.rect.bottom < 0:
            self.kill()

    def draw(self, surf):
        if self.alive:
            pygame.draw.rect(surf, RED, self.rect)

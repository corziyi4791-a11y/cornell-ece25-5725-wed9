import pygame
import os
import random
from constants.global_var import *

score = 0

class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        
        asset_path = os.path.join("assets", "enemy_1_1.png")
        
        if os.path.exists(asset_path):
            self.image = pygame.image.load(asset_path).convert_alpha()
            # Optional: Resize if image is too big
            self.image = pygame.transform.scale(self.image, (30, 30))
        else:
            # Fallback if image missing
            self.image = pygame.Surface((30, 30))
            self.image.fill(RED)
            
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, W - self.rect.width)
        self.rect.y = -self.rect.height # Start just above screen

    def update(self):
        self.rect.y += ENEMY_SPEED
        if self.rect.top > H:
            self.kill()

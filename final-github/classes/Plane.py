import pygame
from constants.global_var import *

class Plane(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Create a simple triangle representation
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, YELLOW, [(15, 0), (0, 30), (30, 30)])
        self.rect = self.image.get_rect(center=(W//2, H//2))
        
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)

    def update(self, roll, pitch, dt):
        # Move based on roll/pitch
        vx = roll * PLANE_SPEED_SCALE
        vy = pitch * PLANE_SPEED_SCALE
        
        self.x += vx * dt
        self.y += vy * dt
        
        # Clamp to screen
        self.x = max(0, min(W - self.rect.width, self.x))
        self.y = max(0, min(H - self.rect.height, self.y))
        
        self.rect.x = int(self.x)
        self.rect.y = int(self.rect.y)

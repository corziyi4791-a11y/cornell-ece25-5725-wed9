import pygame

# ====== Switches ======
USE_PITFT            = True     # True: run on piTFT; False: run on monitor
TIMEOUT_SECONDS      = 300      
HIDE_CURSOR_ON_PITFT = True     
BAILOUT_GPIO         = 27       

# ====== Dimensions ======
W, H       = 320, 240
BTN_H      = 60
PLAY_AREA  = pygame.Rect(0, 0, W, H - BTN_H)
BUTTON_BAR = pygame.Rect(0, H - BTN_H, W, BTN_H)

# ====== Colors ======
WHITE = (255, 255, 255)
GRAY  = (40, 40, 40)
CYAN  = (0, 200, 200)
RED   = (200, 0, 0)
GREEN = (0, 200, 0)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 100)

# ====== Game Settings ======
ENEMY_WIDTH     = 4
ENEMY_MIN_H     = 20
ENEMY_MAX_H     = 70
INITIAL_ENEMIES = 4
SPAWN_TIME      = 1.0   
BULLET_SPEED    = 4
BULLET_INTERVAL = 2.0
FPS  			= 60
PLANE_SPEED_SCALE = 2.0
FILTER_BETA = 0.02
# BULLET_SPEED = 5
ENEMY_SPEED = 2
SPAWN_RATE = 60  # Frames between spawns

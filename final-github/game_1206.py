import os
import sys
import time
import random
from time import sleep

import pygame
import pigame # Make sure pigame.py is in the folder
from pygame.locals import *

# Custom modules
from constants.global_var import *
from utils.hardware import IMUHandler
from classes.Plane import Plane
from classes.Bullet import Bullet
from classes.Enemy import Enemy

# ====== Switches ======
USE_PITFT = True
TIMEOUT_SECONDS = 300
HIDE_CURSOR_ON_PITFT = True
BAILOUT_GPIO = 27
SHOOT_GPIO = 22
# ====== PiTFT preparation ======
def setup_env_for_pitft():
    os.putenv("SDL_VIDEODRIVER", "fbcon")
    os.putenv("SDL_FBDEV", "/dev/fb0") # Ensure this is fb0 or fb1 depending on your Pi
    os.putenv("SDL_MOUSEDRV", "dummy")
    os.putenv("SDL_MOUSEDEV", "/dev/null")
    os.putenv("DISPLAY", "")

# ====== Bail-out button (GPIO) ======
try:
    import RPi.GPIO as GPIO
    HAVE_GPIO = True
except Exception:
    GPIO = None
    HAVE_GPIO = False

_bailout_triggered = False
_shoot_triggered   = False

def _bailout_cb(channel):
    global _bailout_triggered
    print("[GPIO] Bailout button pressed")
    _bailout_triggered = True

def setup_bailout_button():
    if not HAVE_GPIO:
        return
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BAILOUT_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(BAILOUT_GPIO, GPIO.FALLING, callback=_bailout_cb, bouncetime=150)

def cleanup_bailout_button():
    if HAVE_GPIO:
        GPIO.cleanup()
        
def _shoot_cb(channel):
    global _shoot_triggered
    _shoot_triggered = True


def setup_shoot_button():
    if not HAVE_GPIO:
        return

    GPIO.setmode(GPIO.BCM)

    GPIO.setup(SHOOT_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(SHOOT_GPIO,
                          GPIO.FALLING,
                          callback=_shoot_cb,
                          bouncetime=150)

# ====== Helper Function to Draw Menu ======
def draw_menu(screen, font_big, font_small):
    screen.fill((0, 0, 30)) 
    
    # Draw Title
    title = font_big.render("IMU PLANE", True, (255, 255, 0))
    screen.blit(title, (W//2 - title.get_width()//2, 40))

    # Define Buttons
    start_rect = pygame.Rect(W//2 - 60, 100, 120, 50)
    quit_rect  = pygame.Rect(W//2 - 60, 180, 120, 50)

    # Draw Buttons
    pygame.draw.rect(screen, (0, 200, 0), start_rect) # Green
    pygame.draw.rect(screen, (200, 0, 0), quit_rect)  # Red

    # Draw Text
    txt_start = font_small.render("START", True, (255, 255, 255))
    txt_quit  = font_small.render("QUIT",  True, (255, 255, 255))
    
    screen.blit(txt_start, txt_start.get_rect(center=start_rect.center))
    screen.blit(txt_quit, txt_quit.get_rect(center=quit_rect.center))

    return start_rect, quit_rect

def main():
    global _bailout_triggered, _shoot_triggered

    if USE_PITFT:
        setup_env_for_pitft()

    pygame.init()   

    if USE_PITFT and HIDE_CURSOR_ON_PITFT:
        pygame.mouse.set_visible(False)
    
    # Initialize PiTFT (Correction Helper)
    pitft = pigame.PiTft()
    
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Enemy Tapper Integrated")
    clock = pygame.time.Clock()

    # Initialize Hardware
    imu = IMUHandler()
    setup_bailout_button()
    setup_shoot_button()
    # Fonts
    font_big   = pygame.font.Font(None, 52)
    font_small = pygame.font.Font(None, 28)

    # Game State Variables
    mode = "menu"   # Start in menu
    score = 0
    frame_count = 0
    running = True

    # Initialize Sprites
    all_sprites = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    
    player = Plane()
    all_sprites.add(player)

    # Define button rects initially (will be updated in loop)
    start_rect = pygame.Rect(0,0,0,0)
    quit_rect = pygame.Rect(0,0,0,0)

    # ================= MAIN LOOP =================
    while running:
        # 1. ALWAYS Update PiTFT Input First
        if USE_PITFT:
            pitft.update()

        # 2. Check Bailout
        if _bailout_triggered:
            running = False
            break

        dt = clock.tick(FPS) / 1000.0
        
        # ================= EVENT HANDLING =================
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                
                if mode == "menu":
                    # Check Menu Buttons
                    if start_rect.collidepoint(x, y):
                        print("Start Game!")
                        mode = "game"
                        score = 0
                        # Clear enemies from previous run
                        for e in enemies: e.kill()
                        
                    elif quit_rect.collidepoint(x, y):
                        running = False
                        
                # elif mode == "game":
                    # Fire Bullet
                    # if event.key == pygame.K_SPACE:
                    #     b = Bullet(player.rect.centerx, player.rect.top)
                    #     all_sprites.add(b)
                    #    bullets.add(b)
                
            elif event.type == pygame.KEYDOWN:
                # Quit
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    running = False
                # --- FIRE BULLET LOGIC GOES HERE ---
        if mode == "game" and _shoot_triggered:
          b = Bullet(player.rect.centerx, player.rect.top)
          all_sprites.add(b)
          bullets.add(b)
          _shoot_triggered = False

        # ================= UPDATE & DRAW =================
        
        if mode == "menu":
            # Just draw the menu
            start_rect, quit_rect = draw_menu(screen, font_big, font_small)
            pygame.display.flip()

        elif mode == "game":
            frame_count += 1
            
            # 1. Hardware
            roll, pitch = imu.update(dt)

            # 2. Game Logic
            if frame_count % SPAWN_RATE == 0:
                e = Enemy()
                all_sprites.add(e)
                enemies.add(e)

            player.update(roll, pitch, dt)
            bullets.update()
            enemies.update()

            # 3. Collisions
            if pygame.sprite.groupcollide(enemies, bullets, True, True):
                score += 1

            if pygame.sprite.spritecollide(player, enemies, False):
                print("Crashed!")
                # Show Game Over briefly
                msg = font_big.render("GAME OVER", True, RED)
                screen.blit(msg, (W//2 - msg.get_width()//2, H//2))
                pygame.display.flip()
                sleep(2)
                mode = "menu" # Return to menu
                # Reset Player Position (Optional, depends on your Plane class)
                # player.rect.center = (W//2, H - 50) 

            # 4. Draw Game
            screen.fill((0, 0, 30))
            all_sprites.draw(screen)
            
            # Draw Score
            f_score = font_small.render(f"Score: {score}", True, (255, 255, 0))
            screen.blit(f_score, (10, 10))
            
            pygame.display.flip()

    # Cleanup
    pygame.quit()
    cleanup_bailout_button()
    sys.exit()

if __name__ == "__main__":
    main()

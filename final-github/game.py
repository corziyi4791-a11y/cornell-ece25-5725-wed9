# project_week_2
# hl2584_zc569 WedGroup9
# 2025-11-10 Created
# 2025-11-12 (project week 2) Modified / cleaned

import os
import sys
import time
import random
from time import sleep

import pygame
import pigame
from pygame.locals import *

# ====== Switches ======
USE_PITFT              = True     # True: run on piTFT; False: run on monitor (debug)
TIMEOUT_SECONDS        = 300      # Auto-exit after N seconds
HIDE_CURSOR_ON_PITFT   = True     # Hide cursor on piTFT
BAILOUT_GPIO           = 27       # Physical bail-out button (BCM numbering)

# ====== PiTFT preparation ======
def setup_env_for_pitft():
    os.putenv("SDL_VIDEODRIVER", "fbcon")
    os.putenv("SDL_FBDEV", "/dev/fb0")
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

def _bailout_cb(channel):
    global _bailout_triggered
    print("[GPIO] Bailout button pressed")
    _bailout_triggered = True

def setup_bailout_button():
    if not HAVE_GPIO:
        print("[GPIO] RPi.GPIO not available, bailout button disabled")
        return
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BAILOUT_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(
        BAILOUT_GPIO,
        GPIO.FALLING,
        callback=_bailout_cb,
        bouncetime=150
    )
    print(f"[GPIO] Bailout button set up on BCM {BAILOUT_GPIO}")

def cleanup_bailout_button():
    if not HAVE_GPIO:
        return
    try:
        GPIO.cleanup()
        print("[GPIO] Cleaned up")
    except Exception:
        pass

# ====== Game constants (320x240 PiTFT) ======
W, H       = 320, 240
BTN_H      = 60
PLAY_AREA  = pygame.Rect(0, 0, W, H - BTN_H)    # Drawing area
BUTTON_BAR = pygame.Rect(0, H - BTN_H, W, BTN_H)

# ====== Colors ======
WHITE = (255, 255, 255)
GRAY  = (40, 40, 40)
CYAN  = (0, 200, 200)
RED   = (200, 0, 0)
GREEN = (0, 200, 0)
BLACK = (0, 0, 0)

# ====== Enemy settings ======
ENEMY_WIDTH       = 4
ENEMY_MIN_H       = 20
ENEMY_MAX_H       = 70
INITIAL_ENEMIES   = 4
SPAWN_TIME        = 1.0   # Respawn enemies periodically (seconds)

BULLET_SPEED = 4
BULLET_INTERVAL = 2.0
bullets = []
PLANE_IMG = None
PLANE_W = 0
PLANE_H = 0

# bullet class
class Bullet:
    def __init__(self, x, y):
        # generate bullet under enemy
        self.rect = pygame.Rect(x - 2, y, 4, 10)
        self.alive = True

    def update(self):
        # bullet go down
        self.rect.y += BULLET_SPEED
        # out of area then delet
        if self.rect.top > PLAY_AREA.bottom:
            self.alive = False

    def draw(self, surf):
        if self.alive:
            pygame.draw.rect(surf, RED, self.rect)
            
# ====== Enemy class ======
class Enemy:
    def __init__(self, cx, cy):
        self.cx = cx
        self.cy = cy
        self.alive = True
        self.rect = PLANE_IMG.get_rect(center=(cx, cy))
        #speed
        self.speed_y = 1
        #last bullet time
        self.last_shot_time = time.time()
        
    def update(self):
        #move and bullet
        if not self.alive:
           return

        # move done
        self.rect.y += self.speed_y
        if self.rect.top > PLAY_AREA.bottom:
            # appear from top
            self.rect.bottom = PLAY_AREA.top

        # bullet
        now = time.time()
        if now - self.last_shot_time >= BULLET_INTERVAL:
            self.last_shot_time = now
            # from button
            bullets.append(Bullet(self.rect.centerx, self.rect.bottom))

    def draw(self, surf):
        if self.alive:
            surf.blit(PLANE_IMG, self.rect)

def make_enemy():
    
    margin_x = PLANE_W // 2 + 5
    margin_y = PLANE_H // 2 + 5

    cx = random.randint(margin_x, PLAY_AREA.width  - margin_x)
    cy = random.randint(margin_y, PLAY_AREA.height - margin_y)

    return Enemy(cx, cy)


def main():
    pygame.init()  
    global _bailout_triggered, PLANE_IMG, PLANE_W, PLANE_H

    # ----- Environment / init -----
    if USE_PITFT:
        setup_env_for_pitft()

    

    if USE_PITFT and HIDE_CURSOR_ON_PITFT:
        pygame.mouse.set_visible(False)
    else:
        pygame.mouse.set_visible(True)

    pitft = pigame.PiTft()
    lcd = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Enemy Tapper Integrated")

    PLANE_IMG = pygame.image.load("enemy_1_1.png").convert_alpha()
    PLANE_W, PLANE_H = PLANE_IMG.get_size()

    font_big   = pygame.font.Font(None, 52)
    font_small = pygame.font.Font(None, 28)

    setup_bailout_button()

    # ----- Game state -----
    mode        = "menu"   # "menu" or "game"
    score       = 0
    enemies     = []
    last_spawn  = time.time()
    t0          = time.time()
    running     = True

    # ----- Drawing helpers -----
    def draw_menu():
        lcd.fill(BLACK)

        msg = font_small.render("Touch START to begin", True, CYAN)
        lcd.blit(msg, (40, 40))

        half = BUTTON_BAR.width // 2
        start_rect = pygame.Rect(0, BUTTON_BAR.y, half, BTN_H)
        quit_rect  = pygame.Rect(half, BUTTON_BAR.y, half, BTN_H)

        pygame.draw.rect(lcd, GRAY, start_rect)
        pygame.draw.rect(lcd, GRAY, quit_rect)

        st = font_big.render("START", True, WHITE)
        qt = font_big.render("QUIT", True, WHITE)

        lcd.blit(st, st.get_rect(center=start_rect.center))
        lcd.blit(qt, qt.get_rect(center=quit_rect.center))

        pygame.display.flip()
        return start_rect, quit_rect

    def draw_game():
        lcd.fill(BLACK)

        # Play area border
        pygame.draw.rect(lcd, CYAN, PLAY_AREA, 2)

        # Enemies
        for e in enemies:
            e.update()
            e.draw(lcd)

        #draw bullet
        for b in bullets[:]:        
            b.update()
            if not b.alive:
                bullets.remove(b)
            else:
                b.draw(lcd)
        # HUD
        hud = font_small.render(f"Score: {score}", True, CYAN)
        lcd.blit(hud, (10, 10))

        # Buttons at bottom
        half = BUTTON_BAR.width // 2
        stop_rect = pygame.Rect(0, BUTTON_BAR.y, half, BTN_H)
        quit_rect = pygame.Rect(half, BUTTON_BAR.y, half, BTN_H)

        pygame.draw.rect(lcd, WHITE, stop_rect)
        pygame.draw.rect(lcd, WHITE, quit_rect)

        stop_text = font_big.render("STOP", True, BLACK)
        quit_text = font_big.render("QUIT", True, BLACK)

        lcd.blit(stop_text, stop_text.get_rect(center=stop_rect.center))
        lcd.blit(quit_text,  quit_text.get_rect(center=quit_rect.center))

        pygame.display.flip()
        return stop_rect, quit_rect

    def reset_game():
        return [make_enemy() for _ in range(INITIAL_ENEMIES)]

    # First menu draw
    start_rect, quit_rect = draw_menu()
    stop_rect = None  # Will be set when we enter game mode

    # ----- Main loop -----
    while running:
        pitft.update()

        # Physical bailout
        if _bailout_triggered:
            print("[Bail-out] Exiting")
            running = False
            break

        # Timeout
        if TIMEOUT_SECONDS is not None and (time.time() - t0) > TIMEOUT_SECONDS:
            print("[Timeout] Exiting")
            running = False
            break

        now = time.time()

        # Spawn enemies during game
        if mode == "game" and now - last_spawn >= SPAWN_TIME:
            enemies.append(make_enemy())
            last_spawn = now

        # ----- Event handling -----
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
                break

            elif event.type == MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                print("Touch:", x, y, "mode =", mode)
                print("start_rect =", start_rect)

                if mode == "menu":
                    if start_rect.collidepoint(x, y):
                        score   = 0
                        enemies = reset_game()
                        last_spwan = now #new
                        mode    = "game"
                        #stop_rect, quit_rect = draw_game()
                        
                    elif quit_rect.collidepoint(x, y):
                        running = False

                elif mode == "game":
                    if stop_rect is not None and stop_rect.collidepoint(x, y):
                        mode = "menu"
                        #start_rect, quit_rect = draw_menu()
                        
                    elif quit_rect.collidepoint(x, y):
                        running = False
                        
                    elif PLAY_AREA.collidepoint(x, y):
                        # Tap enemies from top-most drawn (reverse list)
                        for e in reversed(enemies):
                            if e.alive and e.rect.collidepoint(x, y):
                                e.alive = False
                                score += 1
                                break

        # ----- Redraw current screen every frame -----
        if mode == "game":
            stop_rect, quit_rect = draw_game()
        else:
            start_rect, quit_rect = draw_menu()

        sleep(0.02)  # Slight delay to reduce CPU usage

    # ----- Exit -----
    pygame.quit()
    cleanup_bailout_button()

if __name__ == "__main__":
    main()

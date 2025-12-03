import pygame
import os
import sys
import time
from time import sleep

# Custom modules
from constants.global_var import *
from utils.hardware import IMUHandler
from classes.Plane import Plane
from classes.Bullet import Bullet
from classes.Enemy import Enemy

# Setup PiTFT Environment
if USE_PITFT:
    os.putenv('SDL_VIDEODRIVER', 'fbcon')
    os.putenv('SDL_FBDEV', '/dev/fb0')
    os.putenv('SDL_MOUSEDRV', 'dummy')
    os.putenv('SDL_MOUSEDEV', '/dev/null')
    os.putenv('DISPLAY', '')

def main():
    pygame.init()
    
    font_small = pygame.font.Font(None, 28)
    
    # Setup Screen
    screen = pygame.display.set_mode((W, H))
    if USE_PITFT:
        pygame.mouse.set_visible(False)
    pygame.display.set_caption("IMU Plane Game")
    
    clock = pygame.time.Clock()

    # Initialize Hardware
    imu = IMUHandler()
    
    # Sprite Groups
    all_sprites = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    
    # Create Player
    player = Plane()
    all_sprites.add(player)

    running = True
    frame_count = 0
    
    print("Game Started")
    
    score = 0

    while running:
        # 1. Time delta (in seconds)
        dt = clock.tick(FPS) / 1000.0
        frame_count += 1

        # 2. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    running = False
                if event.key == pygame.K_SPACE:
                    # Fire bullet on Space
                    b = Bullet(player.rect.centerx, player.rect.top)
                    all_sprites.add(b)
                    bullets.add(b)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Fire bullet on Touch
                b = Bullet(player.rect.centerx, player.rect.top)
                all_sprites.add(b)
                bullets.add(b)

        # 3. Update Hardware
        roll, pitch = imu.update(dt)

        # 4. Game Logic
        # Spawn enemies
        if frame_count % SPAWN_RATE == 0:
            e = Enemy()
            all_sprites.add(e)
            enemies.add(e)

        # Update Player with IMU data
        player.update(roll, pitch, dt)
        
        # Update other sprites
        bullets.update()
        enemies.update()

        # Collisions: Bullets hit Enemies
        hits = pygame.sprite.groupcollide(enemies, bullets, True, True)
        if hits:
            print("Enemy Destroyed!")
            score += 1

        # Collisions: Enemies hit Player
        crashes = pygame.sprite.spritecollide(player, enemies, False)
        if crashes:
            print("Crashed!")
            score = 0
            # f_score = font_small.render(f"Score: {score}", True, YELLOW)
            # screen.blit(f_score, (300, 20))
            sleep(0.5)
            running = False

        # 5. Draw
        screen.fill((0, 0, 30)) # Dark Blue background
        all_sprites.draw(screen)
        f_score = font_small.render(f"Score: {score}", True, YELLOW)
        screen.blit(f_score, (200, 20))
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

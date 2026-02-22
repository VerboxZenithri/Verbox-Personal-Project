import pygame
import random
import math

pygame.init()
W, H = 900, 600
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Valentine Day - Verbox ♡ Scara")
clock = pygame.time.Clock()

# Colors
PINK = (255, 100, 180)
HOT_PINK = (255, 60, 140)
WHITE = (255, 255, 255)
DARK = (15, 10, 30)

font_big = pygame.font.SysFont("comicsansms", 72, bold=True)
font_small = pygame.font.SysFont("comicsansms", 22)

hearts = []
particles = []

class Heart:
    def __init__(self, x, y, speed):
        self.x = x
        self.y = y
        self.speed = speed
        self.size = random.randint(10, 20)
        self.alpha = random.randint(150, 255)

    def update(self):
        self.y += self.speed
        if self.y > H + 50:
            self.y = random.randint(-200, -50)
            self.x = random.randint(0, W)

    def draw(self, surf):
        heart_surf = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        pygame.draw.circle(heart_surf, (*PINK, self.alpha), (self.size//2, self.size//2), self.size//2)
        pygame.draw.circle(heart_surf, (*PINK, self.alpha), (self.size + self.size//2, self.size//2), self.size//2)
        pygame.draw.polygon(heart_surf, (*PINK, self.alpha), [
            (0, self.size//2),
            (self.size*2, self.size//2),
            (self.size, self.size*2)
        ])
        surf.blit(heart_surf, (self.x, self.y))

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-4, -1)
        self.life = random.randint(30, 60)
        self.size = random.randint(4, 8)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.15
        self.life -= 1

    def draw(self, surf):
        pygame.draw.circle(surf, HOT_PINK, (int(self.x), int(self.y)), self.size)

def draw_glow_text(text, font, x, y, color):
    base = font.render(text, True, color)
    for r in range(8, 0, -2):
        glow = font.render(text, True, color)
        glow.set_alpha(20)
        screen.blit(glow, glow.get_rect(center=(x, y)))
    screen.blit(base, base.get_rect(center=(x, y)))

# Spawn hearts
for _ in range(40):
    hearts.append(Heart(random.randint(0, W), random.randint(-H, H), random.uniform(0.5, 2)))

t = 0
running = True
while running:
    clock.tick(60)
    t += 0.05

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        if e.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            for _ in range(30):
                particles.append(Particle(mx, my))

    # Background
    screen.fill(DARK)

    # Floating hearts
    for h in hearts:
        h.update()
        h.draw(screen)

    # Pulse text
    scale = 1 + 0.05 * math.sin(t)
    text_surf = font_big.render("Verbox <3 Scara", True, WHITE)
    w, h = text_surf.get_size()
    text_surf = pygame.transform.smoothscale(text_surf, (int(w*scale), int(h*scale)))

    # Glow effect
    glow = pygame.Surface((text_surf.get_width()+20, text_surf.get_height()+20), pygame.SRCALPHA)
    pygame.draw.rect(glow, (255, 80, 160, 80), glow.get_rect(), border_radius=20)
    screen.blit(glow, glow.get_rect(center=(W//2, H//2 - 40)))
    screen.blit(text_surf, text_surf.get_rect(center=(W//2, H//2 - 40)))

    sub = font_small.render("Click for love explosion", True, (200, 200, 255))
    screen.blit(sub, sub.get_rect(center=(W//2, H//2 + 40)))

    # Particles
    for p in particles[:]:
        p.update()
        p.draw(screen)
        if p.life <= 0:
            particles.remove(p)

    pygame.display.flip()

pygame.quit()
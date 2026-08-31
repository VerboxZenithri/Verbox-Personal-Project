import pygame
import sys

pygame.init()

W, H=920, 720 #width and Height
scrn=pygame.display.set_mode((W, H))
tile=40
clock=pygame.time.Clock()
world = [
"11111111111111111111111",
"10000000000000000000001",
"10111100111100111101101",
"10000000000000000000001",
"10111111100111111100111",
"10000000000000000000001",
"10111101111101011111111",
"10000000000000000000001",
"10000111000000011100111",
"11100111000000011100111",
"11100111000000011100001",
"10000000000000000000001",
"10000000000000000000001",
"10110011001100110110001",
"10110011001100110110001",
"10000000000000000000001",
"10101010100101010010101",
"11111111111111111111111"
]

player_pos=pygame.Vector2(W//2, H//2)
player_spd=4
player_sz=40
player_hp=100

def get_rect(x,y):
    return pygame.Rect(x,y,tile,tile)
def can_move(rect):
    for row in range(len(world)):
        for col in range(len(world[row])):
            if world[row][col]=="1":
                wall_rect=get_rect(col*tile,row*tile)
                if rect.colliderect(wall_rect):return False
    return True

zombie_pos=pygame.Vector2(100, 100)
zombie_spd=2
zombie_sz=40

while True:
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            pygame.quit()
            sys.exit()

    ky = pygame.key.get_pressed()
    m = pygame.Vector2(0, 0)

    if ky[pygame.K_UP]:
        m.y=-1
    if ky[pygame.K_DOWN]:
        m.y=1
    if ky[pygame.K_LEFT]:
        m.x=-1
    if ky[pygame.K_RIGHT]:
        m.x=1

    if m.length() !=0:
        m=m.normalize()


    direction=player_pos-zombie_pos
    if direction.length() !=0:
        direction=direction.normalize()

    new_pos=player_pos+m*player_spd
    player_rect=pygame.Rect(player_pos.x,player_pos.y,player_sz, player_sz)

    if can_move(player_rect):
        player_pos=new_pos

    zombie_pos+=direction*zombie_spd

    player_pos.x=max(0, min(W-player_sz, player_pos.x))
    player_pos.y=max(0, min(H-player_sz, player_pos.y))

    scrn.fill((30, 30, 30))
    for row in range(len(world)):
        for col in range(len(world[row])):
            if world [row][col]=="1":
                pygame.draw.rect(scrn,(100,100,100),
                                 (col*tile,row*tile,tile,tile))
    pygame.draw.rect(scrn, (0,200, 0), (player_pos.x, player_pos.y, player_sz, player_sz))
    pygame.draw.rect(scrn, (200, 0, 0), (zombie_pos.x, zombie_pos.y, zombie_sz, zombie_sz))
    pygame.display.update()                                      
    clock.tick(60)
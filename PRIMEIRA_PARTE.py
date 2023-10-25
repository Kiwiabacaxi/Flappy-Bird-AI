# imports
import pygame
import random
import os
import time
import neat
import visualize
import pickle

pygame.font.init()  # inicializa a fonte

# Constantes
WIN_WIDTH = 600
WIN_HEIGHT = 800
FLOOR = 730
STAT_FONT = pygame.font.SysFont("comicsans", 50)
END_FONT = pygame.font.SysFont("comicsans", 70)
DRAW_LINES = False

# Carrega a tela
WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Flappy Bird")

# Carrega as imagens

# cano
pipe_img = pygame.transform.scale2x(
    pygame.image.load(os.path.join("imgs", "pipe.png")).convert_alpha()
)

# background
bg_img = pygame.transform.scale(
    pygame.image.load(os.path.join("imgs", "bg.png")).convert_alpha(), (600, 900)
)

# pássaro
bird_images = [
    pygame.transform.scale2x(
        pygame.image.load(os.path.join("imgs", "bird" + str(x) + ".png"))
    )
    for x in range(1, 4)
]

# base - "chao"
base_img = pygame.transform.scale2x(
    pygame.image.load(os.path.join("imgs", "base.png")).convert_alpha()
)

# Classe do pássaro
gen = 0


class Bird:
    """
    Classe do pássaro
    """

    MAX_ROTATION = 25  # angulo maximo de rotação
    IMGS = bird_images  # imagens do pássaro
    ROT_VEL = 20  # velocidade angular de rotação
    ANIMATION_TIME = 5  # tempo de animação

    def __init__(self, x, y) -> None:
        """
        Inicializa o objeto e suas variáveis
        :param x: posição inicial x (int)
        :param y: posição inicial y (int)
        :return: None
        """
        self.x = x
        self.y = y
        self.tilt = 0  # angulo de inclinação
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self) -> None:
        """
        função para fazer o pássaro pular
        * o 10.5 foi encontrado experimentalmente :D
        * o eixo y é invertido porque o canto superior esquerdo da tela é (0,0)
        :return: None
        """
        self.vel = -10.5  # velocidade é negativa pois o eixo y é invertido
        self.tick_count = 0
        self.height = self.y

    def move(self) -> None:
        """
        função para fazer o pássaro se mover

        * Tipo de movimento: MUV
        * d = v0*t + (1/2)*a*t^2
        * displacement = deslocamento
        * self.vel = velocidade inicial
        * self.tick_count = tempo
        * 0.5 * (3) * (self.tick_count) ** 2 = aceleração

        :return: None
        """
        self.tick_count += 1

        # para aceleração descendente
        displacement = self.vel * (self.tick_count) + 0.5 * (3) * (self.tick_count) ** 2

        # velocidade terminal - senão é MUV e o pássaro vai acelerar infinitamente
        if displacement >= 16:
            displacement = (displacement / abs(displacement)) * 16

        if displacement < 0:
            displacement -= 2

        self.y = self.y + displacement

        # não inclina de uma vez, o inclinamento é gradual
        if displacement < 0 or self.y < self.height + 50:  # inclina para cima
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:  # inclina para baixo
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win) -> None:
        """
        Função que desenha o pássaro
        :param win: pygame wndow or surface
        :param win: janela do pygame ou superfície
        :return: None
        """
        self.img_count += 1

        # Para animação do pássaro, loop através de três imagens
        if self.img_count <= self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count <= self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count <= self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count <= self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        # If quando o pássaro está mergulhando, ele não está "batendo" as asas
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME * 2

        # Gira em torno do proprio eixo - Creditos: Stack Overflow :D
        blitRotateCenter(win, self.img, (self.x, self.y), self.tilt)

    def get_mask(self) -> None:
        """
        Get para a máscara para a imagem atual do pássaro
        :return: None
        """
        return pygame.mask.from_surface(self.img)


def blitRotateCenter(surf, image, topleft, angle):
    """
    Rotaciona uma superfície e blita na janela - STACK OVERFLOW
    :param surf: the surface to blit to
    :param image: the image surface to rotate
    :param topLeft: the top left position of the image
    :param angle: a float value for angle
    :return: None
    """
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center=image.get_rect(topleft=topleft).center)

    surf.blit(rotated_image, new_rect.topleft)


class Pipe:
    """
    Classe do cano - qual cano?
    """

    GAP = 200  # espaço entre os canos
    VEL = 5  # velocidade de movimento do cano

    def __init__(self, x) -> None:
        """
        Inicializa o objeto e suas variáveis
        :param x: coordenada x (int)
        :return" None
        """
        self.x = x
        self.height = 0

        # where the top and bottom of the pipe is
        self.top = 0
        self.bottom = 0

        self.PIPE_TOP = pygame.transform.flip(pipe_img, False, True)
        self.PIPE_BOTTOM = pipe_img

        self.passed = False

        self.set_height()

    def set_height(self):
        """
        Seta a altura do cano, da parte superior e inferior
        :return: None
        """
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        """
        Movimenta o cano baseado na velocidade
        :return: None
        """
        self.x -= self.VEL

    def draw(self, win):
        """
        Desenha a parte superior e inferior do cano
        :param win: janela do pygame ou superfície (pygame window/surface)
        :return: None
        """
        # draw top
        win.blit(self.PIPE_TOP, (self.x, self.top))
        # draw bottom
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird, win) -> bool:
        """
        retorna se um ponto está colidindo com o cano
        :param bird: Bird object
        :return: Bool
        """

        # máscara para o pássaro e para o cano
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)
        # offset = distancia entre o pássaro e o cano
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        # pontos de colisão
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        # se b_point ou t_point não forem None, então houve colisão
        if b_point or t_point:
            return True  # colisão

        return False  # sem colisão


def draw_window(win, bird):
    win.blit(bg_img, (0, 0))
    bird.draw(win)
    pygame.display.update()


def main():
    bird = Bird(200, 200)
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()  # pode adicionar o clock depois

    run = True
    while run:
        clock.tick(30)  # pode adicionar depois
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            bird.move()  # pode adicionar depois
            draw_window(win, bird)

    pygame.quit()
    quit()


main()

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


class Base:
    """
    Classe que representa a base/chao do jogo
    """

    VEL = 5  # velocidade
    WIDTH = base_img.get_width()  # largura da imagem
    IMG = base_img  # qual imagem

    def __init__(self, y):
        """
        Inicializa o objeto e suas variáveis
        :param y: int
        :return: None
        """
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        """
        Faz com que o chao mexa para parecer que está rolando
        :return: None
        """
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        """
        Desenha o chao. São duas imagens que se movem juntas.
        :param win: the pygame surface/window
        :return: None
        """
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


# desenha a janela do jogo
def draw_window(win, birds, pipes, base, score, gen, pipe_ind):
    """
    desneha a janela do jogo
    :param win: pygame window surface
    :param bird: Um objeto Bird
    :param pipes: List [] de pipes
    :param score: Placar (int)
    :param gen: gen atual
    :param pipe_ind: index do pipe mais proximo
    :return: None
    """

    # se a gen for 0, então é a primeira gen
    if gen == 0:
        gen = 1
    win.blit(bg_img, (0, 0))

    # desenha os pipes
    for pipe in pipes:
        pipe.draw(win)

    base.draw(win)
    for bird in birds:
        # draw lines from bird to pipe
        if DRAW_LINES:
            try:
                pygame.draw.line(
                    win,
                    (255, 0, 0),
                    (
                        bird.x + bird.img.get_width() / 2,
                        bird.y + bird.img.get_height() / 2,
                    ),
                    (
                        pipes[pipe_ind].x + pipes[pipe_ind].PIPE_TOP.get_width() / 2,
                        pipes[pipe_ind].height,
                    ),
                    5,
                )
                pygame.draw.line(
                    win,
                    (255, 0, 0),
                    (
                        bird.x + bird.img.get_width() / 2,
                        bird.y + bird.img.get_height() / 2,
                    ),
                    (
                        pipes[pipe_ind].x + pipes[pipe_ind].PIPE_BOTTOM.get_width() / 2,
                        pipes[pipe_ind].bottom,
                    ),
                    5,
                )
            except:
                pass
        # desenha o pássaro
        bird.draw(win)

    # score
    score_label = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(score_label, (WIN_WIDTH - score_label.get_width() - 15, 10))

    # geraçoes
    score_label = STAT_FONT.render("Gens: " + str(gen - 1), 1, (255, 255, 255))
    win.blit(score_label, (10, 10))

    # Qntos estao vivos
    score_label = STAT_FONT.render(
        "vivos: " + str(len(birds)), 1, (255, 255, 255)
    )
    win.blit(score_label, (10, 50))

    # update
    pygame.display.update()


def eval_genomes(genomes, config):
    """
    Roda a simulação da população atual de pássaros e seta
    a sua fitness baseada na distância que eles alcançam no jogo
    :param genomes: list of genomes
    :param config: configuração do NEAT
    :return: None
    """
    # global variables
    global WIN, gen
    win = WIN
    gen += 1

    # start by creating lists holding the genome itself, the
    # neural network associated with the genome and the
    # bird object that uses that network to play
    # Começa criando listas que contem o genoma em si,
    # a rede neural associada ao genoma e o objeto pássaro
    # que usa a rede neural para jogar
    nets = []
    birds = []
    ge = []
    for genome_id, genome in genomes:
        genome.fitness = 0  # inicia com fitness de zero

        net = neat.nn.FeedForwardNetwork.create(
            genome, config
        )  # cria a rede neural do config

        nets.append(net)
        birds.append(Bird(230, 350))
        ge.append(genome)

    base = Base(FLOOR)
    pipes = [Pipe(700)]
    score = 0

    clock = pygame.time.Clock()

    run = True
    while run and len(birds) > 0:
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break

        pipe_ind = 0
        if len(birds) > 0:
            if (
                len(pipes) > 1
                and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width()
            ):  # determine whether to use the first or second
                pipe_ind = 1  # pipe on the screen for neural network input

        for x, bird in enumerate(
            birds
        ):  # give each bird a fitness of 0.1 for each frame it stays alive
            ge[x].fitness += 0.1
            bird.move()

            # send bird location, top pipe location and bottom pipe location and determine from network whether to jump or not
            output = nets[birds.index(bird)].activate(
                (
                    bird.y,
                    abs(bird.y - pipes[pipe_ind].height),
                    abs(bird.y - pipes[pipe_ind].bottom),
                )
            )

            if output[0] > 0.5:
                # Vamos usar a tanh como função de ativação
                # entao os resultados vao trocar entre -1 e 1. Se for maior que 0.5, pula
                bird.jump()

        base.move()

        rem = []
        add_pipe = False
        for pipe in pipes:
            pipe.move()
            # checa se teve collision
            for bird in birds:
                if pipe.collide(bird, win):
                    ge[birds.index(bird)].fitness -= 1
                    nets.pop(birds.index(bird))
                    ge.pop(birds.index(bird))
                    birds.pop(birds.index(bird))

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True

        if add_pipe:
            score += 1
            # pode adicionar a linha para dar mais recompensa por passar pelo cano (não é necessário)
            for genome in ge:
                genome.fitness += 5
            pipes.append(Pipe(WIN_WIDTH))

        for r in rem:
            pipes.remove(r)

        for bird in birds:
            if bird.y + bird.img.get_height() - 10 >= FLOOR or bird.y < -50:
                nets.pop(birds.index(bird))
                ge.pop(birds.index(bird))
                birds.pop(birds.index(bird))

        draw_window(WIN, birds, pipes, base, score, gen, pipe_ind)

        # sai rapidamente com um break caso o score seja maior que 20
        """if score > 20:
            pickle.dump(nets[0],open("best.pickle", "wb"))
            break"""


def run(config_file):
    """
    Executa o algoritmo NEAT para treinar a rede neural para jogar flappy bird
    :param config_file: location of config file
    :return: None
    """
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_file,
    )

    # cria a população, que é o objeto de nível superior para uma execução do NEAT
    p = neat.Population(config)

    # Adiciona um reporter para mostrar o progresso no terminal
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    # p.add_reporter(neat.Checkpointer(5))

    # executa por até 50 gerações
    winner = p.run(eval_genomes, 50)

    # show final stats
    print("\nBest genome:\n{!s}".format(winner))


if __name__ == "__main__":
    # determina o caminho do arquivo de configuração. Isso é necessário porque
    # o script é executado de forma independente do arquivo em que ele está

    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)

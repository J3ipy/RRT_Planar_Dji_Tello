# config.py
import pygame

# --- CONFIGURAÇÕES DA SIMULAÇÃO E AMBIENTE ---
SCREEN_WIDTH = 200
SCREEN_HEIGHT = 200
START_POS = (20, 20)
GOAL_POS = (180, 180)

# Lista de obstáculos (x, y, largura, altura)
OBSTACLES = [
    pygame.Rect((70, 0), (30, 100)),
    pygame.Rect((70, 150), (30, 50)),
    pygame.Rect((130, 50), (30, 150)),
]

# --- CONFIGURAÇÕES DO ALGORITMO RRT ---
RRT_MAX_ITERATIONS = 2000
RRT_STEP_SIZE = 35 # O "maxd" do passo

# --- CONFIGURAÇÕES DO DRONE TELLO ---
TELLO_TARGET_ALTITUDE = 30 # em cm
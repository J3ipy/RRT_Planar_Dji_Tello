# config.py
import pygame

# --- CONFIGURAÇÕES DA SIMULAÇÃO E AMBIENTE ---
# Mantendo a área total de 2m x 2m (200cm x 200cm)
SCREEN_WIDTH = 200
SCREEN_HEIGHT = 200

# Posição inicial do drone, a 20cm do canto superior esquerdo.
START_POS = (20, 20)

# Posição final (alvo).

GOAL_POS = (133, 133)

SAFETY_MARGIN_CM = 20

# --- Lista de Obstáculos (x, y, largura, altura) ---
# Os valores de X foram calculados com base nas suas medidas.
# Os valores de Y são exemplos. Você deve medir e ajustar.
OBSTACLES = [
    # Caixa 1
    pygame.Rect(
        32,  # x: lado esquerdo a 32cm da borda esquerda
        50,  # y: <<< SUBSTITUA PELA DISTÂNCIA DO TOPO DA CAIXA ATÉ A BORDA DE CIMA
        37,  # largura
        25   # altura
    ),
    
    # Caixa 2
    pygame.Rect(
        111, # x: calculado para o lado direito ficar a 52cm da borda direita
        80,  # y: <<< SUBSTITUA PELA DISTÂNCIA DO TOPO DA CAIXA ATÉ A BORDA DE CIMA
        37,  # largura
        45   # altura
    ),

    # (Opcional) Adicione mais obstáculos se necessário, seguindo o mesmo formato.
    # pygame.Rect(x, y, largura, altura),
]

# --- CONFIGURAÇÕES DO ALGORITMO RRT ---
RRT_MAX_ITERATIONS = 2000
RRT_STEP_SIZE = 35 # O "maxd" do passo

# --- CONFIGURAÇÕES DO DRONE TELLO ---
TELLO_TARGET_ALTITUDE = 40 # Altura de voo em cm. Aumentei um pouco para segurança.

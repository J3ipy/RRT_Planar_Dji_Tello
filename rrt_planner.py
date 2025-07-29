# rrt_planner.py
from datetime import datetime
import pygame
import math
import random

# NOVO: Fator de escala para a imagem de alta resolução
SCALE_FACTOR = 5

class RRTMap:
    def __init__(self, start, goal, map_dimensions):
        self.start, self.goal = start, goal
        self.map_h, self.map_w = map_dimensions
        
        # Janela de visualização em tempo real (tamanho normal)
        pygame.display.set_caption('RRT Path Planning')
        self.map = pygame.display.set_mode((self.map_w, self.map_h))
        self.map.fill((255, 255, 255))

        # NOVO: Superfície de alta resolução para salvar (invisível)
        self.hires_w = self.map_w * SCALE_FACTOR
        self.hires_h = self.map_h * SCALE_FACTOR
        self.hires_map = pygame.Surface((self.hires_w, self.hires_h))
        self.hires_map.fill((255, 255, 255))

        # Ajusta o tamanho dos elementos visuais
        self.node_rad = 2
        self.edge_thickness = 1
        
        # Cores
        self.grey, self.blue, self.green, self.red = (70, 70, 70), (0, 0, 255), (0, 255, 0), (255, 0, 0)

    def draw_map(self, obstacles):
        # Desenha na superfície de alta resolução (com escala)
        pygame.draw.circle(self.hires_map, self.green, (self.start[0]*SCALE_FACTOR, self.start[1]*SCALE_FACTOR), (self.node_rad + 5)*SCALE_FACTOR)
        pygame.draw.circle(self.hires_map, self.red, (self.goal[0]*SCALE_FACTOR, self.goal[1]*SCALE_FACTOR), (self.node_rad + 15)*SCALE_FACTOR, 3*SCALE_FACTOR)
        for obs in obstacles:
            scaled_obs = pygame.Rect(obs.x*SCALE_FACTOR, obs.y*SCALE_FACTOR, obs.w*SCALE_FACTOR, obs.h*SCALE_FACTOR)
            pygame.draw.rect(self.hires_map, self.grey, scaled_obs)
        
        # Copia a versão de alta resolução para a tela, ajustando o tamanho
        # Isso garante que a visualização na tela também fique mais nítida (antialiasing)
        scaled_down_map = pygame.transform.smoothscale(self.hires_map, (self.map_w, self.map_h))
        self.map.blit(scaled_down_map, (0, 0))

    def draw_path(self, path_coords):
        # Desenha o caminho final na superfície de alta resolução
        for x, y in path_coords:
            pygame.draw.circle(self.hires_map, self.red, (x*SCALE_FACTOR, y*SCALE_FACTOR), (self.node_rad + 3)*SCALE_FACTOR)

    def draw_tree_updates(self, x, y, parent_x, parent_y):
        # Desenha o crescimento da árvore na superfície de alta resolução
        pos = (x*SCALE_FACTOR, y*SCALE_FACTOR)
        parent_pos = (parent_x*SCALE_FACTOR, parent_y*SCALE_FACTOR)
        pygame.draw.circle(self.hires_map, self.blue, pos, self.node_rad*SCALE_FACTOR)
        pygame.draw.line(self.hires_map, self.blue, pos, parent_pos, self.edge_thickness*SCALE_FACTOR)
        
    def update_display(self):
        # Atualiza a janela de visualização com a versão em alta resolução
        scaled_down_map = pygame.transform.smoothscale(self.hires_map, (self.map_w, self.map_h))
        self.map.blit(scaled_down_map, (0, 0))
        pygame.display.update()

# ... (Classe RRTGraph sem alterações) ...
class RRTGraph:
    def __init__(self, start, goal, map_dimensions, obstacles):
        self.start, self.goal = start, goal
        self.map_h, self.map_w = map_dimensions
        self.obstacles = obstacles
        self.x, self.y, self.parent = [start[0]], [start[1]], [None]
        self.goal_flag, self.goal_state, self.path = False, None, []
    def number_of_nodes(self): return len(self.x)
    def distance(self, i, j): return math.hypot(self.x[i] - self.x[j], self.y[i] - self.y[j])
    def sample_point(self): return random.randint(0, self.map_w), random.randint(0, self.map_h)
    def nearest(self, idx):
        best, dmin = 0, self.distance(0, idx)
        for i in range(1, idx):
            d = self.distance(i, idx)
            if d < dmin: dmin, best = d, i
        return best
    def is_free(self, x, y): return all(not obs.collidepoint(x, y) for obs in self.obstacles)
    def crosses_obstacle(self, x1, y1, x2, y2):
        for obs in self.obstacles:
            for t in [i / 100 for i in range(101)]:
                x, y = x1 + t * (x2 - x1), y1 + t * (y2 - y1)
                if obs.collidepoint(x, y): return True
        return False
    def add_node(self, x, y, parent_idx):
        self.x.append(x); self.y.append(y); self.parent.append(parent_idx)
        return self.number_of_nodes() - 1
    def remove_last(self): self.x.pop(); self.y.pop(); self.parent.pop()
    def step(self, near, idx, maxd):
        dx, dy = self.x[idx] - self.x[near], self.y[idx] - self.y[near]
        dist = math.hypot(dx, dy)
        if dist > maxd:
            theta = math.atan2(dy, dx)
            self.x[idx], self.y[idx] = int(self.x[near] + maxd * math.cos(theta)), int(self.y[near] + maxd * math.sin(theta))
        self.parent[idx] = near
        if math.hypot(self.x[idx] - self.goal[0], self.y[idx] - self.goal[1]) < maxd:
            self.x[idx], self.y[idx] = self.goal
            self.goal_flag, self.goal_state = True, idx
        return idx
    def connect(self, near, idx):
        if self.crosses_obstacle(self.x[near], self.y[near], self.x[idx], self.y[idx]):
            node_idx_to_remove = self.number_of_nodes() - 1
            if self.goal_state == node_idx_to_remove:
                self.goal_flag = False
                self.goal_state = None
            self.remove_last()
            return False
        return True
    def expand(self, step_size):
        xr, yr = self.sample_point()
        if not self.is_free(xr, yr): return None
        idx = self.add_node(xr, yr, None)
        near = self.nearest(idx)
        self.step(near, idx, maxd=step_size)
        if self.connect(near, idx): return idx, near
        return None
    def bias(self, step_size):
        idx = self.add_node(self.goal[0], self.goal[1], None)
        near = self.nearest(idx)
        self.step(near, idx, maxd=step_size)
        if self.connect(near, idx): return idx, near
        return None
    def path_to_goal(self):
        if not self.goal_flag or self.goal_state is None: return False
        self.path, node = [], self.goal_state
        while node is not None:
            self.path.append(node)
            node = self.parent[node]
        self.path.reverse()
        return True
    def get_path_coords(self): return [(self.x[i], self.y[i]) for i in self.path]

def find_rrt_path(config):
    pygame.init()
    clock = pygame.time.Clock()
    
    dims = (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
    rrt_map = RRTMap(config.START_POS, config.GOAL_POS, dims)
    graph = RRTGraph(config.START_POS, config.GOAL_POS, dims, config.OBSTACLES)
    rrt_map.draw_map(config.OBSTACLES) # Desenha o mapa inicial

    for i in range(config.RRT_MAX_ITERATIONS):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); return None, None

        result = graph.bias(config.RRT_STEP_SIZE) if i % 10 == 0 else graph.expand(config.RRT_STEP_SIZE)
        
        if result:
            last, near = result
            # MODIFICADO: Chama o método de desenho da árvore
            rrt_map.draw_tree_updates(graph.x[last], graph.y[last], graph.x[near], graph.y[near])
        
        if graph.goal_flag:
            print(f"Caminho encontrado na iteração {i}!")
            graph.path_to_goal()
            path = graph.get_path_coords()
            rrt_map.draw_path(path) # Desenha o caminho final
            rrt_map.update_display() # Atualiza a tela uma última vez
            
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            # MODIFICADO: Salva a superfície de alta resolução em formato PNG
            filename = f"rrt_plan_{timestamp}.png"
            pygame.image.save(rrt_map.hires_map, filename)
            print(f"Plano do RRT salvo como '{filename}'")
            
            # ... (código da pausa com a tecla ESPAÇO sem alterações) ...
            pygame.display.set_caption("Caminho Encontrado! Pressione ESPAÇO para continuar.")
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit(); return None, None
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        waiting = False
                clock.tick(30)
            
            return rrt_map, path
        
        if i % 5 == 0:
            # MODIFICADO: Chama o método de atualização da tela
            rrt_map.update_display()

        clock.tick(60)

    print("Caminho não encontrado dentro do limite de iterações.")
    pygame.quit()
    return None, None
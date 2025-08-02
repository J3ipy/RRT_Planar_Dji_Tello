# plotter.py
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.lines import Line2D # CORREÇÃO: Importa a classe Line2D
import numpy as np

class RealTimePlotter:
    def __init__(self, data_queue, config):
        self.data_queue = data_queue
        self.config = config
        self.path_history = []
        self.current_state = None
        self.ax = None
        self.actual_path_line = None
        self.drone_marker = None
        # Inicializa as variáveis das setas
        self.quiver_x = None
        self.quiver_y = None

    def _update_plot(self, frame):
        # Esvazia a fila para pegar os dados mais recentes
        while not self.data_queue.empty():
            self.current_state = self.data_queue.get_nowait()
            self.path_history.append(self.current_state)

        if not self.path_history:
            return []
        
        # Extrai os dados de posição e orientação
        _, x_data, y_data, _, _, _, yaw_data, _, _ = zip(*self.path_history)
        
        # Atualiza o rastro e o marcador do drone
        self.actual_path_line.set_data(x_data, y_data)
        
        # Pega a última posição e orientação
        last_x, last_y, last_yaw = x_data[-1], y_data[-1], yaw_data[-1]
        self.drone_marker.set_data([last_x], [last_y])
        
        # --- Lógica de Atualização das Setas de Orientação ---
        angle_rad = np.radians(last_yaw)
        arrow_len = 15 # Comprimento das setas em cm
        
        # Eixo X do drone (frente, vermelho)
        dx_front = arrow_len * np.sin(angle_rad)
        dy_front = arrow_len * np.cos(angle_rad)
        
        # Eixo Y do drone (direita, verde)
        dx_right = arrow_len * np.cos(angle_rad)
        dy_right = -arrow_len * np.sin(angle_rad)
        
        # Atualiza a posição e a direção das setas
        self.quiver_x.set_offsets((last_x, last_y))
        self.quiver_x.set_UVC(dx_front, dy_front)
        
        self.quiver_y.set_offsets((last_x, last_y))
        self.quiver_y.set_UVC(dx_right, dy_right)

        return [self.actual_path_line, self.drone_marker, self.quiver_x, self.quiver_y]

    def run(self, planned_path_coords):
        fig, ax = plt.subplots(figsize=(10, 10))
        self.ax = ax
        
        ax.set_aspect('equal', adjustable='box')
        ax.set_title('Trajetória 2D em Tempo Real com Orientação')
        ax.set_xlabel('Eixo X (cm)'); ax.set_ylabel('Eixo Y (cm)')
        ax.grid(True)
        ax.set_xlim(0, self.config.SCREEN_WIDTH); ax.set_ylim(0, self.config.SCREEN_HEIGHT)
        
        px, py = zip(*planned_path_coords)
        ax.plot(px, py, 'r--', label='Caminho Planejado')
        ax.plot(px, py, 'ko', markersize=4, label='Nós do RRT')
        
        self.actual_path_line, = ax.plot([], [], 'b-', lw=2, label='Caminho Real')
        self.drone_marker, = ax.plot([], [], 'go', markersize=8, label='Drone')

        # Cria as setas uma única vez
        self.quiver_x = self.ax.quiver(0, 0, 0, 0, angles='xy', scale_units='xy', scale=1, color='red', width=0.005)
        self.quiver_y = self.ax.quiver(0, 0, 0, 0, angles='xy', scale_units='xy', scale=1, color='green', width=0.005)
        
        # --- Lógica para Legenda Customizada ---
        handles, labels = ax.get_legend_handles_labels()
        arrow_x_legend = Line2D([0], [0], color='red', lw=2, label='Eixo X Drone (Frente)')
        arrow_y_legend = Line2D([0], [0], color='green', lw=2, label='Eixo Y Drone (Direita)')
        handles.extend([arrow_x_legend, arrow_y_legend])
        ax.legend(handles=handles)
        
        # blit=False é mais estável quando se manipula artistas complexos como quiver
        self.ani = FuncAnimation(fig, self._update_plot, interval=200, blit=False, cache_frame_data=False)
        plt.show()
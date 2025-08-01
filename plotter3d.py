# plotter3d.py
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D # Essencial para plots 3D

class RealTimePlotter3D:
    def __init__(self, manager, config):
        self.manager = manager
        self.config = config
        
        # --- Configuração da Figura e dos Eixos 3D ---
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        self.ax.set_title('Trajetória do Drone em Tempo Real (3D)')
        self.ax.set_xlabel('Eixo X (cm)')
        self.ax.set_ylabel('Eixo Y (cm)')
        self.ax.set_zlabel('Altitude Z (cm)')
        
        # Define os limites do gráfico
        self.ax.set_xlim(0, self.config.SCREEN_WIDTH)
        self.ax.set_ylim(0, self.config.SCREEN_HEIGHT)
        self.ax.set_zlim(0, 150) # Limite de altura de 1.5m

        # --- Elementos do Gráfico que serão animados ---
        self.planned_path_line, = self.ax.plot([], [], [], 'r--', label='Caminho Planejado (2D)')
        self.actual_path_line, = self.ax.plot([], [], [], 'b-', label='Caminho Real (3D)')
        self.drone_marker, = self.ax.plot([], [], [], 'go', markersize=10, label='Drone')
        self.ax.legend()

    def _update_plot(self, frame):
        """Atualiza o gráfico 3D a cada quadro da animação."""
        history = self.manager.path_history
        if not history:
            return self.actual_path_line, self.drone_marker

        # Desempacota as coordenadas x, y, e z do histórico
        x_data, y_data, z_data = zip(*history)
        
        # Atualiza os dados da linha do caminho real 3D
        self.actual_path_line.set_data(x_data, y_data)
        self.actual_path_line.set_3d_properties(z_data)
        
        # Atualiza a posição do marcador do drone 3D
        self.drone_marker.set_data([x_data[-1]], [y_data[-1]])
        self.drone_marker.set_3d_properties([z_data[-1]])

        return self.actual_path_line, self.drone_marker

    def run(self, planned_path_coords):
        """Inicia a janela do gráfico e a animação."""
        # O caminho planejado é 2D, então plotamos ele na altitude alvo
        px, py = zip(*planned_path_coords)
        pz = [self.config.TELLO_TARGET_ALTITUDE] * len(px)
        self.planned_path_line.set_data(px, py)
        self.planned_path_line.set_3d_properties(pz)
        
        self.ani = FuncAnimation(
            self.fig, 
            self._update_plot, 
            interval=200, 
            blit=True,
            cache_frame_data=False
        )
        
        plt.show()
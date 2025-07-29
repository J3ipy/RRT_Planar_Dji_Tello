# plotter.py
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

class RealTimePlotter:
    # ... (método __init__ sem alterações) ...
    def __init__(self, manager, config):
        self.manager = manager
        self.config = config
        self.fig, self.ax = plt.subplots()
        self.ax.set_aspect('equal', adjustable='box')
        self.ax.set_title('Trajetória do Drone em Tempo Real')
        self.ax.set_xlabel('Eixo X (cm)')
        self.ax.set_ylabel('Eixo Y (cm)')
        self.ax.grid(True)
        self.ax.set_xlim(0, self.config.SCREEN_WIDTH)
        self.ax.set_ylim(0, self.config.SCREEN_HEIGHT)
        self.planned_path_line, = self.ax.plot([], [], 'r--', label='Caminho Planejado')
        self.actual_path_line, = self.ax.plot([], [], 'b-', label='Caminho Real')
        self.drone_marker, = self.ax.plot([], [], 'go', markersize=10, label='Drone')
        self.ax.legend()


    def _update_plot(self, frame):
        """
        Esta função é chamada repetidamente pela FuncAnimation para atualizar o gráfico.
        """
        history = self.manager.path_history
        if not history:
            return self.actual_path_line, self.drone_marker

        x_data, y_data = zip(*history)
        
        self.actual_path_line.set_data(x_data, y_data)
        
        # --- CORREÇÃO AQUI ---
        # Envolvemos as coordenadas em colchetes para criar uma lista com um item.
        self.drone_marker.set_data([x_data[-1]], [y_data[-1]])

        return self.actual_path_line, self.drone_marker

    def run(self, planned_path_coords):
        # ... (método run sem alterações) ...
        px, py = zip(*planned_path_coords)
        self.planned_path_line.set_data(px, py)
        
        self.ani = FuncAnimation(
            self.fig, 
            self._update_plot, 
            interval=200, 
            blit=True,
            cache_frame_data=False
        )
        
        plt.show()
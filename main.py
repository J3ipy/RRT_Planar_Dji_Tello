# main.py (Versão com Pygame e Matplotlib em Tempo Real)
import pygame
import time
import threading
import config
from datetime import datetime
import matplotlib.pyplot as plt
from rrt_planner import find_rrt_path
from tello_handler import TelloManager
from plotter import RealTimePlotter

from plotter3d import RealTimePlotter3D

def console_input_listener(cancel_event):
    """Escuta o console para o comando de cancelamento 'c'."""
    print("\n>>> Pressione a tecla 'c' (e depois Enter) a qualquer momento para cancelar o voo.")
    while not cancel_event.is_set():
        try:
            user_input = input()
            if user_input.lower() == 'c':
                print("\n[!] 'c' pressionado no console! Enviando sinal de cancelamento...")
                cancel_event.set()
                break
        except (EOFError, KeyboardInterrupt):
            cancel_event.set()
            break
    print(">>> Thread de escuta do console finalizada.")

def save_final_plot(manager, planned_path, config):
    """Cria e salva um gráfico estático com o resultado final do voo."""
    # ... (Esta função permanece exatamente a mesma da versão anterior)
    print("Salvando o gráfico final da trajetória...")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"trajetoria_final_matplotlib_{timestamp}.jpg"

    fig, ax = plt.subplots()
    ax.set_aspect('equal', adjustable='box')
    ax.set_title('Resultado Final da Trajetória')
    ax.set_xlabel('Eixo X (cm)')
    ax.set_ylabel('Eixo Y (cm)')
    ax.grid(True)
    ax.set_xlim(0, config.SCREEN_WIDTH)
    ax.set_ylim(0, config.SCREEN_HEIGHT)

    px, py = zip(*planned_path)
    ax.plot(px, py, 'r--', label='Caminho Planejado')

    if len(manager.path_history) > 1:
        real_x, real_y = zip(*manager.path_history)
        ax.plot(real_x, real_y, 'b-', label='Caminho Real')

    ax.legend()
    fig.savefig(filename, dpi=300)
    print(f"Gráfico final salvo como '{filename}'")
    plt.close(fig)


def main():
    # 1. Planejar o caminho usando a visualização Pygame
    rrt_map, path = find_rrt_path(config)
    
    if not path:
        print("Programa encerrado durante o planejamento."); return

    print("Caminho a ser executado:", path)

    if input("Deseja iniciar o voo? (s/n): ").lower() != 's':
        pygame.quit(); print("Voo cancelado pelo usuário."); return

    # 2. Preparar para o voo e as duas visualizações
    manager = TelloManager()
    plotter_2d = RealTimePlotter(manager, config)
    plotter_3d = RealTimePlotter3D(manager, config)

    input_thread = threading.Thread(target=console_input_listener, args=(manager.cancel,), daemon=True)
    flight_thread = threading.Thread(target=manager.execute_flight_plan, args=(path, config.TELLO_TARGET_ALTITUDE))
    

    plot_thread_2d = threading.Thread(target=plotter_2d.run, args=(path,))
    plot_thread_3d = threading.Thread(target=plotter_3d.run, args=(path,))
    
    input_thread.start()
    flight_thread.start()
    plot_thread_2d.start()
    plot_thread_3d.start()
    
    # 3. A thread principal agora gerencia a janela do Pygame em tempo real
    clock = pygame.time.Clock()
    running = True
    while running and flight_thread.is_alive():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                manager.cancel.set(); running = False

        # --- Lógica de Desenho em Tempo Real no Pygame ---
        rrt_map.draw_map(config.OBSTACLES)
        rrt_map.draw_path(path)

        if len(manager.path_history) > 1:
            path_points = [(int(p[0]), int(p[1])) for p in manager.path_history]
            pygame.draw.lines(rrt_map.map, (0, 0, 255), False, path_points, 4)
            pygame.draw.lines(rrt_map.hires_map, (0, 0, 255), False, [(p[0]*5, p[1]*5) for p in path_points], 4*5)

        if manager.current_waypoint_index < len(path):
            target_waypoint = path[manager.current_waypoint_index]
            pygame.draw.circle(rrt_map.map, (0, 255, 0), target_waypoint, 8)
            pygame.draw.circle(rrt_map.map, (0, 0, 0), target_waypoint, 8, 2)
            pygame.draw.circle(rrt_map.hires_map, (0, 255, 0), (target_waypoint[0]*5, target_waypoint[1]*5), 8*5)
            pygame.draw.circle(rrt_map.hires_map, (0, 0, 0), (target_waypoint[0]*5, target_waypoint[1]*5), 8*5, 2*5)

        pygame.display.update()
        clock.tick(30)

    # 4. Finalização
    print("Voo finalizado. Aguardando fechamento das janelas...")
    flight_thread.join()
    

    # Salva a imagem final do Pygame
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename_pygame = f"trajetoria_final_pygame_{timestamp}.png"
    pygame.image.save(rrt_map.hires_map, filename_pygame)
    print(f"Visualização final do Pygame salva como '{filename_pygame}'")
    
    # Salva a imagem final do Matplotlib
    save_final_plot(manager, path, config)
    
    pygame.quit()
    print("Programa finalizado.")

if __name__ == '__main__':
    main()
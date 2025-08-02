import pygame
import time
import threading
import config
from datetime import datetime
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D # Necessário para o plot 3D
import multiprocessing as mp
from rrt_planner import find_rrt_path
from tello_handler import TelloManager
from plotter import RealTimePlotter

def console_input_listener(cancel_event):
    """Escuta o console para o comando de cancelamento 'c'."""
    print("\n>>> Pressione a tecla 'c' (e depois Enter) para cancelar o voo.")
    while not cancel_event.is_set():
        try:
            if input().lower() == 'c':
                print("\n[!] 'c' pressionado! Cancelando...")
                cancel_event.set(); break
        except:
            break
    print(">>> Listener do console finalizado.")

def save_final_plot_2d(manager, planned_path, config):
    """Cria e salva um gráfico estático 2D com o resultado final do voo."""
    print("Salvando o gráfico final da trajetória 2D...")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"trajetoria_final_2d_{timestamp}.jpg"
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect('equal', adjustable='box')
    ax.set_title('Resultado Final da Trajetória (2D)')
    ax.set_xlabel('Eixo X (cm)'); ax.set_ylabel('Eixo Y (cm)')
    ax.grid(True)
    ax.set_xlim(0, config.SCREEN_WIDTH); ax.set_ylim(0, config.SCREEN_HEIGHT)
    px, py = zip(*planned_path)
    ax.plot(px, py, 'r--', label='Caminho Planejado')
    if len(manager.path_history) > 1:
        _, real_x, real_y, _, _, _, _, _, _ = zip(*manager.path_history)
        ax.plot(real_x, real_y, 'b-', label='Caminho Real')
    ax.plot(px, py, 'ko', markersize=4, label='Nós do RRT')
    ax.legend(); fig.savefig(filename, dpi=300)
    print(f"Gráfico 2D salvo como '{filename}'")
    plt.close(fig)

def save_final_plot_3d(manager, planned_path, config):
    """Cria e salva um gráfico estático 3D com o resultado final do voo."""
    print("Salvando o gráfico final da trajetória 3D...")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"trajetoria_final_3d_{timestamp}.jpg"
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_title('Resultado Final da Trajetória (3D)')
    ax.set_xlabel('Eixo X (cm)'); ax.set_ylabel('Eixo Y (cm)'); ax.set_zlabel('Altitude Z (cm)')
    ax.set_xlim(0, config.SCREEN_WIDTH); ax.set_ylim(0, config.SCREEN_HEIGHT); ax.set_zlim(0, 150)
    px, py = zip(*planned_path)
    pz = [config.TELLO_TARGET_ALTITUDE] * len(px)
    ax.plot(px, py, pz, 'r--', label='Caminho Planejado')
    if len(manager.path_history) > 1:
        _, real_x, real_y, real_z, _, _, _, _, _ = zip(*manager.path_history)
        ax.plot(real_x, real_y, real_z, 'b-', label='Caminho Real')
    ax.legend(); fig.savefig(filename, dpi=300)
    print(f"Gráfico 3D salvo como '{filename}'")
    plt.close(fig)

def save_velocity_plot(manager):
    """Cria e salva um gráfico da velocidade do drone ao longo do tempo."""
    print("Salvando o gráfico de velocidade...")
    if len(manager.path_history) < 2:
        print("Não há dados de velocidade suficientes para plotar.")
        return

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"velocidade_vs_tempo_{timestamp}.jpg"
    
    times, _, _, _, _, _, _, speeds, waypoint_indices = zip(*manager.path_history)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_title('Velocidade do Drone vs. Tempo')
    ax.set_xlabel('Tempo (s)')
    ax.set_ylabel('Velocidade (cm/s)')
    ax.grid(True)
    
    ax.plot(times, speeds, '-', label='Velocidade')
    
    last_wp = -1
    for i, wp_index in enumerate(waypoint_indices):
        if wp_index != last_wp and wp_index > 0:
            ax.axvline(x=times[i], color='r', linestyle='--', linewidth=0.8)
            ax.text(times[i] + 0.1, max(speeds)*0.9, f'WP {wp_index}', rotation=90, color='r')
            last_wp = wp_index
            
    ax.legend()
    fig.savefig(filename, dpi=300)
    print(f"Gráfico de velocidade salvo como '{filename}'")
    plt.close(fig)

def plotter_process(plotter_class, data_queue, path):
    """ Função que será executada em um processo separado para o plotter 2D. """
    import config
    plotter = plotter_class(data_queue, config)
    plotter.run(path)

def main():
    _, path = find_rrt_path(config)
    if not path:
        print("Programa encerrado durante o planejamento."); return

    print("Caminho a ser executado:", path)
    pygame.quit()

    if input("Deseja iniciar o voo? (s/n): ").lower() != 's':
        print("Voo cancelado pelo usuário."); return

    data_queue = mp.Queue()
    cancel_event = mp.Event()
    manager = TelloManager(data_queue, cancel_event)
    
    input_thread = threading.Thread(target=console_input_listener, args=(cancel_event,), daemon=True)
    flight_thread = threading.Thread(target=manager.execute_flight_plan, args=(path, config.TELLO_TARGET_ALTITUDE))
    
    # Apenas o processo do plotter 2D é iniciado
    plot_process_2d = mp.Process(target=plotter_process, args=(RealTimePlotter, data_queue, path))
    
    input_thread.start(); flight_thread.start(); plot_process_2d.start()
    flight_thread.join()
    print("\nVoo finalizado. Salvando resultados...")

    if plot_process_2d.is_alive():
        plot_process_2d.terminate(); plot_process_2d.join()

    # Salva todos os gráficos finais
    save_final_plot_2d(manager, path, config)
    save_final_plot_3d(manager, path, config)
    save_velocity_plot(manager)
    
    print("Programa finalizado.")

if __name__ == '__main__':
    mp.freeze_support()
    main()
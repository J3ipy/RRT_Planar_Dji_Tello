# main.py (Versão Final e Corrigida)
import pygame
import time
import threading
import config
from datetime import datetime
import matplotlib.pyplot as plt
from rrt_planner import find_rrt_path
from tello_handler import TelloManager
from plotter import RealTimePlotter

def console_input_listener(cancel_event):
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
    print("Salvando o gráfico final da trajetória...")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"trajetoria_final_{timestamp}.jpg"

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
        # CORRIGIDO: Renomeado para evitar conflito com a variável 'ax' do gráfico.
        real_x, real_y = zip(*manager.path_history)
        ax.plot(real_x, real_y, 'b-', label='Caminho Real')

    ax.legend()
    fig.savefig(filename)
    print(f"Gráfico final salvo como '{filename}'")
    plt.close(fig)

def main():
    rrt_map, path = find_rrt_path(config)
    
    if not path:
        print("Programa encerrado durante o planejamento.")
        return

    print("Caminho a ser executado:", path)
    pygame.quit() 

    if input("Deseja iniciar o voo? (s/n): ").lower() != 's':
        print("Voo cancelado pelo usuário."); return

    manager = TelloManager()
    plotter = RealTimePlotter(manager, config)

    input_thread = threading.Thread(target=console_input_listener, args=(manager.cancel,), daemon=True)
    flight_thread = threading.Thread(target=manager.execute_flight_plan, args=(path, config.TELLO_TARGET_ALTITUDE))
    
    input_thread.start()
    flight_thread.start()

    plotter.run(path)

    print("Janela do gráfico fechada. Enviando comando de pouso, se necessário...")
    manager.cancel.set()
    
    flight_thread.join()

    # Salva o gráfico final após o voo ter terminado completamente
    save_final_plot(manager, path, config)

    print("Programa finalizado.")

if __name__ == '__main__':
    main()
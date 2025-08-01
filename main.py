# main.py (Versão com Visualização em Tempo Real no Pygame)
import pygame
import time
import threading
import config
from datetime import datetime
from rrt_planner import find_rrt_path
from tello_handler import TelloManager

def console_input_listener(cancel_event):
    # ... (função console_input_listener sem alterações) ...
    print("\n>>> Pressione a tecla 'c' (e depois Enter) a qualquer momento para cancelar o voo.")
    while not cancel_event.is_set():
        try:
            user_input = input() 
            if user_input.lower() == 'c':
                print("\n[!] 'c' pressionado no console! Enviando sinal de cancelamento...")
                cancel_event.set(); break
        except (EOFError, KeyboardInterrupt):
            cancel_event.set(); break
    print(">>> Thread de escuta do console finalizada.")


def main():
    # 1. Planejar o caminho. A janela do Pygame é criada aqui.
    rrt_map, path = find_rrt_path(config)
    
    if not path:
        print("Programa encerrado durante o planejamento."); return

    print("Caminho a ser executado:", path)

    if input("Deseja iniciar o voo? (s/n): ").lower() != 's':
        pygame.quit(); print("Voo cancelado pelo usuário."); return

    # 2. Preparar para o voo
    manager = TelloManager()
    
    input_thread = threading.Thread(target=console_input_listener, args=(manager.cancel,), daemon=True)
    flight_thread = threading.Thread(target=manager.execute_flight_plan, args=(path, config.TELLO_TARGET_ALTITUDE))
    
    input_thread.start()
    flight_thread.start()
    
    # 3. NOVO: Loop de Animação no Pygame durante o Voo
    clock = pygame.time.Clock()
    running = True
    while running and flight_thread.is_alive():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                manager.cancel.set(); running = False

        # --- Lógica de Desenho em Tempo Real ---
        # 1. Limpa a tela e redesenha o mapa base
        rrt_map.draw_map(config.OBSTACLES)

        # 2. Desenha o caminho completo planejado (em vermelho)
        rrt_map.draw_path(path)

        # 3. Desenha o rastro do caminho já percorrido (em azul)
        if len(manager.path_history) > 1:
            path_points = [(int(p[0]), int(p[1])) for p in manager.path_history]
            # Desenha na tela principal com escala normal
            pygame.draw.lines(rrt_map.map, (0, 0, 255), False, path_points, 4)
            # Desenha na superfície de alta resolução para salvar no final
            pygame.draw.lines(rrt_map.hires_map, (0, 0, 255), False, [(p[0]*5, p[1]*5) for p in path_points], 4*5)


        # 4. Desenha o "alvo" do drone: o waypoint para onde ele está indo
        if manager.current_waypoint_index < len(path):
            target_waypoint = path[manager.current_waypoint_index]
            # Desenha na tela principal
            pygame.draw.circle(rrt_map.map, (0, 255, 0), target_waypoint, 8) # Ponto verde
            pygame.draw.circle(rrt_map.map, (0, 0, 0), target_waypoint, 8, 2) # Contorno preto
            # Desenha na hires_map
            pygame.draw.circle(rrt_map.hires_map, (0, 255, 0), (target_waypoint[0]*5, target_waypoint[1]*5), 8*5)
            pygame.draw.circle(rrt_map.hires_map, (0, 0, 0), (target_waypoint[0]*5, target_waypoint[1]*5), 8*5, 2*5)


        # Atualiza a tela
        pygame.display.update()
        clock.tick(30) # Limita a 30 quadros por segundo

    # 4. Finalização
    flight_thread.join()

    # Salva a imagem final com o rastro do voo
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"trajetoria_final_pygame_{timestamp}.png"
    pygame.image.save(rrt_map.hires_map, filename)
    print(f"Visualização final da trajetória salva como '{filename}'")
    
    pygame.quit()
    print("Programa finalizado.")

if __name__ == '__main__':
    main()
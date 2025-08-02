import time
import math
import threading
from djitellopy import Tello

class TelloManager:
    def __init__(self, data_queue, cancel_event):
        self.tello = Tello()
        self.data_queue = data_queue
        self.cancel_event = cancel_event
        self.is_flying = False
        
        self.x = self.y = self.z = self.angle = 0
        self.path_history = []
        self.current_waypoint_index = 0
        self.start_time = 0

    def _feedback(self):
        """ Thread simples para imprimir o feedback no console. """
        while not self.cancel_event.is_set():
            try:
                # Lê a velocidade para o feedback do console
                speed = math.hypot(self.tello.get_speed_x(), self.tello.get_speed_y())
                print(f"Pos(x,y)=({self.x:.1f},{self.y:.1f}) | z={self.z}cm | v={speed:.1f}cm/s | Waypoint: {self.current_waypoint_index} ", end='\r')
                time.sleep(0.5)
            except Exception:
                break
        print("\nFeedback encerrado.")

    def execute_flight_plan(self, path, target_altitude):
        feedback_thread = None
        try:
            self.tello.connect()
            self.start_time = time.time()
            bat = self.tello.get_battery()
            print(f"Bateria: {bat}%")
            if bat < 20: print("Bateria baixa. Voo cancelado."); return

            self.tello.takeoff()
            self.is_flying = True
            time.sleep(1)

            h = self.tello.get_height()
            move_down_cm = h - target_altitude
            if move_down_cm >= 20:
                self.tello.move_down(move_down_cm)
                time.sleep(2)
            
            self.x, self.y = path[0]
            self.z = self.tello.get_height()
            
            initial_state = (0, self.x, self.y, self.z, 0, 0, self.angle, 0, self.current_waypoint_index)
            self.path_history.append(initial_state)
            self.data_queue.put(initial_state)

            feedback_thread = threading.Thread(target=self._feedback, daemon=True)
            feedback_thread.start()

            for i in range(len(path) - 1):
                if self.cancel_event.is_set():
                    print("\nVoo cancelado pelo usuário."); break
                
                self.current_waypoint_index = i + 1
                p1, p2 = path[i], path[i+1]
                
                current_yaw = self.tello.get_yaw()
                dx, dy = p2[0] - p1[0], p2[1] - p1[1]
                dist = math.hypot(dx, dy)
                target_angle = math.degrees(math.atan2(dx, dy))
                rot = (target_angle - current_yaw + 180) % 360 - 180
                
                speed = 0 # Inicia a velocidade do segmento como zero

                if abs(rot) > 5:
                    if rot > 0: self.tello.rotate_clockwise(int(rot))
                    else: self.tello.rotate_counter_clockwise(int(-rot))
                    time.sleep(1.5)
                
                if dist > 0 and not self.cancel_event.is_set():
                    step = int(max(20, min(500, dist)))
                    
                    # --- Cálculo de velocidade média ---
                    t_start = time.time()
                    self.tello.move_forward(step)
                    t_end = time.time()
                    
                    duration = t_end - t_start
                    if duration > 0:
                        speed = dist / duration
                    
                    time.sleep(1)

                # Após cada movimento, calcula e envia o estado completo
                self.angle = self.tello.get_yaw()
                rad = math.radians(self.angle)
                self.x += dist * math.sin(rad)
                self.y += dist * math.cos(rad)
                self.z = self.tello.get_height()
                state = self.tello.get_current_state()
                roll, pitch = state['roll'], state['pitch']
                relative_time = time.time() - self.start_time
                
                current_state = (relative_time, self.x, self.y, self.z, roll, pitch, self.angle, speed, self.current_waypoint_index)
                self.path_history.append(current_state)
                self.data_queue.put(current_state)

            if not self.cancel_event.is_set():
                print("\nPlano de voo completo!")

        except Exception as e:
            print(f"\nOcorreu um erro durante o voo: {e}")
        finally:
            self.cancel_event.set()
            if feedback_thread and feedback_thread.is_alive():
                feedback_thread.join(timeout=1)
            try:
                if self.is_flying:
                    print("Pousando..."); self.tello.land()
                    self.is_flying = False
            except Exception as e:
                print(f"Não foi possível pousar automaticamente: {e}")
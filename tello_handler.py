import time
import math
import threading
from djitellopy import Tello

class TelloManager:
    def __init__(self):
        self.tello = Tello()
        self.is_flying = False
        self.stop_fb = threading.Event()
        self.cancel = threading.Event()
        self.x = self.y = self.z = self.angle = self.speed = 0
        
        # Lista para armazenar o histórico de posições.
        self.path_history = []
        self.current_waypoint_index = 0

    def _feedback(self):
        while not self.stop_fb.is_set():
            try:
                self.z = self.tello.get_height()
                vx, vy = self.tello.get_speed_x(), self.tello.get_speed_y()
                self.speed = math.hypot(vx, vy)
                print(f"Pos (x,y)=({self.x:.1f},{self.y:.1f}) | z={self.z}cm | v={self.speed:.1f}cm/s | ", end='\r')
                time.sleep(0.2)
            except Exception:
                break
        print("\nFeedback encerrado.")

    def execute_flight_plan(self, path, target_altitude):
        fb = None
        try:
            self.tello.connect()
            bat = self.tello.get_battery()
            print(f"Bateria: {bat}%")
            if bat < 20:
                print("Bateria baixa. Voo cancelado."); return

            self.tello.takeoff()
            self.is_flying = True
            time.sleep(1)

            h = self.tello.get_height()
            if h > target_altitude:
                self.tello.move_down(h - target_altitude)
            time.sleep(2)

            fb = threading.Thread(target=self._feedback)
            fb.start()
            
            # Inicializa a odometria e o histórico
            self.x, self.y = path[0]
            self.z = self.tello.get_height()
            self.path_history = [(self.x, self.y, self.z)]
            self.current_waypoint_index = 0

            for i in range(len(path) - 1):
                if self.cancel.is_set():
                    print("\nVoo cancelado pelo usuário."); break
                
                self.current_waypoint_index = i + 1
                p1, p2 = path[i], path[i+1]
                dx, dy = p2[0] - p1[0], p2[1] - p1[1]
                dist = math.hypot(dx, dy)
                target = math.degrees(math.atan2(dx, dy))
                rot = (target - self.angle + 180) % 360 - 180

                if abs(rot) > 5:
                    if rot > 0: self.tello.rotate_clockwise(int(rot))
                    else: self.tello.rotate_counter_clockwise(int(-rot))
                    self.angle += rot
                    time.sleep(2)
                
                if dist > 0 and not self.cancel.is_set():
                    step = int(max(20, min(500, dist)))
                    self.tello.move_forward(step)

                    rad = math.radians(self.angle)
                    self.x += step * math.sin(rad)
                    self.y += step * math.cos(rad)
                    self.z = self.tello.get_height()
                    
                    self.path_history.append((self.x, self.y, self.z))
                    time.sleep(2)

            if not self.cancel.is_set():
                print("\nPlano de voo completo!")
        except Exception as e:
            print(f"\nOcorreu um erro durante o voo: {e}")
        finally:
            self.stop_fb.set()
            if self.is_flying:
                print("Pousando..."); self.tello.land()
            if fb and fb.is_alive():
                fb.join()
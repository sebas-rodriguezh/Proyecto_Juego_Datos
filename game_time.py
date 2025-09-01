# game_time.py
import pygame

class GameTime:
    def __init__(self, total_duration_min=15):
        """
        Inicializa el tiempo de juego
        total_duration_min: duración total de la jornada en minutos (tiempo real)
        """
        self.total_duration_sec = total_duration_min * 60  # Convertir a segundos
        self.elapsed_time_sec = 0
        self.is_running = False
        self.game_speed = 1.0  # Velocidad del juego (1.0 = tiempo real)
        
    def start(self):
        """Inicia el temporizador del juego"""
        self.is_running = True
        
    def update(self, dt):
        """Actualiza el tiempo transcurrido"""
        if self.is_running:
            self.elapsed_time_sec += dt * self.game_speed
            
    def get_remaining_time(self):
        """Devuelve el tiempo restante en segundos"""
        return max(0, self.total_duration_sec - self.elapsed_time_sec)
    
    def get_remaining_time_formatted(self):
        """Devuelve el tiempo restante formateado (MM:SS)"""
        remaining = self.get_remaining_time()
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def get_progress(self):
        """Devuelve el progreso de la jornada (0.0 a 1.0)"""
        return min(1.0, self.elapsed_time_sec / self.total_duration_sec)
    
    def is_time_up(self):
        """Verifica si se acabó el tiempo"""
        return self.elapsed_time_sec >= self.total_duration_sec
    
    def pause(self):
        """Pausa el juego"""
        self.is_running = False
        
    def resume(self):
        """Reanuda el juego"""
        self.is_running = True
        
    def set_game_speed(self, speed):
        """Establece la velocidad del juego"""
        self.game_speed = max(0.1, min(5.0, speed))  # Limitar entre 0.1x y 5x
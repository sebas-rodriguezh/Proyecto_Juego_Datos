# game_time.py
import pygame
from datetime import datetime, timedelta

class GameTime:
    def __init__(self, total_duration_min=15):
        self.total_duration = total_duration_min * 60  # Convertir a segundos
        self.start_time = None
        self.paused = False
        self.pause_start = None
        self.pause_duration = 0
    
    def start(self):
        """Inicia el temporizador del juego"""
        self.start_time = pygame.time.get_ticks() / 1000.0  # Tiempo en segundos
        self.paused = False
        self.pause_duration = 0
    
    def pause(self):
        """Pausa el temporizador del juego"""
        if not self.paused and self.start_time is not None:
            self.paused = True
            self.pause_start = pygame.time.get_ticks() / 1000.0
    
    def resume(self):
        """Reanuda el temporizador del juego"""
        if self.paused and self.pause_start is not None:
            self.paused = False
            self.pause_duration += (pygame.time.get_ticks() / 1000.0) - self.pause_start
            self.pause_start = None
    
    def get_elapsed_time(self):
        """Retorna el tiempo transcurrido en segundos (excluyendo pausas)"""
        if self.start_time is None:
            return 0
        
        if self.paused:
            # Si está pausado, usar el tiempo hasta que se pausó
            elapsed = self.pause_start - self.start_time - self.pause_duration
        else:
            # Si no está pausado, calcular tiempo actual menos pausas
            current_time = pygame.time.get_ticks() / 1000.0
            elapsed = current_time - self.start_time - self.pause_duration
        
        return max(0, elapsed)  # Asegurar que no sea negativo
    
    def get_remaining_time(self):
        """Retorna el tiempo restante en segundos"""
        elapsed = self.get_elapsed_time()
        remaining = self.total_duration - elapsed
        return max(0, remaining)  # Asegurar que no sea negativo
    
    def get_remaining_time_formatted(self):
        """Retorna el tiempo restante formateado como MM:SS"""
        remaining = self.get_remaining_time()
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def is_time_up(self):
        """Verifica si el tiempo se ha agotado"""
        return self.get_remaining_time() <= 0
    
    def update(self, dt):
        """Actualiza el estado del tiempo (para consistencia con otros sistemas)"""
        # Este método se mantiene para compatibilidad, pero la lógica principal
        # está en get_elapsed_time() que se calcula on-demand
        pass
    
    # game_time.py - Añadir método para obtener duración total
    def get_total_duration(self):
        """Retorna la duración total en segundos"""
        return self.total_duration
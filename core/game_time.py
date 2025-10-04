import pygame
from datetime import datetime, timedelta

class GameTime:
    #Todos los métodos O(1)
    def __init__(self, total_duration_min=15, game_start_time=None, time_scale=3.0):
        self.real_duration = total_duration_min * 60  
        self.time_scale = time_scale
        
        if game_start_time is None:
            self.game_start_time = datetime.now()
        else:
            self.game_start_time = game_start_time
        
        self.pygame_start_time = pygame.time.get_ticks() / 1000.0
        self.start_real_time = None
        
        self.paused = False
        self.pause_start = None
        self.pause_duration = 0
        
    def start(self):
        """Inicia el temporizador del juego"""
        if self.start_real_time is None:
            current_pygame_time = pygame.time.get_ticks() / 1000.0
            self.start_real_time = current_pygame_time - self.pygame_start_time
        
        self.paused = False
        if self.pause_duration == 0:  
            self.pause_duration = 0
    
    def pause(self):
        if not self.paused and self.start_real_time is not None:
            self.paused = True
            self.pause_start = pygame.time.get_ticks() / 1000.0
    
    def resume(self):
        if self.paused and self.pause_start is not None:
            self.paused = False
            pause_end = pygame.time.get_ticks() / 1000.0
            self.pause_duration += pause_end - self.pause_start
            self.pause_start = None
    
    def get_elapsed_real_time(self):
        """Retorna el tiempo REAL transcurrido en segundos"""
        if self.start_real_time is None:
            return 0
        
        current_pygame_time = pygame.time.get_ticks() / 1000.0
        current_relative_time = current_pygame_time - self.pygame_start_time
        
        if self.paused:
            elapsed = self.pause_start - self.start_real_time - self.pause_duration
        else:
            elapsed = current_relative_time - self.start_real_time - self.pause_duration
        
        return max(0, elapsed)
    
    def normalize_date_to_game_day(self, datetime_obj):
        """Normaliza cualquier datetime para usar la fecha del juego"""
        if isinstance(datetime_obj, datetime):
            return datetime_obj.replace(
                year=self.game_start_time.year,
                month=self.game_start_time.month, 
                day=self.game_start_time.day
            )
        return datetime_obj

    def get_current_game_time(self):
        """Retorna la hora ACTUAL en el mundo del juego"""
        if self.start_real_time is None:
            return self.game_start_time
        
        elapsed_real = self.get_elapsed_real_time()
        elapsed_game_seconds = elapsed_real * self.time_scale
        
        current_game_time = self.game_start_time + timedelta(seconds=elapsed_game_seconds)
        return current_game_time
    
    def get_elapsed_game_time(self):
        """Retorna tiempo de juego transcurrido en segundos (escala de juego)"""
        elapsed_real = self.get_elapsed_real_time()
        return elapsed_real * self.time_scale
    
    def debug_time_comparison(self, order_deadline):
        """Compara tiempo actual vs deadline para debugging"""
        current_time = self.get_current_game_time()
        normalized_deadline = self.normalize_date_to_game_day(order_deadline)
        return current_time, normalized_deadline
    
    def get_remaining_real_time(self):
        elapsed_real = self.get_elapsed_real_time()
        remaining = self.real_duration - elapsed_real
        return max(0, remaining)
    
    def get_remaining_time_formatted(self):
        remaining = self.get_remaining_real_time()
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def get_game_time_formatted(self):
        current_time = self.get_current_game_time()
        return current_time.strftime("%H:%M:%S")
    
    def get_game_datetime_formatted(self):
        current_time = self.get_current_game_time()
        return current_time.strftime("%Y-%m-%d %H:%M:%S")
    
    def is_time_up(self):
        return self.get_remaining_real_time() <= 0
    
    def update(self, dt):
        pass
    

    def get_total_duration(self):
        return self.real_duration
# weather.py
import random
import pygame
import requests
import json
import os
from enum import Enum

class WeatherCondition(Enum):
    CLEAR = "clear"
    CLOUDS = "clouds"
    RAIN_LIGHT = "rain_light"
    RAIN = "rain"
    STORM = "storm"
    FOG = "fog"
    WIND = "wind"
    HEAT = "heat"
    COLD = "cold"

class Weather:
    # Multiplicadores de velocidad para cada condición climática
    SPEED_MULTIPLIERS = {
        WeatherCondition.CLEAR: 1.00,
        WeatherCondition.CLOUDS: 0.98,
        WeatherCondition.RAIN_LIGHT: 0.90,
        WeatherCondition.RAIN: 0.85,
        WeatherCondition.STORM: 0.75,
        WeatherCondition.FOG: 0.88,
        WeatherCondition.WIND: 0.92,
        WeatherCondition.HEAT: 0.90,
        WeatherCondition.COLD: 0.92
    }
    
    # Colores para representar cada condición climática
    WEATHER_COLORS = {
        WeatherCondition.CLEAR: (255, 255, 100),
        WeatherCondition.CLOUDS: (200, 200, 220),
        WeatherCondition.RAIN_LIGHT: (150, 150, 255),
        WeatherCondition.RAIN: (100, 100, 255),
        WeatherCondition.STORM: (150, 50, 200),
        WeatherCondition.FOG: (180, 180, 200),
        WeatherCondition.WIND: (200, 220, 255),
        WeatherCondition.HEAT: (255, 150, 50),
        WeatherCondition.COLD: (150, 220, 255)
    }
    
    def __init__(self, api_manager, transition_duration=3.0):
        self.api_manager = api_manager
        self.transition_duration = transition_duration
        
        # Cargar datos del clima
        self.weather_data = self.load_weather_data()
        
        # Estado actual del clima
        self.current_condition = WeatherCondition(self.weather_data["data"]["initial"]["condition"])
        self.current_intensity = self.weather_data["data"]["initial"]["intensity"]
        self.current_multiplier = self.SPEED_MULTIPLIERS[self.current_condition]
        
        # Estado objetivo (próximo clima)
        self.target_condition = self.current_condition
        self.target_intensity = self.current_intensity
        self.target_multiplier = self.current_multiplier
        
        # Temporizadores
        self.burst_timer = 0
        self.transition_timer = 0
        self.burst_duration = random.randint(1, 2)  # Duración aleatoria entre 45-60 segundos
        
        # Matriz de transición de Markov
        self.transition_matrix = self.weather_data["data"]["transition"]
        
        # Para transiciones suaves
        self.is_transitioning = False
        self.transition_start_multiplier = self.current_multiplier
        
        # Historial de cambios climáticos
        self.weather_history = []
        
    def load_weather_data(self):
        """Carga los datos del clima desde la API o desde caché local"""
        try:
            weather_data = self.api_manager.get_weather()
            
            # Guardar en caché local
            os.makedirs("api_cache", exist_ok=True)
            with open("api_cache/weather.json", "w") as f:
                json.dump(weather_data, f)
                
            return weather_data
        except requests.RequestException:
            try:
                with open("api_cache/weather.json", "r") as f:
                    return json.load(f)
            except FileNotFoundError:
                return {
                    "version": "1.0",
                    "data": {
                        "city": "TigerCity",
                        "initial": {"condition": "clear", "intensity": 0.0},
                        "conditions": ["clear", "clouds", "rain_light", "rain", "storm", "fog", "wind", "heat", "cold"],
                        "transition": {
                            "clear": {"clear": 0.6, "clouds": 0.3, "rain": 0.1},
                            "clouds": {"clear": 0.3, "clouds": 0.5, "rain": 0.2},
                            "rain": {"clouds": 0.4, "rain": 0.4, "storm": 0.2},
                            "rain_light": {"clouds": 0.4, "rain_light": 0.4, "rain": 0.2},
                            "storm": {"rain": 0.5, "clouds": 0.3, "storm": 0.2},
                            "fog": {"fog": 0.5, "clouds": 0.3, "clear": 0.2},
                            "wind": {"wind": 0.5, "clouds": 0.3, "clear": 0.2},
                            "heat": {"heat": 0.5, "clear": 0.3, "clouds": 0.2},
                            "cold": {"cold": 0.5, "clear": 0.3, "clouds": 0.2}
                        }
                    }
                }
    
    def update(self, dt):
        """Actualiza el estado del clima"""
        # Actualizar temporizador de ráfaga
        self.burst_timer += dt
        
        # Si estamos en transición, actualizar el multiplicador
        if self.is_transitioning:
            self.transition_timer += dt
            progress = min(1.0, self.transition_timer / self.transition_duration)
            
            # Interpolar suavemente entre el multiplicador inicial y el objetivo
            self.current_multiplier = self.transition_start_multiplier + (
                self.target_multiplier - self.transition_start_multiplier
            ) * progress
            
            # Si la transición ha terminado
            if progress >= 1.0:
                self.complete_transition()
        
        # Si la ráfaga actual ha terminado y no estamos en transición
        elif self.burst_timer >= self.burst_duration:
            self.change_weather()
    
    def complete_transition(self):
        """Completa la transición climática"""
        self.current_condition = self.target_condition
        self.current_intensity = self.target_intensity
        self.current_multiplier = self.target_multiplier
        self.is_transitioning = False
        
        # Registrar en el historial
        self.weather_history.append({
            "condition": self.current_condition.value,
            "intensity": self.current_intensity,
            "duration": self.burst_duration
        })
    
    def change_weather(self):
        """Cambia el clima usando la cadena de Markov"""
        # Reiniciar temporizador
        self.burst_timer = 0
        self.burst_duration = random.randint(1, 2)
        
        # Obtener probabilidades de transición para el clima actual
        current_condition_str = self.current_condition.value
        transition_probs = self.transition_matrix.get(current_condition_str, {})
        
        # Si no hay probabilidades definidas, usar valores por defecto
        if not transition_probs:
            transition_probs = {"clear": 0.6, "clouds": 0.3, "rain": 0.1}
        
        # Seleccionar el próximo clima basado en las probabilidades
        rand_val = random.random()
        cumulative_prob = 0
        
        for condition, prob in transition_probs.items():
            cumulative_prob += prob
            if rand_val <= cumulative_prob:
                self.target_condition = WeatherCondition(condition)
                break
        
        # Si no se seleccionó ningún clima, usar clear por defecto
        if self.target_condition is None:
            self.target_condition = WeatherCondition.CLEAR
        
        # Establecer intensidad aleatoria (0-1)
        self.target_intensity = random.random()
        
        # Obtener multiplicador objetivo
        self.target_multiplier = self.SPEED_MULTIPLIERS[self.target_condition]
        
        # Iniciar transición
        self.is_transitioning = True
        self.transition_timer = 0
        self.transition_start_multiplier = self.current_multiplier
    
    def get_stamina_consumption(self):
        """Calcula el consumo adicional de stamina basado en el clima actual"""
        base_consumption = 0
        
        if self.current_condition in [WeatherCondition.RAIN, WeatherCondition.WIND]:
            base_consumption += 0.1
        elif self.current_condition == WeatherCondition.STORM:
            base_consumption += 0.3
        elif self.current_condition == WeatherCondition.HEAT:
            base_consumption += 0.2
        
        # Ajustar por intensidad
        return base_consumption * self.current_intensity
    
    def get_speed_multiplier(self):
        """Devuelve el multiplicador de velocidad actual"""
        return self.current_multiplier
    
    def draw(self, screen, x, y):
        """Dibuja un indicador del clima actual"""
        # Dibujar círculo con el color del clima actual
        color = self.WEATHER_COLORS[self.current_condition]
        pygame.draw.circle(screen, color, (x, y), 15)
        pygame.draw.circle(screen, (0, 0, 0), (x, y), 15, 2)
        
        # Dibujar icono según el clima
        self.draw_weather_icon(screen, x, y)
    
    def draw_weather_icon(self, screen, x, y):
        """Dibuja el icono correspondiente al clima actual"""
        if self.current_condition == WeatherCondition.CLEAR:
            pygame.draw.circle(screen, (255, 255, 0), (x, y), 5)  # Sol
        elif self.current_condition == WeatherCondition.CLOUDS:
            pygame.draw.ellipse(screen, (255, 255, 255), (x-7, y-3, 14, 6))  # Nube
        elif self.current_condition in [WeatherCondition.RAIN_LIGHT, WeatherCondition.RAIN]:
            for i in range(3):  # Gotas de lluvia
                pygame.draw.line(screen, (0, 0, 255), (x-5+i*5, y-5), (x-5+i*5, y+5), 2)
        elif self.current_condition == WeatherCondition.STORM:
            pygame.draw.polygon(screen, (255, 255, 0), [(x, y-8), (x-5, y+2), (x+5, y+2)])  # Rayo
        elif self.current_condition == WeatherCondition.FOG:
            for i in range(3):  # Líneas de niebla
                pygame.draw.line(screen, (200, 200, 200), (x-7, y-5+i*5), (x+7, y-5+i*5), 2)
        elif self.current_condition == WeatherCondition.WIND:
            pygame.draw.arc(screen, (255, 255, 255), (x-8, y-8, 16, 16), 0, 3.14, 2)  # Arco de viento
            pygame.draw.line(screen, (255, 255, 255), (x+5, y), (x+8, y-3), 2)
        elif self.current_condition == WeatherCondition.HEAT:
            pygame.draw.line(screen, (255, 0, 0), (x-5, y-5), (x+5, y+5), 2)  # Líneas de calor
            pygame.draw.line(screen, (255, 0, 0), (x+5, y-5), (x-5, y+5), 2)
        elif self.current_condition == WeatherCondition.COLD:
            pygame.draw.polygon(screen, (200, 200, 255), [(x, y-8), (x-5, y-3), (x-3, y), 
                                                         (x-5, y+5), (x, y+3), (x+5, y+5), 
                                                         (x+3, y), (x+5, y-3)])
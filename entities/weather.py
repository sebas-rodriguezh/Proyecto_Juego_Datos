# weather.py - VERSIÓN COMPLETAMENTE REVISADA
from collections import deque
import random
import pygame
import requests
import json
import os
from enum import Enum
import math

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
        
        # Cargar datos del clima DESDE API O CACHÉ
        self.weather_data = self.load_weather_data()
        
        # Estado actual del clima
        initial_data = self.weather_data["data"]["initial"]
        self.current_condition = WeatherCondition(initial_data["condition"])
        self.current_intensity = initial_data["intensity"]
        self.current_multiplier = self.SPEED_MULTIPLIERS[self.current_condition]
        
        # Estado objetivo
        self.target_condition = self.current_condition
        self.target_intensity = self.current_intensity
        self.target_multiplier = self.current_multiplier
        

        self.burst_timer = 0
        self.transition_timer = 0
        self.burst_duration = random.randint(45, 60)
        
        self.transition_matrix = self.weather_data["data"]["transition"]
        
        self.is_transitioning = False
        self.transition_start_multiplier = self.current_multiplier
        
        self.weather_history = []
        
        self.particles = []
        self.particle_timer = 0
        
    def load_weather_data(self):
        """Carga los datos del clima desde la API o desde caché local"""
        try:
            weather_data = self.api_manager.get_weather()
            return weather_data
            
        except Exception as e:
            cache_path = os.path.join("api_cache", "weather_data.json")
            try:
                if os.path.exists(cache_path):
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        weather_data = json.load(f)
                    return weather_data
            except Exception as cache_error:
                print(f"Error cargando desde caché: {cache_error}")
            
        raise Exception(f"No se pudieron cargar los datos del clima: {e}. También falló la carga desde caché: {cache_error}")
    
    def update(self, dt):
        """Actualiza el estado del clima"""
        self.burst_timer += dt
        
        if self.is_transitioning:
            self.transition_timer += dt
            progress = min(1.0, self.transition_timer / self.transition_duration)
            
            self.current_multiplier = self.transition_start_multiplier + (
                self.target_multiplier - self.transition_start_multiplier
            ) * progress
            
            if progress >= 1.0:
                self.complete_transition()
        
        elif self.burst_timer >= self.burst_duration:
            self.change_weather()
        
        # Actualizar partículas
        self.update_particles(dt)
        self.spawn_particles(dt)
    
    def complete_transition(self):
        """Completa la transición climática"""
        self.current_condition = self.target_condition
        self.current_intensity = self.target_intensity
        self.current_multiplier = self.target_multiplier
        self.is_transitioning = False
        
        self.weather_history.append({
            "condition": self.current_condition.value,
            "intensity": self.target_intensity,
            "duration": self.burst_duration
        })
    
    def change_weather(self):
        """Cambia el clima usando la cadena de Markov del JSON"""
        self.burst_timer = 0
        self.burst_duration = random.randint(45, 60)
        
        # Obtener probabilidades de transición para el clima actual DEL JSON
        current_condition_str = self.current_condition.value
        transition_probs = self.transition_matrix.get(current_condition_str, {})
        
        if not transition_probs:
            self.target_condition = self.current_condition
        else:
            rand_val = random.random()
            cumulative_prob = 0
            selected_condition = None
            
            for condition, prob in transition_probs.items():
                cumulative_prob += prob
                if rand_val <= cumulative_prob:
                    selected_condition = condition
                    break
            
            if selected_condition is None:
                selected_condition = list(transition_probs.keys())[0]
            
            self.target_condition = WeatherCondition(selected_condition)
        
        # Establecer intensidad.
        self.target_intensity = random.random()
        

        self.target_multiplier = self.SPEED_MULTIPLIERS[self.target_condition]
        
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
    
    def spawn_particles(self, dt):
        """Genera nuevas partículas según el clima actual"""
        self.particle_timer += dt
        
        spawn_rates = {
            WeatherCondition.CLEAR: 0.0,      
            WeatherCondition.CLOUDS: 0.0,     
            WeatherCondition.RAIN_LIGHT: 0.04, 
            WeatherCondition.RAIN: 0.02,      
            WeatherCondition.STORM: 0.01,     
            WeatherCondition.FOG: 0.1,        
            WeatherCondition.WIND: 0.06,      
            WeatherCondition.HEAT: 0.0,       
            WeatherCondition.COLD: 0.08       
        }
        
        spawn_rate = spawn_rates.get(self.current_condition, 0.01)
        
        if self.particle_timer >= spawn_rate:
            self.particle_timer = 0
            
            if self.current_condition in [WeatherCondition.RAIN_LIGHT, WeatherCondition.RAIN, WeatherCondition.STORM]:
                self.create_rain_particle()
            elif self.current_condition == WeatherCondition.COLD:
                self.create_snow_particle()
            elif self.current_condition == WeatherCondition.FOG:
                self.create_fog_particle()
            elif self.current_condition == WeatherCondition.WIND:
                self.create_wind_particle()
    
    def create_rain_particle(self):
        """Crea una partícula de lluvia"""
        x = random.randint(0, 1920)
        y = random.randint(-50, 0)
        
        # Ajustar velocidad según tipo de lluvia
        if self.current_condition == WeatherCondition.STORM:
            vx = random.uniform(-3, -2)  # Más viento en tormenta
            vy = random.uniform(500, 700)  # Más rápido en tormenta
            life = random.uniform(1.5, 3)
            length = random.randint(10, 18)
        elif self.current_condition == WeatherCondition.RAIN:
            vx = random.uniform(-1.5, -0.5)
            vy = random.uniform(350, 450)
            life = random.uniform(2, 4)
            length = random.randint(6, 12)
        else:  # RAIN_LIGHT
            vx = random.uniform(-1, 0)
            vy = random.uniform(250, 350)
            life = random.uniform(3, 5)
            length = random.randint(4, 8)
        
        self.particles.append([x, y, vx, vy, life, length, "rain"])
    
    def create_snow_particle(self):
        """Crea una partícula de nieve"""
        x = random.randint(0, 1920)
        y = random.randint(-50, 0)
        vx = random.uniform(-25, 25)  
        vy = random.uniform(20, 40)   
        life = random.uniform(6, 10)  
        size = random.uniform(2.0, 4.0)  
        
        self.particles.append([x, y, vx, vy, life, size, "snow"])
    
    def create_fog_particle(self):
        """Crea una partícula de niebla"""
        x = random.randint(0, 1920)
        y = random.randint(0, 1080)
        vx = random.uniform(-10, 10)   
        vy = random.uniform(-3, 3)     
        life = random.uniform(4, 8)    
        size = random.randint(40, 80)  
        alpha = random.randint(15, 35) 
        
        self.particles.append([x, y, vx, vy, life, size, alpha, "fog"])
    
    def create_wind_particle(self):
        """Crea una partícula de viento (líneas)"""
        x = random.randint(-100, 0)
        y = random.randint(0, 1080)
        vx = random.uniform(250, 400) 
        vy = random.uniform(-15, 15)   
        life = random.uniform(0.8, 1.5) 
        length = random.randint(25, 50) 
        
        self.particles.append([x, y, vx, vy, life, length, "wind"])
    
    def update_particles(self, dt):
        """Actualiza todas las partículas"""
        particles_to_keep = []
        
        for particle in self.particles:
            # Actualizar posición
            particle[0] += particle[2] * dt
            particle[1] += particle[3] * dt
            particle[4] -= dt  
            
            if particle[4] > 0 and -200 < particle[0] < 2120 and -200 < particle[1] < 1280:
                particles_to_keep.append(particle)
        
        self.particles = particles_to_keep
    
    def draw_particles(self, screen, camera_x, camera_y):
        """Dibuja todas las partículas - VERSIÓN MEJORADA"""
        if self.current_condition == WeatherCondition.CLEAR:
            return
        
        for particle in self.particles:
            x = particle[0] - camera_x
            y = particle[1] - camera_y
            
            # Solo dibujar si está en pantalla
            if -100 < x < screen.get_width() + 100 and -100 < y < screen.get_height() + 100:
                particle_type = particle[-1]  # Último elemento es el tipo
                
                if particle_type == "rain":
                    length = particle[5]
                    if self.current_condition == WeatherCondition.STORM:
                        color = (100, 100, 255)   
                    elif self.current_condition == WeatherCondition.RAIN:
                        color = (100, 100, 255) 
                    else:  # RAIN_LIGHT
                        color = (150, 150, 255) 
                    
                    pygame.draw.line(screen, color, (int(x), int(y)), 
                                   (int(x + particle[2]*0.1), int(y + length)), 2)
                
                elif particle_type == "snow":
                    size = int(particle[5])
                    if size > 0:
                        pygame.draw.circle(screen, (255, 255, 255), (int(x), int(y)), size)
                
                elif particle_type == "fog":
                    if len(particle) >= 8:
                        size = particle[5]
                        alpha = particle[6]
                        fog_surface = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
                        pygame.draw.circle(fog_surface, (200, 200, 220, alpha), (size, size), size)
                        screen.blit(fog_surface, (int(x - size), int(y - size)))
                
                elif particle_type == "wind":
                    length = particle[5]
                    pygame.draw.line(screen, (220, 220, 255), (int(x), int(y)), 
                                   (int(x + length), int(y)), 2)
    
    def draw(self, screen, x, y):
        """Dibuja un indicador del clima actual"""
        color = self.WEATHER_COLORS[self.current_condition]
        pygame.draw.circle(screen, color, (x, y), 15)
        pygame.draw.circle(screen, (0, 0, 0), (x, y), 15, 2)
        
        self.draw_weather_icon(screen, x, y)
    
    def draw_weather_icon(self, screen, x, y):
        """Dibuja el icono correspondiente al clima actual"""
        if self.current_condition == WeatherCondition.CLEAR:
            pygame.draw.circle(screen, (255, 255, 0), (x, y), 5)
        elif self.current_condition == WeatherCondition.CLOUDS:
            pygame.draw.ellipse(screen, (255, 255, 255), (x-7, y-3, 14, 6))
        elif self.current_condition in [WeatherCondition.RAIN_LIGHT, WeatherCondition.RAIN, WeatherCondition.STORM]:
            # Dibujar líneas de lluvia con colores diferentes
            for i in range(3):
                if self.current_condition == WeatherCondition.STORM:
                    color = (150, 50, 200)   
                elif self.current_condition == WeatherCondition.RAIN:
                    color = (100, 100, 255) 
                else:  # RAIN_LIGHT
                    color = (150, 150, 255)  
                
                pygame.draw.line(screen, color, (x-5+i*5, y-5), (x-5+i*5, y+5), 2)
        elif self.current_condition == WeatherCondition.FOG:
            for i in range(3):
                pygame.draw.line(screen, (200, 200, 200), (x-7, y-5+i*5), (x+7, y-5+i*5), 2)
        elif self.current_condition == WeatherCondition.WIND:
            pygame.draw.arc(screen, (255, 255, 255), (x-8, y-8, 16, 16), 0, 3.14, 2)
            pygame.draw.line(screen, (255, 255, 255), (x+5, y), (x+8, y-3), 2)
        elif self.current_condition == WeatherCondition.HEAT:
            pygame.draw.line(screen, (255, 0, 0), (x-5, y-5), (x+5, y+5), 2)
            pygame.draw.line(screen, (255, 0, 0), (x+5, y-5), (x-5, y+5), 2)
        elif self.current_condition == WeatherCondition.COLD:
            pygame.draw.polygon(screen, (200, 200, 255), [(x, y-8), (x-5, y-3), (x-3, y), 
                                                         (x-5, y+5), (x, y+3), (x+5, y+5), 
                                                         (x+3, y), (x+5, y-3)])
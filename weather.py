import pygame
import random
import time
import math
from api_manager import APIManager  # Importar tu clase APIManager

class Weather:
    # Definición de condiciones climáticas y sus multiplicadores base
    CONDITIONS = {
        "clear": {"name": "Despejado", "multiplier": 1.00, "stamina_cost": 0.0},
        "clouds": {"name": "Nublado", "multiplier": 0.98, "stamina_cost": 0.0},
        "rain_light": {"name": "Lluvia ligera", "multiplier": 0.90, "stamina_cost": 0.1},
        "rain": {"name": "Lluvia", "multiplier": 0.85, "stamina_cost": 0.1},
        "storm": {"name": "Tormenta", "multiplier": 0.75, "stamina_cost": 0.3},
        "fog": {"name": "Niebla", "multiplier": 0.88, "stamina_cost": 0.0},
        "wind": {"name": "Viento", "multiplier": 0.92, "stamina_cost": 0.1},
        "heat": {"name": "Calor extremo", "multiplier": 0.90, "stamina_cost": 0.2},
        "cold": {"name": "Frío extremo", "multiplier": 0.92, "stamina_cost": 0.0}
    }
    
    def __init__(self, api_manager, use_api=True):
        self.api_manager = api_manager
        self.use_api = use_api
        self.weather_data = None
        
        # Cargar datos climáticos
        self._load_weather_data()
        
        # Estado actual del clima (usando los datos iniciales de la API)
        self.current_condition = self.weather_data["initial"]["condition"]
        self.current_intensity = self.weather_data["initial"]["intensity"]
        self.current_duration = random.randint(45, 60)  # Duración aleatoria entre 45-60 segundos
        
        # Para transiciones suaves
        self.target_condition = self.current_condition
        self.target_intensity = self.current_intensity
        self.transition_progress = 0
        self.transition_duration = 4  # segundos para completar la transición
        
        # Tiempo de inicio del burst actual
        self.burst_start_time = time.time()
        
        # Bandera para indicar si estamos en transición
        self.in_transition = False
        
    def _load_weather_data(self):
        """Carga los datos climáticos desde la API o archivo local"""
        try:
            if self.use_api:
                # Intentar obtener datos de la API
                api_response = self.api_manager.get_weather_data()
                
                # Verificar que la respuesta tenga la estructura esperada
                if (api_response and "version" in api_response and 
                    "data" in api_response and "initial" in api_response["data"]):
                    self.weather_data = api_response["data"]
                    print("Datos climáticos obtenidos desde la API")
                else:
                    raise Exception("Formato de respuesta de API inválido")
            else:
                raise Exception("Modo API desactivado")
                
        except Exception as e:
            print(f"Error al cargar datos de la API: {e}. Usando datos locales...")
            # Cargar desde archivo local o datos por defecto
            self.weather_data = self._load_local_weather_data()
    
    def _load_local_weather_data(self):
        """Carga datos climáticos desde archivo local o usa valores por defecto"""
        # Esta función debería cargar desde /data/weather.json
        # Por ahora usamos datos de ejemplo basados en el formato de la API
        return {
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
    
    def get_current_multiplier(self):
        """Obtiene el multiplicador de velocidad actual, considerando transiciones"""
        current_mult = self.CONDITIONS[self.current_condition]["multiplier"]
        
        if self.in_transition:
            target_mult = self.CONDITIONS[self.target_condition]["multiplier"]
            # Interpolación lineal durante la transición
            return current_mult + (target_mult - current_mult) * self.transition_progress
        
        return current_mult
    
    def get_stamina_cost(self):
        """Obtiene el costo adicional de resistencia por celda"""
        return self.CONDITIONS[self.current_condition]["stamina_cost"] * self.current_intensity
    
    def update(self):
        """Actualiza el estado del clima, debe ser llamado en cada frame del juego"""
        current_time = time.time()
        elapsed = current_time - self.burst_start_time
        
        # Comprobar si es tiempo de cambiar de condición climática
        if elapsed >= self.current_duration and not self.in_transition:
            self._start_transition()
        
        # Actualizar transición en curso
        if self.in_transition:
            self.transition_progress = min(1.0, (current_time - self.transition_start_time) / self.transition_duration)
            
            # Si la transición está completa, finalizarla
            if self.transition_progress >= 1.0:
                self._end_transition()
    
    def _start_transition(self):
        """Inicia una transición a una nueva condición climática"""
        # Usar la matriz de transición de la API para generar el próximo clima
        self.target_condition = self._get_next_condition()
        self.target_intensity = random.uniform(0.1, 1.0)  # Intensidad aleatoria
        
        # Duración aleatoria para el próximo burst (45-60 segundos)
        next_duration = random.randint(45, 60)
        
        # Preparar para la transición
        self.transition_start_time = time.time()
        self.transition_progress = 0
        self.in_transition = True
        
        # Guardar información del próximo burst
        self.next_burst = {
            "condition": self.target_condition,
            "intensity": self.target_intensity,
            "duration_sec": next_duration
        }
    
    def _end_transition(self):
        """Finaliza la transición y establece la nueva condición como actual"""
        self.current_condition = self.target_condition
        self.current_intensity = self.target_intensity
        self.current_duration = self.next_burst["duration_sec"]
        
        # Reiniciar el temporizador
        self.burst_start_time = time.time()
        
        # Finalizar la transición
        self.in_transition = False
        self.transition_progress = 0
    
    def _get_next_condition(self):
        """Usa la matriz de transición de la API para determinar la próxima condición climática"""
        current = self.current_condition
        
        # Obtener las probabilidades de transición desde los datos de la API
        transition_matrix = self.weather_data.get("transition", {})
        probabilities = transition_matrix.get(current, {"clear": 1.0})  # Por defecto claro
        
        # Convertir las probabilidades en una lista acumulativa
        choices, weights = zip(*probabilities.items())
        cumulative_weights = []
        cumulative = 0
        
        for w in weights:
            cumulative += w
            cumulative_weights.append(cumulative)
        
        # Seleccionar una condición basada en las probabilidades
        rand = random.random() * cumulative_weights[-1]
        
        for i, weight in enumerate(cumulative_weights):
            if rand <= weight:
                return choices[i]
        
        return "clear"  # Fallback
    
    def get_weather_info(self):
        """Devuelve información sobre el clima actual para la UI"""
        condition_info = self.CONDITIONS[self.current_condition]
        
        return {
            "name": condition_info["name"],
            "multiplier": self.get_current_multiplier(),
            "intensity": self.current_intensity,
            "in_transition": self.in_transition,
            "transition_progress": self.transition_progress if self.in_transition else 0,
            "time_remaining": max(0, self.current_duration - (time.time() - self.burst_start_time)),
            "condition_icon": self._get_weather_icon(),
            "condition_code": self.current_condition
        }
    
    def _get_weather_icon(self):
        """Devuelve el nombre de un icono para la condición actual"""
        icons = {
            "clear": "sun",
            "clouds": "cloud",
            "rain_light": "cloud-drizzle",
            "rain": "cloud-rain",
            "storm": "cloud-lightning",
            "fog": "cloud-fog",
            "wind": "wind",
            "heat": "thermometer-sun",
            "cold": "thermometer-snowflake"
        }
        return icons.get(self.current_condition, "sun")
    
    def get_weather_display_name(self):
        """Devuelve el nombre para mostrar de la condición actual"""
        return self.CONDITIONS[self.current_condition]["name"]
    
    def get_weather_effects(self):
        """Devuelve los efectos actuales del clima para aplicar al jugador"""
        return {
            "speed_multiplier": self.get_current_multiplier(),
            "stamina_cost": self.get_stamina_cost(),
            "condition": self.current_condition,
            "intensity": self.current_intensity
        }
    
    def save_state(self):
        """Guarda el estado actual del clima para persistencia"""
        return {
            "current_condition": self.current_condition,
            "current_intensity": self.current_intensity,
            "current_duration": self.current_duration,
            "burst_start_time": self.burst_start_time,
            "target_condition": self.target_condition,
            "target_intensity": self.target_intensity,
            "transition_progress": self.transition_progress,
            "in_transition": self.in_transition,
            "weather_data": self.weather_data
        }
    
    def load_state(self, state):
        """Carga un estado previamente guardado"""
        self.current_condition = state["current_condition"]
        self.current_intensity = state["current_intensity"]
        self.current_duration = state["current_duration"]
        self.burst_start_time = state["burst_start_time"]
        self.target_condition = state["target_condition"]
        self.target_intensity = state["target_intensity"]
        self.transition_progress = state["transition_progress"]
        self.in_transition = state["in_transition"]
        self.weather_data = state["weather_data"]
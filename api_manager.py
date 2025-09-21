# api_manager.py - MODIFICADO con sistema de caché offline
import requests
from dataclasses import dataclass
import json
import os
from datetime import datetime, timedelta

class APIManager:
    """Clase para interactuar con la API de TigerDS con soporte offline."""
    
    # URL base constante
    BASE_URL = "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io"
    CACHE_DIR = "api_cache"
    CACHE_EXPIRY_HOURS = 24  # Los datos en caché expiran después de 24 horas
    
    def __init__(self):
        # No se necesita argumento; se usa la URL constante
        self.base_url = self.BASE_URL
        
        # Crear directorio de caché si no existe
        os.makedirs(self.CACHE_DIR, exist_ok=True)
    
    def _make_api_call(self, endpoint, cache_filename):
        """Realiza una llamada a la API con soporte para caché offline"""
        try:
            # Intentar llamada a la API
            response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Guardar en caché
            self._save_to_cache(cache_filename, data)
            return data
            
        except (requests.RequestException, requests.Timeout):
            # Falló la conexión, intentar cargar desde caché
            print(f"⚠️  No hay conexión a la API. Intentando cargar desde caché: {cache_filename}")
            cached_data = self._load_from_cache(cache_filename)
            
            if cached_data:
                print("✅ Datos cargados desde caché correctamente")
                return cached_data
            else:
                print("❌ No hay datos en caché disponibles")
                raise Exception(f"No se pudo conectar a la API y no hay datos en caché para {endpoint}")
    
    def _save_to_cache(self, filename, data):
        """Guarda datos en el caché local con timestamp"""
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        cache_path = os.path.join(self.CACHE_DIR, filename)
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
    
    def _load_from_cache(self, filename):
        """Carga datos desde el caché local si no han expirado"""
        cache_path = os.path.join(self.CACHE_DIR, filename)
        
        try:
            if not os.path.exists(cache_path):
                return None
                
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Verificar si el caché ha expirado
            cache_time = datetime.fromisoformat(cache_data["timestamp"])
            if datetime.now() - cache_time > timedelta(hours=self.CACHE_EXPIRY_HOURS):
                print(f"⚠️  Los datos en caché para {filename} han expirado")
                return None
                
            return cache_data["data"]
            
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Error al cargar caché {filename}: {e}")
            return None
    
    def get_map_data(self):
        """Obtiene los datos del mapa desde la API o caché."""
        return self._make_api_call("/city/map", "map_data.json")
    
    def get_health_status(self):
        """Verifica el estado de la API."""
        try:
            response = requests.get(f"{self.base_url}/healthz", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return {"status": "offline", "message": "No hay conexión a la API"}
    
    def get_jobs(self):
        """Obtiene los trabajos disponibles desde API o caché."""
        return self._make_api_call("/city/jobs", "jobs_data.json")
    
    def get_weather(self):
        """Obtiene datos del clima desde API o caché."""
        return self._make_api_call("/city/weather", "weather_data.json")
    
    def is_online(self):
        """Verifica si hay conexión a internet"""
        try:
            requests.get("https://www.google.com", timeout=3)
            return True
        except requests.RequestException:
            return False
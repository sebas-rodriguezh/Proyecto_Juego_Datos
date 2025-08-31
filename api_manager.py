import requests
from dataclasses import dataclass

class APIManager:
    """Clase para interactuar con la API de TigerDS."""

    # URL base constante
    BASE_URL = "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io"
    
    def __init__(self):
        # No se necesita argumento; se usa la URL constante
        self.base_url = self.BASE_URL

    def get_map_data(self):
        """Obtiene los datos del mapa desde la API."""
        response = requests.get(f"{self.base_url}/city/map")    
        response.raise_for_status()
        return response.json()
    
    def get_health_status(self):
        """Verifica el estado de la API."""
        response = requests.get(f"{self.base_url}/healthz")
        response.raise_for_status()
        return response.json()
    
    def get_jobs(self):
        """Obtiene los trabajos disponibles."""
        response = requests.get(f"{self.base_url}/city/jobs")
        response.raise_for_status()
        return response.json()
    
    def get_weather(self):
        """Obtiene datos del clima."""
        response = requests.get(f"{self.base_url}/city/weather")
        response.raise_for_status()
        return response.json()

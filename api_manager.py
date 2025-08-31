import requests

class APIManager:
    def __init__(self, base_url):
        self.base_url = base_url
    
    def get_map_data(self):
        """Obtiene los datos del mapa desde la API"""
        response = requests.get(f"{self.base_url}/city/map")
        response.raise_for_status()
        return response.json()
    
    def get_health_status(self):
        """Verifica el estado de la API"""
        response = requests.get(f"{self.base_url}/healthz")
        response.raise_for_status()
        return response.json()
    
    def get_jobs(self):
        """Obtiene los trabajos disponibles"""
        response = requests.get(f"{self.base_url}/city/jobs")
        response.raise_for_status()
        return response.json()
    
    def get_weather(self):
        """Obtiene datos del clima"""
        response = requests.get(f"{self.base_url}/city/weather")
        response.raise_for_status()
        return response.json()

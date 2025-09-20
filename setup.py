# setup.py
import os
import json
from pathlib import Path

def setup_directories():
    """Crea los directorios necesarios para el juego"""
    directories = [
        "saves",
        "api_cache", 
        "data",
        "exports"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Directorio creado: {directory}")

def create_default_files():
    """Crea archivos por defecto para modo offline"""
    # Datos de mapa por defecto
    map_data = {
        "data": {
            "city_name": "TigerCity",
            "width": 20,
            "height": 15,
            "tiles": [["C" for _ in range(20)] for _ in range(15)],
            "legend": {
                "C": {"name": "calle", "surface_weight": 1.0},
                "B": {"name": "edificio", "blocked": True},
                "P": {"name": "parque", "surface_weight": 0.95}
            },
            "goal": 3000
        }
    }
    
    with open('data/city_map.json', 'w', encoding='utf-8') as f:
        json.dump(map_data, f, indent=2, ensure_ascii=False)
    
    # Datos de trabajos por defecto
    jobs_data = {
        "data": [
            {
                "id": "PED-OFFLINE-001",
                "pickup": [3, 7],
                "dropoff": [10, 2],
                "payout": 120,
                "deadline": "2025-09-01T12:30:00",
                "weight": 2,
                "priority": 0,
                "release_time": 0
            }
        ]
    }
    
    with open('data/city_jobs.json', 'w', encoding='utf-8') as f:
        json.dump(jobs_data, f, indent=2, ensure_ascii=False)
    
    # Datos de clima por defecto
    weather_data = {
        "data": {
            "initial": {"condition": "clear", "intensity": 0.2},
            "transition": {
                "clear": {"clear": 0.6, "clouds": 0.3, "rain_light": 0.1},
                "clouds": {"clear": 0.3, "clouds": 0.5, "rain_light": 0.2}
            }
        }
    }
    
    with open('data/city_weather.json', 'w', encoding='utf-8') as f:
        json.dump(weather_data, f, indent=2, ensure_ascii=False)
    
    # Archivo de puntuaciones vacío
    with open('data/puntajes.json', 'w', encoding='utf-8') as f:
        json.dump([], f, indent=2, ensure_ascii=False)
    
    print("Archivos por defecto creados en la carpeta data/")

if __name__ == "__main__":
    print("Configurando directorios y archivos para Courier Quest...")
    setup_directories()
    create_default_files()
    print("¡Configuración completada!")
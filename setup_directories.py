# setup_directories.py
import os

def setup_directories():
    """Crea la estructura de directorios necesaria"""
    directories = ['api_cache', 'saves']
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Directorio {directory} creado/verificado")

if __name__ == "__main__":
    setup_directories()
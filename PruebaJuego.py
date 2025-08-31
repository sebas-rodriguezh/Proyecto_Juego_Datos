import requests
import pygame
import math
from datetime import datetime
from Player import Player  # Asegúrate de que el archivo se llama Player.py

# Configuración inicial
url = "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io"

# Obtener datos de la API
try:
    resp = requests.get(url + "/city/map")
    data = resp.json()
    resp3 = requests.get(url + "/city/jobs")
    data3 = resp3.json()
    resp4 = requests.get(url + "/city/weather")
    data4 = resp4.json()
except requests.exceptions.RequestException as e:
    print(f"Error al conectar con la API: {e}")
    print("Cargando datos desde caché...")
    # Aquí cargarías los datos desde archivos locales
    # data = load_local_data("data/ciudad.json")
    # data3 = load_local_data("data/pedidos.json")
    # data4 = load_local_data("data/weather.json")
    # Por ahora, salimos del programa
    exit()

# Extraer información
tiles = data["data"]["tiles"]
legend = data["data"]["legend"]
jobs = data3["data"]
weather = data4["data"]

# Inicializar pygame
pygame.init()
tile_size = 32  # Aumentamos el tamaño de los tiles para mejor visualización
rows, cols = len(tiles), len(tiles[0])
screen_width = cols * tile_size + 300  # Espacio adicional para el panel lateral
screen_height = rows * tile_size
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Courier Quest")

# Cargar fuentes
try:
    font_small = pygame.font.Font(None, 12)
    font_medium = pygame.font.Font(None, 14)
    font_large = pygame.font.Font(None, 18)
except:
    font_small = pygame.font.SysFont("Arial", 12)
    font_medium = pygame.font.SysFont("Arial", 14)
    font_large = pygame.font.SysFont("Arial", 18, bold=True)

# Colores según la leyenda
colors = {}
for char, info in legend.items():
    if info["name"] == "street":
        colors[char] = (200, 200, 200)  # gris
    elif info["name"] == "building":
        colors[char] = (50, 50, 50)     # negro
    elif info["name"] == "park":
        colors[char] = (100, 200, 100)  # verde
    else:
        colors[char] = (100, 100, 255)  # azul por defecto

# Colores para los trabajos
job_colors = [
    (255, 100, 100),  # Rojo claro
    (100, 100, 255),  # Azul claro
    (255, 255, 100),  # Amarillo claro
    (255, 100, 255),  # Magenta claro
    (100, 255, 255),  # Cian claro
]

# Colores para las condiciones climáticas
weather_colors = {
    "clear": (255, 255, 100),      # Amarillo claro
    "clouds": (200, 200, 220),     # Gris azulado
    "rain_light": (150, 150, 255), # Azul medio
    "rain": (100, 100, 255),       # Azul
    "storm": (150, 50, 200),       # Púrpura
    "fog": (180, 180, 200),        # Gris azulado claro
    "wind": (200, 220, 255),       # Azul muy claro
    "heat": (255, 150, 50),        # Naranja
    "cold": (150, 220, 255),       # Azul celeste
}

# Crear jugador en una posición inicial (por ejemplo, en el centro)
player = Player(cols // 2, rows // 2, tile_size, legend)

# Cámara para seguir al jugador
camera_x, camera_y = 0, 0

# Función para dibujar el panel lateral
def draw_sidebar():
    sidebar_rect = pygame.Rect(cols * tile_size, 0, 300, screen_height)
    pygame.draw.rect(screen, (240, 240, 240), sidebar_rect)
    pygame.draw.line(screen, (200, 200, 200), (cols * tile_size, 0), (cols * tile_size, screen_height), 2)
    
    # Título
    title = font_large.render("Courier Quest", True, (0, 0, 0))
    screen.blit(title, (cols * tile_size + 10, 10))
    
    # Información del jugador
    player_title = font_medium.render("Estado del Repartidor:", True, (0, 0, 0))
    screen.blit(player_title, (cols * tile_size + 10, 40))
    
    # Barra de resistencia
    stamina_text = font_small.render(f"Resistencia: {int(player.stamina)}/100", True, (0, 0, 0))
    screen.blit(stamina_text, (cols * tile_size + 10, 65))
    pygame.draw.rect(screen, (200, 200, 200), (cols * tile_size + 10, 80, 150, 15))
    pygame.draw.rect(screen, (0, 200, 0), (cols * tile_size + 10, 80, 150 * (player.stamina / 100), 15))
    
    # Reputación
    reputation_text = font_small.render(f"Reputación: {player.reputation}/100", True, (0, 0, 0))
    screen.blit(reputation_text, (cols * tile_size + 10, 100))
    pygame.draw.rect(screen, (200, 200, 200), (cols * tile_size + 10, 115, 150, 15))
    pygame.draw.rect(screen, (0, 100, 200), (cols * tile_size + 10, 115, 150 * (player.reputation / 100), 15))
    
    # Peso actual
    weight_text = font_small.render(f"Peso: {player.current_weight}/{player.max_weight}", True, (0, 0, 0))
    screen.blit(weight_text, (cols * tile_size + 10, 135))
    
    # Información del clima
    weather_title = font_medium.render("Condición Climática:", True, (0, 0, 0))
    screen.blit(weather_title, (cols * tile_size + 10, 160))
    
    # Dibujar círculo con el color del clima actual
    current_weather = weather["initial"]["condition"]
    pygame.draw.circle(screen, weather_colors[current_weather], (cols * tile_size + 40, 195), 15)
    
    weather_text = font_small.render(current_weather.replace("_", " ").title(), True, (0, 0, 0))
    screen.blit(weather_text, (cols * tile_size + 60, 185))
    
    intensity_text = font_small.render(f"Intensidad: {weather['initial']['intensity']:.2f}", True, (0, 0, 0))
    screen.blit(intensity_text, (cols * tile_size + 60, 200))
    
    # Lista de trabajos
    jobs_title = font_medium.render("Trabajos Disponibles:", True, (0, 0, 0))
    screen.blit(jobs_title, (cols * tile_size + 10, 230))
    
    for i, job in enumerate(jobs):
        y_pos = 255 + i * 70
        
        # Dibujar color del trabajo
        pygame.draw.rect(screen, job_colors[i % len(job_colors)], 
                        (cols * tile_size + 10, y_pos, 20, 20))
        
        # Información del trabajo
        job_id = font_small.render(f"ID: {job['id']}", True, (0, 0, 0))
        screen.blit(job_id, (cols * tile_size + 35, y_pos))
        
        payout = font_small.render(f"Pago: ${job['payout']}", True, (0, 0, 0))
        screen.blit(payout, (cols * tile_size + 35, y_pos + 15))
        
        deadline = font_small.render(f"Entrega: {job['deadline'][11:16]}", True, (0, 0, 0))
        screen.blit(deadline, (cols * tile_size + 10, y_pos + 35))
        
        weight = font_small.render(f"Peso: {job['weight']}", True, (0, 0, 0))
        screen.blit(weight, (cols * tile_size + 120, y_pos + 35))
        
        priority = font_small.render(f"Prioridad: {job['priority']}", True, (0, 0, 0))
        screen.blit(priority, (cols * tile_size + 10, y_pos + 50))
    
    # Leyenda del mapa
    legend_title = font_medium.render("Leyenda del Mapa:", True, (0, 0, 0))
    screen.blit(legend_title, (cols * tile_size + 10, screen_height - 150))
    
    y_pos = screen_height - 130
    for char, info in legend.items():
        pygame.draw.rect(screen, colors[char], (cols * tile_size + 10, y_pos, 15, 15))
        name = font_small.render(info["name"].title(), True, (0, 0, 0))
        screen.blit(name, (cols * tile_size + 30, y_pos))
        y_pos += 20

# Función para dibujar marcadores de trabajos en el mapa
def draw_job_markers():
    for i, job in enumerate(jobs):
        color = job_colors[i % len(job_colors)]
        
        # Dibujar punto de recogida
        pickup_x, pickup_y = job["pickup"]
        pygame.draw.circle(screen, color, 
                          (pickup_x * tile_size + tile_size // 2 - camera_x, 
                           pickup_y * tile_size + tile_size // 2 - camera_y), 
                          7)
        pygame.draw.circle(screen, (255, 255, 255), 
                          (pickup_x * tile_size + tile_size // 2 - camera_x, 
                           pickup_y * tile_size + tile_size // 2 - camera_y), 
                          7, 1)
        
        # Dibujar punto de entrega
        dropoff_x, dropoff_y = job["dropoff"]
        pygame.draw.rect(screen, color, 
                        (dropoff_x * tile_size + tile_size // 2 - 5 - camera_x, 
                         dropoff_y * tile_size + tile_size // 2 - 5 - camera_y, 
                         10, 10))
        pygame.draw.rect(screen, (255, 255, 255), 
                        (dropoff_x * tile_size + tile_size // 2 - 5 - camera_x, 
                         dropoff_y * tile_size + tile_size // 2 - 5 - camera_y, 
                         10, 10), 1)
        
        # Dibujar línea conectando recogida y entrega
        pygame.draw.line(screen, color, 
                        (pickup_x * tile_size + tile_size // 2 - camera_x, 
                         pickup_y * tile_size + tile_size // 2 - camera_y),
                        (dropoff_x * tile_size + tile_size // 2 - camera_x, 
                         dropoff_y * tile_size + tile_size // 2 - camera_y), 
                        2)

# Bucle principal
running = True
clock = pygame.time.Clock()
last_time = pygame.time.get_ticks()

while running:
    # Calcular delta time
    current_time = pygame.time.get_ticks()
    dt = (current_time - last_time) / 1000.0  # Convertir a segundos
    last_time = current_time
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Obtener teclas presionadas
    keys = pygame.key.get_pressed()
    dx, dy = 0, 0
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        dx = -1
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        dx = 1
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        dy = -1
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        dy = 1
    
    # Mover al jugador
    current_weather = weather["initial"]["condition"]
    weather_multiplier = {
        "clear": 1.00,
        "clouds": 0.98,
        "rain_light": 0.90,
        "rain": 0.85,
        "storm": 0.75,
        "fog": 0.88,
        "wind": 0.92,
        "heat": 0.90,
        "cold": 0.92
    }.get(current_weather, 1.0)
    
    # Obtener el multiplicador de superficie
    tile_x, tile_y = int(player.x), int(player.y)
    if 0 <= tile_y < len(tiles) and 0 <= tile_x < len(tiles[0]):
        tile_char = tiles[tile_y][tile_x]
        surface_multiplier = legend[tile_char].get("surface_weight", 1.0)
    else:
        surface_multiplier = 1.0
    
    # Mover al jugador
    if dx != 0 or dy != 0:
        player.move(dx, dy, dt, weather_multiplier, surface_multiplier, tiles)
    else:
        # Si no se está moviendo, recuperar stamina
        player.recover_stamina(dt)
    
    # Actualizar cámara para seguir al jugador
    camera_x = player.x * tile_size - screen_width // 2 + 150
    camera_y = player.y * tile_size - screen_height // 2
    
    # Limitar la cámara para que no se salga del mapa
    camera_x = max(0, min(camera_x, cols * tile_size - screen_width + 300))
    camera_y = max(0, min(camera_y, rows * tile_size - screen_height))
    
    # Dibujar
    screen.fill((255, 255, 255))

    # Dibujar mapa
    for y, row in enumerate(tiles):
        for x, char in enumerate(row):
            color = colors.get(char, (100, 100, 255))  # default azul
            rect = pygame.Rect(x * tile_size - camera_x, y * tile_size - camera_y, tile_size, tile_size)
            pygame.draw.rect(screen, color, rect)
            
            # Dibujar borde
            pygame.draw.rect(screen, (0, 0, 0), rect, 1)
            
            # Dibujar nombre del tile (solo si es visible)
            if (0 <= rect.x < screen_width - 300 and 0 <= rect.y < screen_height):
                if char in legend:
                    name = legend[char]["name"]
                    text = font_small.render(name[0].upper(), True, (0, 0, 0))  
                    text_rect = text.get_rect(center=rect.center)
                    screen.blit(text, text_rect)
    
    # Dibujar marcadores de trabajos
    draw_job_markers()
    
    # Dibujar jugador
    player.draw(screen, camera_x, camera_y)
    
    # Dibujar panel lateral
    draw_sidebar()

    pygame.display.flip()
    clock.tick(60)  # Aumentamos a 60 FPS para animaciones más suaves

pygame.quit()
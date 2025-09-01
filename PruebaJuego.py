import pygame
import math
from datetime import datetime
from Player import Player
from OrderList import OrderList
from map import Map  # Tu clase Map existente
from api_manager import APIManager  # Tu clase APIManager existente

# Configuración inicial
api = APIManager()

# Obtener datos de la API
try:
    map_data = api.get_map_data()
    jobs_data = api.get_jobs()
    weather_data = api.get_weather()
except Exception as e:
    print(f"Error al conectar con la API: {e}")
    exit()

# Extraer información
jobs = jobs_data["data"]  # Lista original de trabajos
weather = weather_data["data"]

# Lista para trabajos activos (que pueden ser recogidos)
active_jobs = jobs.copy()
# Lista para trabajos completados
completed_jobs = []

# Inicializar pygame y crear el mapa
pygame.init()
game_map = Map(map_data, tile_size=32)  # Usamos tu clase Map
rows, cols = game_map.height, game_map.width
screen_width = cols * game_map.tile_size + 300
screen_height = rows * game_map.tile_size
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

# Colores para los trabajos
job_colors = [
    (255, 100, 100), (100, 100, 255), (255, 255, 100),
    (255, 100, 255), (100, 255, 255)
]

# Colores para las condiciones climáticas
weather_colors = {
    "clear": (255, 255, 100), "clouds": (200, 200, 220),
    "rain_light": (150, 150, 255), "rain": (100, 100, 255),
    "storm": (150, 50, 200), "fog": (180, 180, 200),
    "wind": (200, 220, 255), "heat": (255, 150, 50),
    "cold": (150, 220, 255)
}

# Crear jugador
player = Player(cols // 2, rows // 2, game_map.tile_size, game_map.legend)

# Cámara para seguir al jugador
camera_x, camera_y = 0, 0

# Variables para control de interacción
selected_job = None
interaction_cooldown = 0
message = ""
message_timer = 0
total_earnings = 0  # Dinero total ganado

# Función para dibujar el panel lateral
def draw_sidebar():
    sidebar_rect = pygame.Rect(cols * game_map.tile_size, 0, 300, screen_height)
    pygame.draw.rect(screen, (240, 240, 240), sidebar_rect)
    pygame.draw.line(screen, (200, 200, 200), (cols * game_map.tile_size, 0), (cols * game_map.tile_size, screen_height), 2)
    
    # Título y ganancias
    title = font_large.render("Courier Quest", True, (0, 0, 0))
    screen.blit(title, (cols * game_map.tile_size + 10, 10))
    
    earnings_text = font_medium.render(f"Ganancias: ${total_earnings}", True, (0, 100, 0))
    screen.blit(earnings_text, (cols * game_map.tile_size + 150, 12))
    
    # Información del jugador
    player_title = font_medium.render("Estado del Repartidor:", True, (0, 0, 0))
    screen.blit(player_title, (cols * game_map.tile_size + 10, 40))
    
    # Barra de resistencia
    stamina_text = font_small.render(f"Resistencia: {int(player.stamina)}/100", True, (0, 0, 0))
    screen.blit(stamina_text, (cols * game_map.tile_size + 10, 65))
    pygame.draw.rect(screen, (200, 200, 200), (cols * game_map.tile_size + 10, 80, 150, 15))
    pygame.draw.rect(screen, (0, 200, 0), (cols * game_map.tile_size + 10, 80, 150 * (player.stamina / 100), 15))
    
    # Reputación
    reputation_text = font_small.render(f"Reputación: {player.reputation}/100", True, (0, 0, 0))
    screen.blit(reputation_text, (cols * game_map.tile_size + 10, 100))
    pygame.draw.rect(screen, (200, 200, 200), (cols * game_map.tile_size + 10, 115, 150, 15))
    pygame.draw.rect(screen, (0, 100, 200), (cols * game_map.tile_size + 10, 115, 150 * (player.reputation / 100), 15))
    
    # Peso actual
    weight_text = font_small.render(f"Peso: {player.current_weight}/{player.max_weight}", True, (0, 0, 0))
    screen.blit(weight_text, (cols * game_map.tile_size + 10, 135))
    
    # Inventario actual
    inventory_title = font_medium.render("Inventario:", True, (0, 0, 0))
    screen.blit(inventory_title, (cols * game_map.tile_size + 10, 160))
    
    if player.inventory:
        for i, job in enumerate(player.inventory):
            y_pos = 185 + i * 40
            pygame.draw.rect(screen, (200, 255, 200), (cols * game_map.tile_size + 10, y_pos, 280, 35))
            pygame.draw.rect(screen, (0, 200, 0), (cols * game_map.tile_size + 10, y_pos, 280, 35), 2)
            
            job_id = font_small.render(f"ID: {job['id']}", True, (0, 0, 0))
            screen.blit(job_id, (cols * game_map.tile_size + 15, y_pos + 5))
            
            destination = font_small.render(f"Entrega: {job['dropoff']}", True, (0, 0, 0))
            screen.blit(destination, (cols * game_map.tile_size + 15, y_pos + 20))
    else:
        no_items = font_small.render("No hay pedidos en inventario", True, (150, 150, 150))
        screen.blit(no_items, (cols * game_map.tile_size + 15, 185))
    
    # Información del clima
    weather_title = font_medium.render("Condición Climática:", True, (0, 0, 0))
    weather_y_pos = 250 if not player.inventory else 185 + len(player.inventory) * 40 + 10
    screen.blit(weather_title, (cols * game_map.tile_size + 10, weather_y_pos))
    
    current_weather = weather["initial"]["condition"]
    pygame.draw.circle(screen, weather_colors[current_weather], (cols * game_map.tile_size + 40, weather_y_pos + 35), 15)
    
    weather_text = font_small.render(current_weather.replace("_", " ").title(), True, (0, 0, 0))
    screen.blit(weather_text, (cols * game_map.tile_size + 60, weather_y_pos + 25))
    
    intensity_text = font_small.render(f"Intensidad: {weather['initial']['intensity']:.2f}", True, (0, 0, 0))
    screen.blit(intensity_text, (cols * game_map.tile_size + 60, weather_y_pos + 40))
    
    # Lista de trabajos disponibles
    jobs_title = font_medium.render("Trabajos Disponibles:", True, (0, 0, 0))
    jobs_y_pos = weather_y_pos + 70
    screen.blit(jobs_title, (cols * game_map.tile_size + 10, jobs_y_pos))
    
    for i, job in enumerate(active_jobs):
        y_pos = jobs_y_pos + 25 + i * 70
        
        pygame.draw.rect(screen, job_colors[i % len(job_colors)], 
                        (cols * game_map.tile_size + 10, y_pos, 20, 20))
        
        job_id = font_small.render(f"ID: {job['id']}", True, (0, 0, 0))
        screen.blit(job_id, (cols * game_map.tile_size + 35, y_pos))
        
        payout = font_small.render(f"Pago: ${job['payout']}", True, (0, 0, 0))
        screen.blit(payout, (cols * game_map.tile_size + 35, y_pos + 15))
        
        deadline = font_small.render(f"Entrega: {job['deadline'][11:16]}", True, (0, 0, 0))
        screen.blit(deadline, (cols * game_map.tile_size + 10, y_pos + 35))
        
        weight = font_small.render(f"Peso: {job['weight']}", True, (0, 0, 0))
        screen.blit(weight, (cols * game_map.tile_size + 120, y_pos + 35))
        
        priority = font_small.render(f"Prioridad: {job['priority']}", True, (0, 0, 0))
        screen.blit(priority, (cols * game_map.tile_size + 10, y_pos + 50))
    
    # Leyenda del mapa
    legend_title = font_medium.render("Leyenda del Mapa:", True, (0, 0, 0))
    screen.blit(legend_title, (cols * game_map.tile_size + 10, screen_height - 150))
    
    y_pos = screen_height - 130
    for char, info in game_map.legend.items():
        color = game_map.COLORS.get(char, (100, 100, 255))  # Usar colores de la clase Map
        pygame.draw.rect(screen, color, (cols * game_map.tile_size + 10, y_pos, 15, 15))
        name = font_small.render(info["name"].title(), True, (0, 0, 0))
        screen.blit(name, (cols * game_map.tile_size + 30, y_pos))
        y_pos += 20

# Función para dibujar marcadores de trabajos en el mapa
def draw_job_markers():
    # Dibujar solo trabajos activos (no completados)
    for i, job in enumerate(active_jobs):
        color = job_colors[i % len(job_colors)]
        
        # Si el trabajo está en el inventario, usar color verde
        if job in player.inventory:
            color = (0, 255, 0)  # Verde para trabajos en inventario
        
        # Dibujar punto de recogida
        pickup_x, pickup_y = job["pickup"]
        pygame.draw.circle(screen, color, 
                          (pickup_x * game_map.tile_size + game_map.tile_size // 2 - camera_x, 
                           pickup_y * game_map.tile_size + game_map.tile_size // 2 - camera_y), 
                          7)
        pygame.draw.circle(screen, (255, 255, 255), 
                          (pickup_x * game_map.tile_size + game_map.tile_size // 2 - camera_x, 
                           pickup_y * game_map.tile_size + game_map.tile_size // 2 - camera_y), 
                          7, 1)
        
        # Dibujar punto de entrega
        dropoff_x, dropoff_y = job["dropoff"]
        pygame.draw.rect(screen, color, 
                        (dropoff_x * game_map.tile_size + game_map.tile_size // 2 - 5 - camera_x, 
                         dropoff_y * game_map.tile_size + game_map.tile_size // 2 - 5 - camera_y, 
                         10, 10))
        pygame.draw.rect(screen, (255, 255, 255), 
                        (dropoff_x * game_map.tile_size + game_map.tile_size // 2 - 5 - camera_x, 
                         dropoff_y * game_map.tile_size + game_map.tile_size // 2 - 5 - camera_y, 
                         10, 10), 1)
        
        # Dibujar línea conectando recogida y entrega (solo si no está en inventario)
        if job not in player.inventory:
            pygame.draw.line(screen, color, 
                            (pickup_x * game_map.tile_size + game_map.tile_size // 2 - camera_x, 
                             pickup_y * game_map.tile_size + game_map.tile_size // 2 - camera_y),
                            (dropoff_x * game_map.tile_size + game_map.tile_size // 2 - camera_x, 
                             dropoff_y * game_map.tile_size + game_map.tile_size // 2 - camera_y), 
                            2)

# Bucle principal
running = True
clock = pygame.time.Clock()
last_time = pygame.time.get_ticks()

while running:
    current_time = pygame.time.get_ticks()
    dt = (current_time - last_time) / 1000.0
    last_time = current_time
    
    if interaction_cooldown > 0:
        interaction_cooldown -= dt
    
    if message_timer > 0:
        message_timer -= dt
    else:
        message = ""
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            
            if mouse_x > cols * game_map.tile_size:
                weather_y_pos = 250 if not player.inventory else 185 + len(player.inventory) * 40 + 10
                jobs_y_pos = weather_y_pos + 70
                job_index = (mouse_y - jobs_y_pos - 25) // 70
                
                if 0 <= job_index < len(active_jobs):
                    selected_job = active_jobs[job_index]
                    message = f"Seleccionado: {selected_job['id']}"
                    message_timer = 3
        
        # Tecla E para interactuar (recoger/entregar)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e and interaction_cooldown <= 0:
            # Primero verificar entregas (tiene prioridad)
            for job in player.inventory[:]:  # Usamos copia para modificar durante iteración
                if player.is_at_location(job["dropoff"]):
                    if player.remove_from_inventory(job["id"]):
                        # Añadir a trabajos completados y remover de activos
                        completed_jobs.append(job)
                        if job in active_jobs:
                            active_jobs.remove(job)
                        
                        # Sumar ganancias
                        total_earnings += job["payout"]
                        
                        message = f"Entregado: {job['id']} +${job['payout']}"
                        message_timer = 3
                        interaction_cooldown = 0.5
                        break
            
            # Luego verificar recogidas
            if interaction_cooldown <= 0:  # Solo si no acabamos de entregar
                for job in active_jobs[:]:  # Usamos copia para modificar durante iteración
                    if player.is_at_location(job["pickup"]):
                        if player.can_pickup_job(job):
                            if player.add_to_inventory(job):
                                message = f"Recogido: {job['id']}"
                                message_timer = 3
                                interaction_cooldown = 0.5
                                break
                        else:
                            message = "¡No tienes capacidad suficiente!"
                            message_timer = 3
                            break
    
    # Movimiento del jugador
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
    
    current_weather = weather["initial"]["condition"]
    weather_multiplier = {
        "clear": 1.00, "clouds": 0.98, "rain_light": 0.90,
        "rain": 0.85, "storm": 0.75, "fog": 0.88,
        "wind": 0.92, "heat": 0.90, "cold": 0.92
    }.get(current_weather, 1.0)
    
    tile_x, tile_y = int(player.x), int(player.y)
    if 0 <= tile_y < len(game_map.tiles) and 0 <= tile_x < len(game_map.tiles[0]):
        tile_char = game_map.tiles[tile_y][tile_x]
        surface_multiplier = game_map.legend[tile_char].get("surface_weight", 1.0)
    else:
        surface_multiplier = 1.0
    
    if dx != 0 or dy != 0:
        player.move(dx, dy, dt, weather_multiplier, surface_multiplier, game_map.tiles)
    else:
        player.recover_stamina(dt)
    
    # Actualizar cámara
    camera_x = player.x * game_map.tile_size - screen_width // 2 + 150
    camera_y = player.y * game_map.tile_size - screen_height // 2
    camera_x = max(0, min(camera_x, cols * game_map.tile_size - screen_width + 300))
    camera_y = max(0, min(camera_y, rows * game_map.tile_size - screen_height))
    
    # Dibujar
    screen.fill((255, 255, 255))

    # Dibujar mapa usando la clase Map - VERSIÓN SIMPLIFICADA
    for y, row in enumerate(game_map.tiles):
        for x, char in enumerate(row):
            color = game_map.COLORS.get(char, (100, 100, 255))  # Usar colores de la clase Map
            rect = pygame.Rect(x * game_map.tile_size - camera_x, y * game_map.tile_size - camera_y, 
                             game_map.tile_size, game_map.tile_size)
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, (0, 0, 0), rect, 1)
    
    # Dibujar marcadores de trabajos (solo activos)
    draw_job_markers()
    
    # Dibujar jugador
    player.draw(screen, camera_x, camera_y)
    
    # Dibujar panel lateral
    draw_sidebar()
    
    # Dibujar mensaje temporal
    if message:
        msg_surface = font_medium.render(message, True, (0, 0, 0))
        screen.blit(msg_surface, (10, 10))
    
    # Dibujar indicador de interacción
    nearby_active = False
    for job in active_jobs:
        if (player.is_at_location(job["pickup"]) and job not in player.inventory) or \
           (job in player.inventory and player.is_at_location(job["dropoff"])):
            nearby_active = True
            break
    
    if nearby_active and interaction_cooldown <= 0:
        hint_text = font_small.render("Presiona E para interactuar", True, (255, 255, 255))
        hint_bg = pygame.Rect(player.x * game_map.tile_size - camera_x - 70, 
                             player.y * game_map.tile_size - camera_y - 25, 
                             140, 20)
        pygame.draw.rect(screen, (0, 0, 0, 128), hint_bg, border_radius=5)
        screen.blit(hint_text, (player.x * game_map.tile_size - camera_x - 65, 
                               player.y * game_map.tile_size - camera_y - 20))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
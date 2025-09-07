import pygame
import math
from datetime import datetime
from Player import Player
from map import Map
from api_manager import APIManager
from weather import Weather
from game_time import GameTime
from OrderList import OrderList
from Order import Order

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

# Crear OrderList desde la respuesta de la API
active_orders = OrderList.from_api_response(jobs_data)
completed_orders = OrderList.create_empty()

# Inicializar pygame y crear el mapa
pygame.init()
game_map = Map(map_data, tile_size=24)
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
    font_xlarge = pygame.font.Font(None, 24)
except:
    font_small = pygame.font.SysFont("Arial", 12)
    font_medium = pygame.font.SysFont("Arial", 14)
    font_large = pygame.font.SysFont("Arial", 18, bold=True)
    font_xlarge = pygame.font.SysFont("Arial", 24, bold=True)

# Colores para los trabajos
job_colors = [
    (255, 100, 100), (100, 100, 255), (255, 255, 100),
    (255, 100, 255), (100, 255, 255)
]

# Crear jugador
player = Player(cols // 2, rows // 2, game_map.tile_size, game_map.legend)

# Crear sistema de clima
weather_system = Weather(api)

# Crear sistema de tiempo de juego (15 minutos de jornada)
game_time = GameTime(total_duration_min=15)
game_time.start()

# Cámara para seguir al jugador
camera_x, camera_y = 0, 0

# Variables para control de interacción
selected_order = None
interaction_cooldown = 0
message = ""
message_timer = 0
total_earnings = 0
game_over = False
victory = False

# Meta de ingresos (podría venir del mapa)
income_goal = map_data.get("goal", 3000)

# Función para dibujar el panel lateral
def draw_sidebar():
    sidebar_rect = pygame.Rect(cols * game_map.tile_size, 0, 300, screen_height)
    pygame.draw.rect(screen, (240, 240, 240), sidebar_rect)
    pygame.draw.line(screen, (200, 200, 200), (cols * game_map.tile_size, 0), (cols * game_map.tile_size, screen_height), 2)
    
    # Título y ganancias
    title = font_large.render("Courier Quest", True, (0, 0, 0))
    screen.blit(title, (cols * game_map.tile_size + 10, 10))
    
    # Tiempo
    time_bg = pygame.Rect(cols * game_map.tile_size + 10, 35, 280, 25)
    pygame.draw.rect(screen, (220, 220, 220), time_bg, border_radius=5)
    pygame.draw.rect(screen, (100, 100, 100), time_bg, 2, border_radius=5)
    
    # Cambiar color del tiempo según cuánto queda
    remaining_time = game_time.get_remaining_time()
    if remaining_time < 60:
        time_color = (255, 50, 50)
    elif remaining_time < 300:
        time_color = (255, 150, 50)
    else:
        time_color = (0, 100, 0)
    
    time_text = font_medium.render(f"⏰ Tiempo: {game_time.get_remaining_time_formatted()}", True, time_color)
    screen.blit(time_text, (cols * game_map.tile_size + 20, 38))
    
    # Ganancias y meta
    earnings_text = font_medium.render(f"💰 Ganancias: ${total_earnings}", True, (0, 100, 0))
    screen.blit(earnings_text, (cols * game_map.tile_size + 10, 65))
    
    goal_text = font_small.render(f"🎯 Meta: ${income_goal}", True, (0, 0, 0))
    screen.blit(goal_text, (cols * game_map.tile_size + 150, 65))
    
    # Información del jugador
    player_title = font_medium.render("Estado del Repartidor:", True, (0, 0, 0))
    screen.blit(player_title, (cols * game_map.tile_size + 10, 90))
    
    # Barra de resistencia
    stamina_text = font_small.render(f"Resistencia: {int(player.stamina)}/100", True, (0, 0, 0))
    screen.blit(stamina_text, (cols * game_map.tile_size + 10, 115))
    pygame.draw.rect(screen, (200, 200, 200), (cols * game_map.tile_size + 10, 130, 150, 15))
    pygame.draw.rect(screen, (0, 200, 0), (cols * game_map.tile_size + 10, 130, 150 * (player.stamina / 100), 15))
    
    # Reputación
    reputation_text = font_small.render(f"Reputación: {player.reputation}/100", True, (0, 0, 0))
    screen.blit(reputation_text, (cols * game_map.tile_size + 10, 150))
    pygame.draw.rect(screen, (200, 200, 200), (cols * game_map.tile_size + 10, 165, 150, 15))
    
    # Color de la barra de reputación según el nivel
    if player.reputation >= 90:
        rep_color = (0, 200, 0)
    elif player.reputation >= 70:
        rep_color = (0, 150, 200)
    elif player.reputation >= 50:
        rep_color = (255, 150, 0)
    else:
        rep_color = (255, 50, 50)
        
    pygame.draw.rect(screen, rep_color, (cols * game_map.tile_size + 10, 165, 150 * (player.reputation / 100), 15))
    
    # Peso actual
    weight_text = font_small.render(f"Peso: {player.current_weight}/{player.max_weight}", True, (0, 0, 0))
    screen.blit(weight_text, (cols * game_map.tile_size + 10, 185))
    
    # Inventario actual
    inventory_title = font_medium.render("Inventario:", True, (0, 0, 0))
    screen.blit(inventory_title, (cols * game_map.tile_size + 10, 210))
    
    if player.inventory:
        for i, order in enumerate(player.inventory):
            y_pos = 235 + i * 40
            pygame.draw.rect(screen, (200, 255, 200), (cols * game_map.tile_size + 10, y_pos, 280, 35))
            pygame.draw.rect(screen, (0, 200, 0), (cols * game_map.tile_size + 10, y_pos, 280, 35), 2)
            
            order_id = font_small.render(f"ID: {order.id}", True, (0, 0, 0))
            screen.blit(order_id, (cols * game_map.tile_size + 15, y_pos + 5))
            
            destination = font_small.render(f"Entrega: {order.dropoff}", True, (0, 0, 0))
            screen.blit(destination, (cols * game_map.tile_size + 15, y_pos + 20))
    else:
        no_items = font_small.render("No hay pedidos en inventario", True, (150, 150, 150))
        screen.blit(no_items, (cols * game_map.tile_size + 15, 235))
    
    # Información del clima
    weather_title = font_medium.render("Condición Climática:", True, (0, 0, 0))
    weather_y_pos = 300 if not player.inventory else 235 + len(player.inventory) * 40 + 10
    screen.blit(weather_title, (cols * game_map.tile_size + 10, weather_y_pos))
    
    # Dibujar el indicador del clima usando la clase Weather
    weather_system.draw(screen, cols * game_map.tile_size + 40, weather_y_pos + 35)
    
    # Información textual del clima
    condition_name = weather_system.current_condition.value.replace("_", " ").title()
    weather_text = font_small.render(condition_name, True, (0, 0, 0))
    screen.blit(weather_text, (cols * game_map.tile_size + 60, weather_y_pos + 25))
    
    intensity_text = font_small.render(f"Intensidad: {weather_system.current_intensity:.2f}", True, (0, 0, 0))
    screen.blit(intensity_text, (cols * game_map.tile_size + 60, weather_y_pos + 40))
    
    speed_text = font_small.render(f"Velocidad: x{weather_system.current_multiplier:.2f}", True, (0, 0, 0))
    screen.blit(speed_text, (cols * game_map.tile_size + 60, weather_y_pos + 55))
    
    # Lista de trabajos disponibles
    jobs_title = font_medium.render("Trabajos Disponibles:", True, (0, 0, 0))
    jobs_y_pos = weather_y_pos + 85
    screen.blit(jobs_title, (cols * game_map.tile_size + 10, jobs_y_pos))
    
    for i, order in enumerate(active_orders):
        y_pos = jobs_y_pos + 25 + i * 70
        
        pygame.draw.rect(screen, job_colors[i % len(job_colors)], 
                        (cols * game_map.tile_size + 10, y_pos, 20, 20))
        
        order_id = font_small.render(f"ID: {order.id}", True, (0, 0, 0))
        screen.blit(order_id, (cols * game_map.tile_size + 35, y_pos))
        
        payout = font_small.render(f"Pago: ${order.payout}", True, (0, 0, 0))
        screen.blit(payout, (cols * game_map.tile_size + 35, y_pos + 15))
        
        deadline = font_small.render(f"Entrega: {order.deadline.strftime('%H:%M')}", True, (0, 0, 0))
        screen.blit(deadline, (cols * game_map.tile_size + 10, y_pos + 35))
        
        weight = font_small.render(f"Peso: {order.weight}", True, (0, 0, 0))
        screen.blit(weight, (cols * game_map.tile_size + 120, y_pos + 35))
        
        priority = font_small.render(f"Prioridad: {order.priority}", True, (0, 0, 0))
        screen.blit(priority, (cols * game_map.tile_size + 10, y_pos + 50))
    
    # Leyenda del mapa
    legend_title = font_medium.render("Leyenda del Mapa:", True, (0, 0, 0))
    legend_y_pos = screen_height - 150
    screen.blit(legend_title, (cols * game_map.tile_size + 10, legend_y_pos))
    
    y_pos = legend_y_pos + 20
    for char, info in game_map.legend.items():
        color = game_map.COLORS.get(char, (100, 100, 255))
        pygame.draw.rect(screen, color, (cols * game_map.tile_size + 10, y_pos, 15, 15))
        name = font_small.render(info["name"].title(), True, (0, 0, 0))
        screen.blit(name, (cols * game_map.tile_size + 30, y_pos))
        y_pos += 20

# Función para dibujar marcadores de trabajos en el mapa
def draw_order_markers():
    # Dibujar solo trabajos activos (no completados)
    for i, order in enumerate(active_orders):
        color = job_colors[i % len(job_colors)]
        
        # Si el trabajo está en el inventario, usar color verde
        # Usar find_by_id en lugar de "in" para objetos Order personalizados
        if player.inventory.find_by_id(order.id) is not None:
            color = (0, 255, 0)  # Verde para trabajos en inventario
        
        # Dibujar punto de recogida
        pickup_x, pickup_y = order.pickup
        pygame.draw.circle(screen, color, 
                          (pickup_x * game_map.tile_size + game_map.tile_size // 2 - camera_x, 
                           pickup_y * game_map.tile_size + game_map.tile_size // 2 - camera_y), 
                          7)
        pygame.draw.circle(screen, (255, 255, 255), 
                          (pickup_x * game_map.tile_size + game_map.tile_size // 2 - camera_x, 
                           pickup_y * game_map.tile_size + game_map.tile_size // 2 - camera_y), 
                          7, 1)
        
        # Dibujar punto de entrega
        dropoff_x, dropoff_y = order.dropoff
        pygame.draw.rect(screen, color, 
                        (dropoff_x * game_map.tile_size + game_map.tile_size // 2 - 5 - camera_x, 
                         dropoff_y * game_map.tile_size + game_map.tile_size // 2 - 5 - camera_y, 
                         10, 10))
        pygame.draw.rect(screen, (255, 255, 255), 
                        (dropoff_x * game_map.tile_size + game_map.tile_size // 2 - 5 - camera_x, 
                         dropoff_y * game_map.tile_size + game_map.tile_size // 2 - 5 - camera_y, 
                         10, 10), 1)
        
        # Dibujar línea conectando recogida y entrega (solo si no está en inventario)
        if player.inventory.find_by_id(order.id) is None:
            pygame.draw.line(screen, color, 
                            (pickup_x * game_map.tile_size + game_map.tile_size // 2 - camera_x, 
                             pickup_y * game_map.tile_size + game_map.tile_size // 2 - camera_y),
                            (dropoff_x * game_map.tile_size + game_map.tile_size // 2 - camera_x, 
                             dropoff_y * game_map.tile_size + game_map.tile_size // 2 - camera_y), 
                            2)

# Función para verificar condiciones de victoria/derrota
def check_game_conditions():
    global game_over, victory
    
    # Verificar derrota por reputación
    if player.reputation < 20:
        game_over = True
        return "Derrota: Reputación muy baja"
    
    # Verificar derrota por tiempo
    if game_time.is_time_up() and total_earnings < income_goal:
        game_over = True
        return "Derrota: Tiempo agotado"
    
    # Verificar victoria
    if total_earnings >= income_goal:
        victory = True
        game_over = True
        return "¡Victoria! Meta alcanzada"
    
    return None

# Función para reiniciar el juego
def restart_game():
    global player, active_orders, completed_orders, total_earnings
    global game_over, victory, game_time, weather_system, camera_x, camera_y
    
    # Reiniciar jugador
    player = Player(cols // 2, rows // 2, game_map.tile_size, game_map.legend)
    
    # Reiniciar listas de trabajos
    active_orders = OrderList.from_api_response(jobs_data)
    completed_orders = OrderList.create_empty()
    
    # Reiniciar variables de juego
    total_earnings = 0
    game_over = False
    victory = False
    camera_x, camera_y = 0, 0
    
    # Reiniciar sistemas
    game_time = GameTime(total_duration_min=15)
    game_time.start()
    weather_system = Weather(api)

# Bucle principal
running = True
clock = pygame.time.Clock()
last_time = pygame.time.get_ticks()

while running:
    current_time = pygame.time.get_ticks()
    dt = (current_time - last_time) / 1000.0
    last_time = current_time
    
    # Actualizar sistemas
    if not game_over:
        game_time.update(dt)
        weather_system.update(dt)
    
    # Verificar condiciones del juego
    game_status = check_game_conditions()
    
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
                weather_y_pos = 300 if not player.inventory else 235 + len(player.inventory) * 40 + 10
                jobs_y_pos = weather_y_pos + 85
                order_index = (mouse_y - jobs_y_pos - 25) // 70
                
                if 0 <= order_index < len(active_orders):
                    selected_order = active_orders[order_index]
                    message = f"Seleccionado: {selected_order.id}"
                    message_timer = 3
        
        # Tecla E para interactuar (recoger/entregar)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e and interaction_cooldown <= 0 and not game_over:
            # Primero verificar entregas (tiene prioridad)
            for order in list(player.inventory):  # Crear copia de la lista para evitar problemas durante la iteración
                if player.is_at_location(order.dropoff):
                    if player.remove_from_inventory(order.id):
                        # Añadir a trabajos completados y remover de activos
                        completed_orders.enqueue(order)
                        active_orders.remove_by_id(order.id)
                        
                        # Sumar ganancias
                        total_earnings += order.payout
                        
                        message = f"Entregado: {order.id} +${order.payout}"
                        message_timer = 3
                        interaction_cooldown = 0.5
                        break
            
            # Luego verificar recogidas
            if interaction_cooldown <= 0:
                for order in list(active_orders):  # Crear copia de la lista para evitar problemas durante la iteración
                    if player.is_at_location(order.pickup):
                        if player.can_pickup_order(order):
                            if player.add_to_inventory(order):
                                message = f"Recogido: {order.id}"
                                message_timer = 3
                                interaction_cooldown = 0.5
                                break
                        else:
                            message = "¡No tienes capacidad suficiente!"
                            message_timer = 3
                            break
        
        # Tecla R para reiniciar el juego
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r and game_over:
            restart_game()
    
    # Movimiento del jugador (solo si el juego no ha terminado)
    if not game_over:
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
        
        # Obtener multiplicadores del sistema de clima
        weather_multiplier = weather_system.get_speed_multiplier()
        weather_stamina_consumption = weather_system.get_stamina_consumption()
        
        tile_x, tile_y = int(player.x), int(player.y)
        if 0 <= tile_y < len(game_map.tiles) and 0 <= tile_x < len(game_map.tiles[0]):
            tile_char = game_map.tiles[tile_y][tile_x]
            surface_multiplier = game_map.legend[tile_char].get("surface_weight", 1.0)
        else:
            surface_multiplier = 1.0
        
        if dx != 0 or dy != 0:
            player.move(dx, dy, dt, weather_multiplier, surface_multiplier, game_map.tiles, weather_stamina_consumption)
        else:
            player.recover_stamina(dt)
    
    # Actualizar cámara
    camera_x = player.x * game_map.tile_size - screen_width // 2 + 150
    camera_y = player.y * game_map.tile_size - screen_height // 2
    camera_x = max(0, min(camera_x, cols * game_map.tile_size - screen_width + 300))
    camera_y = max(0, min(camera_y, rows * game_map.tile_size - screen_height))
    
    # Dibujar
    screen.fill((255, 255, 255))

    # Dibujar mapa
    for y, row in enumerate(game_map.tiles):
        for x, char in enumerate(row):
            color = game_map.COLORS.get(char, (100, 100, 255))
            rect = pygame.Rect(x * game_map.tile_size - camera_x, y * game_map.tile_size - camera_y, 
                             game_map.tile_size, game_map.tile_size)
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, (0, 0, 0), rect, 1)
    
    # Dibujar marcadores de trabajos
    draw_order_markers()
    
    # Dibujar jugador
    player.draw(screen, camera_x, camera_y)
    
    # Dibujar panel lateral
    draw_sidebar()
    
    # Dibujar mensaje temporal
    if message:
        msg_surface = font_medium.render(message, True, (0, 0, 0))
        screen.blit(msg_surface, (10, 10))
    
    # Dibujar mensaje de fin de juego
    if game_over:
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))
        
        if victory:
            result_text = font_xlarge.render("¡VICTORIA!", True, (0, 255, 0))
            reason_text = font_large.render(f"Has ganado ${total_earnings}", True, (255, 255, 255))
        else:
            result_text = font_xlarge.render("DERROTA", True, (255, 0, 0))
            reason_text = font_large.render(game_status, True, (255, 255, 255))
        
        screen.blit(result_text, (screen_width // 2 - result_text.get_width() // 2, screen_height // 2 - 50))
        screen.blit(reason_text, (screen_width // 2 - reason_text.get_width() // 2, screen_height // 2))
        
        restart_text = font_medium.render("Presiona R para reiniciar", True, (255, 255, 255))
        screen.blit(restart_text, (screen_width // 2 - restart_text.get_width() // 2, screen_height // 2 + 50))
    
    # Dibujar indicador de interacción (solo si el juego no ha terminado)
    if not game_over:
        nearby_active = False
        for order in active_orders:
            # Usar find_by_id en lugar de "in" para objetos Order personalizados
            in_inventory = player.inventory.find_by_id(order.id) is not None
            
            if (player.is_at_location(order.pickup) and not in_inventory) or \
               (in_inventory and player.is_at_location(order.dropoff)):
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
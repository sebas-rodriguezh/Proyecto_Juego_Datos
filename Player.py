# Player.py - MODIFICADO
from OrderList import OrderList
from Order import Order
from Speed_Movement import Speed_Movement
import pygame
import os

class Player:
    def __init__(self, x, y, tile_size, legend, scale_factor=1):
        # Posición en COORDENADAS DE MAPA (enteras)
        self.grid_x = int(x)
        self.grid_y = int(y)
        
        # Posición visual (para animación suave)
        self.visual_x = float(x)
        self.visual_y = float(y)
        
        # Movimiento por casillas
        self.is_moving = False
        self.move_timer = 0
        self.move_duration = 1.0  # Tiempo base para moverse 1 casilla
        self.target_x = self.grid_x
        self.target_y = self.grid_y
        
        # Sistema de velocidad integrado
        self.speed_system = Speed_Movement(velocidad_base=3.0)
        
        # Stats del jugador (sin cambios)
        self.stamina = 100
        self.reputation = 70
        self.inventory = OrderList.create_empty()
        self.completed_orders = OrderList.create_empty()
        self.max_weight = 5
        self.current_weight = 0
        self.state = "normal"
        self.direction = "right"
        
        # Rendering (sin cambios)
        self.tile_size = tile_size
        self.legend = legend
        self.scale_factor = scale_factor
        self.target_size = 32 * scale_factor
        self.sprite_sheet = self.load_sprites()
        self.current_frame = 0
        self.animation_time = 0
        self.animation_speed = 0.1
        self.current_job = None
        
    # Métodos de sprites sin cambios (mantener load_sprites y create_fallback_sprites)
    def load_sprites(self):
        try:
            sprite_sheet_image = pygame.image.load("traspa.png").convert_alpha()
            original_size = sprite_sheet_image.get_size()
            
            scaled_image = pygame.Surface((self.target_size, self.target_size), pygame.SRCALPHA)
            pygame.transform.smoothscale(
                sprite_sheet_image, 
                (self.target_size, self.target_size),
                scaled_image
            )
            
            sprites = {
                "right": [],
                "left": [],
                "up": [],
                "down": [],
            }
            
            def rotate_image(image, angle):
                orig_rect = image.get_rect()
                rot_image = pygame.transform.rotate(image, angle)
                rot_rect = orig_rect.copy()
                rot_rect.center = rot_image.get_rect().center
                return rot_image.subsurface(rot_rect).copy()
            
            for i in range(4):
                sprites["right"].append(scaled_image)
                left_img = pygame.transform.flip(scaled_image, True, False)
                sprites["left"].append(left_img)
                up_img = rotate_image(scaled_image, 90)
                sprites["up"].append(up_img)
                down_img = rotate_image(scaled_image, -90)
                sprites["down"].append(down_img)
            
            return sprites
            
        except (pygame.error, FileNotFoundError) as e:
            return self.create_fallback_sprites()
    
    def create_fallback_sprites(self):
        sprites = {
            "right": [pygame.Surface((self.target_size, self.target_size), pygame.SRCALPHA) for _ in range(4)],
            "left": [pygame.Surface((self.target_size, self.target_size), pygame.SRCALPHA) for _ in range(4)],
            "up": [pygame.Surface((self.target_size, self.target_size), pygame.SRCALPHA) for _ in range(4)],
            "down": [pygame.Surface((self.target_size, self.target_size), pygame.SRCALPHA) for _ in range(4)],
        }
        
        colors = {
            "right": (255, 0, 0, 255),
            "left": (0, 255, 0, 255),
            "up": (0, 0, 255, 255),
            "down": (255, 255, 0, 255),
        }
        
        for direction, sprite_list in sprites.items():
            for i, sprite in enumerate(sprite_list):
                sprite.fill((0, 0, 0, 0))
                pygame.draw.circle(sprite, colors[direction], 
                                  (self.target_size//2, self.target_size//2), 
                                  self.target_size//3)
                
        return sprites
    
    def try_move(self, dx, dy, tiles, weather_multiplier, surface_multiplier):
        """Intenta iniciar movimiento a una nueva casilla"""
        if self.is_moving:
            return False  # Ya se está moviendo
            
        if self.state == "exhausted":
            return False  # No se puede mover si está exhausto
        
        # Calcular nueva posición objetivo
        new_x = self.grid_x + dx
        new_y = self.grid_y + dy
        
        # Verificar límites del mapa
        if new_y < 0 or new_y >= len(tiles) or new_x < 0 or new_x >= len(tiles[0]):
            return False
            
        # Verificar si la casilla está bloqueada
        tile_char = tiles[new_y][new_x]
        if self.legend.get(tile_char, {}).get("blocked", False):
            return False
        
        # Actualizar sistema de velocidad con estado actual
        self.speed_system.actualizar_peso(self.current_weight)
        self.speed_system.actualizar_reputacion(self.reputation)
        self.speed_system.cambiar_estado_resistencia(self.state)
        
        # Obtener tipo de superficie
        surface_type = self.legend.get(tile_char, {}).get("name", "asfalto")
        
        # Calcular duración del movimiento basado en la velocidad
        velocidad_final = self.speed_system.calcular_velocidad_final(surface_type)
        velocidad_final *= weather_multiplier  # Aplicar multiplicador del clima
        
        if velocidad_final <= 0:
            return False
            
        # Calcular tiempo para moverse 1 casilla
        self.move_duration = 1.0 / velocidad_final
        
        # Iniciar movimiento
        self.target_x = new_x
        self.target_y = new_y
        self.is_moving = True
        self.move_timer = 0
        
        # Actualizar dirección
        if dx > 0:
            self.direction = "right"
        elif dx < 0:
            self.direction = "left"
        elif dy > 0:
            self.direction = "down"
        elif dy < 0:
            self.direction = "up"
            
        return True
    
    def update_movement(self, dt, weather_stamina_consumption=0):
        """Actualiza el movimiento suave entre casillas"""
        if not self.is_moving:
            # Si no se está moviendo, recuperar stamina
            self.recover_stamina(dt)
            return
        
        # Avanzar timer de movimiento
        self.move_timer += dt
        progress = min(1.0, self.move_timer / self.move_duration)
        
        # Interpolar posición visual
        start_x, start_y = float(self.grid_x), float(self.grid_y)
        target_x, target_y = float(self.target_x), float(self.target_y)
        
        self.visual_x = start_x + (target_x - start_x) * progress
        self.visual_y = start_y + (target_y - start_y) * progress
        
        # Si llegó al destino
        if progress >= 1.0:
            self.grid_x = self.target_x
            self.grid_y = self.target_y
            self.visual_x = float(self.grid_x)
            self.visual_y = float(self.grid_y)
            self.is_moving = False
            
            # Consumir stamina al completar el movimiento
            self.consume_stamina(self.move_duration, weather_stamina_consumption)
        
        # Actualizar animación
        self.animation_time += dt
        if self.animation_time >= self.animation_speed:
            self.animation_time = 0
            self.current_frame = (self.current_frame + 1) % 4
    
    def consume_stamina(self, dt, weather_consumption=0):
        """Consume stamina basado en movimiento, peso y condiciones climáticas"""
        consumption = 0.5 * dt  # Consumo base por movimiento
        consumption += weather_consumption * dt  # Consumo adicional por clima
        
        if self.current_weight > 3:
            consumption += 0.2 * (self.current_weight - 3) * dt
            
        self.stamina -= consumption
        
        if self.stamina <= 0:
            self.state = "exhausted"
            self.stamina = 0
        elif self.stamina <= 30:
            self.state = "tired"
        else:
            self.state = "normal"
    
    def recover_stamina(self, dt, at_rest_point=False):
        """Recupera stamina cuando el jugador está quieto"""
        recovery_rate = 5 if not at_rest_point else 10
        self.stamina += recovery_rate * dt
        
        if self.stamina > 100:
            self.stamina = 100
            
        if self.stamina <= 30:
            self.state = "tired"
        else:
            self.state = "normal"
    
    def is_at_location(self, location):
        """Verifica si el jugador está en una ubicación específica"""
        return self.grid_x == location[0] and self.grid_y == location[1]
    
    def get_position(self):
        """Retorna la posición actual del jugador en el grid"""
        return (self.grid_x, self.grid_y)
    
    def get_visual_position(self):
        """Retorna la posición visual para el rendering"""
        return (self.visual_x, self.visual_y)
    
    # Métodos del inventario sin cambios
    def add_to_inventory(self, order: Order) -> bool:
        if self.current_weight + order.weight <= self.max_weight:
            self.inventory.enqueue(order)
            self.current_weight += order.weight
            return True
        return False
    
    def remove_from_inventory(self, order_id: str) -> bool:
        order = self.inventory.find_by_id(order_id)
        if order:
            self.current_weight -= order.weight
            self.completed_orders.enqueue(order)
            self.inventory.remove_by_id(order_id)
            self.reputation = min(100, self.reputation + 5)
            return True
        return False
    
    def can_pickup_order(self, order: Order) -> bool:
        return self.current_weight + order.weight <= self.max_weight
    
    def get_nearby_orders(self, orders, max_distance=1):
        nearby_orders = []
        for order in orders:
            pickup_dist = abs(self.grid_x - order.pickup[0]) + abs(self.grid_y - order.pickup[1])
            dropoff_dist = abs(self.grid_x - order.dropoff[0]) + abs(self.grid_y - order.dropoff[1])
            
            if pickup_dist <= max_distance or dropoff_dist <= max_distance:
                nearby_orders.append(order)
                
        return nearby_orders
    
    def draw(self, screen, camera_x=0, camera_y=0):
        """Dibuja al jugador usando la posición visual"""
        sprite = self.sprite_sheet[self.direction][self.current_frame]
        
        # Usar posición visual en lugar de grid
        screen_x = (self.visual_x - camera_x) * self.tile_size
        screen_y = (self.visual_y - camera_y) * self.tile_size
        
        screen.blit(sprite, (screen_x, screen_y))
        
        # Barra de stamina
        bar_width = 20 * self.scale_factor
        bar_height = 3 * self.scale_factor
        
        pygame.draw.rect(screen, (100, 100, 100), 
                        (screen_x, screen_y - 10, bar_width, bar_height))
        
        pygame.draw.rect(screen, (0, 255, 0), 
                        (screen_x, screen_y - 10, bar_width * (self.stamina / 100), bar_height))
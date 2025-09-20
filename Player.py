# Player.py - MODIFICADO con sistema de recogida adyacente
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
            return False
            
        if self.state == "exhausted":
            return False
        
        new_x = self.grid_x + dx
        new_y = self.grid_y + dy
        
        if new_y < 0 or new_y >= len(tiles) or new_x < 0 or new_x >= len(tiles[0]):
            return False
            
        tile_char = tiles[new_y][new_x]
        if self.legend.get(tile_char, {}).get("blocked", False):
            return False
        
        self.speed_system.actualizar_peso(self.current_weight)
        self.speed_system.actualizar_reputacion(self.reputation)
        self.speed_system.cambiar_estado_resistencia(self.state)
        
        surface_type = self.legend.get(tile_char, {}).get("name", "asfalto")
        velocidad_final = self.speed_system.calcular_velocidad_final(surface_type)
        velocidad_final *= weather_multiplier
        
        if velocidad_final <= 0:
            return False
            
        self.move_duration = 1.0 / velocidad_final
        
        self.target_x = new_x
        self.target_y = new_y
        self.is_moving = True
        self.move_timer = 0
        
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
            self.recover_stamina(dt)
            return
        
        self.move_timer += dt
        progress = min(1.0, self.move_timer / self.move_duration)
        
        start_x, start_y = float(self.grid_x), float(self.grid_y)
        target_x, target_y = float(self.target_x), float(self.target_y)
        
        self.visual_x = start_x + (target_x - start_x) * progress
        self.visual_y = start_y + (target_y - start_y) * progress
        
        if progress >= 1.0:
            self.grid_x = self.target_x
            self.grid_y = self.target_y
            self.visual_x = float(self.grid_x)
            self.visual_y = float(self.grid_y)
            self.is_moving = False
            
            self.consume_stamina(self.move_duration, weather_stamina_consumption)
        
        self.animation_time += dt
        if self.animation_time >= self.animation_speed:
            self.animation_time = 0
            self.current_frame = (self.current_frame + 1) % 4
    
    def consume_stamina(self, dt, weather_consumption=0):
        consumption = 10.5 * dt
        consumption += weather_consumption * dt
        
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
        recovery_rate = 5 if not at_rest_point else 10
        self.stamina += recovery_rate * dt
        
        if self.stamina > 100:
            self.stamina = 100
            
        if self.stamina <= 30:
            self.state = "tired"
        else:
            self.state = "normal"
    
    def is_at_location(self, location):
        """Verifica si el jugador está EXACTAMENTE en una ubicación"""
        return self.grid_x == location[0] and self.grid_y == location[1]
    
    def is_adjacent_to_location(self, location):
        """NUEVO: Verifica si el jugador está adyacente (incluye diagonal) a una ubicación"""
        dx = abs(self.grid_x - location[0])
        dy = abs(self.grid_y - location[1])
        
        # Adyacente incluye las 8 direcciones: arriba, abajo, izquierda, derecha y diagonales
        return dx <= 1 and dy <= 1 and (dx != 0 or dy != 0)
    
    def is_near_location(self, location, include_exact=True):
        """NUEVO: Verifica si está en la ubicación exacta O adyacente"""
        if include_exact and self.is_at_location(location):
            return True
        return self.is_adjacent_to_location(location)
    
    def get_adjacent_positions(self):
        """NUEVO: Retorna todas las posiciones adyacentes al jugador"""
        adjacent = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:  # Saltar posición actual
                    continue
                adjacent.append((self.grid_x + dx, self.grid_y + dy))
        return adjacent
    
    def get_interactable_orders(self, orders):
        """NUEVO: Obtiene órdenes con las que puede interactuar (exacta + adyacente)"""
        interactable = []
        
        for order in orders:
            # Verificar recogida (si no está en inventario)
            if self.inventory.find_by_id(order.id) is None:
                if self.is_near_location(order.pickup):
                    interactable.append({
                        'order': order,
                        'action': 'pickup',
                        'location': order.pickup,
                        'is_exact': self.is_at_location(order.pickup)
                    })
            
            # Verificar entrega (si está en inventario)
            elif self.inventory.find_by_id(order.id) is not None:
                if self.is_near_location(order.dropoff):
                    interactable.append({
                        'order': order,
                        'action': 'dropoff',
                        'location': order.dropoff,
                        'is_exact': self.is_at_location(order.dropoff)
                    })
        
        # Priorizar interacciones exactas sobre adyacentes
        interactable.sort(key=lambda x: not x['is_exact'])
        return interactable
    
    def get_position(self):
        """Retorna la posición actual del jugador en el grid"""
        return (self.grid_x, self.grid_y)
    
    def get_visual_position(self):
        """Retorna la posición visual para el rendering"""
        return (self.visual_x, self.visual_y)
    
    # Métodos del inventario (sin cambios)
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
        """MEJORADO: Usa distancia Manhattan para órdenes cercanas"""
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
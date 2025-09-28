# Player.py - VERSIÓN CORREGIDA con movimiento adecuado
from datetime import datetime
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
        
        # Movimiento por casillas con cooldown
        self.is_moving = False
        self.move_cooldown = 0
        self.move_cooldown_duration = 0.3  # AUMENTADO a 300ms para movimiento más lento
        
        # Sistema de velocidad integrado
        self.speed_system = Speed_Movement(velocidad_base=3.0)
        
        # Stats del jugador
        self.stamina = 100
        self.reputation = 70
        self.inventory = OrderList.create_empty()
        self.completed_orders = OrderList.create_empty()
        self.max_weight = 5
        self.current_weight = 0
        self.state = "normal"
        self.direction = "right"
        
        # Rendering
        self.tile_size = tile_size
        self.legend = legend
        self.scale_factor = scale_factor
        self.target_size = tile_size  # Tamaño igual al tile
        self.sprite_sheet = self.load_sprites()
        self.current_frame = 0
        self.animation_time = 0
        self.animation_speed = 0.2  # Animación más lenta
        self.current_job = None
    
    def load_sprites(self):
        try:
            sprite_sheet_image = pygame.image.load("bicicleta.png").convert_alpha()
            
            # Escalar al tamaño del tile
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
        """Intenta moverse a una nueva casilla con velocidad adecuada"""
        if self.move_cooldown > 0:
            return False
            
        if self.state == "exhausted":
            print("❌ No se puede mover: EXHAUSTED")
            return False
        
        new_x = self.grid_x + dx
        new_y = self.grid_y + dy
        
        # Verificar límites del mapa y tiles bloqueados
        if (new_y < 0 or new_y >= len(tiles) or 
            new_x < 0 or new_x >= len(tiles[0]) or
            self.legend.get(tiles[new_y][new_x], {}).get("blocked", False)):
            return False
        
        # ACTUALIZAR SISTEMA DE VELOCIDAD
        self.speed_system.actualizar_peso(self.current_weight)
        self.speed_system.actualizar_reputacion(self.reputation)
        self.speed_system.cambiar_estado_resistencia(self.state)
        
        tile_char = tiles[new_y][new_x]
        surface_type = self.legend.get(tile_char, {}).get("name", "calle")
        velocidad_final = self.speed_system.calcular_velocidad_final(surface_type)
        velocidad_final *= weather_multiplier
        
       # print(f"🚴 Velocidad: {velocidad_final:.2f} | Estado: {self.state} | Stamina: {self.stamina:.1f}")
        
        if velocidad_final <= 0:
            print("❌ Velocidad <= 0, no se puede mover")
            return False
        
        # ✅ CORRECCIÓN: Calcular consumo ANTES de mover
        stamina_consumption = self.calculate_stamina_consumption(velocidad_final, weather_multiplier)
        
        # Verificar si tiene suficiente stamina
        if self.stamina - stamina_consumption < 0:
            print("❌ Stamina insuficiente para moverse")
            return False
        
        # MOVIMIENTO INSTANTÁNEO
        self.grid_x = new_x
        self.grid_y = new_y
        
        # Actualizar dirección
        if dx > 0:
            self.direction = "right"
        elif dx < 0:
            self.direction = "left"
        elif dy > 0:
            self.direction = "down"
        elif dy < 0:
            self.direction = "up"
        
        # ✅ CORRECCIÓN: Cooldown inversamente proporcional a la velocidad
        base_cooldown = 0.5
        self.move_cooldown = base_cooldown / max(0.1, velocidad_final)
        self.move_cooldown = max(0.1, min(1.0, self.move_cooldown))
        
        # ✅ CORRECCIÓN: Consumir stamina DESPUÉS de moverse exitosamente
        self.consume_stamina(stamina_consumption)
        
        self.is_moving = True
        
        return True
    
    
    def calculate_stamina_consumption(self, velocidad_final, weather_multiplier):
        """Calcula el consumo de stamina POR CELDA movida"""
        # Consumo BASE por celda (según especificaciones del proyecto)
        base_consumption = 0.5  # -0.5 base por celda como dice el documento
        
        # Penalización por peso (si lleva más de 3kg)
        weight_penalty = 0
        if self.current_weight > 3:
            weight_penalty = 0.2 * (self.current_weight - 3)  # -0.2 por cada kg sobre 3
        
        # Penalización por clima adverso
        weather_penalty = 0
        if weather_multiplier < 0.9:  # Clima adverso
            # Ajustar según el clima específico (rain/wind: -0.1, storm: -0.3, heat: -0.2)
            if weather_multiplier <= 0.75:  # Storm
                weather_penalty = 0.3
            elif weather_multiplier <= 0.85:  # Rain
                weather_penalty = 0.1
            elif weather_multiplier <= 0.90:  # Light rain/heat
                weather_penalty = 0.2
        
        total_consumption = base_consumption + weight_penalty + weather_penalty
        
        # ✅ CORRECCIÓN: Más velocidad = MÁS consumo de stamina
        # Ajustar por velocidad (moverse rápido cansa más)
        speed_factor = 1.0 + (3.0 - min(velocidad_final, 3.0)) * 0.3  # Velocidad baja = más esfuerzo
        total_consumption *= speed_factor
        
       # print(f"💪 Consumo stamina: base={base_consumption:.2f}, peso={weight_penalty:.2f}, clima={weather_penalty:.2f}, velocidad_factor={speed_factor:.2f}")
        
        return total_consumption
    def update_movement(self, dt, weather_stamina_consumption=0):
        """Actualiza el cooldown del movimiento y la animación"""
        # Actualizar cooldown
        if self.move_cooldown > 0:
            self.move_cooldown -= dt
            if self.move_cooldown <= 0:
                self.move_cooldown = 0
                self.is_moving = False
        
        # Si no nos estamos moviendo, recuperar stamina
        if not self.is_moving:
            self.recover_stamina(dt)
        
        # Actualizar animación (más lenta cuando está tired/exhausted)
        animation_modifier = 1.0
        if self.state == "tired":
            animation_modifier = 0.7
        elif self.state == "exhausted":
            animation_modifier = 0.3
            
        self.animation_time += dt * animation_modifier
        if self.animation_time >= self.animation_speed:
            self.animation_time = 0
            self.current_frame = (self.current_frame + 1) % 4
    
    def consume_stamina(self, consumption):
        """Consume stamina directamente (sin parámetro dt)"""
        # print(f"=== CONSUMO STAMINA ===")
        # print(f"Consumo: {consumption:.3f}")
        # print(f"Stamina antes: {self.stamina:.1f}")
        
        self.stamina -= consumption
        
        # Actualizar estado basado en stamina
        if self.stamina <= 0:
            self.state = "exhausted"
            self.stamina = 0
            print("¡¡¡EXHAUSTED!!! - Stamina agotada")
        elif self.stamina <= 30:
            if self.state != "tired" and self.state != "exhausted":
                print("Estado cambiado a TIRED")
            self.state = "tired"
        # else:
        #     if self.state != "normal" and self.state != "exhausted":
        #         print("Estado cambiado a NORMAL")
        #     self.state = "normal"
        
        # print(f"Stamina después: {self.stamina:.1f}")
        # print(f"Estado actual: {self.state}")
        # print("======================")

    def recover_stamina(self, dt, at_rest_point=False):
        """Recupera stamina cuando no se está moviendo"""
        # ✅ CORRECCIÓN: Tasas de recuperación según especificaciones
        recovery_rate = 5.0  # +5 por segundo (base)
        if at_rest_point:
            recovery_rate = 10.0  # +10 por segundo en puntos de descanso
        
        recovery = recovery_rate * dt
        
        old_stamina = self.stamina
        self.stamina = min(100, self.stamina + recovery)
        
        # Manejar transición de estado exhausted
        if self.state == "exhausted" and self.stamina >= 30:
            self.state = "normal"
            print("✅ Recuperado de EXHAUSTED a NORMAL")
        elif self.state != "exhausted":
            # Actualizar estado normal/tired
            if self.stamina <= 30:
                self.state = "tired"
            else:
                self.state = "normal"
        
        # Debug de recuperación
        # if recovery > 0 and abs(old_stamina - self.stamina) > 0.01:
        #     print(f"💚 Recuperando stamina: +{recovery:.2f} (total: {self.stamina:.1f})")

    def reorganize_inventory_by_priority(self):
        if not self.inventory.is_empty():
            self.inventory.reorganize_by_priority()

    def reorganize_inventory_by_deadline(self):
        if not self.inventory.is_empty():
            self.inventory.reorganize_by_deadline()
    
    def is_at_location(self, location):
        return self.grid_x == location[0] and self.grid_y == location[1]
    
    def is_adjacent_to_location(self, location, radius=4):
        dx = abs(self.grid_x - location[0])
        dy = abs(self.grid_y - location[1])
        return dx <= radius and dy <= radius and (dx != 0 or dy != 0)

    def is_near_location(self, location, include_exact=True, radius=2):
        if include_exact and self.is_at_location(location):
            return True
        distance_x = abs(self.grid_x - location[0])
        distance_y = abs(self.grid_y - location[1])
        return distance_x <= radius and distance_y <= radius
    
    def get_adjacent_positions(self):
        adjacent = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                adjacent.append((self.grid_x + dx, self.grid_y + dy))
        return adjacent
    
    def get_interactable_orders(self, orders, game_map, radius=1, game_time=None):
        interactable = []
        
        if game_time is None:
            raise ValueError("game_time es requerido para verificar expiraciones")
        else:
            current_time = game_time.get_current_game_time()
        
        # Pedidos para RECOGER
        for order in orders:
            if (not order.is_expired and 
                not order.is_completed and 
                not order.is_in_inventory and
                not self.inventory.find_by_id(order.id)):
                
                if order.check_expiration(current_time):
                    continue
                
                can_pickup = self.is_near_location(order.pickup, include_exact=True, radius=radius)
                
                if can_pickup:
                    distance = max(abs(self.grid_x - order.pickup[0]), 
                                abs(self.grid_y - order.pickup[1]))
                    interactable.append({
                        'order': order,
                        'action': 'pickup',
                        'location': order.pickup,
                        'is_exact': self.is_at_location(order.pickup),
                        'distance': distance,
                        'is_building': self.is_building_location(order.pickup, game_map)
                    })
        
        # Pedidos para ENTREGAR
        for order in self.inventory:
            if not order.is_completed:
                if order.check_expiration(current_time):
                    continue
                
                can_dropoff = self.is_near_location(order.dropoff, include_exact=True, radius=radius)
                
                if can_dropoff:
                    distance = max(abs(self.grid_x - order.dropoff[0]), 
                                abs(self.grid_y - order.dropoff[1]))
                    interactable.append({
                        'order': order,
                        'action': 'dropoff',
                        'location': order.dropoff,
                        'is_exact': self.is_at_location(order.dropoff),
                        'distance': distance,
                        'is_building': self.is_building_location(order.dropoff, game_map)
                    })
        
        interactable.sort(key=lambda x: (not x['is_exact'], x['distance']))
        return interactable

    def is_building_location(self, location, game_map):
        x, y = location
        if 0 <= y < len(game_map.tiles) and 0 <= x < len(game_map.tiles[0]):
            tile_char = game_map.tiles[y][x]
            return game_map.legend.get(tile_char, {}).get("blocked", False)
        return False
        
    def get_position(self):
        return (self.grid_x, self.grid_y)
    
    def get_visual_position(self):
        return (self.grid_x, self.grid_y)
    
    def add_to_inventory(self, order: Order) -> bool:
        print(f"DEBUG: Intentando añadir {order.id} (peso: {order.weight}kg)")
        print(f"DEBUG: Peso actual: {self.current_weight}kg, Capacidad máxima: {self.max_weight}kg")
        
        if self.current_weight + order.weight <= self.max_weight:
            self.inventory.enqueue(order)
            self.current_weight += order.weight
            print(f"DEBUG: ✅ {order.id} añadido. Nuevo peso: {self.current_weight}kg")
            return True
        else:
            print(f"DEBUG: ❌ No se puede añadir {order.id}. Peso necesario: {order.weight}kg, Espacio disponible: {self.max_weight - self.current_weight}kg")
            return False
    
    def remove_from_inventory(self, order_id: str) -> bool:
        print(f"DEBUG: Intentando remover {order_id}")
        print(f"DEBUG: Peso antes de remover: {self.current_weight}kg")
        
        order = self.inventory.find_by_id(order_id)
        if order:
            removed = self.inventory.remove_by_id(order_id)
            if removed:
                self.current_weight -= order.weight
                print(f"DEBUG: ✅ {order_id} removido. Peso reducido en {order.weight}kg")
                print(f"DEBUG: Peso después de remover: {self.current_weight}kg")
                return True
            else:
                print(f"ERROR: No se pudo remover {order_id} del inventario")
                return False
        else:
            print(f"ERROR: Pedido {order_id} no encontrado en inventario")
            return False
  
    def verify_weight_consistency(self):
        calculated_weight = sum(order.weight for order in self.inventory)
        if self.current_weight != calculated_weight:
            print(f"ERROR: Inconsistencia de peso! Actual: {self.current_weight}, Calculado: {calculated_weight}")
            self.current_weight = calculated_weight
            print(f"Peso corregido a: {self.current_weight}kg")
        return self.current_weight == calculated_weight

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
        sprite = self.sprite_sheet[self.direction][self.current_frame]
        
        screen_x = (self.grid_x - camera_x) * self.tile_size
        screen_y = (self.grid_y - camera_y) * self.tile_size
        
        screen.blit(sprite, (screen_x, screen_y))
        
        # Barra de stamina con color según estado
        bar_width = 20 * self.scale_factor
        bar_height = 3 * self.scale_factor
        
        # Color de la barra según estado
        if self.state == "exhausted":
            color = (255, 0, 0)  # Rojo
        elif self.state == "tired":
            color = (255, 165, 0)  # Naranja
        else:
            color = (0, 255, 0)  # Verde
        
        pygame.draw.rect(screen, (100, 100, 100), 
                        (screen_x, screen_y - 10, bar_width, bar_height))
        
        pygame.draw.rect(screen, color, 
                        (screen_x, screen_y - 10, bar_width * (self.stamina / 100), bar_height))
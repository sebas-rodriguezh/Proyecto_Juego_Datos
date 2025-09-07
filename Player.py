# Player.py
import pygame
import os
import sys
import OrderList

class Player:
    def __init__(self, x, y, tile_size, legend, scale_factor=1):
        self.x = x
        self.y = y
        self.speed = 3
        self.stamina = 100
        self.reputation = 70
        self.inventory = OrderList.OrderList()
        self.completed_orders = []
        self.max_weight = 5
        self.current_weight = 0
        self.state = "normal"
        self.direction = "right"
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
            # Cargar imagen con canal alpha
            sprite_sheet_image = pygame.image.load("traspa.png").convert_alpha()
            original_size = sprite_sheet_image.get_size()
            
            print(f"Tamaño original de la imagen: {original_size[0]}x{original_size[1]}")
            
            # Escalar manteniendo la transparencia
            scaled_image = pygame.Surface((self.target_size, self.target_size), pygame.SRCALPHA)
            pygame.transform.smoothscale(
                sprite_sheet_image, 
                (self.target_size, self.target_size),
                scaled_image
            )
            
            print(f"Imagen escalada a: {self.target_size}x{self.target_size}")
            
            sprites = {
                "right": [],
                "left": [],
                "up": [],
                "down": [],
            }
            
            # Función auxiliar para rotar manteniendo transparencia
            def rotate_image(image, angle):
                """Rota una imagen manteniendo la transparencia"""
                orig_rect = image.get_rect()
                rot_image = pygame.transform.rotate(image, angle)
                rot_rect = orig_rect.copy()
                rot_rect.center = rot_image.get_rect().center
                return rot_image.subsurface(rot_rect).copy()
            
            # Crear sprites para todas las direcciones
            for i in range(4):
                # Derecha (imagen original)
                sprites["right"].append(scaled_image)
                
                # Izquierda (volteo horizontal manteniendo transparencia)
                left_img = pygame.transform.flip(scaled_image, True, False)
                sprites["left"].append(left_img)
                
                # Arriba (rotación 90 grados manteniendo transparencia)
                up_img = rotate_image(scaled_image, 90)
                sprites["up"].append(up_img)
                
                # Abajo (rotación -90 grados manteniendo transparencia)
                down_img = rotate_image(scaled_image, -90)
                sprites["down"].append(down_img)
            
            print("Imagen individual procesada correctamente con transparencia")
            return sprites
            
        except (pygame.error, FileNotFoundError) as e:
            print(f"No se pudieron cargar los sprites: {e}")
            print("Usando sprites de respaldo (colores sólidos)")
            
            return self.create_fallback_sprites()
    
    def create_fallback_sprites(self):
        sprites = {
            "right": [pygame.Surface((self.target_size, self.target_size), pygame.SRCALPHA) for _ in range(4)],
            "left": [pygame.Surface((self.target_size, self.target_size), pygame.SRCALPHA) for _ in range(4)],
            "up": [pygame.Surface((self.target_size, self.target_size), pygame.SRCALPHA) for _ in range(4)],
            "down": [pygame.Surface((self.target_size, self.target_size), pygame.SRCALPHA) for _ in range(4)],
        }
        
        colors = {
            "right": (255, 0, 0, 255),      # Rojo con alpha
            "left": (0, 255, 0, 255),       # Verde con alpha
            "up": (0, 0, 255, 255),         # Azul con alpha
            "down": (255, 255, 0, 255),     # Amarillo con alpha
        }
        
        for direction, sprite_list in sprites.items():
            for i, sprite in enumerate(sprite_list):
                sprite.fill((0, 0, 0, 0))  # Rellenar con transparente
                pygame.draw.circle(sprite, colors[direction], 
                                  (self.target_size//2, self.target_size//2), 
                                  self.target_size//3)
                
                # Dibujar una flecha indicando la dirección
                if direction == "right":
                    points = [(self.target_size//4, self.target_size//4),
                             (3*self.target_size//4, self.target_size//2),
                             (self.target_size//4, 3*self.target_size//4)]
                elif direction == "left":
                    points = [(3*self.target_size//4, self.target_size//4),
                             (self.target_size//4, self.target_size//2),
                             (3*self.target_size//4, 3*self.target_size//4)]
                elif direction == "up":
                    points = [(self.target_size//4, 3*self.target_size//4),
                             (self.target_size//2, self.target_size//4),
                             (3*self.target_size//4, 3*self.target_size//4)]
                else:  # down
                    points = [(self.target_size//4, self.target_size//4),
                             (self.target_size//2, 3*self.target_size//4),
                             (3*self.target_size//4, self.target_size//4)]
                
                pygame.draw.polygon(sprite, (255, 255, 255, 255), points)
                
        return sprites
    
    def move(self, dx, dy, dt, weather_multiplier, surface_multiplier, tiles, weather_stamina_consumption=0):
        """Mueve al jugador con los multiplicadores de clima y superficie"""
        if self.state == "exhausted":
            return False
            
        # Calcular velocidad con todos los multiplicadores
        speed = self.speed * weather_multiplier * surface_multiplier
        
        # Reducir velocidad si está cansado
        if self.state == "tired":
            speed *= 0.8
            
        # Calcular nueva posición
        new_x = self.x + dx * speed * dt
        new_y = self.y + dy * speed * dt
        

        # tile_x, tile_y = int(new_x), int(new_y)
        # if 0 <= tile_y < len(tiles) and 0 <= tile_x < len(tiles[0]):
        #    tile_char = tiles[tile_y][tile_x]
        #    if self.legend.get(tile_char, {}).get("blocked", False):
        #        return False  # No se puede mover a través de edificios
        
        # Actualizar dirección
        if dx > 0:
            self.direction = "right"
        elif dx < 0:
            self.direction = "left"
        elif dy > 0:
            self.direction = "down"
        elif dy < 0:
            self.direction = "up"
            
        # Actualizar posición
        self.x = new_x
        self.y = new_y
        
        # Consumir stamina (incluyendo el consumo adicional por clima)
        self.consume_stamina(dt, weather_stamina_consumption)
        
        # Actualizar animación
        self.animation_time += dt
        if self.animation_time >= self.animation_speed:
            self.animation_time = 0
            self.current_frame = (self.current_frame + 1) % 4
            
        return True
    
    def consume_stamina(self, dt, weather_consumption=0):
        """Consume stamina basado en movimiento, peso y condiciones climáticas"""
        # Consumo base por movimiento
        consumption = 1 * dt
        
        # Consumo adicional por clima
        consumption += weather_consumption * dt
        
        # Consumo adicional por peso excesivo
        if self.current_weight > 3:
            consumption += 0.2 * (self.current_weight - 3) * dt
            
        # Aplicar consumo
        self.stamina -= consumption
        
        # Actualizar estado basado en stamina
        if self.stamina <= 0:
            self.state = "exhausted"
            self.stamina = 0
        elif self.stamina <= 30:
            self.state = "tired"
        else:
            self.state = "normal"
    
    def recover_stamina(self, dt, at_rest_point=False):
        """Recupera stamina cuando el jugador está quieto"""
        recovery_rate = 5  # Tasa base de recuperación
        if at_rest_point:
            recovery_rate = 10  # Recuperación más rápida en puntos de descanso
            
        self.stamina += recovery_rate * dt
        
        # Limitar stamina al máximo
        if self.stamina > 100:
            self.stamina = 100
            
        # Actualizar estado
        if self.stamina <= 30:
            self.state = "tired"
        else:
            self.state = "normal"
    
    def add_to_inventory(self, job):
        """Añade un trabajo al inventario si hay capacidad"""
        if self.current_weight + job["weight"] <= self.max_weight:
            self.inventory.enqueue(job)
            self.current_weight += job["weight"]
            return True
        return False

    def remove_from_inventory(self, job_id):
        """Elimina un trabajo del inventario y lo marca como completado"""
        job = self.inventory.remove_by_id(job_id)
        if job:
            self.current_weight -= job["weight"]
            self.completed_orders.append(job)
            self.reputation = min(100, self.reputation + 5)
            return True
        return False
    
    def can_pickup_job(self, job):
        """Verifica si el jugador puede cargar un trabajo adicional"""
        return self.current_weight + job["weight"] <= self.max_weight
    
    def is_at_location(self, location):
        """Verifica si el jugador está en una ubicación específica"""
        return int(self.x) == location[0] and int(self.y) == location[1]
    
    def get_nearby_jobs(self, jobs, max_distance=1):
        """Obtiene trabajos cercanos al jugador"""
        nearby_jobs = []
        for job in jobs:
            # Calcular distancia Manhattan a los puntos de recogida y entrega
            pickup_dist = abs(int(self.x) - job["pickup"][0]) + abs(int(self.y) - job["pickup"][1])
            dropoff_dist = abs(int(self.x) - job["dropoff"][0]) + abs(int(self.y) - job["dropoff"][1])
            
            # Añadir si está dentro de la distancia máxima
            if pickup_dist <= max_distance or dropoff_dist <= max_distance:
                nearby_jobs.append(job)
                
        return nearby_jobs
    
    def draw(self, screen, camera_x=0, camera_y=0):
        """Dibuja al jugador en la pantalla"""
        # Obtener sprite actual según dirección y frame de animación
        sprite = self.sprite_sheet[self.direction][self.current_frame]
        
        # Calcular posición en pantalla
        screen_x = (self.x - camera_x) * self.tile_size
        screen_y = (self.y - camera_y) * self.tile_size
        
        # Dibujar sprite
        screen.blit(sprite, (screen_x, screen_y))
        
        # Dibujar barra de stamina
        bar_width = 20 * self.scale_factor
        bar_height = 3 * self.scale_factor
        
        # Fondo de la barra
        pygame.draw.rect(screen, (100, 100, 100), 
                        (screen_x, screen_y - 10, bar_width, bar_height))
        
        # Barra de stamina (verde)
        pygame.draw.rect(screen, (0, 255, 0), 
                        (screen_x, screen_y - 10, bar_width * (self.stamina / 100), bar_height))
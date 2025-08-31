# Player.py
import pygame
import os

class Player:
    def __init__(self, x, y, tile_size, legend, scale_factor=1):
        self.x = x
        self.y = y
        self.speed = 3  # celdas por segundo
        self.stamina = 100
        self.reputation = 70
        self.inventory = []  # Lista de trabajos/pedidos activos
        self.completed_orders = []  # Lista de pedidos completados
        self.max_weight = 5
        self.current_weight = 0
        self.state = "normal"  # normal, tired, exhausted
        self.direction = "right"
        self.tile_size = tile_size
        self.legend = legend
        self.scale_factor = scale_factor
        self.target_size = 32 * scale_factor  # Tamaño base escalado
        self.sprite_sheet = self.load_sprites()
        self.current_frame = 0
        self.animation_time = 0
        self.animation_speed = 0.1  # segundos por frame
        self.current_job = None  # Trabajo actualmente seleccionado
        
    def load_sprites(self):
        try:
            sprite_sheet_image = pygame.image.load("images.png").convert_alpha()
            original_size = sprite_sheet_image.get_size()
            
            print(f"Tamaño original de la imagen: {original_size[0]}x{original_size[1]}")
            
            # Escalar la imagen si es necesario
            if original_size[0] > 128 or original_size[1] > 128:
                # Calcular nuevo tamaño manteniendo relación de aspecto
                scale = self.target_size / 32
                new_width = int(original_size[0] * scale)
                new_height = int(original_size[1] * scale)
                sprite_sheet_image = pygame.transform.smoothscale(sprite_sheet_image, (new_width, new_height))
                print(f"Imagen escalada a: {new_width}x{new_height}")
            
            sprites = {
                "right": [],
                "left": [],
                "up": [],
                "down": [],
            }
            
            img_width, img_height = sprite_sheet_image.get_size()
            
            # Detectar el tipo de spritesheet
            if img_width == self.target_size and img_height == self.target_size:
                # Es una imagen única del tamaño objetivo
                for i in range(4):
                    # Derecha (imagen original)
                    sprites["right"].append(sprite_sheet_image)
                    
                    # Izquierda (volteo horizontal)
                    left_img = pygame.transform.flip(sprite_sheet_image, True, False)
                    sprites["left"].append(left_img)
                    
                    # Arriba (rotación 90 grados)
                    up_img = pygame.transform.rotate(sprite_sheet_image, 90)
                    sprites["up"].append(up_img)
                    
                    # Abajo (rotación -90 grados)
                    down_img = pygame.transform.rotate(sprite_sheet_image, -90)
                    sprites["down"].append(down_img)
                
                print("Usando rotaciones de imagen para diferentes direcciones")
                
            elif img_height >= self.target_size * 4:
                # Es un spritesheet con múltiples filas
                frame_width = self.target_size
                frame_height = self.target_size
                
                for i in range(4):
                    rect_right = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
                    rect_left = pygame.Rect(i * frame_width, frame_height, frame_width, frame_height)
                    rect_up = pygame.Rect(i * frame_width, 2 * frame_height, frame_width, frame_height)
                    rect_down = pygame.Rect(i * frame_width, 3 * frame_height, frame_width, frame_height)
                    
                    sprites["right"].append(sprite_sheet_image.subsurface(rect_right))
                    sprites["left"].append(sprite_sheet_image.subsurface(rect_left))
                    sprites["up"].append(sprite_sheet_image.subsurface(rect_up))
                    sprites["down"].append(sprite_sheet_image.subsurface(rect_down))
                
                print("Usando spritesheet con múltiples direcciones")
                
            else:
                # Formato no reconocido, intentar dividir horizontalmente
                frame_count = img_width // self.target_size
                if frame_count >= 4:
                    for i in range(4):
                        rect = pygame.Rect(i * self.target_size, 0, self.target_size, self.target_size)
                        frame = sprite_sheet_image.subsurface(rect)
                        
                        sprites["right"].append(frame)
                        
                        left_img = pygame.transform.flip(frame, True, False)
                        sprites["left"].append(left_img)
                        
                        up_img = pygame.transform.rotate(frame, 90)
                        sprites["up"].append(up_img)
                        
                        down_img = pygame.transform.rotate(frame, -90)
                        sprites["down"].append(down_img)
                    
                    print("Dividiendo imagen horizontalmente y aplicando rotaciones")
                else:
                    # Si no se puede procesar, usar sprites de respaldo
                    raise pygame.error("Formato de imagen no reconocido")
                
            return sprites
            
        except (pygame.error, FileNotFoundError) as e:
            print(f"No se pudieron cargar los sprites: {e}")
            print("Usando sprites de respaldo (colores sólidos)")
            
            return self.create_fallback_sprites()
    
    def create_fallback_sprites(self):
        sprites = {
            "right": [pygame.Surface((self.target_size, self.target_size)) for _ in range(4)],
            "left": [pygame.Surface((self.target_size, self.target_size)) for _ in range(4)],
            "up": [pygame.Surface((self.target_size, self.target_size)) for _ in range(4)],
            "down": [pygame.Surface((self.target_size, self.target_size)) for _ in range(4)],
        }
        
        colors = {
            "right": (255, 0, 0),      # Rojo
            "left": (0, 255, 0),       # Verde
            "up": (0, 0, 255),         # Azul
            "down": (255, 255, 0),     # Amarillo
        }
        
        for direction, sprite_list in sprites.items():
            for i, sprite in enumerate(sprite_list):
                sprite.fill(colors[direction])
                pygame.draw.circle(sprite, (255, 255, 255), 
                                  (self.target_size//2, self.target_size//2), 
                                  self.target_size//4)
                
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
                
                pygame.draw.polygon(sprite, (0, 0, 0), points)
                
        return sprites
    
    def move(self, dx, dy, dt, weather_multiplier, surface_multiplier, tiles):
        if self.state == "exhausted":
            return False
            
        # Calcular velocidad real considerando todos los factores
        speed = self.speed * weather_multiplier * surface_multiplier
        
        if self.state == "tired":
            speed *= 0.8
            
        # Calcular nueva posición
        new_x = self.x + dx * speed * dt
        new_y = self.y + dy * speed * dt
        
        # Verificar colisiones con edificios
        # (Tu código de colisiones aquí)
            
        # Actualizar dirección para animación
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
        
        # Consumir stamina
        self.consume_stamina(dt)
        
        # Actualizar animación
        self.animation_time += dt
        if self.animation_time >= self.animation_speed:
            self.animation_time = 0
            self.current_frame = (self.current_frame + 1) % 4
            
        return True
    
    def consume_stamina(self, dt):
        # Base consumption
        consumption = 1 * dt
        
        # Extra consumption for weight
        if self.current_weight > 3:
            consumption += 0.2 * (self.current_weight - 3) * dt
            
        # TODO: Add weather effects on consumption
        
        self.stamina -= consumption
        
        # Update state based on stamina
        if self.stamina <= 0:
            self.state = "exhausted"
            self.stamina = 0
        elif self.stamina <= 30:
            self.state = "tired"
        else:
            self.state = "normal"
    
    def recover_stamina(self, dt, at_rest_point=False):
        recovery_rate = 5  # puntos por segundo
        if at_rest_point:
            recovery_rate = 10  # puntos por segundo en punto de descanso
            
        self.stamina += recovery_rate * dt
        if self.stamina > 100:
            self.stamina = 100
            
        # Update state based on stamina
        if self.stamina <= 30:
            self.state = "tired"
        else:
            self.state = "normal"
    
    def add_to_inventory(self, job):
        """Añade un trabajo al inventario si hay capacidad"""
        if self.current_weight + job["weight"] <= self.max_weight:
            self.inventory.append(job)
            self.current_weight += job["weight"]
            return True
        return False
    
    def remove_from_inventory(self, job_id):
        """Elimina un trabajo del inventario por su ID"""
        for i, job in enumerate(self.inventory):
            if job["id"] == job_id:
                self.current_weight -= job["weight"]
                self.completed_orders.append(job)  # Añadir a completados
                self.inventory.pop(i)
                # Aumentar reputación por completar pedido
                self.reputation = min(100, self.reputation + 5)
                return True
        return False
    
    def can_pickup_job(self, job):
        """Verifica si puede recoger un trabajo"""
        return self.current_weight + job["weight"] <= self.max_weight
    
    def is_at_location(self, location):
        """Verifica si el jugador está en una ubicación específica"""
        return int(self.x) == location[0] and int(self.y) == location[1]
    
    def get_nearby_jobs(self, jobs, max_distance=1):
        """Obtiene trabajos cercanos al jugador"""
        nearby_jobs = []
        for job in jobs:
            pickup_dist = abs(int(self.x) - job["pickup"][0]) + abs(int(self.y) - job["pickup"][1])
            dropoff_dist = abs(int(self.x) - job["dropoff"][0]) + abs(int(self.y) - job["dropoff"][1])
            
            if pickup_dist <= max_distance or dropoff_dist <= max_distance:
                nearby_jobs.append(job)
                
        return nearby_jobs
    
    def draw(self, screen, camera_x=0, camera_y=0):
        # Obtener el sprite actual según la dirección y frame de animación
        sprite = self.sprite_sheet[self.direction][self.current_frame]
        
        # Calcular posición en pantalla
        screen_x = (self.x - camera_x) * self.tile_size
        screen_y = (self.y - camera_y) * self.tile_size
        
        # Dibujar el sprite
        screen.blit(sprite, (screen_x, screen_y))
        
        # Dibujar barra de stamina
        bar_width = 20 * self.scale_factor
        bar_height = 3 * self.scale_factor
        pygame.draw.rect(screen, (100, 100, 100), 
                        (screen_x, screen_y - 10, bar_width, bar_height))
        pygame.draw.rect(screen, (0, 255, 0), 
                        (screen_x, screen_y - 10, bar_width * (self.stamina / 100), bar_height))
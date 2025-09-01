# Player.py
import pygame
import os

class Player:
    def __init__(self, x, y, tile_size, legend, scale_factor=1):
        self.x = x
        self.y = y
        self.speed = 3
        self.stamina = 100
        self.reputation = 70
        self.inventory = []
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
    
    # El resto de los métodos se mantienen igual...
    def move(self, dx, dy, dt, weather_multiplier, surface_multiplier, tiles):
        if self.state == "exhausted":
            return False
            
        speed = self.speed * weather_multiplier * surface_multiplier
        
        if self.state == "tired":
            speed *= 0.8
            
        new_x = self.x + dx * speed * dt
        new_y = self.y + dy * speed * dt
        
        if dx > 0:
            self.direction = "right"
        elif dx < 0:
            self.direction = "left"
        elif dy > 0:
            self.direction = "down"
        elif dy < 0:
            self.direction = "up"
            
        self.x = new_x
        self.y = new_y
        
        self.consume_stamina(dt)
        
        self.animation_time += dt
        if self.animation_time >= self.animation_speed:
            self.animation_time = 0
            self.current_frame = (self.current_frame + 1) % 4
            
        return True
    
    def consume_stamina(self, dt):
        consumption = 1 * dt
        
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
        recovery_rate = 5
        if at_rest_point:
            recovery_rate = 10
            
        self.stamina += recovery_rate * dt
        if self.stamina > 100:
            self.stamina = 100
            
        if self.stamina <= 30:
            self.state = "tired"
        else:
            self.state = "normal"
    
    def add_to_inventory(self, job):
        if self.current_weight + job["weight"] <= self.max_weight:
            self.inventory.append(job)
            self.current_weight += job["weight"]
            return True
        return False
    
    def remove_from_inventory(self, job_id):
        for i, job in enumerate(self.inventory):
            if job["id"] == job_id:
                self.current_weight -= job["weight"]
                self.completed_orders.append(job)
                self.inventory.pop(i)
                self.reputation = min(100, self.reputation + 5)
                return True
        return False
    
    def can_pickup_job(self, job):
        return self.current_weight + job["weight"] <= self.max_weight
    
    def is_at_location(self, location):
        return int(self.x) == location[0] and int(self.y) == location[1]
    
    def get_nearby_jobs(self, jobs, max_distance=1):
        nearby_jobs = []
        for job in jobs:
            pickup_dist = abs(int(self.x) - job["pickup"][0]) + abs(int(self.y) - job["pickup"][1])
            dropoff_dist = abs(int(self.x) - job["dropoff"][0]) + abs(int(self.y) - job["dropoff"][1])
            
            if pickup_dist <= max_distance or dropoff_dist <= max_distance:
                nearby_jobs.append(job)
                
        return nearby_jobs
    
    def draw(self, screen, camera_x=0, camera_y=0):
        sprite = self.sprite_sheet[self.direction][self.current_frame]
        
        screen_x = (self.x - camera_x) * self.tile_size
        screen_y = (self.y - camera_y) * self.tile_size
        
        screen.blit(sprite, (screen_x, screen_y))
        
        bar_width = 20 * self.scale_factor
        bar_height = 3 * self.scale_factor
        pygame.draw.rect(screen, (100, 100, 100), 
                        (screen_x, screen_y - 10, bar_width, bar_height))
        pygame.draw.rect(screen, (0, 255, 0), 
                        (screen_x, screen_y - 10, bar_width * (self.stamina / 100), bar_height))
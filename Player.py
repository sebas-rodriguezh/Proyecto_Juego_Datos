import pygame

class Player:
    def __init__(self, x, y, tile_size, legend):
        self.x = x
        self.y = y
        self.speed = 3  # celdas por segundo
        self.stamina = 100
        self.reputation = 70
        self.inventory = [] #Se cambia por lista de tipo objeto pedod
        self.max_weight = 5
        self.current_weight = 0
        self.state = "normal"  # normal, tired, exhausted
        self.direction = "right"
        self.tile_size = tile_size
        self.legend = legend
        self.sprite_sheet = self.load_sprites()
        self.current_frame = 0
        self.animation_time = 0
        self.animation_speed = 0.1  # segundos por frame
        
    def load_sprites(self):
        try:
            sprite_sheet_image = pygame.image.load("images.png").convert_alpha()
            img_width, img_height = sprite_sheet_image.get_size()
            
            print(f"Tamaño de la imagen: {img_width}x{img_height}")
            
            sprites = {
                "right": [],
                "left": [],
                "up": [],
                "down": [],
            }
            
            # Si la imagen es 32x32, rotarla para crear las diferentes direcciones
            if img_width == 32 and img_height == 32:
                # Crear 4 frames idénticos para cada dirección
                for i in range(4):
                    # Derecha (imagen original)
                    sprites["right"].append(sprite_sheet_image)
                    
                    # Izquierda (volteo horizontal)
                    left_img = pygame.transform.flip(sprite_sheet_image, True, False)
                    sprites["left"].append(left_img)
                    
                    # Arriba (rotación -90 grados)
                    up_img = pygame.transform.rotate(sprite_sheet_image, 90)
                    sprites["up"].append(up_img)
                    
                    # Abajo (rotación 90 grados)
                    down_img = pygame.transform.rotate(sprite_sheet_image, -90)
                    sprites["down"].append(down_img)
                
                print("Usando rotaciones de imagen para diferentes direcciones")
                return sprites
                
            else:
                # Tu código original para spritesheets más grandes
                frame_width = 32
                frame_height = 32
                
                for i in range(4):
                    rect_right = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
                    rect_left = pygame.Rect(i * frame_width, frame_height, frame_width, frame_height)
                    rect_up = pygame.Rect(i * frame_width, 2 * frame_height, frame_width, frame_height)
                    rect_down = pygame.Rect(i * frame_width, 3 * frame_height, frame_width, frame_height)
                    
                    sprites["right"].append(sprite_sheet_image.subsurface(rect_right))
                    sprites["left"].append(sprite_sheet_image.subsurface(rect_left))
                    sprites["up"].append(sprite_sheet_image.subsurface(rect_up))
                    sprites["down"].append(sprite_sheet_image.subsurface(rect_down))
                
                return sprites
                
        except pygame.error as e:
            print(f"No se pudieron cargar los sprites: {e}")
            print("Usando sprites de respaldo (colores sólidos)")
            
            # Código de respaldo
            sprites = {
                "right": [pygame.Surface((20, 20)) for _ in range(4)],
                "left": [pygame.Surface((20, 20)) for _ in range(4)],
                "up": [pygame.Surface((20, 20)) for _ in range(4)],
                "down": [pygame.Surface((20, 20)) for _ in range(4)],
            }
            
            for direction in sprites:
                for i, sprite in enumerate(sprites[direction]):
                    if direction == "right":
                        sprite.fill((255, 0, 0))
                    elif direction == "left":
                        sprite.fill((0, 255, 0))
                    elif direction == "up":
                        sprite.fill((0, 0, 255))
                    elif direction == "down":
                        sprite.fill((255, 255, 0))
                    
                    pygame.draw.circle(sprite, (0, 0, 0), (10, 10), 5, 1)
                    pygame.draw.rect(sprite, (0, 0, 0), (5, 5, 10, 2))
                    
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
  #      tile_x, tile_y = int(new_x), int(new_y)
   #     if 0 <= tile_y < len(tiles) and 0 <= tile_x < len(tiles[0]):
   #         tile_char = tiles[tile_y][tile_x]
      #      if self.legend.get(tile_char, {}).get("blocked", False):
       #         return False  # No se puede mover a través de edificios

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
        consumption = 15 * dt
        
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
        if self.current_weight + job["weight"] <= self.max_weight:
            self.inventory.append(job)
            self.current_weight += job["weight"]
            return True
        return False
    
    def remove_from_inventory(self, job_id):
        for i, job in enumerate(self.inventory):
            if job["id"] == job_id:
                self.current_weight -= job["weight"]
                self.inventory.pop(i)
                return True
        return False
    
    def draw(self, screen, camera_x=0, camera_y=0):
        # Obtener el sprite actual según la dirección y frame de animación
        sprite = self.sprite_sheet[self.direction][self.current_frame]
        
        # Calcular posición en pantalla
        screen_x = (self.x - camera_x) * self.tile_size
        screen_y = (self.y - camera_y) * self.tile_size
        
        # Dibujar el sprite
        screen.blit(sprite, (screen_x, screen_y))
        
        # Dibujar barra de stamina
        bar_width = 20
        bar_height = 3
        pygame.draw.rect(screen, (100, 100, 100), 
                        (screen_x, screen_y - 10, bar_width, bar_height))
        pygame.draw.rect(screen, (0, 255, 0), 
                        (screen_x, screen_y - 10, bar_width * (self.stamina / 100), bar_height))
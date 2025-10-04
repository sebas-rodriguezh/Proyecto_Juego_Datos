
import pygame

class PauseMenu:
    def __init__(self, screen, save_manager):
        self.screen = screen
        self.save_manager = save_manager
        self.width, self.height = screen.get_size()
        self.active = False
        self.selected_option = 0
        self.selected_slot = 0
        self.show_save_slots = False
        
        # Configurar fuentes
        try:
            self.font_large = pygame.font.Font(None, 48)
            self.font_medium = pygame.font.Font(None, 32)
            self.font_small = pygame.font.Font(None, 24)
        except:
            self.font_large = pygame.font.SysFont("Arial", 48)
            self.font_medium = pygame.font.SysFont("Arial", 32)
            self.font_small = pygame.font.SysFont("Arial", 24)
        
        # Opciones del menú de pausa
        self.options = [
            {"text": "Reanudar", "action": "resume"},
            {"text": "Guardar Partida", "action": "save_game"},
            {"text": "Salir al Menú Principal", "action": "main_menu"}
        ]
        
        # Slots de guardado
        self.save_slots = [
            {"name": "slot1", "display": "Slot 1"},
            {"name": "slot2", "display": "Slot 2"}, 
            {"name": "slot3", "display": "Slot 3"}
        ]
    
    def toggle(self):
        """Activa/desactiva el menú de pausa"""
        self.active = not self.active
        if self.active:
            self.selected_option = 0
            self.selected_slot = 0
            self.show_save_slots = False
            self.update_slot_info()
    
    def update_slot_info(self):
        """Actualiza la información de los slots de guardado"""
        saves = self.save_manager.list_saves()
        for slot in self.save_slots:
            if slot["name"] in saves:
                info = saves[slot["name"]]
                slot["info"] = f"${info.get('earnings', 0)} - {info.get('orders_completed', 0)} pedidos"
            else:
                slot["info"] = "Vacío"
    
    def handle_event(self, event):
        """Maneja eventos del menú de pausa - VERSIÓN MEJORADA"""
        if not self.active:
            return None
        
        if event.type == pygame.KEYDOWN:
            if self.show_save_slots:
                # Navegación en slots de guardado
                if event.key == pygame.K_UP:
                    self.selected_slot = (self.selected_slot - 1) % len(self.save_slots)
                elif event.key == pygame.K_DOWN:
                    self.selected_slot = (self.selected_slot + 1) % len(self.save_slots)
                elif event.key == pygame.K_RETURN:
                    slot_name = self.save_slots[self.selected_slot]["name"]
                    return {"action": "confirm_save", "slot": slot_name}
                elif event.key == pygame.K_ESCAPE:
                    self.show_save_slots = False
                    return None
            else:
                # Navegación en menú principal de pausa
                if event.key == pygame.K_UP:
                    self.selected_option = (self.selected_option - 1) % len(self.options)
                elif event.key == pygame.K_DOWN:
                    self.selected_option = (self.selected_option + 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    action = self.options[self.selected_option]["action"]
                    if action == "save_game":
                        self.show_save_slots = True
                        self.selected_slot = 0
                        self.update_slot_info()
                        return None
                    else:
                        return {"action": action}
                elif event.key == pygame.K_ESCAPE:
                    return {"action": "resume"}
        
        return None
    
    def draw(self):
        """Dibuja el menú de pausa"""
        if not self.active:
            return
        
        # Fondo semitransparente
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        if self.show_save_slots:
            self.draw_save_slots()
        else:
            self.draw_main_menu()
    
    def draw_main_menu(self):
        """Dibuja el menú principal de pausa"""
        # Título
        title = self.font_large.render("JUEGO EN PAUSA", True, (255, 215, 0))
        title_rect = title.get_rect(center=(self.width // 2, self.height // 4))
        self.screen.blit(title, title_rect)
        
        # Opciones del menú
        for i, option in enumerate(self.options):
            if i == self.selected_option:
                color = (255, 215, 0)
                text = self.font_medium.render("> " + option["text"] + " <", True, color)
            else:
                color = (200, 200, 200)
                text = self.font_medium.render(option["text"], True, color)
            
            text_rect = text.get_rect(center=(self.width // 2, self.height // 2 + i * 50))
            self.screen.blit(text, text_rect)
        
        # Instrucciones
        instructions = self.font_small.render("ESC: Reanudar  |  ENTER: Seleccionar", True, (150, 150, 150))
        instructions_rect = instructions.get_rect(center=(self.width // 2, self.height - 50))
        self.screen.blit(instructions, instructions_rect)
    
    def draw_save_slots(self):
        """Dibuja la selección de slots de guardado"""
        # Título
        title = self.font_large.render("GUARDAR PARTIDA", True, (255, 215, 0))
        title_rect = title.get_rect(center=(self.width // 2, self.height // 4))
        self.screen.blit(title, title_rect)
        
        # Instrucción
        instruction = self.font_medium.render("Selecciona un slot:", True, (200, 200, 200))
        instruction_rect = instruction.get_rect(center=(self.width // 2, self.height // 4 + 50))
        self.screen.blit(instruction, instruction_rect)
        
        # Slots de guardado
        for i, slot in enumerate(self.save_slots):
            y_pos = self.height // 2 + i * 60
            
            if i == self.selected_slot:
                # Slot seleccionado
                slot_bg = pygame.Rect(self.width // 2 - 150, y_pos - 10, 300, 50)
                pygame.draw.rect(self.screen, (50, 50, 100), slot_bg)
                pygame.draw.rect(self.screen, (255, 215, 0), slot_bg, 3)
                
                slot_text = self.font_medium.render(f"> {slot['display']} <", True, (255, 215, 0))
                info_text = self.font_small.render(slot["info"], True, (200, 200, 200))
            else:
                # Slot no seleccionado
                slot_text = self.font_medium.render(slot["display"], True, (200, 200, 200))
                info_text = self.font_small.render(slot["info"], True, (150, 150, 150))
            
            slot_rect = slot_text.get_rect(center=(self.width // 2, y_pos - 5))
            info_rect = info_text.get_rect(center=(self.width // 2, y_pos + 15))
            
            self.screen.blit(slot_text, slot_rect)
            self.screen.blit(info_text, info_rect)
        
        # Instrucciones
        instructions = self.font_small.render("ENTER: Guardar  |  ESC: Volver", True, (150, 150, 150))
        instructions_rect = instructions.get_rect(center=(self.width // 2, self.height - 50))
        self.screen.blit(instructions, instructions_rect)
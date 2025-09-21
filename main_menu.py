# main_menu.py - MEJORADO PARA MANEJAR EVENTOS
import pygame
import sys

class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        
        # Configurar fuentes
        try:
            self.font_large = pygame.font.Font(None, 48)
            self.font_medium = pygame.font.Font(None, 32)
            self.font_small = pygame.font.Font(None, 24)
        except:
            self.font_large = pygame.font.SysFont("Arial", 48)
            self.font_medium = pygame.font.SysFont("Arial", 32)
            self.font_small = pygame.font.SysFont("Arial", 24)
        
        # Opciones del menú
        self.options = [
            {"text": "Nueva Partida", "action": "new_game"},
            {"text": "Cargar Partida", "action": "load_game"},
            {"text": "Ver Puntuaciones", "action": "high_scores"},
            {"text": "Salir", "action": "quit"}
        ]
        
        self.selected_option = 0
        self.background = self.create_background()
    
    def create_background(self):
        """Crea un fondo atractivo para el menú"""
        background = pygame.Surface((self.width, self.height))
        background.fill((30, 30, 60))  # Fondo azul oscuro
        
        # Añadir patrones o gradientes al fondo
        for i in range(0, self.width, 20):
            pygame.draw.line(background, (50, 50, 100), (i, 0), (i, self.height), 1)
        for i in range(0, self.height, 20):
            pygame.draw.line(background, (50, 50, 100), (0, i), (self.width, i), 1)
        
        return background
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_option = (self.selected_option - 1) % len(self.options)
                elif event.key == pygame.K_DOWN:
                    self.selected_option = (self.selected_option + 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    return self.options[self.selected_option]["action"]
                elif event.key == pygame.K_ESCAPE:
                    return "quit"
        
        return None
    
    def draw(self):
        # Dibujar fondo
        self.screen.blit(self.background, (0, 0))
        
        # Título
        title = self.font_large.render("COURIER QUEST", True, (255, 215, 0))  # Dorado
        title_shadow = self.font_large.render("COURIER QUEST", True, (150, 100, 0))
        
        # Efecto de sombra para el título
        self.screen.blit(title_shadow, (self.width // 2 - title.get_width() // 2 + 2, 102))
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 100))
        
        # Subtítulo
        subtitle = self.font_small.render("Sistema de Entregas", True, (200, 200, 200))
        self.screen.blit(subtitle, (self.width // 2 - subtitle.get_width() // 2, 160))
        
        # Dibujar opciones del menú
        for i, option in enumerate(self.options):
            if i == self.selected_option:
                color = (255, 215, 0)  # Dorado para la opción seleccionada
                text = self.font_medium.render("> " + option["text"] + " <", True, color)
            else:
                color = (200, 200, 200)  # Gris claro para opciones no seleccionadas
                text = self.font_medium.render(option["text"], True, color)
            
            y_pos = 250 + i * 60
            self.screen.blit(text, (self.width // 2 - text.get_width() // 2, y_pos))
        
        # Instrucciones
        instructions = self.font_small.render("Usa ↑↓ para navegar, ENTER para seleccionar, ESC para salir", 
                                            True, (150, 150, 150))
        self.screen.blit(instructions, (self.width // 2 - instructions.get_width() // 2, self.height - 50))

# Este código solo se ejecuta si el archivo se ejecuta directamente
if __name__ == "__main__":
    print("⚠️  Este archivo no debe ejecutarse directamente.")
    print("💡 Ejecuta 'main.py' en su lugar.")
    pygame.quit()
    sys.exit(1)
import pygame
from api.api_manager import APIManager   # Importa la clase desde api_manager.py

class Map:
    # Colores RGB para cada tipo de celda
    COLORS = {
        "C": (200, 200, 200),  # Calles → gris claro
        "B": (50, 50, 50),     # Edificios → gris oscuro/negro
        "P": (34, 139, 34)     # Parques → verde
    }

    def __init__(self, map_data, tile_size=20):
        self.city_name = map_data["data"]["city_name"]
        self.width = map_data["data"]["width"]
        self.height = map_data["data"]["height"]
        self.tiles = map_data["data"]["tiles"]
        self.legend = map_data["data"]["legend"]
        self.tile_size = tile_size

        # Inicializar pygame y ventana
        pygame.init()
        self.screen = pygame.display.set_mode(
            (self.width * tile_size, self.height * tile_size)
        )
        pygame.display.set_caption(f"Mapa de {self.city_name}")

    def draw(self):
        """Dibuja el mapa con colores"""
        for y, row in enumerate(self.tiles):
            for x, cell in enumerate(row):
                color = self.COLORS.get(cell, (255, 0, 0))  # rojo si no está en legend
                rect = pygame.Rect(x * self.tile_size, y * self.tile_size,
                                   self.tile_size, self.tile_size)
                pygame.draw.rect(self.screen, color, rect)

                # Dibujar borde de cada celda para que se vea tipo "grid"
                pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)

    def run(self):
        """Loop principal para mostrar el mapa"""
        running = True
        clock = pygame.time.Clock()

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.draw()
            pygame.display.flip()
            clock.tick(30)

        pygame.quit()


# --- SOLO PARA PROBAR ---
if __name__ == "__main__":
    api = APIManager()   


    # Crear y ejecutar el mapa
    game_map = Map(api.get_map_data(), tile_size=20)
    game_map.run()
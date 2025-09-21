# main.py - VERSIÓN SIMPLE Y EFECTIVA
import pygame
import sys
from main_menu import MainMenu

def main():
    pygame.init()
    
    # Bucle principal que siempre vuelve al menú
    while True:
        try:
            # 1. Crear pantalla y menú
            screen = pygame.display.set_mode((800, 600))
            pygame.display.set_caption("Courier Quest")
            menu = MainMenu(screen)
            clock = pygame.time.Clock()
            
            # 2. Mostrar menú
            menu_running = True
            while menu_running:
                action = menu.handle_events()
                
                if action == "quit":
                    pygame.quit()
                    sys.exit()
                elif action == "new_game":
                    menu_running = False
                
                menu.draw()
                pygame.display.flip()
                clock.tick(60)
            
            # 3. Ejecutar juego (SIN MODIFICAR GameEngine)
            from game_engine import GameEngine
            game = GameEngine()
            game.run()
            
        except pygame.error as e:
            # Si el display se cerró, volver al menú
            if "display Surface quit" in str(e):
                continue
            else:
                print(f"Error de Pygame: {e}")
                break
        except Exception as e:
            print(f"Error: {e}")
            break
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
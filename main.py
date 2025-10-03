# main.py - VERSIÓN ACTUALIZADA CON INICIALIZACIÓN CENTRALIZADA
import pygame
import sys
from ui.main_menu import MainMenu
from utils.setup_directories import setup_directories
from utils.score_manager import initialize_score_system

def main():
    pygame.init()
    
    # ✅ INICIALIZACIÓN CENTRALIZADA ANTES DEL BUCLE
    print("🎮 Iniciando Courier Quest...")
    
    # 1. Configurar directorios
    setup_directories()
    
    # 2. Inicializar sistema de puntuación
    score_success = initialize_score_system()
    if not score_success:
        print("⚠️ Continuando sin sistema de puntuación...")
    
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
            load_slot = None
            
            while menu_running:
                action = menu.handle_events()
                
                if action == "quit":
                    pygame.quit()
                    sys.exit()
                elif action == "new_game":
                    menu_running = False
                elif action and action.startswith("load_"):
                    load_slot = action[5:]  # Extraer el nombre del slot
                    menu_running = False
                
                menu.draw()
                pygame.display.flip()
                clock.tick(60)
            
            # 3. Ejecutar juego (con opción de cargar partida)
            from game_engine import GameEngine
            game = GameEngine(load_slot=load_slot)
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
            import traceback
            traceback.print_exc()
            break
    
    pygame.quit()
    sys.exit()  

if __name__ == "__main__":
    main()
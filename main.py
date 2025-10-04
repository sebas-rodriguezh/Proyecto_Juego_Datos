import pygame
import sys
from ui.main_menu import MainMenu
from utils.setup_directories import setup_directories
from utils.score_manager import initialize_score_system

def main():
    pygame.init()
    
    setup_directories()
    
    score_success = initialize_score_system()
    if not score_success:
        print("Continuando sin sistema de puntuación...")
    
    while True:
        try:
            screen = pygame.display.set_mode((800, 600))
            pygame.display.set_caption("Courier Quest")
            menu = MainMenu(screen)
            clock = pygame.time.Clock()
            
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
                    load_slot = action[5:]  
                    menu_running = False
                
                menu.draw()
                pygame.display.flip()
                clock.tick(60)
            
            from game_engine import GameEngine
            game = GameEngine(load_slot=load_slot)
            game.run()
            
        except pygame.error as e:
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

#CONTROLES DEL JUEGO

# MOVIMIENTO
# • WASD - Moverse

# INTERACCIÓN
# • Y - Aceptar
# • N - Rechazar
# • E - Agarrar/Dejar pedido
# • Clic derecho en pedido - Cancelar

# ÓRDENES
# • P - Ordenar por Prioridad
# • O - Ordenar por Deadline

# SISTEMA
# • Esc - Pausa
# • Ctrl + S - Guardar (primer slot)
# • Ctrl + Z - Volver al estado anterior
# • Ctrl + Y - Volver al estado normal
# game_engine.py - VERSIÓN COMPLETA ACTUALIZADA
import pygame
from datetime import datetime
from Player import Player
from map import Map
from api_manager import APIManager
from weather import Weather
from game_time import GameTime
from OrderList import OrderList
from Order import Order
from ui_manager import UIManager
from interaction_manager import InteractionManager
from game_state import GameState
from undo_stack import UndoRedoManager

class GameEngine:
    """Motor principal del juego que coordina todos los sistemas"""
    
    def __init__(self):
        # Inicializar pygame
        pygame.init()
        
        # Configuración inicial
        self.api = APIManager()
        self.setup_game_data()
        
        # Crear sistemas principales
        self.game_state = GameState()
        self.setup_display()
        self.setup_game_objects()
        self.setup_managers()
        
        # Variables de control del bucle principal
        self.running = True
        self.clock = pygame.time.Clock()
        self.last_time = pygame.time.get_ticks()
        
    def setup_game_data(self):
        """Carga datos iniciales de la API"""
        try:
            self.map_data = self.api.get_map_data()
            self.jobs_data = self.api.get_jobs()
            self.weather_data = self.api.get_weather()
        except Exception as e:
            print(f"Error al conectar con la API: {e}")
            raise
    
    def setup_display(self):
        """Configura la pantalla y elementos visuales"""
        self.game_map = Map(self.map_data, tile_size=24)
        self.rows, self.cols = self.game_map.height, self.game_map.width
        self.screen_width = self.cols * self.game_map.tile_size + 300
        self.screen_height = self.rows * self.game_map.tile_size
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Courier Quest")
    
    def setup_game_objects(self):
        """Crea los objetos principales del juego"""
        # Crear listas de pedidos
        self.active_orders = OrderList.from_api_response(self.jobs_data)
        self.completed_orders = OrderList.create_empty()
        
        # Crear jugador
        self.player = Player(self.cols // 2, self.rows // 2, 
                           self.game_map.tile_size, self.game_map.legend)
        
        # Crear sistemas
        self.weather_system = Weather(self.api)
        self.game_time = GameTime(total_duration_min=15)
        self.game_time.start()
        
        # Configurar meta de ingresos
        self.income_goal = self.map_data.get("goal", 1000)
        self.game_state.set_income_goal(self.income_goal)
        
        # NUEVO: Sistema de undo/redo
        self.undo_manager = UndoRedoManager(max_states=10)
        self.undo_manager.save_game_state(self, force=True)
    
    def setup_managers(self):
        """Configura los managers del juego"""
        self.ui_manager = UIManager(self.screen, self.game_map, self.screen_width, self.screen_height)
        self.interaction_manager = InteractionManager(self.player, self.active_orders, self.completed_orders)
        
        # Variables de cámara
        self.camera_x, self.camera_y = 0, 0
    
    def handle_events(self):
        """Maneja todos los eventos del juego"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # NUEVO: Manejo de undo/redo
            if event.type == pygame.KEYDOWN:
                # Undo con Ctrl+Z
                if event.key == pygame.K_z and pygame.key.get_pressed()[pygame.K_LCTRL]:
                    if self.undo_manager.undo_last_action(self):
                        self.ui_manager.show_message("Acción deshecha", 2)
                    else:
                        self.ui_manager.show_message("No se puede deshacer", 2)
                
                # Redo con Ctrl+Y
                elif event.key == pygame.K_y and pygame.key.get_pressed()[pygame.K_LCTRL]:
                    if self.undo_manager.redo_last_action(self):
                        self.ui_manager.show_message("Acción rehecha", 2)
                    else:
                        self.ui_manager.show_message("No se puede rehacer", 2)

                if event.key == pygame.K_p:  # Tecla P para prioridad
                    self.player.reorganize_inventory_by_priority()
                    self.ui_manager.show_message("Inventario ordenado por PRIORIDAD", 2)
                    
                elif event.key == pygame.K_o:  # Tecla O para deadline
                    self.player.reorganize_inventory_by_deadline()
                    self.ui_manager.show_message("Inventario ordenado por URGENCIA", 2)                

                
                # Reiniciar juego
                elif event.key == pygame.K_r and self.game_state.game_over:
                    self.restart_game()
            
            # Delegar eventos a los managers apropiados
            self.ui_manager.handle_event(event, self.active_orders, self.player)
            
            if not self.game_state.game_over:
                self.interaction_manager.handle_event(event, self.game_state)
            
            # NUEVO: Guardar estado después de interacciones importantes
            if not self.game_state.game_over:
                self.undo_manager.save_game_state(self)
    
    def update(self, dt):
        """Actualiza todos los sistemas del juego"""
        if not self.game_state.game_over:
            # Actualizar sistemas principales
            self.game_time.update(dt)
            self.weather_system.update(dt)
            
            # Actualizar movimiento del jugador
            self.update_player_movement(dt)
            
            # Actualizar managers
            self.interaction_manager.update(dt)
            
            # Actualizar estado del juego
            self.update_game_state()
            
            # NUEVO: Guardar estado periódicamente durante movimiento
            if self.player.is_moving:
                self.undo_manager.save_game_state(self)
        
        # Actualizar cámara
        self.update_camera()
    
    def update_player_movement(self, dt):
        """Actualiza el movimiento del jugador - VERSIÓN MODIFICADA"""
        
        # Siempre actualizar el movimiento (para animaciones suaves)
        weather_multiplier = self.weather_system.get_speed_multiplier()
        weather_stamina_consumption = self.weather_system.get_stamina_consumption()
        
        self.player.update_movement(dt, weather_stamina_consumption)
        
        # Solo procesar input si no se está moviendo
        if not self.player.is_moving:
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            
            # Solo permitir movimiento en 4 direcciones (no diagonal)
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx = -1
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx = 1
            elif keys[pygame.K_UP] or keys[pygame.K_w]:
                dy = -1
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dy = 1
            
            # Intentar movimiento
            if dx != 0 or dy != 0:
                # Obtener multiplicador de superficie
                tile_x, tile_y = self.player.grid_x, self.player.grid_y
                if 0 <= tile_y < len(self.game_map.tiles) and 0 <= tile_x < len(self.game_map.tiles[0]):
                    tile_char = self.game_map.tiles[tile_y][tile_x]
                    surface_multiplier = self.game_map.legend[tile_char].get("surface_weight", 1.0)
                else:
                    surface_multiplier = 1.0
                
                self.player.try_move(dx, dy, self.game_map.tiles, weather_multiplier, surface_multiplier)
    
    def update_camera(self):
        """Actualiza la posición de la cámara - USAR POSICIÓN VISUAL"""
        visual_x, visual_y = self.player.get_visual_position()
        
        self.camera_x = visual_x * self.game_map.tile_size - self.screen_width // 2 + 150
        self.camera_y = visual_y * self.game_map.tile_size - self.screen_height // 2
        self.camera_x = max(0, min(self.camera_x, self.cols * self.game_map.tile_size - self.screen_width + 300))
        self.camera_y = max(0, min(self.camera_y, self.rows * self.game_map.tile_size - self.screen_height))
    
    def update_game_state(self):
        """Actualiza el estado general del juego"""
        # Verificar condiciones de victoria/derrota
        if self.player.reputation < 20:
            self.game_state.set_game_over(False, "Derrota: Reputación muy baja")
        elif self.game_time.is_time_up() and self.game_state.total_earnings < self.income_goal:
            self.game_state.set_game_over(False, "Derrota: Tiempo agotado")
        elif self.game_state.total_earnings >= self.income_goal:
            self.game_state.set_game_over(True, "¡Victoria! Meta alcanzada")
    
    def render(self):
        """Renderiza todos los elementos del juego"""
        self.screen.fill((255, 255, 255))
        
        # Dibujar mapa
        self.render_map()
        
        # Dibujar elementos del juego
        self.ui_manager.draw_order_markers(self.active_orders, self.player, self.camera_x, self.camera_y)
        
        # Dibujar jugador
        self.player.draw(self.screen, self.camera_x, self.camera_y)
        
        # Dibujar UI
        self.ui_manager.draw_sidebar(self.player, self.active_orders, self.weather_system, 
                                   self.game_time, self.game_state)
        
        # Dibujar mensajes y overlays
        self.ui_manager.draw_messages()
        self.ui_manager.draw_interaction_hints(self.player, self.active_orders, self.camera_x, self.camera_y)
        
        if self.game_state.game_over:
            self.ui_manager.draw_game_over_screen(self.game_state)
        
        pygame.display.flip()
    
    def render_map(self):
        """Renderiza el mapa del juego"""
        for y, row in enumerate(self.game_map.tiles):
            for x, char in enumerate(row):
                color = self.game_map.COLORS.get(char, (100, 100, 255))
                rect = pygame.Rect(x * self.game_map.tile_size - self.camera_x, 
                                 y * self.game_map.tile_size - self.camera_y, 
                                 self.game_map.tile_size, self.game_map.tile_size)
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)
    
    def restart_game(self):
        """Reinicia el juego"""
        # Reiniciar jugador
        self.player = Player(self.cols // 2, self.rows // 2, 
                           self.game_map.tile_size, self.game_map.legend)
        
        # Reiniciar listas de trabajos
        self.active_orders = OrderList.from_api_response(self.jobs_data)
        self.completed_orders = OrderList.create_empty()
        
        # Reiniciar estado del juego
        self.game_state = GameState()
        self.game_state.set_income_goal(self.income_goal)
        
        # Reiniciar sistemas
        self.game_time = GameTime(total_duration_min=15)
        self.game_time.start()
        self.weather_system = Weather(self.api)
        
        # Reiniciar managers
        self.interaction_manager = InteractionManager(self.player, self.active_orders, self.completed_orders)
        self.camera_x, self.camera_y = 0, 0
        
        # NUEVO: Reiniciar sistema de undo
        self.undo_manager = UndoRedoManager(max_states=10)
        self.undo_manager.save_game_state(self, force=True)
    
    def run(self):
        """Bucle principal del juego"""
        while self.running:
            current_time = pygame.time.get_ticks()
            dt = (current_time - self.last_time) / 1000.0
            self.last_time = current_time
            
            self.handle_events()
            self.update(dt)
            self.render()
            
            self.clock.tick(60)
        
        pygame.quit()

# Punto de entrada
if __name__ == "__main__":
    game = GameEngine()
    game.run()
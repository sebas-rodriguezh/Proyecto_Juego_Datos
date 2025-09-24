# game_engine.py - VERSIÓN COMPLETA ACTUALIZADA CON SISTEMA DE GUARDADO/CARGA
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
from setup_directories import setup_directories
import json
import os
from save_load_manager import SaveLoadManager
from datetime import timedelta
from OrderPopupManager import OrderPopupManager
from score_manager import score_manager
    
class GameEngine:
    """Motor principal del juego que coordina todos los sistemas"""
    
    def __init__(self, load_slot=None):
        # Inicializar pygame
        pygame.init()
        try:
            pygame.font.init()
            test_font = pygame.font.Font(None, 16)
        except:
            print("❌ Error inicializando fuentes de Pygame")
        # ✅ PRIMERO inicializar el sistema de puntuación
        from setup_directories import setup_directories
        setup_directories()  # Esto creará la carpeta 'saves'
        
        # ✅ INICIALIZAR score_manager ANTES de usarlo
        from score_manager import score_manager
        score_manager.initialize_score_system()
        
        # Configuración inicial
        self.api = APIManager()
        self.setup_game_data()
        
        # Crear sistemas principales
        self.game_state = GameState()
        self.setup_display()

        self.popup_manager = OrderPopupManager(self.screen_width, self.screen_height)

        # Sistema de guardado/carga
        self.save_manager = SaveLoadManager()
        
        # PRIMERO cargar o crear partida (para que el player exista)
        if load_slot:
            self.load_game(load_slot)
        else:
            self.setup_game_objects()
        
        # LUEGO configurar managers (después de que el player exista)
        self.setup_managers()
        
        # Variables de control del bucle principal
        self.running = True
        self.clock = pygame.time.Clock()
        self.last_time = pygame.time.get_ticks()
    def setup_game_data(self):
        """Carga datos iniciales de la API o caché local"""
        try:
            self.map_data = self.api.get_map_data()
            self.jobs_data = self.api.get_jobs()
            self.weather_data = self.api.get_weather()
            print("✅ Datos cargados desde API")
        except Exception as e:
            print(f"❌ Error al conectar con la API: {e}")
            print("🔄 Intentando cargar datos por defecto...")
            self.load_default_data()

    def load_default_data(self):
        """Carga datos por defecto desde archivos locales"""
        try:
            import json
            import os
            
            # Cargar mapa por defecto
            with open('data/map_data.json', 'r', encoding='utf-8') as f:
                self.map_data = json.load(f)
            
            # Cargar trabajos por defecto
            with open('data/jobs_data.json', 'r', encoding='utf-8') as f:
                self.jobs_data = json.load(f)
            
            # Cargar clima por defecto
            with open('data/weather_data.json', 'r', encoding='utf-8') as f:
                self.weather_data = json.load(f)
                
            print("✅ Datos por defecto cargados correctamente")
            
        except Exception as e:
            print(f"❌ Error crítico: No se pudieron cargar los datos por defecto: {e}")
            raise
    
    def setup_display(self):
        """Configura la pantalla y elementos visuales"""
        self.game_map = Map(self.map_data, tile_size=20)
        self.rows, self.cols = self.game_map.height, self.game_map.width
        self.screen_width = self.cols * self.game_map.tile_size + 300
        self.screen_height = self.rows * self.game_map.tile_size
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Courier Quest")
    
    def setup_game_objects(self, loaded_data=None):
        """Crea los objetos principales del juego"""
        if loaded_data:
            # Cargar desde datos guardados
            self.load_from_save_data(loaded_data)
        else:
            # Configuración inicial nueva partida
            self.setup_new_game()
    
    def setup_new_game(self):
        """Configura una nueva partida desde cero"""
        # Crear listas de pedidos con sistema de release time
        self.all_orders = OrderList.from_api_response(self.jobs_data)  # Todos los pedidos
        self.active_orders = OrderList.create_empty()  # Pedidos activos (liberados)
        self.pending_orders = OrderList.create_empty()  # Pedidos pendientes de liberar
        self.completed_orders = OrderList.create_empty()
        
        # Separar pedidos por release_time
        for order in self.all_orders:
            if order.release_time == 0:
                self.active_orders.enqueue(order)  # Liberar inmediatamente
            else:
                self.pending_orders.enqueue(order)  # Pendientes por tiempo
        
        # Crear jugador
        self.player = Player(self.cols // 2, self.rows // 2, 
                        self.game_map.tile_size, self.game_map.legend)
        
        # Crear sistemas
        self.weather_system = Weather(self.api)
        self.game_time = GameTime(total_duration_min=15)
        self.game_time.start()
        
        # Configurar meta de ingresos
        self.income_goal = self.map_data.get("goal", 100)
        self.game_state.set_income_goal(self.income_goal)
        
        # Sistema de undo/redo
        self.undo_manager = UndoRedoManager(max_states=10)
        self.undo_manager.save_game_state(self, force=True)
        
# Añadir este método en game_engine.py
    def _create_order_from_save_data(self, order_data):
        """Crea una orden desde datos de guardado"""
        from datetime import datetime
        
        # Manejar diferentes formatos de deadline
        deadline = order_data["deadline"]
        if isinstance(deadline, str):
            deadline = datetime.fromisoformat(deadline)
        
        # Crear orden
        order = Order(
            id=order_data["id"],
            pickup=order_data["pickup"],
            dropoff=order_data["dropoff"],
            payout=order_data["payout"],
            deadline=deadline,
            weight=order_data["weight"],
            priority=order_data["priority"],
            release_time=order_data["release_time"]
        )
        
        # Restaurar color si existe
        if "color" in order_data:
            order.color = tuple(order_data["color"])
        
        return order
    def load_from_save_data(self, save_data):
        """Carga el estado del juego desde datos guardados - VERSIÓN MEJORADA"""
        try:
            print(f"🔄 Cargando partida desde datos guardados...")
            
            # ✅ INICIALIZAR TODAS LAS LISTAS DE ÓRDENES
            self.active_orders = OrderList.create_empty()
            self.completed_orders = OrderList.create_empty()
            self.pending_orders = OrderList.create_empty()
            
            # Cargar estado del jugador
            player_data = save_data["player_data"]
            self.player = Player(
                player_data["grid_x"],
                player_data["grid_y"], 
                self.game_map.tile_size, 
                self.game_map.legend
            )
            
            # Restaurar propiedades del jugador
            self.player.stamina = player_data["stamina"]
            self.player.reputation = player_data["reputation"]
            self.player.current_weight = player_data["current_weight"]
            self.player.state = player_data["state"]
            self.player.direction = player_data["direction"]
            self.player.visual_x = player_data.get("visual_x", player_data["grid_x"])
            self.player.visual_y = player_data.get("visual_y", player_data["grid_y"])
            
            # Limpiar inventarios existentes
            self.player.inventory.clear()
            self.player.completed_orders.clear()
            
            # Cargar inventario
            for order_data in player_data["inventory"]:
                try:
                    order = self._create_order_from_save_data(order_data)
                    self.player.add_to_inventory(order)
                except Exception as e:
                    print(f"⚠️ Error cargando orden al inventario: {e}")
            
            # Cargar órdenes completadas del jugador
            for order_data in player_data["completed_orders"]:
                try:
                    order = self._create_order_from_save_data(order_data)
                    self.player.completed_orders.enqueue(order)
                except Exception as e:
                    print(f"⚠️ Error cargando orden completada: {e}")
            
            # Cargar listas de órdenes
            for order_data in save_data["active_orders"]:
                try:
                    order = self._create_order_from_save_data(order_data)
                    self.active_orders.enqueue(order)
                except Exception as e:
                    print(f"⚠️ Error cargando orden activa: {e}")
            
            for order_data in save_data["completed_orders"]:
                try:
                    order = self._create_order_from_save_data(order_data)
                    self.completed_orders.enqueue(order)
                except Exception as e:
                    print(f"⚠️ Error cargando orden completada global: {e}")
            
            # ✅ CARGAR ÓRDENES PENDIENTES
            if "pending_orders" in save_data:
                for order_data in save_data["pending_orders"]:
                    try:
                        order = self._create_order_from_save_data(order_data)
                        self.pending_orders.enqueue(order)
                    except Exception as e:
                        print(f"⚠️ Error cargando orden pendiente: {e}")
            
            # Cargar estado del juego
            game_state_data = save_data["game_state"]
            self.game_state.total_earnings = game_state_data["total_earnings"]
            self.game_state.income_goal = game_state_data["income_goal"]
            self.game_state.game_over = game_state_data["game_over"]
            self.game_state.victory = game_state_data["victory"]
            self.game_state.game_over_reason = game_state_data["game_over_reason"]
            self.game_state.orders_completed = game_state_data["orders_completed"]
            self.game_state.orders_cancelled = game_state_data["orders_cancelled"]
            self.game_state.perfect_deliveries = game_state_data["perfect_deliveries"]
            self.game_state.late_deliveries = game_state_data["late_deliveries"]
            self.game_state.current_streak = game_state_data["current_streak"]
            self.game_state.best_streak = game_state_data["best_streak"]
            
            # Convertir string de start_time a datetime
            start_time_str = game_state_data["start_time"]
            if isinstance(start_time_str, str):
                self.game_state.start_time = datetime.fromisoformat(start_time_str)
            
            # Cargar tiempo de juego - CORRECCIÓN IMPORTANTE
            game_time_data = save_data["game_time"]
            elapsed_time = game_time_data.get("elapsed_time_sec", 0)
            total_duration = game_time_data.get("total_duration", 900)
            
            # Reiniciar game_time con la duración correcta
            self.game_time = GameTime(total_duration_min=total_duration/60)
            self.game_time.start()
            
            # Ajustar tiempo transcurrido manualmente
            current_time_seconds = pygame.time.get_ticks() / 1000.0
            adjusted_start_time = current_time_seconds - elapsed_time
            self.game_time.start_time = adjusted_start_time
            
            # Cargar clima
            weather_data = save_data["weather_state"]
            self.weather_system = Weather(self.api)
            
            # Configurar clima actual
            try:
                from weather import WeatherCondition
                condition_str = weather_data["current_condition"]
                # Buscar la condición climática correspondiente
                for condition in WeatherCondition:
                    if condition.value == condition_str:
                        self.weather_system.current_condition = condition
                        break
                
                self.weather_system.current_intensity = weather_data.get("current_intensity", 0.0)
                self.weather_system.current_multiplier = weather_data.get("current_multiplier", 1.0)
            except Exception as e:
                print(f"⚠️ Error configurando clima: {e}")
            
            # Cargar cámara y meta
            self.camera_x, self.camera_y = save_data["camera_position"]
            self.income_goal = save_data["income_goal"]
            
            # Reiniciar sistema de undo
            self.undo_manager = UndoRedoManager(max_states=10)
            self.undo_manager.save_game_state(self, force=True)
            
            print("✅ Partida cargada correctamente")
            
        except Exception as e:
            print(f"❌ Error al cargar partida: {e}")
            import traceback
            traceback.print_exc()
            print("🔄 Iniciando nueva partida...")
            self.setup_new_game()

    def _create_order_from_save_data(self, order_data):
        """Crea una orden desde datos de guardado"""
        from datetime import datetime
        
        # Manejar diferentes formatos de deadline
        deadline = order_data["deadline"]
        if isinstance(deadline, str):
            deadline = datetime.fromisoformat(deadline)
        
        # Crear orden
        order = Order(
            id=order_data["id"],
            pickup=order_data["pickup"],
            dropoff=order_data["dropoff"],
            payout=order_data["payout"],
            deadline=deadline,
            weight=order_data["weight"],
            priority=order_data["priority"],
            release_time=order_data["release_time"]
        )
        
        # Restaurar color si existe
        if "color" in order_data:
            order.color = tuple(order_data["color"])
        
        return order
    def save_game(self, slot_name="slot1"):
        """Guarda el estado actual del juego"""
        success = self.save_manager.save_game(self, slot_name)
        if success:
            print(f"✅ Partida guardada en slot: {slot_name}")
            return True
        else:
            print("❌ Error al guardar partida")
            return False
    def load_game(self, slot_name="slot1"):
        """Carga una partida guardada"""
        save_data = self.save_manager.load_game(slot_name)
        if save_data:
            self.setup_game_objects(save_data)
            return True
        else:
            print(f"❌ No se encontró partida en slot: {slot_name}")
            print("🔄 Iniciando nueva partida...")
            self.setup_game_objects()
            return False
    
    def update_release_times(self, dt):
        """Libera pedidos según su release_time"""
        current_time = self.game_time.get_elapsed_time()
        
        # Crear lista temporal de pedidos pendientes
        orders_to_release = []
        remaining_orders = OrderList.create_empty()
        
        # Revisar todos los pedidos pendientes
        while not self.pending_orders.is_empty():
            order = self.pending_orders.dequeue()
            
            if current_time >= order.release_time:
                orders_to_release.append(order)
                # Mostrar mensaje de nuevo pedido
                self.ui_manager.show_message(f"📦 Nuevo pedido: {order.id}", 3)
            else:
                remaining_orders.enqueue(order)
        
        # Devolver pedidos que aún no se liberan
        self.pending_orders = remaining_orders
        
        # Liberar pedidos que cumplieron su tiempo
        # for order in orders_to_release:
        #     self.active_orders.enqueue(order) 

        for order in orders_to_release:
            if not self.popup_manager.is_popup_active():  # Solo si no hay popup activo
                self.popup_manager.show_new_order_popup(order)
                break  # Solo mostrar uno a la vez
            else:
                # Si hay popup activo, volver a poner en pendientes con delay
                order.release_time = current_time + 5  # Intentar de nuevo en 5 segundos
                self.pending_orders.enqueue(order)
          
    
    def setup_managers(self):
        """Configura los managers del juego"""
        self.ui_manager = UIManager(self.screen, self.game_map, self.screen_width, self.screen_height)
        self.interaction_manager = InteractionManager(self.player, self.active_orders, self.completed_orders)
        
        # NUEVO: Dar acceso al interaction_manager desde ui_manager
        self.ui_manager.interaction_manager = self.interaction_manager
        
        # Variables de cámara
        self.camera_x, self.camera_y = 0, 0
    
    # game_engine.py - CORRECCIÓN para pasar game_map al interaction manager
    def handle_events(self):
        """Maneja todos los eventos del juego"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            popup_result = self.popup_manager.handle_event(event, self.game_state, self.player, self.active_orders)

            if popup_result:
                message = popup_result.get("message", "")
                if message:
                    self.ui_manager.show_message(message, 3)

                penalty = popup_result.get("penalty")
                if penalty:
                    self.player.reputation = max(0, self.player.reputation - penalty)
                    # Actualizar estadísticas si es cancelación
                    if popup_result.get("type") == "cancel_order" and popup_result.get("result") == "confirmed":
                        self.game_state.orders_cancelled += 1            

            # AÑADIR: Manejar cancelación desde inventario (click derecho)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # Click derecho
                mouse_x, mouse_y = pygame.mouse.get_pos()
                self.handle_inventory_right_click(mouse_x, mouse_y)            

            # Manejo de undo/redo
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
                
                # Guardar partida con Ctrl+S
                elif event.key == pygame.K_s and pygame.key.get_pressed()[pygame.K_LCTRL]:
                    if self.save_game("slot1"):
                        self.ui_manager.show_message("Partida guardada", 2)
                    else:
                        self.ui_manager.show_message("Error al guardar", 2)
                
                # Cargar partida con Ctrl+L
                elif event.key == pygame.K_l and pygame.key.get_pressed()[pygame.K_LCTRL]:
                    if self.load_game("slot1"):
                        self.ui_manager.show_message("Partida cargada", 2)
                    else:
                        self.ui_manager.show_message("Error al cargar", 2)
                
                if event.key == pygame.K_p:  # Tecla P para prioridad
                    self.player.reorganize_inventory_by_priority()
                    self.ui_manager.show_message("Inventario ordenado por PRIORIDAD", 2)
                    
                elif event.key == pygame.K_o:  # Tecla O para deadline
                    self.player.reorganize_inventory_by_deadline()
                    self.ui_manager.show_message("Inventario ordenado por URGENCIA", 2)                
            
            # Delegar eventos a los managers apropiados
            self.ui_manager.handle_event(event, self.active_orders, self.player)
            
            if not self.game_state.game_over:
                # CORRECCIÓN: Pasar game_map al interaction_manager
                self.interaction_manager.handle_event(event, self.game_state, self.game_map)  # ← AQUÍ
            
            # Guardar estado después de interacciones importantes
            if not self.game_state.game_over:
                self.undo_manager.save_game_state(self)

    def handle_inventory_right_click(self, mouse_x, mouse_y):
        """Maneja cancelación de pedidos desde el inventario con click derecho"""
        # Verificar si el click está en el área del inventario
        cols = self.game_map.width
        x_offset = cols * self.game_map.tile_size
        
        if mouse_x > x_offset:  # Está en el sidebar
            # Calcular qué pedido del inventario fue clickeado
            inventory_start_y = 235
            item_height = 45
            
            if mouse_y >= inventory_start_y and self.player.inventory:
                item_index = (mouse_y - inventory_start_y) // item_height
                
                if 0 <= item_index < len(self.player.inventory):
                    order = self.player.inventory[item_index]
                    self.popup_manager.show_cancel_order_popup(order)


    def update(self, dt):
        """Actualiza todos los sistemas del juego"""
        if not self.game_state.game_over:
            # Actualizar sistemas principales
            self.game_time.update(dt)
            self.weather_system.update(dt)
            self.update_release_times(dt)

            
            # Actualizar movimiento del jugador
            self.update_player_movement(dt)
            
            # Actualizar managers
            self.interaction_manager.update(dt)
            
            # Actualizar estado del juego
            self.update_game_state()
            self.popup_manager.update(dt)
            
            # Guardar estado periódicamente durante movimiento
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
        if self.player.reputation < 20 and not self.game_state.game_over:
            print("🎮 Fin del juego: Reputación muy baja")
            self.game_state.set_game_over(False, "Derrota: Reputación muy baja")
            self.save_final_score(False)
        elif self.game_time.is_time_up() and self.game_state.total_earnings < self.income_goal and not self.game_state.game_over:
            print("🎮 Fin del juego: Tiempo agotado")
            self.game_state.set_game_over(False, "Derrota: Tiempo agotado")
            self.save_final_score(False)
        elif self.game_state.total_earnings >= self.income_goal and not self.game_state.game_over:
            print("🎮 Fin del juego: Victoria alcanzada")
            self.game_state.set_game_over(True, "¡Victoria! Meta alcanzada")
            self.save_final_score(True)

    def save_final_score(self, victory: bool):
        """Guarda la puntuación final - VERSIÓN MEJORADA"""
        try:
            print(f"💾 Intentando guardar puntuación final: victoria={victory}")
            
            # Verificar que el juego haya terminado
            if not self.game_state.game_over:
                print("⚠️ El juego no ha terminado, no se puede guardar puntuación")
                return
                
            from score_manager import score_manager
            
            # Asegurar inicialización
            if not score_manager.initialized:
                print("🔄 Inicializando sistema de puntuación...")
                score_manager.initialize_score_system()
            
            game_duration = self.game_time.get_elapsed_time()
            print(f"⏱️ Duración del juego: {game_duration:.1f} segundos")
            
            # Guardar puntuación
            success = score_manager.add_score(self.game_state, victory, game_duration)
            
            if success:
                print("✅ Puntuación guardada exitosamente en el sistema")
            else:
                print("❌ Error al guardar puntuación en el sistema principal")
                
        except Exception as e:
            print(f"❌ Error guardando puntuación final: {e}")
            import traceback
            traceback.print_exc()
    def render(self):
        """Renderiza todos los elementos del juego"""
        self.screen.fill((255, 255, 255))
        
        # Dibujar mapa
        self.render_map()
        
        # Dibujar elementos del juego
        self.ui_manager.draw_order_markers(self.active_orders, self.player, self.camera_x, self.camera_y)
        
        # Dibujar jugador
        self.player.draw(self.screen, self.camera_x, self.camera_y)
        
        # Dibujar UI - Pasar el conteo de pedidos pendientes
        pending_count = len(self.pending_orders)
        self.ui_manager.draw_sidebar(self.player, self.active_orders, self.weather_system, 
                                self.game_time, self.game_state, pending_count)
        
        # Dibujar mensajes y overlays
        self.ui_manager.draw_messages()
        
        # CORRECCIÓN: Pasar game_map a draw_interaction_hints
        self.ui_manager.draw_interaction_hints(self.player, self.active_orders, self.camera_x, self.camera_y, self.game_map)
        
        if self.game_state.game_over:
            self.ui_manager.draw_game_over_screen(self.game_state)

        self.popup_manager.draw_new_order_popup(self.screen)
        self.popup_manager.draw_cancel_order_popup(self.screen) 
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
        
        # Reiniciar listas de trabajos con release time
        self.all_orders = OrderList.from_api_response(self.jobs_data)
        self.active_orders = OrderList.create_empty()
        self.pending_orders = OrderList.create_empty()
        self.completed_orders = OrderList.create_empty()
        
        # Separar pedidos por release_time
        for order in self.all_orders:
            if order.release_time == 0:
                self.active_orders.enqueue(order)
            else:
                self.pending_orders.enqueue(order)
        
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
        
        # Reiniciar sistema de undo
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
    # Verificar y crear directorios necesarios
    setup_directories()
    
    # Crear instancia del API manager
    api = APIManager()
    
    # Verificar estado de conexión
    if api.is_online():
        print("🌐 Conectado a internet - Usando datos en tiempo real")
    else:
        print("📴 Modo offline - Usando datos cacheados o por defecto")
    
    # Iniciar juego
    game = GameEngine()
    game.run()
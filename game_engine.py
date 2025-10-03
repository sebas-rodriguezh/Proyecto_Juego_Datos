# game_engine.py - VERSIÓN COMPLETA ACTUALIZADA CON SISTEMA DE GUARDADO/CARGA
import pygame
from datetime import datetime
from entities.player import Player
from ui.map import Map
from api.api_manager import APIManager
from entities.weather import Weather
from core.game_time import GameTime
from entities.order_list import OrderList
from entities.order import Order
from ui.ui_manager import UIManager
from utils.interaction_manager import InteractionManager
from core.game_state import GameState
from utils.undo_stack import UndoRedoManager
from utils.setup_directories import setup_directories
import json
import os
from utils.save_load_manager import SaveLoadManager
from datetime import timedelta
from ui.order_popup_manager import OrderPopupManager
from utils.score_manager import score_manager
    
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
        from utils.setup_directories import setup_directories
        setup_directories()  # Esto creará la carpeta 'saves'
        
        # ✅ INICIALIZAR score_manager ANTES de usarlo
        from utils.score_manager import score_manager
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
        from ui.pause_menu import PauseMenu
        self.pause_menu = PauseMenu(self.screen, self.save_manager)
        
        # Variables de control del bucle principal
        self.running = True
        self.clock = pygame.time.Clock()
        self.last_time = pygame.time.get_ticks()
    def setup_game_data(self):
        """Carga datos iniciales de la API o caché local - VERSIÓN SIMPLIFICADA"""
        try:
            self.map_data = self.api.get_map_data()
            self.jobs_data = self.api.get_jobs()
            self.weather_data = self.api.get_weather()
            print("✅ Datos cargados correctamente")
        except Exception as e:
            print(f"❌ Error crítico: No se pudieron cargar los datos: {e}")
            # NO hay datos por defecto - el juego no puede continuar
            raise Exception("No se pueden cargar datos y no hay respaldo disponible")

# ELIMINA completamente la función load_default_data()
# ELIMINA completamente la función create_default_data_files()
# ELIMINA completamente la función create_emergency_data()

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
            # ✅ VERIFICAR CONSISTENCIA después de cargar
            self.verify_order_consistency()
        else:
            # Configuración inicial nueva partida
            self.setup_new_game()
    
    def setup_new_game(self):
        """Configura una nueva partida desde cero"""
        # Crear listas de pedidos con sistema de release time
        game_start_datetime = self.get_game_start_time_from_json()

        self.all_orders = OrderList.from_api_response(self.jobs_data)  # Todos los pedidos
        self.active_orders = OrderList.create_empty()  # Pedidos activos (liberados)
        self.pending_orders = OrderList.create_empty()  # Pedidos pendientes de liberar
        self.completed_orders = OrderList.create_empty()
        self.rejected_orders = OrderList.create_empty()  # NUEVO: Pedidos rechazados

        # DEBUG: Verificar release_time de los pedidos
        print("🔍 DEBUG RELEASE_TIMES:")
        for i, order in enumerate(self.all_orders):
            print(f"   Pedido {i+1}: {order.id} - release_time: {order.release_time}s")
            if order.release_time == 0:
                self.active_orders.enqueue(order)  # Liberar inmediatamente
            else:
                self.pending_orders.enqueue(order)  # Pendientes por tiempo
        
        # Crear jugador
        self.player = Player(self.cols // 2, self.rows // 2, 
                        self.game_map.tile_size, self.game_map.legend)

        # Crear tiempo de juego - SOLO UNA VEZ
        self.game_time = GameTime(
            total_duration_min=15,
            game_start_time=game_start_datetime,  # Hora del JSON
            time_scale=7.0  # ← ESCALA TEMPORAL (1s real = 3s juego)
        )
        self.game_time.start()

        # Crear sistemas (ELIMINAR la segunda creación de GameTime)
        self.weather_system = Weather(self.api)
        
        # Configurar meta de ingresos
        self.income_goal = self.map_data.get("goal", 1000)
        self.game_state.set_income_goal(self.income_goal)
        self.game_state.set_player_reference(self.player)

        # Sistema de undo/redo
        self.undo_manager = UndoRedoManager(max_states=10)
        self.undo_manager.save_game_state(self, force=True)
        
        print("\n" + "="*50)
        self.verify_order_deadlines()
        print("="*50 + "\n")
        
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
    
    def update_order_expirations(self):
        """Actualiza el estado de expiración de todos los pedidos activos - CORREGIDO"""
        current_game_time = self.game_time.get_current_game_time()
        
        expired_orders = []
        
        # 1. Pedidos activos (aceptados pero no recogidos)
        for order in list(self.active_orders):  # Usar list() para evitar modificar durante iteración
            if not order.is_in_inventory and not order.is_completed:
                if order.check_expiration(current_game_time):
                    expired_orders.append(order)
                    print(f"⚠️ Pedido {order.id} EXPIRADO (no recogido) a las {current_game_time.strftime('%H:%M:%S')}")
        
        # 2. Pedidos en inventario (recogidos pero no entregados)
        for order in list(self.player.inventory):  # Usar list() para evitar modificar durante iteración
            if order.is_in_inventory and not order.is_completed:
                if order.check_expiration(current_game_time):
                    expired_orders.append(order)
                    print(f"⚠️ Pedido {order.id} EXPIRADO (no entregado) a las {current_game_time.strftime('%H:%M:%S')}")
        
        # Procesar pedidos expirados
        for expired_order in expired_orders:
            self.handle_expired_order(expired_order, current_game_time)

    def handle_expired_order(self, order, current_time):
        """Maneja las consecuencias de un pedido expirado"""
        # Penalización por perder/expirar paquete: -6 reputación
        reputation_penalty = 6
        old_reputation = self.player.reputation
        self.player.reputation = max(0, self.player.reputation - reputation_penalty)
        
        # Actualizar estadísticas
        self.game_state.orders_cancelled += 1
        self.game_state.current_streak = 0  # Resetear racha
        
        # Remover de donde esté
        if order.is_in_inventory:
            # Remover del inventario del jugador
            self.player.remove_from_inventory(order.id)
            location = "inventario"
        else:
            # Remover de pedidos activos
            self.active_orders.remove_by_id(order.id)
            location = "activos"
        
        # Mostrar mensaje al jugador
        message = f"❌ {order.id} EXPIRADO (-{reputation_penalty} reputación)"
        self.ui_manager.show_message(message, 5)
        
        print(f"📉 Pedido {order.id} expirado ({location}). Reputación: {old_reputation} → {self.player.reputation}")
        print(f"⏰ Deadline: {order.deadline.strftime('%H:%M:%S')}, Hora actual: {current_time.strftime('%H:%M:%S')}")

    def verify_order_deadlines(self):
        """Verifica que todos los deadlines sean correctos"""
        print(f"\n=== VERIFICACIÓN DE DEADLINES ===")
        print(f"🕐 Hora inicio juego: {self.game_time.game_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        all_orders = list(self.all_orders) if hasattr(self, 'all_orders') else []
        
        print(f"\n📦 TODOS LOS PEDIDOS ({len(all_orders)}):")
        for order in all_orders:
            time_remaining = order.get_time_remaining(self.game_time.get_current_game_time())
            minutes = time_remaining / 60
            print(f"   {order.id}: {time_remaining:.0f}s ({minutes:.1f} min) - {order.deadline.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Verificar consistencia
        expected_date = self.game_time.game_start_time.date()
        inconsistent_orders = []
        
        for order in all_orders:
            if order.deadline.date() != expected_date:
                inconsistent_orders.append(order)
        
        if inconsistent_orders:
            print(f"\n⚠️  PEDIDOS CON FECHA INCONSISTENTE:")
            for order in inconsistent_orders:
                print(f"   {order.id}: {order.deadline.strftime('%Y-%m-%d')} (esperado: {expected_date})")
        else:
            print(f"\n✅ Todos los pedidos tienen la fecha correcta: {expected_date}")

    def get_game_start_time_from_json(self):
        """Extrae la hora de inicio desde map_data - VERSIÓN CORREGIDA CON DEBUG"""
        try:
            # ✅ PRIORIDAD 1: Usar start_time del mapa si existe
            if "start_time" in self.map_data.get("data", {}):
                start_time_str = self.map_data["data"]["start_time"]
                
                print(f"🕐 START_TIME RAW: {start_time_str}")  # DEBUG
                
                # Remover Z y convertir a datetime
                if start_time_str.endswith('Z'):
                    start_time_str = start_time_str[:-1]
                
                # Asegurar formato completo
                if len(start_time_str) == 16:  # Formato YYYY-MM-DDTHH:MM
                    start_time_str += ":00"
                
                start_time = datetime.fromisoformat(start_time_str)
                print(f"✅ START_TIME PARSED: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                return start_time
            
            # FALLBACK: Buscar en el primer pedido
            if self.jobs_data and len(self.jobs_data.get('data', [])) > 0:
                first_job = self.jobs_data['data'][0]
                if "deadline" in first_job:
                    deadline_str = first_job["deadline"]
                    print(f"🕐 USING FIRST JOB DEADLINE: {deadline_str}")
                    
                    # Convertir deadline y restar tiempo estimado
                    if deadline_str.endswith('Z'):
                        deadline_str = deadline_str[:-1]
                    
                    if len(deadline_str) == 16:
                        deadline_str += ":00"
                    
                    deadline = datetime.fromisoformat(deadline_str)
                    # Asumir que el juego empieza 10 minutos antes del primer deadline
                    start_time = deadline - timedelta(minutes=10)
                    print(f"✅ CALCULATED START_TIME: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    return start_time
                        
        except Exception as e:
            print(f"❌ ERROR leyendo hora del JSON: {e}")
            import traceback
            traceback.print_exc()
        
        # Último fallback
        default_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        print(f"⚠️ USING DEFAULT START_TIME: {default_time.strftime('%Y-%m-%d %H:%M:%S')}")
        return default_time
    def load_from_save_data(self, save_data):
        """Carga el estado del juego desde datos guardados - VERSIÓN COMPLETA MEJORADA"""
        try:
            print(f"📄 Cargando partida desde datos guardados...")
            
            # ✅ INICIALIZAR TODAS LAS LISTAS DE ÓRDENES PRIMERO
            self.active_orders = OrderList.create_empty()
            self.completed_orders = OrderList.create_empty()
            self.pending_orders = OrderList.create_empty()
            self.rejected_orders = OrderList.create_empty()
            
            # ✅ PRIMERO: Cargar todos los pedidos base
            if "all_orders" in save_data:
                self.all_orders = OrderList.create_empty()
                for order_data in save_data["all_orders"]:
                    try:
                        order = self._create_order_from_save_data(order_data)
                        self.all_orders.enqueue(order)
                    except Exception as e:
                        print(f"⚠️ Error cargando orden base: {e}")
                print(f"✅ {len(self.all_orders)} pedidos base cargados")
            else:
                # Fallback: recrear desde jobs_data
                self.all_orders = OrderList.from_api_response(self.jobs_data)
                print(f"⚠️ No hay all_orders en guardado, recreando desde API: {len(self.all_orders)} pedidos")
            
            # ✅ LUEGO: Cargar listas específicas de órdenes
            print("🔄 Cargando listas de órdenes específicas...")
            
            # Cargar órdenes activas
            for order_data in save_data["active_orders"]:
                try:
                    order = self._find_or_create_order(order_data, self.all_orders)
                    if order:
                        self.active_orders.enqueue(order)
                except Exception as e:
                    print(f"⚠️ Error cargando orden activa: {e}")
            
            # Cargar órdenes pendientes
            if "pending_orders" in save_data:
                for order_data in save_data["pending_orders"]:
                    try:
                        order = self._find_or_create_order(order_data, self.all_orders)
                        if order:
                            self.pending_orders.enqueue(order)
                    except Exception as e:
                        print(f"⚠️ Error cargando orden pendiente: {e}")
            
            # Cargar órdenes completadas
            for order_data in save_data["completed_orders"]:
                try:
                    order = self._find_or_create_order(order_data, self.all_orders)
                    if order:
                        order.mark_as_completed()  # ✅ Marcar como completada
                        self.completed_orders.enqueue(order)
                except Exception as e:
                    print(f"⚠️ Error cargando orden completada: {e}")
            
            # Cargar órdenes rechazadas
            if "rejected_orders" in save_data:
                for order_data in save_data["rejected_orders"]:
                    try:
                        order = self._find_or_create_order(order_data, self.all_orders)
                        if order:
                            self.rejected_orders.enqueue(order)
                    except Exception as e:
                        print(f"⚠️ Error cargando orden rechazada: {e}")
            
            print(f"📊 Resumen de órdenes cargadas:")
            print(f"   - Activas: {len(self.active_orders)}")
            print(f"   - Pendientes: {len(self.pending_orders)}")
            print(f"   - Completadas: {len(self.completed_orders)}")
            print(f"   - Rechazadas: {len(self.rejected_orders)}")
            print(f"   - Base (all_orders): {len(self.all_orders)}")
            
            # ✅ CARGAR ESTADO DEL JUGADOR
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
            
            # Limpiar inventarios existentes
            self.player.inventory.clear()
            self.player.completed_orders.clear()
            
            # ✅ CARGAR INVENTARIO DEL JUGADOR - MEJORADO
            print("🎒 Cargando inventario del jugador...")
            for order_data in player_data["inventory"]:
                try:
                    order = self._find_or_create_order(order_data, self.all_orders)
                    if order:
                        # Restaurar estado de la orden en inventario
                        order.is_in_inventory = True
                        order.is_expired = order_data.get("is_expired", False)
                        
                        # Añadir al inventario del jugador
                        self.player.inventory.enqueue(order)
                        print(f"   ✅ {order.id} añadido al inventario")
                except Exception as e:
                    print(f"⚠️ Error cargando orden al inventario: {e}")
            
            # ✅ CARGAR ÓRDENES COMPLETADAS DEL JUGADOR
            for order_data in player_data["completed_orders"]:
                try:
                    order = self._find_or_create_order(order_data, self.all_orders)
                    if order:
                        order.mark_as_completed()
                        self.player.completed_orders.enqueue(order)
                except Exception as e:
                    print(f"⚠️ Error cargando orden completada del jugador: {e}")
            
            # ✅ CARGAR ESTADO DEL JUEGO
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
                self.game_state.start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            
            # ✅ ESTABLECER REFERENCIA DEL JUGADOR EN GAME_STATE
            self.game_state.set_player_reference(self.player)
            
            # ✅ CARGAR TIEMPO DE JUEGO - CORREGIDO COMPLETAMENTE
            game_time_data = save_data["game_time"]
            elapsed_time = game_time_data.get("elapsed_time_sec", 0)
            total_duration = game_time_data.get("total_duration", 900)
            time_scale = game_time_data.get("time_scale", 3.0)
            
            # Obtener tiempo de inicio del juego
            if "game_start_time" in save_data:
                game_start_time_str = save_data["game_start_time"]
                if isinstance(game_start_time_str, str):
                    game_start_time = datetime.fromisoformat(game_start_time_str.replace('Z', '+00:00'))
                else:
                    game_start_time = self.get_game_start_time_from_json()
            else:
                game_start_time = self.get_game_start_time_from_json()
            
            # ✅ CREAR GAME_TIME CON DATOS CORRECTOS
            self.game_time = GameTime(
                total_duration_min=total_duration/60,
                game_start_time=game_start_time,
                time_scale=time_scale
            )
            self.game_time.start()
            
            # ✅ RESTAURAR TIEMPO TRANSCURRIDO CORRECTAMENTE
            import pygame
            current_pygame_time = pygame.time.get_ticks() / 1000.0
            
            # Ajustar el tiempo de inicio para que refleje el tiempo transcurrido guardado
            if "pygame_start_time" in game_time_data and "start_real_time" in game_time_data:
                # Usar valores guardados si están disponibles
                self.game_time.pygame_start_time = game_time_data["pygame_start_time"]
                self.game_time.start_real_time = game_time_data["start_real_time"]
            else:
                # Ajuste manual para tiempo transcurrido
                adjusted_start_time = current_pygame_time - self.game_time.pygame_start_time - elapsed_time
                self.game_time.start_real_time = adjusted_start_time
            
            print(f"🕒 Tiempo restaurado: {elapsed_time:.1f}s transcurridos de {total_duration}s totales")
            
            # ✅ CARGAR CLIMA
            weather_data = save_data["weather_state"]
            self.weather_system = Weather(self.api)
            
            # Configurar clima actual
            try:
                from entities.weather import WeatherCondition
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
            
            # ✅ CARGAR CÁMARA Y META
            self.camera_x, self.camera_y = save_data["camera_position"]
            self.income_goal = save_data["income_goal"]
            
            # ✅ REINICIAR SISTEMA DE UNDO
            self.undo_manager = UndoRedoManager(max_states=10)
            self.undo_manager.save_game_state(self, force=True)
            
            # ✅ CONFIGURAR MANAGERS DESPUÉS DE QUE TODO ESTÉ CARGADO
            self.setup_managers()
            
            print("✅ Partida cargada correctamente")
            print(f"   - Jugador en posición: ({self.player.grid_x}, {self.player.grid_y})")
            print(f"   - Órdenes activas: {len(self.active_orders)}")
            print(f"   - Órdenes en inventario: {len(self.player.inventory)}")
            print(f"   - Ganancias: ${self.game_state.total_earnings}")
            print(f"   - Tiempo restante: {self.game_time.get_remaining_time_formatted()}")
            
            # ✅ VERIFICACIÓN FINAL DE CONSISTENCIA
            self.verify_order_consistency()
            
        except Exception as e:
            print(f"❌ Error al cargar partida: {e}")
            import traceback
            traceback.print_exc()
            print("🔄 Iniciando nueva partida...")
            self.setup_new_game()

    def _find_or_create_order(self, order_data, all_orders):
        """Busca una orden en all_orders o la crea si no existe - MEJORADO"""
        # Primero buscar por ID en all_orders
        existing_order = all_orders.find_by_id(order_data["id"])
        if existing_order:
            # Actualizar estados de la orden existente
            existing_order.is_expired = order_data.get("is_expired", False)
            existing_order.is_completed = order_data.get("is_completed", False)
            existing_order.is_in_inventory = order_data.get("is_in_inventory", False)
            
            # Restaurar accepted_time si existe
            if order_data.get("accepted_time"):
                try:
                    existing_order.accepted_time = datetime.fromisoformat(
                        order_data["accepted_time"].replace('Z', '+00:00')
                    )
                except:
                    pass
            
            # Restaurar color si existe
            if "color" in order_data:
                existing_order.color = tuple(order_data["color"])
                    
            print(f"   🔄 Orden {existing_order.id} encontrada, actualizando estados")
            return existing_order
        else:
            # Crear nueva orden si no existe
            print(f"   📝 Creando nueva orden {order_data['id']} desde datos guardados")
            return self._create_order_from_save_data(order_data)

    def verify_order_consistency(self):
        """Verifica la consistencia de las órdenes después de cargar - MEJORADO"""
        print("🔍 Verificando consistencia de órdenes...")
        
        all_order_ids = set()
        duplicates = []
        
        # Verificar todas las listas de órdenes
        order_lists = [
            ("active_orders", self.active_orders),
            ("pending_orders", self.pending_orders), 
            ("completed_orders", self.completed_orders),
            ("rejected_orders", self.rejected_orders),
            ("inventory", self.player.inventory),
            ("all_orders", self.all_orders)
        ]
        
        for order_list_name, order_list in order_lists:
            for order in order_list:
                if order.id in all_order_ids:
                    duplicates.append((order.id, order_list_name))
                all_order_ids.add(order.id)
        
        # Reportar duplicados
        if duplicates:
            print("⚠️ ÓRDENES DUPLICADAS ENCONTRADAS:")
            for order_id, list_name in duplicates:
                print(f"   - {order_id} en {list_name}")
        else:
            print("✅ No se encontraron órdenes duplicadas")
        
        # Verificar peso del inventario
        calculated_weight = sum(order.weight for order in self.player.inventory)
        if self.player.current_weight != calculated_weight:
            print(f"⚠️ Peso inconsistente: {self.player.current_weight} vs {calculated_weight}")
            self.player.current_weight = calculated_weight
            print(f"   ✅ Peso corregido a: {self.player.current_weight}kg")
        else:
            print(f"✅ Peso del inventario consistente: {self.player.current_weight}kg")
        
        # Verificar que las órdenes en inventario tienen el estado correcto
        inventory_issues = 0
        for order in self.player.inventory:
            if not order.is_in_inventory:
                print(f"⚠️ Orden {order.id} en inventario pero is_in_inventory=False")
                order.is_in_inventory = True
                inventory_issues += 1
        
        if inventory_issues > 0:
            print(f"✅ Corregidos {inventory_issues} estados de inventario")
        
        print(f"📊 Resumen final: {len(all_order_ids)} órdenes únicas encontradas")

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
        # ✅ Verificar consistencia antes de guardar
        self.verify_order_consistency()
        
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
        current_game_time_elapsed = self.game_time.get_elapsed_game_time()  # ← CAMBIAR AQUÍ
        
        # Crear lista temporal de pedidos pendientes
        orders_to_release = []
        remaining_orders = OrderList.create_empty()
        
        # Revisar todos los pedidos pendientes
        while not self.pending_orders.is_empty():
            order = self.pending_orders.dequeue()
            
            if current_game_time_elapsed  >= order.release_time:
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
                order.release_time = current_game_time_elapsed  + 5  # Intentar de nuevo en 5 segundos
                self.pending_orders.enqueue(order)
          
    
    def setup_managers(self):
        """Configura los managers del juego"""
        self.ui_manager = UIManager(self.screen, self.game_map, self.screen_width, self.screen_height)
        self.interaction_manager = InteractionManager(self.player, self.active_orders, self.completed_orders, self.game_time)
        
        # NUEVO: Dar acceso al interaction_manager desde ui_manager
        self.ui_manager.interaction_manager = self.interaction_manager
        
        # NUEVO: Dar acceso a game_engine desde popup_manager
        self.popup_manager.game_engine = self
        
        # Variables de cámara
        self.camera_x, self.camera_y = 0, 0
    # game_engine.py - CORRECCIÓN para pasar game_map al interaction manager
    def handle_events(self):
        """Maneja todos los eventos del juego - VERSIÓN CORREGIDA"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # ✅ CORRECCIÓN: Manejar ESC primero y evitar conflictos
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if not self.game_state.game_over:
                    # Si hay popups activos, cerrarlos primero
                    if self.popup_manager.popup_active:
                        self.popup_manager.popup_active = False
                        self.popup_manager.pending_order = None
                    elif self.popup_manager.cancel_popup_active:
                        self.popup_manager.cancel_popup_active = False
                        self.popup_manager.selected_order_for_cancel = None
                    else:
                        # Solo abrir menú de pausa si no hay popups
                        self.pause_menu.toggle()
                continue  # ✅ IMPORTANTE: Saltar otros procesamientos
            
            # Si el juego está pausado, manejar eventos del menú de pausa
            if self.pause_menu.active:
                pause_result = self.pause_menu.handle_event(event)
                if pause_result:
                    self.handle_pause_result(pause_result)
                continue  # Saltar otros eventos si está pausado
            
            # Manejar popups (solo si no está pausado)
            popup_result = self.popup_manager.handle_event(event, self, self.player, self.active_orders)
            if popup_result:
                message = popup_result.get("message", "")
                if message:
                    self.ui_manager.show_message(message, 3)

                penalty = popup_result.get("penalty")
                if penalty:
                    self.player.reputation = max(0, self.player.reputation - penalty)
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
            
            if not self.game_state.game_over and not self.pause_menu.active:
                # CORRECCIÓN: Pasar game_map al interaction_manager
                self.interaction_manager.handle_event(event, self.game_state, self.game_map)
            
            # Guardar estado después de interacciones importantes
            if not self.game_state.game_over and not self.pause_menu.active:
                self.undo_manager.save_game_state(self)   
    def handle_pause_result(self, result):
        """Maneja las acciones del menú de pausa"""
        action = result.get("action")
        
        if action == "resume":
            self.pause_menu.toggle()
        elif action == "confirm_save":
            slot_name = result.get("slot")
            if self.save_game(slot_name):
                self.ui_manager.show_message(f"Partida guardada en {slot_name}", 3)
            self.pause_menu.toggle()
        elif action == "main_menu":
            self.running = False
            # Aquí podrías agregar lógica para volver al menú principal

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
        """Actualiza todos los sistemas del juego - MODIFICADO"""
        if not self.game_state.game_over:
            # Actualizar sistemas principales
            self.game_time.update(dt)
            self.weather_system.update(dt)
            self.update_release_times(dt)
            
            # NUEVO: Actualizar expiraciones de pedidos
            self.update_order_expirations()
            
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
        """Actualiza el estado general del juego - VERSIÓN MEJORADA"""
        # Si el juego ya terminó, no hacer nada
        if self.game_state.game_over:
            return
        
        # Verificar condiciones de victoria/derrota
        if self.player.reputation < 20:
            print("🎮 Fin del juego: Reputación muy baja")
            self.game_state.set_game_over(False, "Derrota: Reputación muy baja")
            self.save_final_score(False)
            return
        
        if self.game_time.is_time_up() and self.game_state.total_earnings < self.income_goal:
            print("🎮 Fin del juego: Tiempo agotado")
            self.game_state.set_game_over(False, "Derrota: Tiempo agotado")
            self.save_final_score(False)
            return
        
        if self.game_state.total_earnings >= self.income_goal:
            print("🎮 Fin del juego: Victoria alcanzada")
            self.game_state.set_game_over(True, "¡Victoria! Meta alcanzada")
            self.save_final_score(True)
            return
        
        if self.no_more_available_orders() and self.game_state.total_earnings <= self.income_goal:
            print("🎮 Fin del juego: No quedan pedidos y no se alcanzó la meta")
            self.game_state.set_game_over(False, "Derrota: No quedan pedidos y no se alcanzó la meta")
            self.save_final_score(False)
            return
            
        
        
        
        
        # NUEVA CONDICIÓN: Verificar si no quedan pedidos disponibles
        if self.no_more_available_orders():
            print("🎮 Fin del juego: No quedan pedidos disponibles")
            self.game_state.set_game_over(False, "Derrota: No quedan pedidos disponibles")
            self.save_final_score(False)
            return
    def no_more_available_orders(self):
        """Verifica si no quedan pedidos disponibles para completar - VERSIÓN CORREGIDA"""
        

        
        # Verificar si no hay pedidos activos, pendientes o en inventario
        no_active_orders = (
            len(self.active_orders) == 0 and 
            len(self.pending_orders) == 0 and 
            len(self.player.inventory) == 0
        )
        
        if not no_active_orders:
            #print("   ⚠️  Aún hay pedidos disponibles")
            return False
        
        # Calcular total de pedidos procesados (completados + rechazados)
        total_processed = len(self.completed_orders) + len(self.rejected_orders)
        
        # Verificar si hemos procesado todos los pedidos del juego
        all_orders_processed = (total_processed >= len(self.all_orders))
        
        print(f"   Procesados: {total_processed}/{len(self.all_orders)}")
        
        if all_orders_processed:
            print("   ✅ Todos los pedidos han sido procesados")
        else:
            print(f"   ❌ Faltan {len(self.all_orders) - total_processed} pedidos por procesar")
        
        return all_orders_processed
    def save_final_score(self, victory: bool):
        """Guarda la puntuación final - VERSIÓN CORREGIDA"""
        try:
            print(f"💾 Intentando guardar puntuación final: victoria={victory}")
            
            # Verificar que el juego haya terminado
            if not self.game_state.game_over:
                print("⚠️ El juego no ha terminado, no se puede guardar puntuación")
                return
                
            from utils.score_manager import score_manager
            
            # Asegurar inicialización
            if not score_manager.initialized:
                print("🔄 Inicializando sistema de puntuación...")
                score_manager.initialize_score_system()
            
            # USAR TIEMPO DE JUEGO REAL
            game_duration = self.game_time.get_elapsed_game_time()
            total_game_duration = 15 * 60  # 15 minutos en segundos
            
            print(f"⏱️ Duración del juego: {game_duration:.1f}s de {total_game_duration}s totales")
            
            # Calcular el puntaje UNA SOLA VEZ y guardarlo en cache
            final_score = self.game_state.calculate_final_score(game_duration, total_game_duration)
            
            # Obtener estadísticas (usará el cache)
            stats = self.game_state.get_game_stats(game_duration)
            
            print(f"📊 ESTADÍSTICAS FINALES:")
            print(f"   - Reputación final: {self.player.reputation}")
            print(f"   - Ganancias totales: ${stats['earnings']}")
            print(f"   - Pedidos completados: {stats['orders_completed']}")
            print(f"   - Pedidos cancelados: {stats['orders_cancelled']}")
            print(f"   - Entregas perfectas: {stats['perfect_deliveries']}")
            print(f"   - Entregas tardías: {stats['late_deliveries']}")
            print(f"   - Mejor racha: {stats['best_streak']}")
            print(f"   - Victoria: {victory}")
            print(f"   - Puntaje calculado: {stats['final_score']}")
            
            # Guardar puntuación
            success = score_manager.add_score(
                self.game_state, 
                victory, 
                game_duration,
                total_game_duration
            )
            
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
        
        # Dibujar juego normal
        self.render_map()
        self.weather_system.draw_particles(self.screen, self.camera_x, self.camera_y)
        self.ui_manager.draw_order_markers(self.active_orders, self.player, self.camera_x, self.camera_y)
        self.player.draw(self.screen, self.camera_x, self.camera_y)
        
        pending_count = len(self.pending_orders)
        self.ui_manager.draw_sidebar(self.player, self.active_orders, self.weather_system, 
                                self.game_time, self.game_state, pending_count)
        
        self.ui_manager.draw_messages()
        self.ui_manager.draw_interaction_hints(self.player, self.active_orders, self.camera_x, self.camera_y, self.game_map)
        
        if self.game_state.game_over:
            self.ui_manager.draw_game_over_screen(self.game_state)

        self.popup_manager.draw_new_order_popup(self.screen)
        self.popup_manager.draw_cancel_order_popup(self.screen)
        
        # Dibujar menú de pausa SIEMPRE AL FINAL (encima de todo)
        if self.pause_menu.active:
            self.pause_menu.draw()
        
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
        game_start_datetime = self.get_game_start_time_from_json()


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
        self.game_time = GameTime(
            total_duration_min=15,
            game_start_time=game_start_datetime,
            time_scale=3.0
        )
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
        
    def verify_order_consistency(self):
        """Verifica la consistencia de las órdenes después de cargar"""
        print("🔍 Verificando consistencia de órdenes...")
        
        # Verificar que no hay órdenes duplicadas entre listas
        all_order_ids = set()
        
        for order_list_name, order_list in [
            ("active_orders", self.active_orders),
            ("pending_orders", self.pending_orders), 
            ("completed_orders", self.completed_orders),
            ("rejected_orders", self.rejected_orders),
            ("inventory", self.player.inventory)
        ]:
            for order in order_list:
                if order.id in all_order_ids:
                    print(f"⚠️ ORDEN DUPLICADA: {order.id} en {order_list_name}")
                all_order_ids.add(order.id)
        
        # Verificar peso del inventario
        calculated_weight = sum(order.weight for order in self.player.inventory)
        if self.player.current_weight != calculated_weight:
            print(f"⚠️ Peso inconsistente: {self.player.current_weight} vs {calculated_weight}")
            self.player.current_weight = calculated_weight
        
        print(f"✅ Verificación completada. {len(all_order_ids)} órdenes únicas encontradas")

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
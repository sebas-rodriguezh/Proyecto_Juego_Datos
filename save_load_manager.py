# save_load_manager.py - VERSIÓN MEJORADA
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
import pickle
import base64

class SaveLoadManager:
    """Sistema de guardado y carga del juego - VERSIÓN MEJORADA"""
    
    SAVE_DIR = "saves"
    
    def __init__(self):
        os.makedirs(self.SAVE_DIR, exist_ok=True)
    
    def save_game(self, game_engine, slot_name="slot1"):
        """Guarda el estado completo del juego como binario - MEJORADO"""
        try:
            # Crear datos de guardado COMPLETOS
            save_data = {
                "version": "2.2",  # Incrementar versión
                "timestamp": datetime.now().isoformat(),
                "player_data": self._serialize_player(game_engine.player),
                "active_orders": self._serialize_order_list(game_engine.active_orders),
                "completed_orders": self._serialize_order_list(game_engine.completed_orders),
                "pending_orders": self._serialize_order_list(game_engine.pending_orders),
                "rejected_orders": self._serialize_order_list(game_engine.rejected_orders),
                "all_orders": self._serialize_order_list(game_engine.all_orders),  # ✅ NUEVO: Guardar todos los pedidos
                "game_state": self._serialize_game_state(game_engine.game_state),
                "game_time": self._serialize_game_time(game_engine.game_time),
                "weather_state": self._serialize_weather(game_engine.weather_system),
                "camera_position": (game_engine.camera_x, game_engine.camera_y),
                "income_goal": game_engine.income_goal,
                "game_start_time": game_engine.game_time.game_start_time.isoformat(),
                "map_info": {
                    "width": game_engine.game_map.width,
                    "height": game_engine.game_map.height,
                    "city_name": game_engine.game_map.city_name
                }
            }
            
            # Guardar como binario usando pickle
            save_file = os.path.join(self.SAVE_DIR, f"{slot_name}.sav")
            with open(save_file, "wb") as f:
                pickle.dump(save_data, f)
            
            print(f"✅ Partida guardada correctamente en {save_file}")
            print(f"📊 Estadísticas de guardado:")
            print(f"   - Pedidos activos: {len(game_engine.active_orders)}")
            print(f"   - Pedidos en inventario: {len(game_engine.player.inventory)}")
            print(f"   - Pedidos pendientes: {len(game_engine.pending_orders)}")
            print(f"   - Pedidos completados: {len(game_engine.completed_orders)}")
            print(f"   - Todos los pedidos: {len(game_engine.all_orders)}")
            return True
            
        except Exception as e:
            print(f"❌ Error al guardar: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_game(self, slot_name="slot1") -> Optional[Dict[str, Any]]:
        """Carga el estado del juego desde archivo binario"""
        try:
            save_file = os.path.join(self.SAVE_DIR, f"{slot_name}.sav")
            
            if not os.path.exists(save_file):
                print(f"❌ No se encontró archivo de guardado: {save_file}")
                return None
            
            with open(save_file, "rb") as f:
                save_data = pickle.load(f)
            
            print(f"✅ Partida cargada desde {save_file}")
            print(f"📊 Datos cargados:")
            print(f"   - Pedidos activos: {len(save_data.get('active_orders', []))}")
            print(f"   - Pedidos en inventario: {len(save_data.get('player_data', {}).get('inventory', []))}")
            print(f"   - Pedidos pendientes: {len(save_data.get('pending_orders', []))}")
            print(f"   - Pedidos completados: {len(save_data.get('completed_orders', []))}")
            print(f"   - Todos los pedidos: {len(save_data.get('all_orders', []))}")
            
            return save_data
            
        except Exception as e:
            print(f"❌ Error al cargar: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _serialize_player(self, player):
        """Serializa el estado del jugador - MEJORADO"""
        try:
            player_data = {
                "grid_x": player.grid_x,
                "grid_y": player.grid_y,
                "stamina": player.stamina,
                "reputation": player.reputation,
                "current_weight": player.current_weight,
                "state": player.state,
                "direction": player.direction,
                "inventory": self._serialize_order_list(player.inventory),
                "completed_orders": self._serialize_order_list(player.completed_orders)
            }
            
            print(f"💾 Serializando jugador:")
            print(f"   - Posición: ({player.grid_x}, {player.grid_y})")
            print(f"   - Inventario: {len(player.inventory)} pedidos")
            print(f"   - Peso actual: {player.current_weight}kg")
            
            return player_data
        except Exception as e:
            print(f"Error serializando jugador: {e}")
            return {
                "grid_x": 0,
                "grid_y": 0,
                "stamina": 100,
                "reputation": 70,
                "current_weight": 0,
                "state": "normal",
                "direction": "right",
                "inventory": [],
                "completed_orders": []
            }
            
# Agregar este método en la clase SaveLoadManager (después de _serialize_player)
    def _serialize_game_state(self, game_state):
        """Serializa el estado del juego - NUEVO MÉTODO"""
        try:
            game_state_data = {
                "total_earnings": game_state.total_earnings,
                "income_goal": game_state.income_goal,
                "game_over": game_state.game_over,
                "victory": game_state.victory,
                "game_over_reason": game_state.game_over_reason,
                "orders_completed": game_state.orders_completed,
                "orders_cancelled": game_state.orders_cancelled,
                "perfect_deliveries": game_state.perfect_deliveries,
                "late_deliveries": game_state.late_deliveries,
                "current_streak": game_state.current_streak,
                "best_streak": game_state.best_streak,
                "start_time": game_state.start_time.isoformat() if hasattr(game_state.start_time, 'isoformat') else str(game_state.start_time)
            }
            
            print(f"💾 Serializando game_state: ${game_state_data['total_earnings']} ganancias")
            return game_state_data
            
        except Exception as e:
            print(f"Error serializando game_state: {e}")
            return {
                "total_earnings": 0,
                "income_goal": 2000,
                "game_over": False,
                "victory": False,
                "game_over_reason": "",
                "orders_completed": 0,
                "orders_cancelled": 0,
                "perfect_deliveries": 0,
                "late_deliveries": 0,
                "current_streak": 0,
                "best_streak": 0,
                "start_time": datetime.now().isoformat()
            }
    
    def _serialize_order_list(self, order_list):
        """Serializa una OrderList - VERSIÓN COMPATIBLE CON Z"""
        orders_data = []
        try:
            for order in order_list:
                # Convertir deadline a string sin Z
                deadline_str = order.deadline.isoformat()
                if not deadline_str.endswith('Z'):
                    deadline_str = deadline_str  # Ya está bien
                
                order_data = {
                    "id": order.id,
                    "pickup": order.pickup,
                    "dropoff": order.dropoff,
                    "payout": order.payout,
                    "deadline": deadline_str,  # Sin Z para compatibilidad interna
                    "weight": order.weight,
                    "priority": order.priority,
                    "release_time": order.release_time,
                    "color": list(order.color) if hasattr(order, 'color') else [100, 100, 255],
                    "is_expired": getattr(order, 'is_expired', False),
                    "is_completed": getattr(order, 'is_completed', False),
                    "is_in_inventory": getattr(order, 'is_in_inventory', False),
                    "accepted_time": order.accepted_time.isoformat() if getattr(order, 'accepted_time', None) else None
                }
                orders_data.append(order_data)
                
            print(f"💾 Serializando {len(orders_data)} órdenes")
            
        except Exception as e:
            print(f"Error serializando órdenes: {e}")
            import traceback
            traceback.print_exc()
        return orders_data

    def _serialize_game_time(self, game_time):
        """Serializa el tiempo de juego - MEJORADO"""
        try:
            return {
                "elapsed_time_sec": game_time.get_elapsed_real_time(),
                "total_duration": game_time.real_duration,
                "time_scale": game_time.time_scale,
                "game_start_time": game_time.game_start_time.isoformat(),
                "pygame_start_time": game_time.pygame_start_time,
                "start_real_time": game_time.start_real_time
            }
        except Exception as e:
            print(f"Error serializando tiempo de juego: {e}")
            return {
                "elapsed_time_sec": 0,
                "total_duration": 900,
                "time_scale": 3.0,
                "game_start_time": datetime.now().isoformat(),
                "pygame_start_time": 0,
                "start_real_time": 0
            }
    
    def _serialize_weather(self, weather_system):
        """Serializa el sistema de clima"""
        try:
            return {
                "current_condition": weather_system.current_condition.value if hasattr(weather_system.current_condition, 'value') else str(weather_system.current_condition),
                "current_intensity": weather_system.current_intensity,
                "current_multiplier": weather_system.current_multiplier
            }
        except Exception as e:
            print(f"Error serializando clima: {e}")
            return {
                "current_condition": "clear",
                "current_intensity": 0.0,
                "current_multiplier": 1.0
            }
    
    # En el método list_saves(), mejora la información:
    def list_saves(self):
        """Lista todas las partidas guardadas disponibles - MEJORADO"""
        saves = {}
        
        for i in range(1, 4):  # 3 slots de guardado
            slot_name = f"slot{i}"
            save_file = os.path.join(self.SAVE_DIR, f"{slot_name}.sav")
            
            if os.path.exists(save_file):
                try:
                    with open(save_file, "rb") as f:
                        save_data = pickle.load(f)
                    
                    # Extraer información mejorada
                    game_state = save_data.get("game_state", {})
                    player_data = save_data.get("player_data", {})
                    
                    saves[slot_name] = {
                        "earnings": game_state.get("total_earnings", 0),
                        "orders_completed": game_state.get("orders_completed", 0),
                        "player_level": player_data.get("reputation", 0),
                        "timestamp": save_data.get("timestamp", "Desconocido"),
                        "format": "binario",
                        "exists": True
                    }
                except Exception as e:
                    print(f"Error leyendo información de {slot_name}: {e}")
                    saves[slot_name] = {"error": "Archivo corrupto", "exists": True}
            else:
                saves[slot_name] = {"exists": False, "info": "Vacío"}
        
        return saves
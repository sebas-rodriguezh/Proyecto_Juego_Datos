# save_load_manager.py - VERSIÓN BINARIA
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
import pickle
import base64

class SaveLoadManager:
    """Sistema de guardado y carga del juego - VERSIÓN BINARIA"""
    
    SAVE_DIR = "saves"
    
    def __init__(self):
        os.makedirs(self.SAVE_DIR, exist_ok=True)
    
    def save_game(self, game_engine, slot_name="slot1"):
        """Guarda el estado completo del juego como binario"""
        try:
            # Crear datos de guardado (igual que antes)
            save_data = {
                "version": "2.0",
                "timestamp": datetime.now().isoformat(),
                "player_data": self._serialize_player(game_engine.player),
                "active_orders": self._serialize_order_list(game_engine.active_orders),
                "completed_orders": self._serialize_order_list(game_engine.completed_orders),
                "pending_orders": self._serialize_order_list(game_engine.pending_orders),
                "game_state": self._serialize_game_state(game_engine.game_state),
                "game_time": self._serialize_game_time(game_engine.game_time),
                "weather_state": self._serialize_weather(game_engine.weather_system),
                "camera_position": (game_engine.camera_x, game_engine.camera_y),
                "income_goal": game_engine.income_goal,
                "map_info": {
                    "width": game_engine.game_map.width,
                    "height": game_engine.game_map.height,
                    "city_name": game_engine.game_map.city_name
                }
            }
            
            # Guardar como binario usando pickle
            save_file = os.path.join(self.SAVE_DIR, f"{slot_name}.sav")
            with open(save_file, "wb") as f:  # 'wb' para escritura binaria
                pickle.dump(save_data, f)
            
            print(f"✅ Partida guardada correctamente en {save_file} (formato binario)")
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
            
            with open(save_file, "rb") as f:  # 'rb' para lectura binaria
                save_data = pickle.load(f)
            
            print(f"✅ Partida cargada desde {save_file} (formato binario)")
            return save_data
            
        except Exception as e:
            print(f"❌ Error al cargar: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_game_from_json(self, json_data: Dict[str, Any], slot_name="slot1"):
        """Guarda datos JSON recibidos como archivo binario"""
        try:
            # Validar que sea un diccionario
            if not isinstance(json_data, dict):
                raise ValueError("Los datos deben ser un diccionario JSON")
            
            # Agregar timestamp si no existe
            if "timestamp" not in json_data:
                json_data["timestamp"] = datetime.now().isoformat()
            
            # Guardar como binario
            save_file = os.path.join(self.SAVE_DIR, f"{slot_name}.sav")
            with open(save_file, "wb") as f:
                pickle.dump(json_data, f)
            
            print(f"✅ JSON guardado como binario en {save_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error al guardar JSON como binario: {e}")
            return False
    
    def load_game_to_json(self, slot_name="slot1") -> Optional[Dict[str, Any]]:
        """Carga el archivo binario y lo devuelve como JSON/diccionario"""
        try:
            save_file = os.path.join(self.SAVE_DIR, f"{slot_name}.sav")
            
            if not os.path.exists(save_file):
                print(f"❌ No se encontró archivo de guardado: {save_file}")
                return None
            
            with open(save_file, "rb") as f:
                save_data = pickle.load(f)
            
            # Asegurarse de que sea un diccionario (JSON compatible)
            if not isinstance(save_data, dict):
                raise ValueError("Los datos cargados no son un diccionario válido")
            
            print(f"✅ Binario cargado como JSON desde {save_file}")
            return save_data
            
        except Exception as e:
            print(f"❌ Error al cargar binario como JSON: {e}")
            return None
    
    def list_saves(self):
        """Lista todas las partidas guardadas disponibles"""
        saves = {}
        
        for i in range(1, 4):  # 3 slots de guardado
            slot_name = f"slot{i}"
            save_file = os.path.join(self.SAVE_DIR, f"{slot_name}.sav")
            
            if os.path.exists(save_file):
                try:
                    with open(save_file, "rb") as f:
                        save_data = pickle.load(f)
                    
                    # Extraer información básica
                    saves[slot_name] = {
                        "earnings": save_data.get("game_state", {}).get("total_earnings", 0),
                        "orders_completed": save_data.get("game_state", {}).get("orders_completed", 0),
                        "timestamp": save_data.get("timestamp", "Desconocido"),
                        "format": "binario"
                    }
                except Exception as e:
                    print(f"Error leyendo información de {slot_name}: {e}")
                    saves[slot_name] = {"error": "Archivo corrupto"}
        
        return saves

    # Los métodos de serialización se mantienen igual
    def _serialize_order_list(self, order_list):
        """Serializa una OrderList - VERSIÓN MEJORADA"""
        orders_data = []
        try:
            for order in order_list:
                order_data = {
                    "id": order.id,
                    "pickup": order.pickup,
                    "dropoff": order.dropoff,
                    "payout": order.payout,
                    "deadline": order.deadline.isoformat() if hasattr(order.deadline, 'isoformat') else str(order.deadline),
                    "weight": order.weight,
                    "priority": order.priority,
                    "release_time": order.release_time,
                    "color": list(order.color) if hasattr(order, 'color') else [100, 100, 255]
                }
                orders_data.append(order_data)
        except Exception as e:
            print(f"Error serializando órdenes: {e}")
        return orders_data
    
    def _serialize_game_state(self, game_state):
        """Serializa el estado del juego"""
        try:
            return {
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
        except Exception as e:
            print(f"Error serializando estado del juego: {e}")
            return {}
    
    def _serialize_game_time(self, game_time):
        """Serializa el tiempo de juego"""
        try:
            return {
                "elapsed_time_sec": game_time.get_elapsed_time() if hasattr(game_time, 'get_elapsed_time') else 0,
                "total_duration": game_time.total_duration if hasattr(game_time, 'total_duration') else 900
            }
        except Exception as e:
            print(f"Error serializando tiempo de juego: {e}")
            return {}
    
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
            return {}
    
    def _serialize_player(self, player):
        """Serializa el estado del jugador"""
        try:
            return {
                "grid_x": player.grid_x,
                "grid_y": player.grid_y,
                "visual_x": player.visual_x,
                "visual_y": player.visual_y,
                "stamina": player.stamina,
                "reputation": player.reputation,
                "current_weight": player.current_weight,
                "state": player.state,
                "direction": player.direction,
                "inventory": self._serialize_order_list(player.inventory),
                "completed_orders": self._serialize_order_list(player.completed_orders)
            }
        except Exception as e:
            print(f"Error serializando jugador: {e}")
            return {}
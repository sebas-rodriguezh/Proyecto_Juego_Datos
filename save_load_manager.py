# save_load_manager.py
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any

class SaveLoadManager:
    """Sistema de guardado y carga del juego"""
    
    SAVE_DIR = "saves"
    CACHE_DIR = "api_cache"
    DATA_DIR = "data"
    
    def __init__(self):
        # Crear directorios si no existen
        for directory in [self.SAVE_DIR, self.CACHE_DIR, self.DATA_DIR]:
            os.makedirs(directory, exist_ok=True)
    
    def save_game(self, game_engine, slot_name="slot1"):
        """Guarda el estado completo del juego en formato JSON"""
        try:
            # Serializar datos básicos primero
            save_data = {
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "player_data": self._serialize_player(game_engine.player),
                "active_orders": self._serialize_order_list(game_engine.active_orders),
                "completed_orders": self._serialize_order_list(game_engine.completed_orders),
                "game_state": self._serialize_game_state(game_engine.game_state),
                "game_time": self._serialize_game_time(game_engine.game_time),
                "weather_state": self._serialize_weather(game_engine.weather_system),
                "camera_position": (game_engine.camera_x, game_engine.camera_y),
                "income_goal": game_engine.income_goal
            }
            
            # NO guardar map_data completo (es muy grande y causa problemas)
            # En su lugar, guardar solo la referencia necesaria
            save_data["map_reference"] = {
                "width": game_engine.game_map.width,
                "height": game_engine.game_map.height,
                "city_name": getattr(game_engine.game_map, 'city_name', 'Unknown')
            }
            
            save_file = os.path.join(self.SAVE_DIR, f"{slot_name}.sav")
            with open(save_file, "w", encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Partida guardada correctamente en {save_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error al guardar: {e}")
            import traceback
            traceback.print_exc()  # Esto mostrará el error completo
            return False
    
    def load_game(self, slot_name="slot1") -> Optional[Dict[str, Any]]:
        """Carga el estado del juego desde archivo JSON"""
        try:
            save_file = os.path.join(self.SAVE_DIR, f"{slot_name}.sav")
            
            if not os.path.exists(save_file):
                print(f"❌ No se encontró archivo de guardado: {save_file}")
                return None
            
            with open(save_file, "r", encoding='utf-8') as f:
                save_data = json.load(f)
            
            print(f"✅ Partida cargada desde {save_file}")
            return save_data
            
        except Exception as e:
            print(f"❌ Error al cargar: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_save_info(self, slot_name="slot1") -> Optional[Dict[str, str]]:
        """Obtiene información básica de un archivo de guardado"""
        try:
            save_file = os.path.join(self.SAVE_DIR, f"{slot_name}.sav")
            
            if not os.path.exists(save_file):
                return None
            
            with open(save_file, "r", encoding='utf-8') as f:
                save_data = json.load(f)
            
            return {
                "timestamp": save_data.get("timestamp", "Desconocido"),
                "version": save_data.get("version", "1.0"),
                "earnings": save_data.get("game_state", {}).get("total_earnings", 0),
                "orders_completed": save_data.get("game_state", {}).get("orders_completed", 0)
            }
            
        except Exception as e:
            print(f"Error al leer información del guardado: {e}")
            return None
    
    def list_saves(self) -> Dict[str, Dict[str, str]]:
        """Lista todos los archivos de guardado disponibles"""
        saves = {}
        
        if not os.path.exists(self.SAVE_DIR):
            return saves
            
        for filename in os.listdir(self.SAVE_DIR):
            if filename.endswith(".sav"):
                slot_name = filename[:-4]  # Remover extensión .sav
                info = self.get_save_info(slot_name)
                if info:
                    saves[slot_name] = info
        
        return saves
    
    def delete_save(self, slot_name="slot1") -> bool:
        """Elimina un archivo de guardado"""
        try:
            save_file = os.path.join(self.SAVE_DIR, f"{slot_name}.sav")
            if os.path.exists(save_file):
                os.remove(save_file)
                print(f"✅ Partida {slot_name} eliminada")
                return True
            return False
        except Exception as e:
            print(f"Error al eliminar guardado: {e}")
            return False
    
    # Métodos de serialización privados - CORREGIDOS
    def _serialize_player(self, player):
        """Serializa el objeto jugador - VERSIÓN CORREGIDA"""
        try:
            return {
                "grid_x": player.grid_x,
                "grid_y": player.grid_y,
                "visual_x": player.visual_x,
                "visual_y": player.visual_y,
                "stamina": player.stamina,
                "reputation": player.reputation,
                "current_weight": player.current_weight,
                "max_weight": player.max_weight,
                "state": player.state,
                "direction": player.direction,
                "inventory": self._serialize_order_list(player.inventory),
                "completed_orders": self._serialize_order_list(player.completed_orders)
            }
        except Exception as e:
            print(f"Error serializando jugador: {e}")
            return {}
    
    def _serialize_order_list(self, order_list):
        """Serializa una OrderList - VERSIÓN CORREGIDA"""
        orders_data = []
        try:
            for order in order_list:
                orders_data.append({
                    "id": order.id,
                    "pickup": order.pickup,
                    "dropoff": order.dropoff,
                    "payout": order.payout,
                    "deadline": order.deadline.isoformat() if hasattr(order.deadline, 'isoformat') else str(order.deadline),
                    "weight": order.weight,
                    "priority": order.priority,
                    "release_time": order.release_time
                })
        except Exception as e:
            print(f"Error serializando órdenes: {e}")
        return orders_data
    
    def _serialize_game_state(self, game_state):
        """Serializa el estado del juego - VERSIÓN CORREGIDA"""
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
        """Serializa el tiempo de juego - VERSIÓN CORREGIDA"""
        try:
            return {
                "elapsed_time_sec": game_time.get_elapsed_time() if hasattr(game_time, 'get_elapsed_time') else 0
            }
        except Exception as e:
            print(f"Error serializando tiempo de juego: {e}")
            return {}
    
    def _serialize_weather(self, weather_system):
        """Serializa el sistema de clima - VERSIÓN CORREGIDA"""
        try:
            return {
                "current_condition": weather_system.current_condition.value if hasattr(weather_system.current_condition, 'value') else str(weather_system.current_condition),
                "current_intensity": weather_system.current_intensity,
                "current_multiplier": weather_system.current_multiplier
            }
        except Exception as e:
            print(f"Error serializando clima: {e}")
            return {}
# save_load_manager.py
import pickle
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from collections import deque

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
        """Guarda el estado completo del juego en formato binario"""
        try:
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
                "map_data": game_engine.map_data,
                "income_goal": game_engine.income_goal
            }
            
            save_file = os.path.join(self.SAVE_DIR, f"{slot_name}.sav")
            with open(save_file, "wb") as f:
                pickle.dump(save_data, f)
            
            return True
            
        except Exception as e:
            print(f"Error al guardar: {e}")
            return False
    
    def load_game(self, slot_name="slot1") -> Optional[Dict[str, Any]]:
        """Carga el estado del juego desde archivo binario"""
        try:
            save_file = os.path.join(self.SAVE_DIR, f"{slot_name}.sav")
            
            if not os.path.exists(save_file):
                return None
            
            with open(save_file, "rb") as f:
                save_data = pickle.load(f)
            
            return save_data
            
        except Exception as e:
            print(f"Error al cargar: {e}")
            return None
    
    def get_save_info(self, slot_name="slot1") -> Optional[Dict[str, str]]:
        """Obtiene información básica de un archivo de guardado"""
        try:
            save_file = os.path.join(self.SAVE_DIR, f"{slot_name}.sav")
            
            if not os.path.exists(save_file):
                return None
            
            with open(save_file, "rb") as f:
                save_data = pickle.load(f)
            
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
                return True
            return False
        except Exception as e:
            print(f"Error al eliminar guardado: {e}")
            return False
    
    def cache_api_data(self, endpoint: str, data: Dict[str, Any]):
        """Guarda datos de la API en caché local"""
        try:
            cache_file = os.path.join(self.CACHE_DIR, f"{endpoint.replace('/', '_')}.json")
            
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            
            with open(cache_file, "w", encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error al guardar caché: {e}")
    
    def load_cached_data(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Carga datos desde caché local"""
        try:
            cache_file = os.path.join(self.CACHE_DIR, f"{endpoint.replace('/', '_')}.json")
            
            if not os.path.exists(cache_file):
                return None
            
            with open(cache_file, "r", encoding='utf-8') as f:
                cache_data = json.load(f)
            
            return cache_data.get("data")
            
        except Exception as e:
            print(f"Error al cargar caché: {e}")
            return None
    
    # Métodos de serialización privados
    def _serialize_player(self, player):
        """Serializa el objeto jugador"""
        return {
            "x": player.x,
            "y": player.y,
            "stamina": player.stamina,
            "reputation": player.reputation,
            "current_weight": player.current_weight,
            "max_weight": player.max_weight,
            "state": player.state,
            "direction": player.direction,
            "inventory": self._serialize_order_list(player.inventory),
            "completed_orders": self._serialize_order_list(player.completed_orders)
        }
    
    def _serialize_order_list(self, order_list):
        """Serializa una OrderList"""
        orders_data = []
        for order in order_list:
            orders_data.append({
                "id": order.id,
                "pickup": order.pickup,
                "dropoff": order.dropoff,
                "payout": order.payout,
                "deadline": order.deadline.isoformat(),
                "weight": order.weight,
                "priority": order.priority,
                "release_time": order.release_time
            })
        return orders_data
    
    def _serialize_game_state(self, game_state):
        """Serializa el estado del juego"""
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
            "start_time": game_state.start_time.isoformat()
        }
    
    def _serialize_game_time(self, game_time):
        """Serializa el tiempo de juego"""
        return {
            "total_duration_sec": game_time.total_duration_sec,
            "elapsed_time_sec": game_time.elapsed_time_sec,
            "is_running": game_time.is_running,
            "game_speed": game_time.game_speed
        }
    
    def _serialize_weather(self, weather_system):
        """Serializa el sistema de clima"""
        return {
            "current_condition": weather_system.current_condition.value,
            "current_intensity": weather_system.current_intensity,
            "current_multiplier": weather_system.current_multiplier,
            "burst_timer": weather_system.burst_timer,
            "burst_duration": weather_system.burst_duration,
            "is_transitioning": weather_system.is_transitioning,
            "weather_history": weather_system.weather_history
        }

class UndoRedoManager:
    """Sistema de deshacer/rehacer acciones del jugador"""
    
    def __init__(self, max_states=50):
        self.max_states = max_states
        self.state_history = deque(maxlen=max_states)
        self.current_index = -1
    
    def save_state(self, game_engine):
        """Guarda el estado actual para poder deshacerlo"""
        try:
            state_data = {
                "player_position": (game_engine.player.x, game_engine.player.y),
                "player_stamina": game_engine.player.stamina,
                "player_reputation": game_engine.player.reputation,
                "player_inventory": self._serialize_inventory(game_engine.player.inventory),
                "total_earnings": game_engine.game_state.total_earnings,
                "active_orders": self._serialize_order_list_simple(game_engine.active_orders),
                "game_time": game_engine.game_time.elapsed_time_sec,
                "timestamp": datetime.now()
            }
            
            # Si estamos en el medio del historial, eliminar estados futuros
            if self.current_index < len(self.state_history) - 1:
                # Crear nueva deque con solo los estados hasta el índice actual
                new_history = deque(list(self.state_history)[:self.current_index + 1], maxlen=self.max_states)
                self.state_history = new_history
            
            self.state_history.append(state_data)
            self.current_index = len(self.state_history) - 1
            
        except Exception as e:
            print(f"Error al guardar estado para undo: {e}")
    
    def undo(self, game_engine) -> bool:
        """Deshace la última acción"""
        if self.current_index > 0:
            self.current_index -= 1
            return self._restore_state(game_engine, self.state_history[self.current_index])
        return False
    
    def redo(self, game_engine) -> bool:
        """Rehace una acción deshecha"""
        if self.current_index < len(self.state_history) - 1:
            self.current_index += 1
            return self._restore_state(game_engine, self.state_history[self.current_index])
        return False
    
    def can_undo(self) -> bool:
        """Verifica si se puede deshacer"""
        return self.current_index > 0
    
    def can_redo(self) -> bool:
        """Verifica si se puede rehacer"""
        return self.current_index < len(self.state_history) - 1
    
    def clear_history(self):
        """Limpia el historial de estados"""
        self.state_history.clear()
        self.current_index = -1
    
    def _restore_state(self, game_engine, state_data) -> bool:
        """Restaura un estado guardado"""
        try:
            # Restaurar posición del jugador
            game_engine.player.x, game_engine.player.y = state_data["player_position"]
            
            # Restaurar stats del jugador
            game_engine.player.stamina = state_data["player_stamina"]
            game_engine.player.reputation = state_data["player_reputation"]
            
            # Restaurar inventario (esto es más complejo, necesitaría reconstruir las órdenes)
            # Por simplicidad, solo restauramos las básicas por ahora
            
            # Restaurar ganancias
            game_engine.game_state.total_earnings = state_data["total_earnings"]
            
            # Restaurar tiempo de juego
            game_engine.game_time.elapsed_time_sec = state_data["game_time"]
            
            return True
            
        except Exception as e:
            print(f"Error al restaurar estado: {e}")
            return False
    
    def _serialize_inventory(self, inventory):
        """Serialización simple del inventario para undo/redo"""
        return [order.id for order in inventory]
    
    def _serialize_order_list_simple(self, order_list):
        """Serialización simple de lista de órdenes"""
        return [order.id for order in order_list]
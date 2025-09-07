# undo_stack.py
from collections import deque
from datetime import datetime
import copy

class GameStateSnapshot:
    """Snapshot del estado del juego para undo/redo"""
    
    def __init__(self, player_pos, player_stats, earnings, inventory_ids, timestamp=None):
        self.player_pos = player_pos  # (grid_x, grid_y)
        self.player_stats = player_stats  # {'stamina': x, 'reputation': y, 'weight': z}
        self.earnings = earnings
        self.inventory_ids = inventory_ids[:]  # Lista de IDs de órdenes en inventario
        self.timestamp = timestamp or datetime.now()
    
    def __str__(self):
        return f"Snapshot({self.player_pos}, ${self.earnings}, {len(self.inventory_ids)} orders)"

class UndoStack:
    """Stack (LIFO) para manejar operaciones de undo/redo usando deque"""
    
    def __init__(self, max_size=10):
        self.max_size = max_size
        self._undo_stack = deque(maxlen=max_size)  # Stack principal
        self._redo_stack = deque(maxlen=max_size)  # Stack para redo
        self._operation_count = 0
    
    def push_state(self, snapshot):
        """
        Empuja un nuevo estado al stack (LIFO)
        Complejidad: O(1)
        """
        self._undo_stack.append(snapshot)
        
        # Limpiar redo stack cuando se hace una nueva acción
        self._redo_stack.clear()
        
        self._operation_count += 1
        
        print(f"Estado guardado: {snapshot} (Total: {len(self._undo_stack)})")
    
    def pop_for_undo(self):
        """
        Saca el último estado del stack para deshacer (LIFO)
        Complejidad: O(1)
        """
        if len(self._undo_stack) > 1:  # Mantener al menos 1 estado
            current_state = self._undo_stack.pop()
            self._redo_stack.append(current_state)  # Mover a redo stack
            
            # Retornar el estado anterior
            previous_state = self._undo_stack[-1]
            print(f"Undo: Regresando a {previous_state}")
            return previous_state
        
        print("No hay más estados para deshacer")
        return None
    
    def pop_for_redo(self):
        """
        Saca un estado del redo stack para rehacer
        Complejidad: O(1)
        """
        if self._redo_stack:
            state_to_restore = self._redo_stack.pop()
            self._undo_stack.append(state_to_restore)
            print(f"Redo: Restaurando {state_to_restore}")
            return state_to_restore
        
        print("No hay estados para rehacer")
        return None
    
    def can_undo(self):
        """Verifica si se puede deshacer"""
        return len(self._undo_stack) > 1
    
    def can_redo(self):
        """Verifica si se puede rehacer"""
        return len(self._redo_stack) > 0
    
    def peek_top(self):
        """Ve el estado actual sin sacarlo del stack"""
        return self._undo_stack[-1] if self._undo_stack else None
    
    def clear(self):
        """Limpia todos los stacks"""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._operation_count = 0
    
    def size(self):
        """Retorna el tamaño del undo stack"""
        return len(self._undo_stack)
    
    def get_stack_info(self):
        """Retorna información del stack para debugging"""
        return {
            "undo_size": len(self._undo_stack),
            "redo_size": len(self._redo_stack),
            "total_operations": self._operation_count,
            "can_undo": self.can_undo(),
            "can_redo": self.can_redo()
        }

class UndoRedoManager:
    """Manager que integra el UndoStack con el juego"""
    
    def __init__(self, max_states=10):
        self.undo_stack = UndoStack(max_states)
        self.last_save_time = 0
        self.save_interval = 1.0  # Guardar estado cada 1 segundo mínimo
    
    def should_save_state(self, current_time):
        """Determina si debería guardar el estado actual"""
        return (current_time - self.last_save_time) > self.save_interval
    
    def save_game_state(self, game_engine, force=False):
        """
        Captura y guarda el estado actual del juego
        """
        current_time = datetime.now().timestamp()
        
        if not force and not self.should_save_state(current_time):
            return False
        
        try:
            # Capturar posición del jugador
            player_pos = (game_engine.player.grid_x, game_engine.player.grid_y)
            
            # Capturar stats del jugador
            player_stats = {
                'stamina': game_engine.player.stamina,
                'reputation': game_engine.player.reputation,
                'current_weight': game_engine.player.current_weight,
                'state': game_engine.player.state
            }
            
            # Capturar earnings
            earnings = game_engine.game_state.total_earnings
            
            # Capturar IDs del inventario
            inventory_ids = [order.id for order in game_engine.player.inventory]
            
            # Crear snapshot
            snapshot = GameStateSnapshot(
                player_pos=player_pos,
                player_stats=player_stats,
                earnings=earnings,
                inventory_ids=inventory_ids
            )
            
            # Guardar en stack
            self.undo_stack.push_state(snapshot)
            self.last_save_time = current_time
            
            return True
            
        except Exception as e:
            print(f"Error al guardar estado para undo: {e}")
            return False
    
    def undo_last_action(self, game_engine):
        """
        Deshace la última acción
        """
        snapshot = self.undo_stack.pop_for_undo()
        if snapshot:
            return self._restore_snapshot(game_engine, snapshot)
        return False
    
    def redo_last_action(self, game_engine):
        """
        Rehace la última acción deshecha
        """
        snapshot = self.undo_stack.pop_for_redo()
        if snapshot:
            return self._restore_snapshot(game_engine, snapshot)
        return False
    
    def _restore_snapshot(self, game_engine, snapshot):
        """
        Restaura un snapshot al estado del juego
        """
        try:
            # Restaurar posición del jugador
            game_engine.player.grid_x, game_engine.player.grid_y = snapshot.player_pos
            game_engine.player.visual_x = float(game_engine.player.grid_x)
            game_engine.player.visual_y = float(game_engine.player.grid_y)
            game_engine.player.is_moving = False
            
            # Restaurar stats del jugador
            game_engine.player.stamina = snapshot.player_stats['stamina']
            game_engine.player.reputation = snapshot.player_stats['reputation']
            game_engine.player.current_weight = snapshot.player_stats['current_weight']
            game_engine.player.state = snapshot.player_stats['state']
            
            # Restaurar earnings
            game_engine.game_state.total_earnings = snapshot.earnings
            
            # Restaurar inventario (simplificado - solo limpiar por ahora)
            # En una implementación completa, reconstruirías las órdenes
            if len(snapshot.inventory_ids) != len(game_engine.player.inventory):
                print(f"Nota: Inventario cambió de {len(game_engine.player.inventory)} a {len(snapshot.inventory_ids)} items")
            
            return True
            
        except Exception as e:
            print(f"Error al restaurar snapshot: {e}")
            return False
    
    def get_undo_info(self):
        """Información para mostrar en UI"""
        return self.undo_stack.get_stack_info()
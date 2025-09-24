# game_state.py
import json
import os
from datetime import datetime

class GameState:
    """Gestor del estado global del juego"""
    
    def __init__(self):
        self.total_earnings = 0
        self.income_goal = 3000
        self.game_over = False
        self.victory = False
        self.game_over_reason = ""
        
        # Estadísticas del juego
        self.orders_completed = 0
        self.orders_cancelled = 0
        self.perfect_deliveries = 0  # Entregas a tiempo sin penalización
        self.late_deliveries = 0
        
        # Racha de entregas perfectas
        self.current_streak = 0
        self.best_streak = 0
        
        # Tiempo de juego
        self.start_time = datetime.now()
        self.end_time = None
    
    def set_income_goal(self, goal):
        """Establece la meta de ingresos"""
        self.income_goal = goal
    
    def add_earnings(self, amount):
        """Añade ganancias al total"""
        self.total_earnings += amount
    
    def complete_order(self, order, on_time=True, early=False):
        """Registra la finalización de un pedido"""
        self.orders_completed += 1
        
        if on_time and not early:
            self.perfect_deliveries += 1
            self.current_streak += 1
            self.best_streak = max(self.best_streak, self.current_streak)
        elif early:
            self.perfect_deliveries += 1
            self.current_streak += 1
            self.best_streak = max(self.best_streak, self.current_streak)
        else:
            self.late_deliveries += 1
            self.current_streak = 0
    
    def cancel_order(self):
        """Registra la cancelación de un pedido"""
        self.orders_cancelled += 1
        self.current_streak = 0
    
    def set_game_over(self, victory, reason):
        """Establece el fin del juego"""
        self.game_over = True
        self.victory = victory
        self.game_over_reason = reason
        self.end_time = datetime.now()
        
        # Guardar puntaje final - NUEVO: Integración con ScoreManager
        #self.save_final_score()
    
    def save_final_score(self):
        """Guarda el puntaje final usando el ScoreManager"""
        try:
            from score_manager import score_manager
            if self.end_time and self.start_time:
                game_duration = (self.end_time - self.start_time).total_seconds()
                score_manager.add_score(self, self.victory, game_duration)
                print("✅ Puntuación guardada en el sistema de récords")
        except Exception as e:
            print(f"❌ Error al guardar puntuación: {e}")
            # Fallback: guardar en archivo local
            self._save_high_score_fallback()
    
    def _save_high_score_fallback(self):
        """Método de respaldo para guardar puntuaciones"""
        try:
            score_data = {
                "score": self.calculate_final_score(),
                "earnings": self.total_earnings,
                "orders_completed": self.orders_completed,
                "orders_cancelled": self.orders_cancelled,
                "best_streak": self.best_streak,
                "victory": self.victory,
                "date": datetime.now().isoformat(),
                "game_duration": (self.end_time - self.start_time).total_seconds() if self.end_time else 0
            }
            
            # Cargar puntajes existentes
            scores = self.load_high_scores()
            scores.append(score_data)
            
            # Ordenar por puntaje (mayor a menor) y mantener top 10
            scores.sort(key=lambda x: x["score"], reverse=True)
            scores = scores[:10]
            
            # Guardar
            os.makedirs("data", exist_ok=True)
            with open("data/puntajes.json", "w", encoding='utf-8') as f:
                json.dump(scores, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error en fallback de guardado: {e}")
    
    def calculate_final_score(self):
        """Calcula el puntaje final del juego"""
        if not self.game_over:
            return 0
        
        # Puntuación base por ganancias
        base_score = self.total_earnings
        
        # Bonus por terminar temprano (si es victoria)
        time_bonus = 0
        if self.victory and self.end_time:
            game_duration = (self.end_time - self.start_time).total_seconds()
            # Bonus si termina en menos del 80% del tiempo
            if game_duration < 15 * 60 * 0.8:  # 12 minutos
                time_bonus = int(self.total_earnings * 0.1)  # 10% bonus
        
        # Bonus por racha perfecta
        streak_bonus = self.best_streak * 50
        
        # Penalizaciones
        cancellation_penalty = self.orders_cancelled * 100
        late_penalty = self.late_deliveries * 25
        
        final_score = base_score + time_bonus + streak_bonus - cancellation_penalty - late_penalty
        return max(0, final_score)
    
    def load_high_scores(self):
        """Carga los puntajes guardados"""
        try:
            with open("data/puntajes.json", "r", encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def get_progress_percentage(self):
        """Retorna el porcentaje de progreso hacia la meta"""
        if self.income_goal == 0:
            return 0
        return min(100, (self.total_earnings / self.income_goal) * 100)
    
    def get_game_stats(self):
        """Retorna estadísticas del juego actual"""
        return {
            "earnings": self.total_earnings,
            "goal": self.income_goal,
            "progress": self.get_progress_percentage(),
            "orders_completed": self.orders_completed,
            "orders_cancelled": self.orders_cancelled,
            "perfect_deliveries": self.perfect_deliveries,
            "late_deliveries": self.late_deliveries,
            "current_streak": self.current_streak,
            "best_streak": self.best_streak,
            "final_score": self.calculate_final_score() if self.game_over else 0
        }
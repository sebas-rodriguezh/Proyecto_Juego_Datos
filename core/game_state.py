import json
import os
from datetime import datetime

class GameState:    

    def __init__(self):
        self.total_earnings = 0
        self.income_goal = 3000
        self.game_over = False
        self.victory = False
        self.game_over_reason = ""
        self.orders_completed = 0
        self.orders_cancelled = 0
        self.perfect_deliveries = 0
        self.late_deliveries = 0
        self.current_streak = 0
        self.best_streak = 0
        
        self.start_time = datetime.now()
        self.end_time = None
        
        self.player = None
        
        self._cached_final_score = None
        self._cached_game_duration = None
    
    def set_player_reference(self, player):
        """Establece referencia al jugador para acceder a la reputación actual"""
        self.player = player
        self._cached_final_score = None
    
    def set_income_goal(self, goal):
        """Establece la meta de ingresos"""
        self.income_goal = goal
    
    def add_earnings(self, amount):
        """Añade ganancias al total"""
        self.total_earnings += amount
        self._cached_final_score = None
    
    def complete_order(self, order, on_time=True, early=False):
        """Registra la finalización de un pedido"""
        self.orders_completed += 1
        
        if on_time and not early:
            self.perfect_deliveries += 1
            self.current_streak += 1
            self.best_streak = max(self.best_streak, self.current_streak)
            print(f"DEBUG STREAK: Entrega a tiempo - racha: {self.current_streak}")
        elif early:
            self.perfect_deliveries += 1
            self.current_streak += 1
            self.best_streak = max(self.best_streak, self.current_streak)
            print(f"DEBUG STREAK: Entrega temprana - racha: {self.current_streak}")
        else:
            self.late_deliveries += 1
            self.current_streak = 0
            print(f"DEBUG STREAK: Entrega tardía - racha rota")
        
        if self.current_streak >= 3:
                # Solo aplicar el bonus una vez por cada racha de 3
                if self.current_streak % 3 == 0:
                    reputation_bonus = 2
                    old_reputation = getattr(self.player, 'reputation', 70)
                    if hasattr(self.player, 'reputation'):
                        self.player.reputation = min(100, self.player.reputation + reputation_bonus)
                        print(f"🏆 BONUS DE RACHA: +{reputation_bonus} reputación por racha de {self.current_streak} entregas perfectas")
                        print(f"   Reputación: {old_reputation} → {self.player.reputation}")        

        self._cached_final_score = None
    
    def cancel_order(self):
        """Registra la cancelación de un pedido"""
        self.orders_cancelled += 1
        self.current_streak = 0
        self._cached_final_score = None
    
    def set_game_over(self, victory, reason):
        """Establece el fin del juego"""
        self.game_over = True
        self.victory = victory
        self.game_over_reason = reason
        self.end_time = datetime.now()
        self._cached_final_score = None
    
    def calculate_final_score(self, game_duration, total_game_duration=900):
        """Calcula el puntaje final SEGÚN ESPECIFICACIONES DEL PROYECTO"""
        if not self.game_over or not self.player:
            return 0
        
        if (self._cached_final_score is not None and 
            self._cached_game_duration == game_duration):
            return self._cached_final_score
        
        print(f"CALCULANDO PUNTAJE FINAL:")
        print(f"   - Reputación final: {self.player.reputation}")
        print(f"   - Ganancias totales: ${self.total_earnings}")
        print(f"   - Duración del juego: {game_duration:.1f}s de {total_game_duration}s")
        
        # 1. SCORE_BASE = suma de pagos * pay_mult (por reputación alta)
        pay_mult = 1.05 if self.player.reputation >= 90 else 1.0
        base_score = self.total_earnings * pay_mult
        
        print(f"   - Multiplicador por reputación alta (≥90): {pay_mult}")
        print(f"   - Score base: ${base_score}")
        
        # 2. BONUS_TIEMPO = +X si terminas antes del 20% del tiempo restante
        time_bonus = 0
        if self.victory and game_duration < total_game_duration * 0.8:
            time_bonus = int(self.total_earnings * 0.1)
            print(f"   - Bonus por terminar temprano: +${time_bonus}")
        
        # 3. PENALIZACIONES = -Y por cancelaciones
        cancellation_penalty = self.orders_cancelled * 100
        late_penalty = self.late_deliveries * 25
        
        print(f"   - Penalización por {self.orders_cancelled} cancelaciones: -${cancellation_penalty}")
        print(f"   - Penalización por {self.late_deliveries} entregas tardías: -${late_penalty}")
        
        # Cálculo final
        final_score = base_score + time_bonus - cancellation_penalty - late_penalty
        final_score = max(0, int(final_score))
        
        print(f"   - PUNTAJE FINAL: ${final_score}")
        
        self._cached_final_score = final_score
        self._cached_game_duration = game_duration
        
        return final_score
    
    def get_progress_percentage(self):
        """Retorna el porcentaje de progreso hacia la meta"""
        if self.income_goal == 0:
            return 0
        return min(100, (self.total_earnings / self.income_goal) * 100)
    
    def get_game_stats(self, game_duration=0):
        """Retorna estadísticas del juego actual SIN calcular puntaje repetidamente"""
        stats = {
            "earnings": self.total_earnings,
            "goal": self.income_goal,
            "progress": self.get_progress_percentage(),
            "orders_completed": self.orders_completed,
            "orders_cancelled": self.orders_cancelled,
            "perfect_deliveries": self.perfect_deliveries,
            "late_deliveries": self.late_deliveries,
            "current_streak": self.current_streak,
            "best_streak": self.best_streak,
            "victory": self.victory,
            "game_over_reason": self.game_over_reason,
            "final_reputation": self.player.reputation if self.player else 0
        }
        
        if self.game_over:
            if self._cached_final_score is not None:
                stats["final_score"] = self._cached_final_score
            else:
                stats["final_score"] = self.calculate_final_score(game_duration)
        else:
            stats["final_score"] = 0
            
        return stats
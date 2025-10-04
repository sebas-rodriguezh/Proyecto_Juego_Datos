from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List

@dataclass
class Order:
    id: str
    pickup: List[int]
    dropoff: List[int]
    payout: float
    deadline: datetime
    weight: int
    priority: int
    release_time: int
    color: tuple = field(default_factory=lambda: (100, 100, 255))
    
    # Campos para gestión de estados
    is_expired: bool = field(default=False, init=False)
    is_completed: bool = field(default=False, init=False)
    is_in_inventory: bool = field(default=False, init=False)
    accepted_time: datetime = field(default=None, init=False)


    @classmethod
    def from_dict(cls, data: dict):
        deadline_str = data['deadline']
        
        if deadline_str.endswith('Z'):
            deadline_str = deadline_str[:-1] 
        
        # Completar formato si es necesario
        if len(deadline_str) == 16:  # "2025-09-01T12:10"
            deadline_str += ":00"     # "2025-09-01T12:10:00"
        
        try:
            deadline = datetime.fromisoformat(deadline_str)
        except Exception as e:
            print(f"❌ ERROR PARSING DEADLINE: {e}")
            deadline = datetime.now() + timedelta(minutes=15)
        
        return cls(
            id=data['id'],
            pickup=data['pickup'],
            dropoff=data['dropoff'],
            payout=data['payout'],
            deadline=deadline,
            weight=data['weight'],
            priority=data['priority'],
            release_time=data['release_time']
        )
    def _normalize_times_for_comparison(self, current_time):
        """CORREGIDO: Normaliza fechas para comparación consistente usando solo la fecha del juego"""
        if not isinstance(current_time, datetime) or not isinstance(self.deadline, datetime):
            return current_time, self.deadline
        
        # Usar SOLO la fecha del current_time (que viene del juego)
        game_date = current_time.date()
        
        # Normalizar deadline para usar la misma fecha pero mantener su hora original
        normalized_deadline = self.deadline.replace(
            year=game_date.year,
            month=game_date.month,
            day=game_date.day
        )
        return current_time, normalized_deadline
    
    
    
    def check_expiration(self, current_time: datetime) -> bool:
        """Verifica si el pedido ha expirado - VERSIÓN CORREGIDA"""
        if self.is_completed or self.is_expired:
            return self.is_expired
        
        # Normalizar fechas para comparación
        normalized_current, normalized_deadline = self._normalize_times_for_comparison(current_time)
        
        # Expirar EXACTAMENTE en el deadline
        if normalized_current >= normalized_deadline:
            self.is_expired = True
            print(f"Pedido {self.id} EXPIRÓ")
            print(f"   Deadline: {normalized_deadline.strftime('%H:%M:%S')}")
            print(f"   Hora actual: {normalized_current.strftime('%H:%M:%S')}")
            return True
        
        return False
    
    def get_time_remaining(self, current_time: datetime) -> float:
        """Retorna el tiempo restante en segundos - VERSIÓN CORREGIDA"""
        if self.is_expired or self.is_completed:
            return 0
        
        # Normalizar fechas para usar misma fecha
        normalized_current, normalized_deadline = self._normalize_times_for_comparison(current_time)
        
        # Calcular diferencia
        delta = normalized_deadline - normalized_current
        remaining_seconds = delta.total_seconds()
    
        
        return max(0, remaining_seconds)
    
    def get_delivery_timeliness(self, current_time: datetime) -> str:
        """Determina la puntualidad de la entrega - VERSIÓN MEJORADA"""
        if self.is_completed:
            return "completed"
        if self.is_expired:
            return "expired"
        
        time_remaining = self.get_time_remaining(current_time)
        
        # Calcular porcentaje de tiempo usado basado en tiempo total disponible
        if self.accepted_time:
            normalized_current, _ = self._normalize_times_for_comparison(current_time)
            normalized_accepted = self.accepted_time.replace(
                year=normalized_current.year,
                month=normalized_current.month,
                day=normalized_current.day
            )
            total_available_time = (self.deadline.replace(
                year=normalized_current.year,
                month=normalized_current.month,
                day=normalized_current.day
            ) - normalized_accepted).total_seconds()
            
            if total_available_time > 0:
                time_used = total_available_time - time_remaining
                percentage_used = (time_used / total_available_time) * 100
            else:
                percentage_used = 100
        else:
            total_available_time = 900  
            time_used = total_available_time - time_remaining
            percentage_used = (time_used / total_available_time) * 100
        
        # Categorizar
        if percentage_used <= 50:  # Usó ≤50% del tiempo, este puede ser 20 profe, pero la verdad es que no es muy funcional, además para efectos prácticos, mejor este. 
            return "early"
        elif time_remaining > 120:  # Más de 2 minutos restantes
            return "on_time"
        elif time_remaining > 30:   # 31-120 segundos 
            return "late_120"
        elif time_remaining > 0:    # 1-30 segundos 
            return "late_30"
        else:                       # 0 segundos o menos 
            return "very_late"
    
    def calculate_reputation_change(self, current_time: datetime) -> int:
        """Calcula el cambio de reputación según especificaciones del proyecto"""
        timeliness = self.get_delivery_timeliness(current_time)
        time_remaining = self.get_time_remaining(current_time)
        
        print(f"🔍 REPUTACIÓN {self.id}: {timeliness}, {time_remaining:.0f}s restantes")
        
        if timeliness == "early":
            print("   +5 reputación (entrega temprana)")
            return 5
        elif timeliness == "on_time":
            print("   +3 reputación (a tiempo)")
            return 3
        elif timeliness == "late_120":
            print("   -5 reputación (31-120s tarde)")
            return -5
        elif timeliness == "late_30":
            print("   -2 reputación (1-30s tarde)")
            return -2
        elif timeliness == "very_late":
            print("   -10 reputación (>120s tarde)")
            return -10
        
        return 0
    

    def calculate_payout_modifier(self, current_time: datetime, player_reputation: int) -> float:
        """Calcula modificadores de pago según especificaciones"""
        modifier = 1.0
        timeliness = self.get_delivery_timeliness(current_time)
        
        # Penalización por entrega tardía según especificaciones del proyecto
        if timeliness == "late_30":
            modifier *= 0.95   # -5% por tardanza leve
        elif timeliness == "late_120":
            modifier *= 0.90   # -10% por tardanza moderada
        elif timeliness == "very_late":
            modifier *= 0.80   # -20% por tardanza severa
        
        # Bonus por reputación alta (≥90)
        if player_reputation >= 90:
            modifier *= 1.05  # +5% bonus
        
        return modifier
    
    # Métodos existentes se mantienen igual
    def mark_as_accepted(self, acceptance_time: datetime):
        self.accepted_time = acceptance_time
    
    def mark_as_completed(self):
        self.is_completed = True
        self.is_in_inventory = False
    
    def mark_as_picked_up(self):
        self.is_in_inventory = True
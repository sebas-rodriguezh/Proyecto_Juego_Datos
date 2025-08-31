from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass
class Pedido:
    id: str
    pickup: List[int]
    dropoff: List[int]
    payout: float
    deadline: datetime
    weight: int
    priority: int
    release_time: int
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data['id'],
            pickup=data['pickup'],
            dropoff=data['dropoff'],
            payout=data['payout'],
            deadline=datetime.fromisoformat(data['deadline']),
            weight=data['weight'],
            priority=data['priority'],
            release_time=data['release_time']
        )
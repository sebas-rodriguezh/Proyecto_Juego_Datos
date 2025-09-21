from dataclasses import dataclass, field
from datetime import datetime
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
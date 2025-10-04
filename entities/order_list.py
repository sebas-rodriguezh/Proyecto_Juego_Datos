from collections.abc import Iterator
from entities.order import Order
from collections import deque
from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from api.api_manager import APIManager
import requests


@dataclass
class OrderList:
    """Cola (Queue) especializada para manejar objetos Order - FIFO (First In, First Out)"""
    _orders: deque = field(default_factory=deque, init=False)
    
    def enqueue(self, order: Order) -> None:
        """Añade una orden al final de la cola"""
        self._orders.append(order)
    
    def enqueue_priority(self, order: Order) -> None:
        """Añade una orden al inicio de la cola (para casos de alta prioridad)"""
        self._orders.appendleft(order)
    
    def dequeue(self) -> Order:
        """Remueve y retorna la primera orden de la cola (FIFO)"""
        if self.is_empty():
            raise IndexError("Dequeue from empty OrderList")
        return self._orders.popleft()
    
    def front(self) -> Order:
        """Retorna la primera orden de la cola sin removerla"""
        if self.is_empty():
            raise IndexError("Front from empty OrderList")
        return self._orders[0]
    
    def rear(self) -> Order:
        """Retorna la última orden de la cola sin removerla"""
        if self.is_empty():
            raise IndexError("Rear from empty OrderList")
        return self._orders[-1]
    
    def is_empty(self) -> bool:
        """Verifica si la cola está vacía"""
        return len(self._orders) == 0
    
    def size(self) -> int:
        """Retorna el número de órdenes en la cola"""
        return len(self._orders)
    
    def clear(self) -> None:
        """Limpia toda la cola"""
        self._orders.clear()
    
    def find_by_id(self, order_id: str) -> Optional[Order]: # O(n)
        """Busca una orden por su ID"""
        for order in self._orders:
            if order.id == order_id:
                return order
        return None
    

    def remove_by_id(self, order_id: str) -> bool: # O(n)
        """Remueve una orden por su ID manteniendo la estructura de cola"""
        new_orders = deque()
        removed = False
        for order in self._orders:
            if order.id == order_id and not removed:
                removed = True
                continue
            new_orders.append(order)
        
        self._orders = new_orders
        return removed

    def get_highest_priority(self) -> int: # O(n)
        """Obtiene la prioridad más alta de todas las órdenes"""
        if self.is_empty():
            return -1
        return max(order.priority for order in self._orders)

    def filter_by_priority(self, priority: int) -> List[Order]: # O(n)
        """Filtra órdenes por nivel de prioridad"""
        return [order for order in self._orders if order.priority == priority]
    
    def get_high_priority_orders(self) -> List[Order]:
        """Obtiene todas las órdenes con la prioridad más alta"""
        if self.is_empty():
            return []
        val = self.get_highest_priority()
        return self.filter_by_priority(val)
    
    def get_normal_priority_orders(self) -> List[Order]:
        """Retorna todas las órdenes de prioridad normal (priority = 0)"""
        return self.filter_by_priority(0)
    
    def to_list(self) -> List[Order]:
        """Convierte la OrderList a una lista Python"""
        return list(self._orders)
    
    def _insertion_sort_by_priority(self, arr: List[Order]) -> List[Order]: # O(n^2)
        """Ordena una lista de órdenes por prioridad usando Insertion Sort (mayor prioridad primero)"""
        for i in range(1, len(arr)):
            key = arr[i]
            j = i - 1
            
            while j >= 0 and arr[j].priority < key.priority:
                arr[j + 1] = arr[j]
                j -= 1
            arr[j + 1] = key
            
        return arr
    
    def _insertion_sort_by_payout(self, arr: List[Order]) -> List[Order]: # O(n^2)
        """Ordena una lista de órdenes por payout usando Insertion Sort (mayor payout primero)"""
        for i in range(1, len(arr)):
            key = arr[i]
            j = i - 1
            
            while j >= 0 and arr[j].payout < key.payout:
                arr[j + 1] = arr[j]
                j -= 1
            arr[j + 1] = key
            
        return arr
    
    def _insertion_sort_by_deadline(self, arr: List[Order]) -> List[Order]: # O(n^2)
        """Ordena una lista de órdenes por deadline usando Insertion Sort (fechas más cercanas primero)"""
        for i in range(1, len(arr)):
            key = arr[i]
            j = i - 1
            
            while j >= 0 and arr[j].deadline > key.deadline:
                arr[j + 1] = arr[j]
                j -= 1
            arr[j + 1] = key
            
        return arr
    
    def reorganize_by_priority(self) -> None: # O(n^2)
        """Reorganiza la cola poniendo las órdenes de mayor prioridad al frente usando Insertion Sort"""
        if self.is_empty():
            return
        orders_list = list(self._orders)
        sorted_orders = self._insertion_sort_by_priority(orders_list)
        self._orders = deque(sorted_orders)
    
    def reorganize_by_payout(self) -> None: # O(n^2)
        """Reorganiza la cola poniendo las órdenes de mayor payout al frente usando Insertion Sort"""
        if self.is_empty():
            return
        orders_list = list(self._orders)
        sorted_orders = self._insertion_sort_by_payout(orders_list)
        self._orders = deque(sorted_orders)
    
    def reorganize_by_deadline(self) -> None: # O(n^2)
        """Reorganiza la cola poniendo las órdenes más urgentes (deadline cercano) al frente usando Insertion Sort"""
        if self.is_empty():
            return
        orders_list = list(self._orders)
        sorted_orders = self._insertion_sort_by_deadline(orders_list)
        self._orders = deque(sorted_orders)
    
    def get_next_orders(self, count: int) -> List[Order]:
        """Obtiene los próximos 'count' órdenes sin removerlas de la cola"""
        if count <= 0:
            return []
        return [self._orders[i] for i in range(min(count, len(self._orders)))]
    
    def process_batch(self, count: int) -> List[Order]:
        """Remueve y retorna un lote de órdenes de la cola"""
        batch = []
        for _ in range(min(count, len(self._orders))):
            if not self.is_empty():
                batch.append(self.dequeue())
        return batch
    
    @classmethod
    def from_api_response(cls, api_response: dict) -> 'OrderList': # O(n)
        """Crea una OrderList directamente desde la respuesta de la API - CORREGIDO"""
        order_list = cls()
        
        job_colors = [
            (255, 100, 100), (100, 100, 255), (255, 255, 100),
            (255, 100, 255), (100, 255, 255)
        ]
        

        for i, order_data in enumerate(api_response['data']):
            order = Order.from_dict(order_data)
            color_index = i % len(job_colors)
            order.color = job_colors[color_index]
            order_list.enqueue(order)
        
        return order_list
    
    @classmethod
    def from_list(cls, orders: List[Order]) -> 'OrderList': # O(n)
        """Crea una OrderList desde una lista de Orders existente"""
        order_list = cls()
        for order in orders:
            order_list.enqueue(order)
        return order_list
    
    @classmethod
    def create_empty(cls) -> 'OrderList':
        """Crea una OrderList vacía"""
        return cls()
    
    # Métodos especiales
    def append(self, order: Order) -> None:
        """Alias para enqueue para compatibilidad con código existente"""
        self.enqueue(order)

    def __bool__(self) -> bool:
        """Permite evaluar la OrderList como booleano (verificar si está vacía)"""
        return not self.is_empty()
    
    def __iter__(self) -> Iterator[Order]:
        """Iterador sobre las órdenes (desde el frente hasta atrás)"""
        return iter(self._orders)
    
    def __len__(self) -> int:
        """Permite usar len(order_list)"""
        return len(self._orders)
    
    def __contains__(self, order_id: str) -> bool:
        """Permite usar 'in' operator: 'REQ-001' in order_list"""
        return self.find_by_id(order_id) is not None
    
    def __getitem__(self, index: int) -> Order:
        """Permite indexación: order_list[0] (orden al frente de la cola)"""
        return list(self._orders)[index]
    
    def __str__(self) -> str:
        """Representación string de la cola"""
        order_ids = [order.id for order in self._orders]
        return f"OrderQueue({len(self._orders)} orders: {order_ids})"
    
    def __repr__(self) -> str:
        """Representación para debugging"""
        return f"OrderQueue(orders={list(self._orders)})"


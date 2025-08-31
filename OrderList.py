from collections.abc import Iterator
from Order import Order
from collections import deque
from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from api_manager import APIManager
import requests


@dataclass
class OrderList:
    """Clase especializada para manejar listas de objetos Order"""
    _orders: deque = field(default_factory=deque, init=False)
    
    def append(self, order: Order) -> None:
        """Añade una orden al final de la lista"""
        self._orders.append(order)
    
    def append_left(self, order: Order) -> None:
        """Añade una orden al inicio de la lista"""
        self._orders.appendleft(order)
    
    def pop(self) -> Order:
        """Remueve y retorna la última orden"""
        if self.is_empty():
            raise IndexError("Pop from empty OrderList")
        return self._orders.pop()
    
    def dequeue(self) -> Order:
        """Remueve y retorna la primera orden"""
        if self.is_empty():
            raise IndexError("Pop from empty OrderList")
        return self._orders.popleft()
    
    def peek(self) -> Order:
        """Retorna la última orden sin removerla"""
        if self.is_empty():
            raise IndexError("Peek from empty OrderList")
        return self._orders[-1]
    
    def peek_left(self) -> Order:
        """Retorna la primera orden sin removerla"""
        if self.is_empty():
            raise IndexError("Peek from empty OrderList")
        return self._orders[0]
    
    def is_empty(self) -> bool:
        """Verifica si la lista está vacía"""
        return len(self._orders) == 0
    
    def size(self) -> int:
        """Retorna el número de órdenes en la lista"""
        return len(self._orders)
    
    def clear(self) -> None:
        """Limpia toda la lista"""
        self._orders.clear()
    
    def find_by_id(self, order_id: str) -> Optional[Order]:
        """Busca una orden por su ID"""
        for order in self._orders:
            if order.id == order_id:
                return order
        return None
    
    def remove_by_id(self, order_id: str) -> bool:
        """Remueve una orden por su ID"""
        for i, order in enumerate(self._orders):
            if order.id == order_id:
                del self._orders[i]
                return True
        return False
    
    def get_highest_priority(self) -> int:
        """Obtiene la prioridad más alta de todas las órdenes"""
        if self.is_empty():
            return -1
        return max(order.priority for order in self._orders)

    def filter_by_priority(self, priority: int) -> List[Order]:
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
    
    def sort_by_payout(self, reverse: bool = False) -> None:
        """Ordena las órdenes por payout (mayor a menor por defecto)"""
        self._orders = deque(sorted(self._orders, key=lambda x: x.payout, reverse=not reverse))
    
    def sort_by_priority(self, reverse: bool = False) -> None:
        """Ordena las órdenes por prioridad (mayor a menor por defecto)"""
        if self.is_empty():
            return
        # Ordenar usando la prioridad de cada orden
        self._orders = deque(sorted(self._orders, key=lambda order: order.priority, reverse=not reverse))

    def get_sorted_by_priority(self, reverse: bool = False) -> List[Order]:
        """Devuelve una lista ordenada por prioridad sin modificar la original"""
        if self.is_empty():
            return []
        return sorted(self._orders, 
                    key=lambda order: order.priority, 
                    reverse=not reverse)
        
    def sort_by_deadline(self, reverse: bool = False) -> None:
        """Ordena las órdenes por deadline (más cercano primero por defecto)"""
        self._orders = deque(sorted(self._orders, key=lambda x: x.deadline, reverse=reverse))
    
    @classmethod
    def from_api_response(cls, api_response: dict) -> 'OrderList':
        """Crea una OrderList directamente desde la respuesta de la API"""
        order_list = cls()
        
        # Procesar cada orden de la respuesta de la API
        for order_data in api_response['data']:
            # Convertir el string de deadline a datetime si es necesario
            if isinstance(order_data['deadline'], str):
                try:
                    deadline = datetime.strptime(order_data['deadline'], '%Y-%m-%dT%H:%M')
                except ValueError:
                    # Si falla el parsing, usar datetime actual como fallback
                    deadline = datetime.now()
            else:
                deadline = order_data['deadline']
            
            # Crear la orden
            order = Order(
                id=order_data['id'],
                pickup=order_data['pickup'],
                dropoff=order_data['dropoff'],
                payout=order_data['payout'],
                deadline=deadline,
                weight=order_data['weight'],
                priority=order_data['priority'],
                release_time=order_data['release_time']
            )
            order_list.append(order)
        
        return order_list
    
    @classmethod
    def from_list(cls, orders: List[Order]) -> 'OrderList':
        """Crea una OrderList desde una lista de Orders existente"""
        order_list = cls()
        for order in orders:
            order_list.append(order)
        return order_list
    
    @classmethod
    def create_empty(cls) -> 'OrderList':
        """Crea una OrderList vacía"""
        return cls()
    
    # Métodos especiales
    def __iter__(self) -> Iterator[Order]:
        """Iterador sobre las órdenes"""
        return iter(self._orders)
    
    def __len__(self) -> int:
        """Permite usar len(order_list)"""
        return len(self._orders)
    
    def __contains__(self, order_id: str) -> bool:
        """Permite usar 'in' operator: 'REQ-001' in order_list"""
        return self.find_by_id(order_id) is not None
    
    def __getitem__(self, index: int) -> Order:
        """Permite indexación: order_list[0]"""
        return list(self._orders)[index]
    
    def __str__(self) -> str:
        """Representación string de la lista"""
        order_ids = [order.id for order in self._orders]
        return f"OrderList({len(self._orders)} orders: {order_ids})"
    
    def __repr__(self) -> str:
        """Representación para debugging"""
        return f"OrderList(orders={list(self._orders)})"
    

def probar_metodos_simples():

    # 9. Probar from_api_response con datos simulados
    print("---------Prueba from_api_response---------")
    
    # Simular respuesta de API

    data3 = APIManager()

    lista_desde_api = OrderList.from_api_response(data3.get_jobs())

    #print([o for o in lista_desde_api])

    lista_desde_api.sort_by_priority()
    print("  " 
    "" 
    "")

    print(lista_desde_api.peek_left())
    print("Pedido entregado...")
    lista_desde_api.dequeue()
    print("Pedido a entregar:")
    print(lista_desde_api.peek_left())
    print("Pedido entregado...")
    lista_desde_api.dequeue()
    print("Pedido a entregar:")
    print(lista_desde_api.peek_left())
    print("Pedido entregado...")
    lista_desde_api.dequeue()
    print("Pedido a entregar:")
    print(lista_desde_api.peek_left())
    print("Pedido entregado...")
    lista_desde_api.dequeue()
    print("Pedido a entregar:")
    print(lista_desde_api.peek_left())

# Ejecutar pruebas simples
if __name__ == "__main__":
    probar_metodos_simples()


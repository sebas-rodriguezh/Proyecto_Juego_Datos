from collections.abc import Iterator
from Order import Order
from collections import deque
from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta


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
    
    def pop_left(self) -> Order:
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
    
    def get_highest_priority (self) -> int:
        if self.is_empty():
            return -1
        return max(order.priority for order in self._orders)

    def filter_by_priority(self, priority: int) -> List[Order]:
        """Filtra órdenes por nivel de prioridad"""
        return [order for order in self._orders if order.priority == priority]
    
    def get_high_priority_orders(self) -> List[Order]:
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
        orders = orders.from_list(api_response['data'])
        for order in orders:
            order_list.append(order)
        return order_list
    
    @classmethod
    def from_orders(cls, orders: List[Order]) -> 'OrderList':
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
    print("🔧 PROBANDO MÉTODOS BÁSICOS")
    print("=" * 40)
    
    # Crear órdenes simples
    ahora = datetime.now()
    
    order1 = Order("REQ-001", [20, 19], [10, 22], 180.0, 
                  ahora + timedelta(hours=1), 1, 0, 0)
    
    order2 = Order("REQ-002", [27, 24], [4, 6], 260.0, 
                  ahora + timedelta(hours=2), 2, 1, 45)
    
    order3 = Order("REQ-003", [15, 20], [8, 12], 150.0, 
                  ahora + timedelta(hours=3), 1, 0, 30)
    
    order4 = Order("REQ-004", [15, 20], [8, 12], 150.0, 
                  ahora + timedelta(hours=3), 1, 4, 30)
    
    order5 = Order("REQ-005", [15, 20], [8, 12], 150.0, 
                  ahora + timedelta(hours=3), 1, 4, 30)


    # 1. Crear lista
    orders = OrderList()
    print("✅ Lista creada vacía")
    
    # 2. Añadir órdenes
    orders.append(order1)
    orders.append(order2)
    orders.append(order4)
    orders.append(order5)
    orders.append_left(order3)
    print(f"✅ Órdenes añadidas: {orders}")
    
    # 3. Métodos básicos
    print(f"   Tamaño: {len(orders)}")
    print(f"   ¿Vacía?: {orders.is_empty()}")
    print(f"   Primera: {orders.peek_left().id}")
    print(f"   Última: {orders.peek().id}")
    
    # 4. Buscar
    encontrada = orders.find_by_id("REQ-002")
    print(f"   Buscar REQ-002: {encontrada.payout if encontrada else 'No'}")
    
    # 5. Filtrar
    urgentes = orders.get_high_priority_orders()
    print(f"   Urgentes: {[(o.priority, o.id) for o in urgentes]}")
    
    #Probar sorted de lista por prioridad.
    ordersnew = orders.get_sorted_by_priority()
    print(f"Por prioridad: {[o.id for o in ordersnew]}")


    # 6. Remover
    orders.remove_by_id("REQ-001")
    print(f"   REQ-001 removida: {orders}")
    
    # 7. Convertir a lista
    lista_normal = orders.to_list()
    print(f"   Como lista: {[o.id for o in lista_normal]}")
    lista_normal
    print("🎉 ¡Todas las pruebas pasaron!")
    
    #8. from_api_response, crea la lista directamente
    print("---------Prueba from_api_response---------")
    lista_directa = OrderList.from_api_response(orders)
   

    # #9 from_orders, si funciona se puede optimizar para hacer busca por Id...
    # lista_directa2 = OrderList.from_orders(lista_normal)
    # print(lista_directa2)


# Ejecutar pruebas simples
if __name__ == "__main__":
    probar_metodos_simples()


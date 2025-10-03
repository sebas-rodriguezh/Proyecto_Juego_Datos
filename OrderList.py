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
    
    def find_by_id(self, order_id: str) -> Optional[Order]:
        """Busca una orden por su ID"""
        for order in self._orders:
            if order.id == order_id:
                return order
        return None
    
    # def remove_by_id(self, order_id: str) -> bool:
    #     """Remueve una orden por su ID (rompe la estructura de cola, usar con cuidado)"""
    #     for i, order in enumerate(self._orders):
    #         if order.id == order_id:
    #             del self._orders[i]
    #             return True
    #     return False
    
    def remove_by_id(self, order_id: str) -> bool:
        """Remueve una orden por su ID manteniendo la estructura de cola"""
        # Crear una nueva cola sin el elemento a eliminar
        new_orders = deque()
        removed = False
        for order in self._orders:
            if order.id == order_id and not removed:
                removed = True  # Remover solo la primera ocurrencia
                continue
            new_orders.append(order)
        
        self._orders = new_orders
        return removed

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
    
    def reorganize_by_priority(self) -> None:
        """Reorganiza la cola poniendo las órdenes de mayor prioridad al frente"""
        if self.is_empty():
            return
        # Convertir a lista, ordenar por prioridad (mayor primero), y reconstruir deque
        sorted_orders = sorted(self._orders, key=lambda order: order.priority, reverse=True)
        self._orders = deque(sorted_orders)
    
    def reorganize_by_payout(self) -> None:
        """Reorganiza la cola poniendo las órdenes de mayor payout al frente"""
        if self.is_empty():
            return
        sorted_orders = sorted(self._orders, key=lambda order: order.payout, reverse=True)
        self._orders = deque(sorted_orders)
    
    def reorganize_by_deadline(self) -> None:
        """Reorganiza la cola poniendo las órdenes más urgentes (deadline cercano) al frente"""
        if self.is_empty():
            return
        sorted_orders = sorted(self._orders, key=lambda order: order.deadline)
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
    def from_api_response(cls, api_response: dict) -> 'OrderList':
        """Crea una OrderList directamente desde la respuesta de la API - CORREGIDO"""
        order_list = cls()
        
        job_colors = [
            (255, 100, 100), (100, 100, 255), (255, 255, 100),
            (255, 100, 255), (100, 255, 255)
        ]
        
        print(f"📦 PROCESANDO {len(api_response['data'])} PEDIDOS DESDE API:")
        
        for i, order_data in enumerate(api_response['data']):
            print(f"   Pedido {i+1}: {order_data['id']}")
            print(f"     Deadline raw: {order_data['deadline']}")
            
            # Usar el método corregido de Order para crear el pedido
            order = Order.from_dict(order_data)
            
            # Asignar color
            color_index = i % len(job_colors)
            order.color = job_colors[color_index]
            
            order_list.enqueue(order)
            print(f"     ✅ Creado: {order.id} - Deadline: {order.deadline.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return order_list
    @classmethod
    def from_list(cls, orders: List[Order]) -> 'OrderList':
        """Crea una OrderList desde una lista de Orders existente"""
        order_list = cls()
        for order in orders:
            order_list.enqueue(order)  # Usar enqueue en lugar de append
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


def probar_cola_pura():
    """Función de prueba para demostrar el comportamiento de cola pura"""
    
    print("========== Prueba de Cola Pura ==========")
    
    # Crear cola vacía
    cola = OrderList.create_empty()
    print(f"Cola vacía: {cola}")
    print(f"¿Está vacía? {cola.is_empty()}")
    
    # Simular algunas órdenes
    from datetime import datetime
    
    ordenes_prueba = [
        Order("REQ-001", [1, 2], [3, 4], 100.0, datetime.now(), 10, 2, 0),
        Order("REQ-002", [2, 3], [4, 5], 150.0, datetime.now(), 15, 1, 0),
        Order("REQ-003", [3, 4], [5, 6], 200.0, datetime.now(), 20, 3, 0),
        Order("REQ-004", [4, 5], [6, 7], 80.0, datetime.now(), 5, 0, 0),
    ]
    
    # Añadir órdenes a la cola (FIFO)
    print("\n--- Añadiendo órdenes a la cola ---")
    for orden in ordenes_prueba:
        cola.enqueue(orden)
        print(f"Enqueued: {orden.id} (priority: {orden.priority})")
    
    print(f"\nCola después de enqueue: {cola}")
    print(f"Tamaño: {cola.size()}")
    print(f"Frente de la cola: {cola.front().id}")
    print(f"Final de la cola: {cola.rear().id}")
    
    # Procesar órdenes (FIFO)
    print("\n--- Procesando órdenes (FIFO) ---")
    while not cola.is_empty():
        orden_actual = cola.dequeue()
        print(f"Procesando: {orden_actual.id} (priority: {orden_actual.priority})")
    
    print(f"\nCola después de procesar todo: {cola}")
    
    # Probar reorganización por prioridad
    print("\n--- Prueba con reorganización por prioridad ---")
    
    # Volver a llenar la cola
    for orden in ordenes_prueba:
        cola.enqueue(orden)
    
    print("Cola original (orden FIFO):")
    for i, orden in enumerate(cola):
        print(f"  {i}: {orden.id} (priority: {orden.priority})")
    
    # Reorganizar por prioridad
    cola.reorganize_by_priority()
    print("\nDespués de reorganizar por prioridad:")
    for i, orden in enumerate(cola):
        print(f"  {i}: {orden.id} (priority: {orden.priority})")
    
    # Procesar con prioridad
    print("\nProcesando con prioridad:")
    for _ in range(4):
        if not cola.is_empty():
            orden = cola.dequeue()
            print(f"  Procesado: {orden.id} (priority: {orden.priority})")


def demo_api_integration():
    """Demo de integración con API"""
    
    print("\n========== Demo Integración API ==========")
    
    try:
        # Obtener órdenes de la API
        data_manager = APIManager()
        cola_desde_api = OrderList.from_api_response(data_manager.get_jobs())
        
        print(f"Órdenes obtenidas de API: {cola_desde_api.size()}")
        
        # Reorganizar por prioridad para procesamiento eficiente
        cola_desde_api.reorganize_by_priority()
        
        # Procesar las primeras 5 órdenes
        print("\nProcesando primeras 5 órdenes por prioridad:")
        for i in range(min(5, cola_desde_api.size())):
            if not cola_desde_api.is_empty():
                orden = cola_desde_api.dequeue()
                print(f"  {i+1}. {orden.id} - Priority: {orden.priority} - Payout: ${orden.payout}")
        
        print(f"\nÓrdenes restantes en cola: {cola_desde_api.size()}")
        
    except Exception as e:
        print(f"Error en demo API: {e}")


# Ejecutar pruebas
if __name__ == "__main__":
    probar_cola_pura()
    demo_api_integration()
# interaction_manager.py - CORRECCIÓN COMPLETA
import pygame

class InteractionManager:
    """Gestor de interacciones del jugador con el mundo del juego - CON RADIO AMPLIADO"""
    
    def __init__(self, player, active_orders, completed_orders):
        self.player = player
        self.active_orders = active_orders
        self.completed_orders = completed_orders
        
        # Control de interacciones
        self.interaction_cooldown = 0
        self.interaction_message = ""
        self.message_timer = 0
        self.interaction_radius = 7  # Radio ampliado pero razonable
    
    def handle_event(self, event, game_state, game_map=None):
        """Maneja eventos de interacción"""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e and self.interaction_cooldown <= 0:
            self.handle_interaction(game_state, game_map)




    
    def handle_interaction(self, game_state, game_map):
        """Procesa interacciones de recogida y entrega - CON DEBUG DETALLADO Y CORREGIDO"""
        print("=== DEBUG INTERACCIÓN ===")
        print(f"Posición jugador: ({self.player.grid_x}, {self.player.grid_y})")
        
        interactable_orders = self.player.get_interactable_orders(self.active_orders, game_map, self.interaction_radius)
        
        print(f"Órdenes interactuables encontradas: {len(interactable_orders)}")
        
        # Mostrar información detallada de cada orden
        for i, order_info in enumerate(interactable_orders):
            order = order_info['order']
            print(f"{i+1}. {order.id} - {order_info['action']} - "
                f"Loc: {order_info['location']} - "
                f"Exacto: {order_info['is_exact']} - "
                f"Dist: {order_info['distance']} - "
                f"Edificio: {order_info['is_building']}")
        
        if not interactable_orders:
            print("RAZÓN: No hay órdenes cerca o todas están completadas")
            # Mostrar información de las órdenes activas para debugging
            print(f"Órdenes activas totales: {len(self.active_orders)}")
            for i, order in enumerate(self.active_orders):
                print(f"  {i+1}. {order.id} - Pickup: {order.pickup} - Dropoff: {order.dropoff}")
            
            self.show_message("No hay nada que hacer aquí", 2)
            print("=== FIN DEBUG ===")
            return
        
        # Procesar la primera interacción disponible
        interaction = interactable_orders[0]
        order = interaction['order']
        action = interaction['action']
        is_exact = interaction['is_exact']
        distance = interaction['distance']
        is_building = interaction['is_building']
        
        print(f"Procesando: {order.id} - {action} - Distancia: {distance}")
        
        if action == 'dropoff':
            # Entregar pedido - EL PEDIDO ESTÁ EN EL INVENTARIO, NO EN ACTIVE_ORDERS
            if self.player.remove_from_inventory(order.id):
                # Calcular ganancias ANTES de mover a completed_orders
                earnings = self.calculate_earnings(order, distance, is_exact, is_building)
                game_state.add_earnings(earnings)
                self.player.reputation = min(100, self.player.reputation + 5)
                print(f"DEBUG: Reputación aumentada +5. Nueva reputación: {self.player.reputation}")

                # Mover a completed_orders después de calcular ganancias
                self.completed_orders.enqueue(order)
                
                location_text = self.get_location_text(is_exact, distance, is_building)
                self.show_message(f"✓ Entregado {order.id} +${earnings} ({location_text})", 3)
                self.interaction_cooldown = 0.5
                print(f"¡ÉXITO! Entregado {order.id} - Ganancia: ${earnings}")
            else:
                self.show_message("Error: No se pudo encontrar el pedido en inventario", 2)
                print(f"ERROR: No se encontró {order.id} en el inventario del jugador")
        
        elif action == 'pickup':
            # Recoger pedido
            if self.player.can_pickup_order(order):
                if self.player.add_to_inventory(order):
                    # CORRECCIÓN: Eliminar el pedido de active_orders después de recogerlo
                    if self.active_orders.remove_by_id(order.id):
                        location_text = self.get_location_text(is_exact, distance, is_building)
                        self.show_message(f"📦 Recogido {order.id} ({location_text})", 3)
                        self.interaction_cooldown = 0.5
                        print(f"¡ÉXITO! Recogido {order.id}")
                    else:
                        self.show_message("Error al remover pedido de la lista activa", 2)
                        print(f"ERROR: No se pudo remover {order.id} de active_orders")
                else:
                    self.show_message("Error al recoger pedido", 2)
                    print(f"ERROR: No se pudo agregar {order.id} al inventario")
            else:
                self.show_message("¡No tienes capacidad suficiente!", 2)
                print(f"ERROR: Capacidad insuficiente para {order.id}")

        print("=== FIN DEBUG ===")
    



















    def get_location_text(self, is_exact, distance, is_building):
        """Obtiene texto descriptivo de la ubicación - CORREGIDO"""
        if is_exact:
            return "exacta"
        elif is_building and distance <= 1:
            return "desde afuera"
        elif distance == 1:
            return "adyacente"
        else:
            return f"a {distance} casillas"
    
    def calculate_earnings(self, order, distance, is_exact, is_building):
        """Calcula ganancias con posibles penalizaciones por distancia - CORREGIDO"""
        base_payout = order.payout
        
        # Penalización por distancia (solo para entregas no exactas y no edificios)
        if not is_exact and not is_building and distance > 1:
            distance_penalty = 0.1 * (distance - 1)  # 10% por casilla adicional
            base_payout *= max(0.7, 1 - distance_penalty)  # Mínimo 70% del pago
        
        # Penalización por entrega tardía (si el deadline ya pasó)
        from datetime import datetime
        if datetime.now() > order.deadline:
            tardiness_penalty = 0.2  # 20% de penalización
            base_payout *= (1 - tardiness_penalty)
            print(f"DEBUG: Penalización por entrega tardía: -20%")
        
        # Bonus por reputación alta (≥90)
        if self.player.reputation >= 90:
            base_payout *= 1.05
            print(f"DEBUG: Bonus por reputación alta: +5%")
        
        return int(base_payout)
    
    def show_message(self, message, duration=3):
        """Muestra un mensaje de interacción"""
        self.interaction_message = message
        self.message_timer = duration
    
    def update(self, dt):
        """Actualiza el estado del manager"""
        if self.interaction_cooldown > 0:
            self.interaction_cooldown -= dt
        
        if self.message_timer > 0:
            self.message_timer -= dt
        else:
            self.interaction_message = ""
    
    def get_message(self):
        """Retorna el mensaje actual si existe"""
        return self.interaction_message if self.message_timer > 0 else ""
    
    def get_interaction_hint(self, game_map):
        """Obtiene pista de qué se puede hacer en la posición actual - CORREGIDO"""
        interactable_orders = self.player.get_interactable_orders(self.active_orders, game_map, self.interaction_radius)
        
        if not interactable_orders:
            return ""
        
        interaction = interactable_orders[0]
        action = interaction['action']
        is_exact = interaction['is_exact']
        distance = interaction['distance']
        is_building = interaction['is_building']
        order_id = interaction['order'].id
        
        location_text = self.get_location_text(is_exact, distance, is_building)
        
        if action == 'dropoff':
            return f"Presiona E para entregar {order_id} ({location_text})"
        elif action == 'pickup':
            return f"Presiona E para recoger {order_id} ({location_text})"
        
        return ""
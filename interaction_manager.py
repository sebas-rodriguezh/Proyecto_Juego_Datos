# interaction_manager.py
import pygame

class InteractionManager:
    """Gestor de interacciones del jugador con el mundo del juego"""
    
    def __init__(self, player, active_orders, completed_orders):
        self.player = player
        self.active_orders = active_orders
        self.completed_orders = completed_orders
        
        # Control de interacciones
        self.interaction_cooldown = 0
        self.interaction_message = ""
        self.message_timer = 0
    
    def handle_event(self, event, game_state):
        """Maneja eventos de interacción"""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e and self.interaction_cooldown <= 0:
            self.handle_interaction(game_state)
    
    def handle_interaction(self, game_state):
        """Procesa interacciones de recogida y entrega"""
        # Primero verificar entregas (tiene prioridad)
        if self.try_delivery(game_state):
            return
        
        # Luego verificar recogidas
        self.try_pickup()
    
    def try_delivery(self, game_state):
        """Intenta entregar pedidos en la ubicación actual"""
        for order in list(self.player.inventory):
            if self.player.is_at_location(order.dropoff):
                if self.player.remove_from_inventory(order.id):
                    # Añadir a trabajos completados y remover de activos
                    self.completed_orders.enqueue(order)
                    self.active_orders.remove_by_id(order.id)
                    
                    # Sumar ganancias con multiplicador de reputación
                    earnings = self.calculate_earnings(order)
                    game_state.add_earnings(earnings)
                    
                    self.show_message(f"Entregado: {order.id} +${earnings}")
                    self.interaction_cooldown = 0.5
                    return True
        return False
    
    def try_pickup(self):
        """Intenta recoger pedidos en la ubicación actual"""
        for order in list(self.active_orders):
            if self.player.is_at_location(order.pickup):
                # Verificar si el pedido ya está en el inventario
                if self.player.inventory.find_by_id(order.id) is not None:
                    continue
                
                if self.player.can_pickup_order(order):
                    if self.player.add_to_inventory(order):
                        self.show_message(f"Recogido: {order.id}")
                        self.interaction_cooldown = 0.5
                        return True
                else:
                    self.show_message("¡No tienes capacidad suficiente!")
                    break
        return False
    
    def calculate_earnings(self, order):
        """Calcula las ganancias de un pedido considerando la reputación"""
        base_payout = order.payout
        
        # Bonus por reputación alta (≥90)
        if self.player.reputation >= 90:
            return int(base_payout * 1.05)
        
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
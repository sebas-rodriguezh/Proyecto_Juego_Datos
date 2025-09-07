# interaction_manager.py - MODIFICADO con sistema adyacente
import pygame

class InteractionManager:
    """Gestor de interacciones del jugador con el mundo del juego - CON RECOGIDA ADYACENTE"""
    
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
        """Procesa interacciones de recogida y entrega - CON SISTEMA ADYACENTE"""
        # Obtener todas las órdenes con las que puede interactuar
        interactable_orders = self.player.get_interactable_orders(self.active_orders)
        
        if not interactable_orders:
            self.show_message("No hay nada que hacer aquí", 2)
            return
        
        # Procesar la primera interacción disponible (ya ordenada por prioridad)
        interaction = interactable_orders[0]
        order = interaction['order']
        action = interaction['action']
        is_exact = interaction['is_exact']
        
        if action == 'dropoff':
            # Entregar pedido
            if self.player.remove_from_inventory(order.id):
                self.completed_orders.enqueue(order)
                self.active_orders.remove_by_id(order.id)
                
                earnings = self.calculate_earnings(order)
                game_state.add_earnings(earnings)
                
                location_text = "exacta" if is_exact else "adyacente"
                self.show_message(f"✓ Entregado {order.id} +${earnings} ({location_text})", 3)
                self.interaction_cooldown = 0.5
        
        elif action == 'pickup':
            # Recoger pedido
            if self.player.can_pickup_order(order):
                if self.player.add_to_inventory(order):
                    location_text = "exacta" if is_exact else "adyacente"
                    self.show_message(f"📦 Recogido {order.id} ({location_text})", 3)
                    self.interaction_cooldown = 0.5
                else:
                    self.show_message("Error al recoger pedido", 2)
            else:
                self.show_message("¡No tienes capacidad suficiente!", 2)
    
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
    
    def get_interaction_hint(self):
        """NUEVO: Obtiene pista de qué se puede hacer en la posición actual"""
        interactable_orders = self.player.get_interactable_orders(self.active_orders)
        
        if not interactable_orders:
            return ""
        
        interaction = interactable_orders[0]
        action = interaction['action']
        is_exact = interaction['is_exact']
        order_id = interaction['order'].id
        
        if action == 'dropoff':
            location_hint = "" if is_exact else " (adyacente)"
            return f"Presiona E para entregar {order_id}{location_hint}"
        elif action == 'pickup':
            location_hint = "" if is_exact else " (adyacente)"
            return f"Presiona E para recoger {order_id}{location_hint}"
        
        return ""

import pygame
from datetime import datetime

class InteractionManager:
    """Gestor de interacciones del jugador con el mundo del juego"""
    
    def __init__(self, player, active_orders, completed_orders, game_time):
        self.player = player
        self.active_orders = active_orders
        self.completed_orders = completed_orders
        self.game_time = game_time  
        
        # Control de interacciones
        self.interaction_cooldown = 0
        self.interaction_message = ""
        self.message_timer = 0
        self.interaction_radius = 4

    def handle_event(self, event, game_state, game_map=None):
        """Maneja eventos de interacción"""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e and self.interaction_cooldown <= 0:
            self.handle_interaction(game_state, game_map)

    def handle_interaction(self, game_state, game_map):
        """Procesa interacciones con gestión completa de deadlines"""
        print("=== DEBUG INTERACCIÓN ===")
        print(f"Posición jugador: ({self.player.grid_x}, {self.player.grid_y})")
        
        interactable_orders = self.player.get_interactable_orders(
            self.active_orders, game_map, self.interaction_radius, self.game_time
        )
        
        if not interactable_orders:
            self.show_message("No hay nada que hacer aquí", 2)
            return
        
        interaction = interactable_orders[0]
        order = interaction['order']
        action = interaction['action']
        
        current_time = self.game_time.get_current_game_time()  
        
        if action == 'dropoff':
            self.handle_dropoff_interaction(order, interaction, game_state, current_time)
        elif action == 'pickup':
            self.handle_pickup_interaction(order, interaction, game_state, current_time)


    def handle_dropoff_interaction(self, order, interaction, game_state, current_time):
        """Maneja la entrega de un pedido"""
        if self.player.remove_from_inventory(order.id):
            # Calcular ganancias y reputación ANTES de mover a completed_orders
            earnings = self.calculate_earnings(order, interaction, current_time)
            reputation_change = order.calculate_reputation_change(current_time)
            
            # Aplicar cambios
            game_state.add_earnings(earnings)
            old_reputation = self.player.reputation
            self.player.reputation = min(100, max(0, self.player.reputation + reputation_change))
            

            timeliness = order.get_delivery_timeliness(current_time)
            is_early = (timeliness == "early")
            is_on_time = (timeliness == "on_time" or timeliness == "early")
            
            print(f" TIMELINESS DEBUG: {order.id}")
            print(f"   - Timeliness: {timeliness}")
            print(f"   - Es temprano: {is_early}")
            print(f"   - Es a tiempo: {is_on_time}")
            
            game_state.complete_order(order, on_time=is_on_time, early=is_early)
            
            # Marcar como completado y mover
            order.mark_as_completed()
            self.completed_orders.enqueue(order)
            
            self.record_delivery_stats(game_state, order, current_time, reputation_change)
            
            # Mostrar mensaje con detalles
            location_text = self.get_location_text(interaction['is_exact'], 
                                                interaction['distance'], 
                                                interaction['is_building'])
            
            rep_symbol = "+" if reputation_change >= 0 else ""
            message = f"✓ Entregado {order.id} +${earnings} ({rep_symbol}{reputation_change} rep) ({location_text})"
            self.show_message(message, 3)
            
            print(f" Entrega: {order.id} - ${earnings} - Rep: {old_reputation}→{self.player.reputation}")
            
        else:
            self.show_message("Error: Pedido no encontrado en inventario", 2)




    def record_delivery_stats(self, game_state, order, current_time, reputation_change):
        """Registra estadísticas de la entrega según el timing"""
        timeliness = order.get_delivery_timeliness(current_time)
        
        game_state.orders_completed += 1
        
        if reputation_change >= 0:  # Sin penalización = perfecta
            game_state.perfect_deliveries += 1
            if timeliness == "early":
                print(f" Entrega TEMPRANA: {order.id}")
                self.show_message(f" ¡Entrega TEMPRANA! +5 reputación", 3)
            elif timeliness == "on_time":
                print(f" Entrega A TIEMPO: {order.id}")
                self.show_message(f" Entrega A TIEMPO! +3 reputación", 3)
        else:  # Con penalización = tardía
            game_state.late_deliveries += 1
            print(f" Entrega TARDÍA: {order.id}")
            self.show_message(f" Entrega TARDÍA - Penalización aplicada", 3)        


    def handle_pickup_interaction(self, order, interaction, game_state, current_time):
        """Maneja la recogida de un pedido"""
        if self.player.can_pickup_order(order):
            if self.player.add_to_inventory(order):
                # Marcar como recogido y aceptado
                order.mark_as_picked_up()
                order.mark_as_accepted(current_time)
                
                # Remover de active_orders después de recogerlo
                if self.active_orders.remove_by_id(order.id):
                    location_text = self.get_location_text(interaction['is_exact'], 
                                                        interaction['distance'], 
                                                        interaction['is_building'])
                    self.show_message(f"📦 Recogido {order.id} ({location_text})", 3)
                    print(f" Recogido: {order.id} a las {current_time.strftime('%H:%M:%S')}")
                else:
                    self.show_message("Error al remover pedido de lista activa", 2)
            else:
                self.show_message("Error al recoger pedido", 2)
        else:
            self.show_message("¡No tienes capacidad suficiente!", 2)


    def get_location_text(self, is_exact, distance, is_building):
        """Obtiene texto descriptivo de la ubicación"""
        if is_exact:
            return "exacta"
        elif is_building and distance <= 1:
            return "desde afuera"
        elif distance == 1:
            return "adyacente"
        else:
            return f"a {distance} casillas"
    
    def calculate_earnings(self, order, interaction, current_time):
        """Calcula ganancias según especificaciones del proyecto"""
        base_payout = order.payout
        
        # Aplicar modificador por timing y reputación
        payout_modifier = order.calculate_payout_modifier(current_time, self.player.reputation)
        base_payout *= payout_modifier
        
        if not interaction['is_exact'] and not interaction['is_building'] and interaction['distance'] > 1:
            distance_penalty = 0.1 * (interaction['distance'] - 1)
            base_payout *= max(0.7, 1 - distance_penalty)
        
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
        """Obtiene pista de qué se puede hacer en la posición actual"""
        interactable_orders = self.player.get_interactable_orders(
            self.active_orders, game_map, self.interaction_radius, self.game_time
        )
        
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
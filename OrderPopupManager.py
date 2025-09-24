import pygame
from datetime import datetime

class OrderPopupManager:
    """Gestor de popups para aceptar/rechazar pedidos y cancelar pedidos del inventario"""
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Estado del popup de nuevo pedido
        self.pending_order = None  # Pedido esperando respuesta
        self.popup_timer = 0
        self.popup_duration = 10.0  # 10 segundos para decidir
        self.popup_active = False
        
        # Estado del popup de cancelación
        self.cancel_popup_active = False
        self.selected_order_for_cancel = None
        
        # Configurar fuentes
        self.setup_fonts()
        
    def setup_fonts(self):
        """Configura las fuentes del sistema"""
        try:
            self.font_small = pygame.font.Font(None, 14)
            self.font_medium = pygame.font.Font(None, 16)
            self.font_large = pygame.font.Font(None, 20)
        except:
            self.font_small = pygame.font.SysFont("Arial", 14)
            self.font_medium = pygame.font.SysFont("Arial", 16)
            self.font_large = pygame.font.SysFont("Arial", 20, bold=True)
    
    def show_new_order_popup(self, order):
        """Muestra popup para aceptar/rechazar un nuevo pedido"""
        if not self.popup_active:  # Solo mostrar si no hay otro popup activo
            self.pending_order = order
            self.popup_timer = self.popup_duration
            self.popup_active = True
            print(f"🔔 Mostrando popup para pedido: {order.id}")
    
    def show_cancel_order_popup(self, order):
        """Muestra popup para confirmar cancelación de pedido"""
        if not self.cancel_popup_active:
            self.selected_order_for_cancel = order
            self.cancel_popup_active = True
            print(f"⚠️ Mostrando popup de cancelación para: {order.id}")
    
    def handle_event(self, event, game_state, player, active_orders):
        """Maneja eventos relacionados con los popups"""
        result = None
        
        if event.type == pygame.KEYDOWN:
            # Popup de nuevo pedido
            if self.popup_active and self.pending_order:
                if event.key == pygame.K_y:  # Aceptar pedido
                    result = self.accept_order(game_state, player, active_orders)
                elif event.key == pygame.K_n:  # Rechazar pedido
                    result = self.reject_order(game_state)
                elif event.key == pygame.K_ESCAPE:  # Auto-rechazar
                    result = self.reject_order(game_state)
            
            # Popup de cancelación
            elif self.cancel_popup_active and self.selected_order_for_cancel:
                if event.key == pygame.K_y:  # Confirmar cancelación
                    result = self.confirm_cancel_order(game_state, player)
                elif event.key == pygame.K_n or event.key == pygame.K_ESCAPE:  # No cancelar
                    self.cancel_popup_active = False
                    self.selected_order_for_cancel = None
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            
            # Clicks en popup de nuevo pedido
            if self.popup_active and self.pending_order:
                popup_result = self.handle_popup_click(mouse_x, mouse_y, game_state, player, active_orders)
                if popup_result:
                    result = popup_result
            
            # Clicks en popup de cancelación
            elif self.cancel_popup_active:
                cancel_result = self.handle_cancel_popup_click(mouse_x, mouse_y, game_state, player)
                if cancel_result:
                    result = cancel_result
        
        return result
    
    def handle_popup_click(self, mouse_x, mouse_y, game_state, player, active_orders):
        """Maneja clicks en el popup de nuevo pedido"""
        popup_x, popup_y = self.get_popup_position()
        popup_width, popup_height = 350, 200
        
        # Verificar si el click está dentro del popup
        if (popup_x <= mouse_x <= popup_x + popup_width and 
            popup_y <= mouse_y <= popup_y + popup_height):
            
            # Botón Aceptar (izquierda)
            accept_button_x = popup_x + 50
            accept_button_y = popup_y + popup_height - 40
            if (accept_button_x <= mouse_x <= accept_button_x + 100 and
                accept_button_y <= mouse_y <= accept_button_y + 30):
                return self.accept_order(game_state, player, active_orders)
            
            # Botón Rechazar (derecha)
            reject_button_x = popup_x + 200
            reject_button_y = popup_y + popup_height - 40
            if (reject_button_x <= mouse_x <= reject_button_x + 100 and
                reject_button_y <= mouse_y <= reject_button_y + 30):
                return self.reject_order(game_state)
        
        return None
    
    def handle_cancel_popup_click(self, mouse_x, mouse_y, game_state, player):
        """Maneja clicks en el popup de cancelación"""
        popup_x = self.screen_width // 2 - 175
        popup_y = self.screen_height // 2 - 75
        popup_width, popup_height = 350, 150
        
        if (popup_x <= mouse_x <= popup_x + popup_width and 
            popup_y <= mouse_y <= popup_y + popup_height):
            
            # Botón Sí (izquierda)
            yes_button_x = popup_x + 50
            yes_button_y = popup_y + popup_height - 40
            if (yes_button_x <= mouse_x <= yes_button_x + 100 and
                yes_button_y <= mouse_y <= yes_button_y + 30):
                return self.confirm_cancel_order(game_state, player)
            
            # Botón No (derecha)
            no_button_x = popup_x + 200
            no_button_y = popup_y + popup_height - 40
            if (no_button_x <= mouse_x <= no_button_x + 100 and
                no_button_y <= mouse_y <= no_button_y + 30):
                self.cancel_popup_active = False
                self.selected_order_for_cancel = None
                return {"type": "cancel_order", "result": "cancelled"}
        
        return None
    
    def accept_order(self, game_state, player, active_orders):
        """Procesa la aceptación de un pedido"""
        if not self.pending_order:
            return None
        
        order = self.pending_order
        
        # Verificar si el jugador tiene capacidad
        if player.can_pickup_order(order):
            # Añadir a órdenes activas
            active_orders.enqueue(order)
            
            # Limpiar popup
            self.popup_active = False
            self.pending_order = None
            
            print(f"✅ Pedido {order.id} ACEPTADO y añadido a órdenes activas")
            return {
                "type": "accept_order", 
                "result": "accepted", 
                "order": order,
                "message": f"Pedido {order.id} aceptado"
            }
        else:
            # No puede aceptar por capacidad
            print(f"❌ No se puede aceptar {order.id} - Sin capacidad")
            return {
                "type": "accept_order", 
                "result": "no_capacity", 
                "order": order,
                "message": f"No tienes capacidad para {order.id}"
            }
    
    def reject_order(self, game_state):
        """Procesa el rechazo de un pedido"""
        if not self.pending_order:
            return None
        
        order = self.pending_order
        
        # Limpiar popup
        self.popup_active = False
        self.pending_order = None
        
        print(f"❌ Pedido {order.id} RECHAZADO")
        return {
            "type": "reject_order", 
            "result": "rejected", 
            "order": order,
            "message": f"Pedido {order.id} rechazado (-1 reputación)",
            "penalty": 1  # Añadir penalización para aplicar después
        }
    
    def confirm_cancel_order(self, game_state, player):
        """Confirma la cancelación de un pedido del inventario"""
        if not self.selected_order_for_cancel:
            return None
        
        order = self.selected_order_for_cancel
        
        # Remover del inventario
        if player.remove_from_inventory(order.id):
  
            # Actualizar estadísticas
            game_state.orders_cancelled += 1
            
            print(f"🗑️ Pedido {order.id} CANCELADO del inventario")
            
            # Limpiar popup
            self.cancel_popup_active = False
            self.selected_order_for_cancel = None
                
            return {
                "type": "cancel_order", 
                "result": "confirmed", 
                "order": order,
                "message": f"Pedido {order.id} cancelado (-4 reputación)",
                "penalty": 4  # Añadir penalización para aplicar después
            }
        
        else:
            print(f"❌ Error cancelando {order.id}")
            return {
                "type": "cancel_order", 
                "result": "error", 
                "order": order,
                "message": f"Error cancelando {order.id}"
            }
    
    def update(self, dt):
        """Actualiza los timers de los popups"""
        # Timer del popup de nuevo pedido
        if self.popup_active and self.popup_timer > 0:
            self.popup_timer -= dt
            if self.popup_timer <= 0:
                # Auto-rechazar si se acaba el tiempo
                print(f"⏰ Tiempo agotado para {self.pending_order.id} - Auto-rechazando")
                self.reject_order(None)  # Auto-rechazar
    
    def get_popup_position(self):
        """Calcula la posición del popup de nuevo pedido"""
        popup_width, popup_height = 350, 200
        # Posición en esquina superior derecha
        popup_x = self.screen_width - popup_width - 20
        popup_y = 20
        return popup_x, popup_y
    
    def draw_new_order_popup(self, screen):
        """Dibuja el popup de nuevo pedido"""
        if not self.popup_active or not self.pending_order:
            return
        
        order = self.pending_order
        popup_x, popup_y = self.get_popup_position()
        popup_width, popup_height = 350, 200
        
        # Fondo del popup con transparencia
        popup_surface = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA)
        
        # Color de fondo basado en prioridad
        if order.priority > 0:
            bg_color = (255, 200, 200, 240)  # Rojo claro para prioritarios
            border_color = (255, 0, 0)
        else:
            bg_color = (200, 200, 255, 240)  # Azul claro para normales
            border_color = (0, 0, 200)
        
        popup_surface.fill(bg_color)
        screen.blit(popup_surface, (popup_x, popup_y))
        
        # Borde del popup
        pygame.draw.rect(screen, border_color, (popup_x, popup_y, popup_width, popup_height), 3)
        
        # Título
        priority_text = "🚨 PEDIDO PRIORITARIO" if order.priority > 0 else "📦 NUEVO PEDIDO"
        title = self.font_large.render(priority_text, True, border_color)
        screen.blit(title, (popup_x + 10, popup_y + 10))
        
        # Información del pedido
        info_lines = [
            f"ID: {order.id}",
            f"Pago: ${order.payout}",
            f"Peso: {order.weight}kg",
            f"Prioridad: {order.priority}",
            f"Límite: {order.deadline.strftime('%H:%M')}",
            f"Recogida: {order.pickup}",
            f"Entrega: {order.dropoff}"
        ]
        
        for i, line in enumerate(info_lines):
            text = self.font_small.render(line, True, (0, 0, 0))
            screen.blit(text, (popup_x + 15, popup_y + 40 + i * 18))
        
        # Timer countdown
        timer_text = f"⏰ Tiempo restante: {int(self.popup_timer)}s"
        timer_color = (255, 0, 0) if self.popup_timer < 3 else (0, 0, 0)
        timer_surface = self.font_small.render(timer_text, True, timer_color)
        screen.blit(timer_surface, (popup_x + 15, popup_y + 165))
        
        # Botones
        # Botón Aceptar
        accept_button_rect = pygame.Rect(popup_x + 50, popup_y + popup_height - 40, 100, 30)
        pygame.draw.rect(screen, (0, 200, 0), accept_button_rect)
        pygame.draw.rect(screen, (0, 150, 0), accept_button_rect, 2)
        
        accept_text = self.font_medium.render("Aceptar (Y)", True, (255, 255, 255))
        text_x = accept_button_rect.centerx - accept_text.get_width() // 2
        text_y = accept_button_rect.centery - accept_text.get_height() // 2
        screen.blit(accept_text, (text_x, text_y))
        
        # Botón Rechazar
        reject_button_rect = pygame.Rect(popup_x + 200, popup_y + popup_height - 40, 100, 30)
        pygame.draw.rect(screen, (200, 0, 0), reject_button_rect)
        pygame.draw.rect(screen, (150, 0, 0), reject_button_rect, 2)
        
        reject_text = self.font_medium.render("Rechazar (N)", True, (255, 255, 255))
        text_x = reject_button_rect.centerx - reject_text.get_width() // 2
        text_y = reject_button_rect.centery - reject_text.get_height() // 2
        screen.blit(reject_text, (text_x, text_y))
        
        # Instrucciones
        instruction_text = "Click en los botones o presiona Y/N"
        instruction_surface = self.font_small.render(instruction_text, True, (100, 100, 100))
        screen.blit(instruction_surface, (popup_x + 10, popup_y + popup_height - 15))
    
    def draw_cancel_order_popup(self, screen):
        """Dibuja el popup de cancelación de pedido"""
        if not self.cancel_popup_active or not self.selected_order_for_cancel:
            return
        
        order = self.selected_order_for_cancel
        popup_width, popup_height = 350, 150
        popup_x = self.screen_width // 2 - popup_width // 2
        popup_y = self.screen_height // 2 - popup_height // 2
        
        # Fondo del popup
        popup_surface = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA)
        popup_surface.fill((255, 255, 200, 240))  # Amarillo claro
        screen.blit(popup_surface, (popup_x, popup_y))
        
        # Borde
        pygame.draw.rect(screen, (200, 100, 0), (popup_x, popup_y, popup_width, popup_height), 3)
        
        # Título
        title = self.font_large.render("⚠️ CANCELAR PEDIDO", True, (200, 100, 0))
        screen.blit(title, (popup_x + 10, popup_y + 10))
        
        # Pregunta
        question = f"¿Cancelar pedido {order.id}?"
        question_surface = self.font_medium.render(question, True, (0, 0, 0))
        screen.blit(question_surface, (popup_x + 15, popup_y + 40))
        
        # Consecuencias
        penalty_text = "Esto reducirá tu reputación en 4 puntos"
        penalty_surface = self.font_small.render(penalty_text, True, (150, 0, 0))
        screen.blit(penalty_surface, (popup_x + 15, popup_y + 65))
        
        # Botones
        # Botón Sí
        yes_button_rect = pygame.Rect(popup_x + 50, popup_y + popup_height - 40, 100, 30)
        pygame.draw.rect(screen, (200, 0, 0), yes_button_rect)
        pygame.draw.rect(screen, (150, 0, 0), yes_button_rect, 2)
        
        yes_text = self.font_medium.render("Sí (Y)", True, (255, 255, 255))
        text_x = yes_button_rect.centerx - yes_text.get_width() // 2
        text_y = yes_button_rect.centery - yes_text.get_height() // 2
        screen.blit(yes_text, (text_x, text_y))
        
        # Botón No
        no_button_rect = pygame.Rect(popup_x + 200, popup_y + popup_height - 40, 100, 30)
        pygame.draw.rect(screen, (0, 150, 0), no_button_rect)
        pygame.draw.rect(screen, (0, 100, 0), no_button_rect, 2)
        
        no_text = self.font_medium.render("No (N)", True, (255, 255, 255))
        text_x = no_button_rect.centerx - no_text.get_width() // 2
        text_y = no_button_rect.centery - no_text.get_height() // 2
        screen.blit(no_text, (text_x, text_y))
    
    def is_popup_active(self):
        """Verifica si algún popup está activo"""
        return self.popup_active or self.cancel_popup_active
    
    def has_pending_order(self):
        """Verifica si hay un pedido pendiente de decisión"""
        return self.popup_active and self.pending_order is not None
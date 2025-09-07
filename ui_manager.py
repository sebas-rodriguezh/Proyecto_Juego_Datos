# ui_manager.py
import pygame
from datetime import datetime

class UIManager:
    """Gestor de la interfaz de usuario del juego"""
    
    def __init__(self, screen, game_map, screen_width, screen_height):
        self.screen = screen
        self.game_map = game_map
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Configurar fuentes
        self.setup_fonts()
        
        # Colores para los trabajos
        self.job_colors = [
            (255, 100, 100), (100, 100, 255), (255, 255, 100),
            (255, 100, 255), (100, 255, 255)
        ]
        
        # Variables para mensajes
        self.message = ""
        self.message_timer = 0
        self.selected_order = None
    
    def setup_fonts(self):
        """Configura las fuentes del juego"""
        try:
            self.font_small = pygame.font.Font(None, 12)
            self.font_medium = pygame.font.Font(None, 14)
            self.font_large = pygame.font.Font(None, 18)
            self.font_xlarge = pygame.font.Font(None, 24)
        except:
            self.font_small = pygame.font.SysFont("Arial", 12)
            self.font_medium = pygame.font.SysFont("Arial", 14)
            self.font_large = pygame.font.SysFont("Arial", 18, bold=True)
            self.font_xlarge = pygame.font.SysFont("Arial", 24, bold=True)
    
    def handle_event(self, event, active_orders, player):
        """Maneja eventos relacionados con la UI"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            
            # Verificar clic en el panel lateral
            if mouse_x > self.game_map.width * self.game_map.tile_size:
                self.handle_sidebar_click(mouse_x, mouse_y, active_orders, player)
    
    def handle_sidebar_click(self, mouse_x, mouse_y, active_orders, player):
        """Maneja clics en el panel lateral"""
        # Calcular posición de la lista de trabajos
        weather_y_pos = 300 if not player.inventory else 235 + len(player.inventory) * 40 + 10
        jobs_y_pos = weather_y_pos + 85
        order_index = (mouse_y - jobs_y_pos - 25) // 70
        
        if 0 <= order_index < len(active_orders):
            self.selected_order = active_orders[order_index]
            self.show_message(f"Seleccionado: {self.selected_order.id}", 3)
    
    def show_message(self, message, duration):
        """Muestra un mensaje temporal"""
        self.message = message
        self.message_timer = duration
    
    def update_messages(self, dt):
        """Actualiza los mensajes temporales"""
        if self.message_timer > 0:
            self.message_timer -= dt
        else:
            self.message = ""
    
    def draw_sidebar(self, player, active_orders, weather_system, game_time, game_state):
        """Dibuja el panel lateral completo"""
        cols = self.game_map.width
        sidebar_rect = pygame.Rect(cols * self.game_map.tile_size, 0, 300, self.screen_height)
        pygame.draw.rect(self.screen, (240, 240, 240), sidebar_rect)
        pygame.draw.line(self.screen, (200, 200, 200), 
                        (cols * self.game_map.tile_size, 0), 
                        (cols * self.game_map.tile_size, self.screen_height), 2)
        
        # Dibujar cada sección
        self.draw_header(cols, game_time, game_state)
        self.draw_player_status(cols, player)
        self.draw_inventory(cols, player)
        self.draw_weather_info(cols, weather_system, player)
        self.draw_available_jobs(cols, active_orders, weather_system, player)
        self.draw_legend(cols)
    
    def draw_header(self, cols, game_time, game_state):
        """Dibuja el encabezado con título, tiempo y ganancias"""
        x_offset = cols * self.game_map.tile_size
        
        # Título
        title = self.font_large.render("Courier Quest", True, (0, 0, 0))
        self.screen.blit(title, (x_offset + 10, 10))
        
        # Tiempo
        time_bg = pygame.Rect(x_offset + 10, 35, 280, 25)
        pygame.draw.rect(self.screen, (220, 220, 220), time_bg, border_radius=5)
        pygame.draw.rect(self.screen, (100, 100, 100), time_bg, 2, border_radius=5)
        
        # Color del tiempo según urgencia
        remaining_time = game_time.get_remaining_time()
        if remaining_time < 60:
            time_color = (255, 50, 50)
        elif remaining_time < 300:
            time_color = (255, 150, 50)
        else:
            time_color = (0, 100, 0)
        
        time_text = self.font_medium.render(f"⏰ Tiempo: {game_time.get_remaining_time_formatted()}", 
                                          True, time_color)
        self.screen.blit(time_text, (x_offset + 20, 38))
        
        # Ganancias y meta
        earnings_text = self.font_medium.render(f"💰 Ganancias: ${game_state.total_earnings}", 
                                              True, (0, 100, 0))
        self.screen.blit(earnings_text, (x_offset + 10, 65))
        
        goal_text = self.font_small.render(f"🎯 Meta: ${game_state.income_goal}", 
                                         True, (0, 0, 0))
        self.screen.blit(goal_text, (x_offset + 150, 65))
    
    def draw_player_status(self, cols, player):
        """Dibuja el estado del jugador"""
        x_offset = cols * self.game_map.tile_size
        
        # Título
        player_title = self.font_medium.render("Estado del Repartidor:", True, (0, 0, 0))
        self.screen.blit(player_title, (x_offset + 10, 90))
        
        # Barra de resistencia
        stamina_text = self.font_small.render(f"Resistencia: {int(player.stamina)}/100", 
                                            True, (0, 0, 0))
        self.screen.blit(stamina_text, (x_offset + 10, 115))
        self.draw_bar(x_offset + 10, 130, 150, 15, player.stamina / 100, (0, 200, 0))
        
        # Reputación
        reputation_text = self.font_small.render(f"Reputación: {player.reputation}/100", 
                                               True, (0, 0, 0))
        self.screen.blit(reputation_text, (x_offset + 10, 150))
        
        # Color de la barra de reputación según el nivel
        if player.reputation >= 90:
            rep_color = (0, 200, 0)
        elif player.reputation >= 70:
            rep_color = (0, 150, 200)
        elif player.reputation >= 50:
            rep_color = (255, 150, 0)
        else:
            rep_color = (255, 50, 50)
        
        self.draw_bar(x_offset + 10, 165, 150, 15, player.reputation / 100, rep_color)
        
        # Peso actual
        weight_text = self.font_small.render(f"Peso: {player.current_weight}/{player.max_weight}", 
                                           True, (0, 0, 0))
        self.screen.blit(weight_text, (x_offset + 10, 185))
    
    def draw_bar(self, x, y, width, height, progress, color):
        """Dibuja una barra de progreso"""
        pygame.draw.rect(self.screen, (200, 200, 200), (x, y, width, height))
        pygame.draw.rect(self.screen, color, (x, y, width * progress, height))
    
    def draw_inventory(self, cols, player):
        """Dibuja el inventario del jugador"""
        x_offset = cols * self.game_map.tile_size
        
        inventory_title = self.font_medium.render("Inventario:", True, (0, 0, 0))
        self.screen.blit(inventory_title, (x_offset + 10, 210))
        
        if player.inventory:
            for i, order in enumerate(player.inventory):
                y_pos = 235 + i * 40
                pygame.draw.rect(self.screen, (200, 255, 200), (x_offset + 10, y_pos, 280, 35))
                pygame.draw.rect(self.screen, (0, 200, 0), (x_offset + 10, y_pos, 280, 35), 2)
                
                order_id = self.font_small.render(f"ID: {order.id}", True, (0, 0, 0))
                self.screen.blit(order_id, (x_offset + 15, y_pos + 5))
                
                destination = self.font_small.render(f"Entrega: {order.dropoff}", True, (0, 0, 0))
                self.screen.blit(destination, (x_offset + 15, y_pos + 20))
        else:
            no_items = self.font_small.render("No hay pedidos en inventario", True, (150, 150, 150))
            self.screen.blit(no_items, (x_offset + 15, 235))
    
    def draw_weather_info(self, cols, weather_system, player):
        """Dibuja información del clima"""
        x_offset = cols * self.game_map.tile_size
        
        weather_title = self.font_medium.render("Condición Climática:", True, (0, 0, 0))
        weather_y_pos = 300 if not player.inventory else 235 + len(player.inventory) * 40 + 10
        self.screen.blit(weather_title, (x_offset + 10, weather_y_pos))
        
        # Dibujar indicador del clima
        weather_system.draw(self.screen, x_offset + 40, weather_y_pos + 35)
        
        # Información textual del clima
        condition_name = weather_system.current_condition.value.replace("_", " ").title()
        weather_text = self.font_small.render(condition_name, True, (0, 0, 0))
        self.screen.blit(weather_text, (x_offset + 60, weather_y_pos + 25))
        
        intensity_text = self.font_small.render(f"Intensidad: {weather_system.current_intensity:.2f}", 
                                              True, (0, 0, 0))
        self.screen.blit(intensity_text, (x_offset + 60, weather_y_pos + 40))
        
        speed_text = self.font_small.render(f"Velocidad: x{weather_system.current_multiplier:.2f}", 
                                          True, (0, 0, 0))
        self.screen.blit(speed_text, (x_offset + 60, weather_y_pos + 55))
    
    def draw_available_jobs(self, cols, active_orders, weather_system, player):
        """Dibuja la lista de trabajos disponibles"""
        x_offset = cols * self.game_map.tile_size
        
        weather_y_pos = 300 if not player.inventory else 235 + len(player.inventory) * 40 + 10
        jobs_title = self.font_medium.render("Trabajos Disponibles:", True, (0, 0, 0))
        jobs_y_pos = weather_y_pos + 85
        self.screen.blit(jobs_title, (x_offset + 10, jobs_y_pos))
        
        for i, order in enumerate(active_orders):
            y_pos = jobs_y_pos + 25 + i * 70
            
            pygame.draw.rect(self.screen, self.job_colors[i % len(self.job_colors)], 
                           (x_offset + 10, y_pos, 20, 20))
            
            order_id = self.font_small.render(f"ID: {order.id}", True, (0, 0, 0))
            self.screen.blit(order_id, (x_offset + 35, y_pos))
            
            payout = self.font_small.render(f"Pago: ${order.payout}", True, (0, 0, 0))
            self.screen.blit(payout, (x_offset + 35, y_pos + 15))
            
            deadline = self.font_small.render(f"Entrega: {order.deadline.strftime('%H:%M')}", 
                                            True, (0, 0, 0))
            self.screen.blit(deadline, (x_offset + 10, y_pos + 35))
            
            weight = self.font_small.render(f"Peso: {order.weight}", True, (0, 0, 0))
            self.screen.blit(weight, (x_offset + 120, y_pos + 35))
            
            priority = self.font_small.render(f"Prioridad: {order.priority}", True, (0, 0, 0))
            self.screen.blit(priority, (x_offset + 10, y_pos + 50))
    
    def draw_legend(self, cols):
        """Dibuja la leyenda del mapa"""
        x_offset = cols * self.game_map.tile_size
        
        legend_title = self.font_medium.render("Leyenda del Mapa:", True, (0, 0, 0))
        legend_y_pos = self.screen_height - 150
        self.screen.blit(legend_title, (x_offset + 10, legend_y_pos))
        
        y_pos = legend_y_pos + 20
        for char, info in self.game_map.legend.items():
            color = self.game_map.COLORS.get(char, (100, 100, 255))
            pygame.draw.rect(self.screen, color, (x_offset + 10, y_pos, 15, 15))
            name = self.font_small.render(info["name"].title(), True, (0, 0, 0))
            self.screen.blit(name, (x_offset + 30, y_pos))
            y_pos += 20
    
    def draw_order_markers(self, active_orders, player, camera_x, camera_y):
        """Dibuja los marcadores de trabajos en el mapa"""
        for i, order in enumerate(active_orders):
            color = self.job_colors[i % len(self.job_colors)]
            
            # Si el trabajo está en el inventario, usar color verde
            if player.inventory.find_by_id(order.id) is not None:
                color = (0, 255, 0)
            
            # Dibujar punto de recogida
            pickup_x, pickup_y = order.pickup
            pygame.draw.circle(self.screen, color, 
                             (pickup_x * self.game_map.tile_size + self.game_map.tile_size // 2 - camera_x, 
                              pickup_y * self.game_map.tile_size + self.game_map.tile_size // 2 - camera_y), 
                             7)
            pygame.draw.circle(self.screen, (255, 255, 255), 
                             (pickup_x * self.game_map.tile_size + self.game_map.tile_size // 2 - camera_x, 
                              pickup_y * self.game_map.tile_size + self.game_map.tile_size // 2 - camera_y), 
                             7, 1)
            
            # Dibujar punto de entrega
            dropoff_x, dropoff_y = order.dropoff
            pygame.draw.rect(self.screen, color, 
                           (dropoff_x * self.game_map.tile_size + self.game_map.tile_size // 2 - 5 - camera_x, 
                            dropoff_y * self.game_map.tile_size + self.game_map.tile_size // 2 - 5 - camera_y, 
                            10, 10))
            pygame.draw.rect(self.screen, (255, 255, 255), 
                           (dropoff_x * self.game_map.tile_size + self.game_map.tile_size // 2 - 5 - camera_x, 
                            dropoff_y * self.game_map.tile_size + self.game_map.tile_size // 2 - 5 - camera_y, 
                            10, 10), 1)
            
            # Dibujar línea conectando recogida y entrega (solo si no está en inventario)
            if player.inventory.find_by_id(order.id) is None:
                pygame.draw.line(self.screen, color, 
                               (pickup_x * self.game_map.tile_size + self.game_map.tile_size // 2 - camera_x, 
                                pickup_y * self.game_map.tile_size + self.game_map.tile_size // 2 - camera_y),
                               (dropoff_x * self.game_map.tile_size + self.game_map.tile_size // 2 - camera_x, 
                                dropoff_y * self.game_map.tile_size + self.game_map.tile_size // 2 - camera_y), 
                               2)
    
    def draw_messages(self):
        """Dibuja mensajes temporales"""
        if self.message:
            msg_surface = self.font_medium.render(self.message, True, (0, 0, 0))
            self.screen.blit(msg_surface, (10, 10))
    
    def draw_interaction_hints(self, player, active_orders, camera_x, camera_y):
        """Dibuja pistas de interacción cerca del jugador"""
        nearby_active = False
        for order in active_orders:
            in_inventory = player.inventory.find_by_id(order.id) is not None
            
            if (player.is_at_location(order.pickup) and not in_inventory) or \
               (in_inventory and player.is_at_location(order.dropoff)):
                nearby_active = True
                break
        
        if nearby_active:
            hint_text = self.font_small.render("Presiona E para interactuar", True, (255, 255, 255))
            hint_bg = pygame.Rect(player.x * self.game_map.tile_size - camera_x - 70, 
                                 player.y * self.game_map.tile_size - camera_y - 25, 
                                 140, 20)
            pygame.draw.rect(self.screen, (0, 0, 0, 128), hint_bg, border_radius=5)
            self.screen.blit(hint_text, (player.x * self.game_map.tile_size - camera_x - 65, 
                                       player.y * self.game_map.tile_size - camera_y - 20))
    
    def draw_game_over_screen(self, game_state):
        """Dibuja la pantalla de fin de juego"""
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))
        
        if game_state.victory:
            result_text = self.font_xlarge.render("¡VICTORIA!", True, (0, 255, 0))
            reason_text = self.font_large.render(f"Has ganado ${game_state.total_earnings}", True, (255, 255, 255))
        else:
            result_text = self.font_xlarge.render("DERROTA", True, (255, 0, 0))
            reason_text = self.font_large.render(game_state.game_over_reason, True, (255, 255, 255))
        
        self.screen.blit(result_text, (self.screen_width // 2 - result_text.get_width() // 2, self.screen_height // 2 - 50))
        self.screen.blit(reason_text, (self.screen_width // 2 - reason_text.get_width() // 2, self.screen_height // 2))
        
        # Mostrar estadísticas finales
        stats = game_state.get_game_stats()
        final_score = self.font_medium.render(f"Puntaje Final: {stats['final_score']}", True, (255, 255, 255))
        self.screen.blit(final_score, (self.screen_width // 2 - final_score.get_width() // 2, self.screen_height // 2 + 25))
        
        orders_text = self.font_small.render(f"Pedidos completados: {stats['orders_completed']}", True, (255, 255, 255))
        self.screen.blit(orders_text, (self.screen_width // 2 - orders_text.get_width() // 2, self.screen_height // 2 + 45))
        
        restart_text = self.font_medium.render("Presiona R para reiniciar", True, (255, 255, 255))
        self.screen.blit(restart_text, (self.screen_width // 2 - restart_text.get_width() // 2, self.screen_height // 2 + 70))
    
    def update(self, dt):
        """Actualiza el estado del UI Manager"""
        self.update_messages(dt)
    
    def draw_progress_bar(self, x, y, width, height, progress, bg_color=(200, 200, 200), fg_color=(0, 200, 0)):
        """Dibuja una barra de progreso genérica"""
        # Fondo
        pygame.draw.rect(self.screen, bg_color, (x, y, width, height))
        # Progreso
        progress_width = int(width * min(1.0, max(0.0, progress)))
        pygame.draw.rect(self.screen, fg_color, (x, y, progress_width, height))
        # Borde
        pygame.draw.rect(self.screen, (0, 0, 0), (x, y, width, height), 1)
    
    def draw_minimap(self, x, y, size, player, active_orders, game_map):
        """Dibuja un minimapa del área"""
        # Fondo del minimapa
        pygame.draw.rect(self.screen, (50, 50, 50), (x, y, size, size))
        pygame.draw.rect(self.screen, (255, 255, 255), (x, y, size, size), 2)
        
        # Escala del minimapa
        scale_x = size / game_map.width
        scale_y = size / game_map.height
        
        # Dibujar elementos del mapa simplificados
        for row_idx, row in enumerate(game_map.tiles):
            for col_idx, tile in enumerate(row):
                tile_x = x + col_idx * scale_x
                tile_y = y + row_idx * scale_y
                
                if tile == "B":  # Edificios
                    pygame.draw.rect(self.screen, (100, 100, 100), 
                                   (tile_x, tile_y, max(1, scale_x), max(1, scale_y)))
                elif tile == "P":  # Parques
                    pygame.draw.rect(self.screen, (0, 100, 0), 
                                   (tile_x, tile_y, max(1, scale_x), max(1, scale_y)))
        
        # Dibujar pedidos activos
        for i, order in enumerate(active_orders):
            color = self.job_colors[i % len(self.job_colors)]
            
            # Punto de recogida
            pickup_x = x + order.pickup[0] * scale_x
            pickup_y = y + order.pickup[1] * scale_y
            pygame.draw.circle(self.screen, color, (int(pickup_x), int(pickup_y)), 2)
            
            # Punto de entrega
            dropoff_x = x + order.dropoff[0] * scale_x
            dropoff_y = y + order.dropoff[1] * scale_y
            pygame.draw.rect(self.screen, color, 
                           (int(dropoff_x-1), int(dropoff_y-1), 2, 2))
        
        # Dibujar jugador
        player_x = x + player.x * scale_x
        player_y = y + player.y * scale_y
        pygame.draw.circle(self.screen, (255, 0, 0), (int(player_x), int(player_y)), 3)
    
    def draw_order_details_popup(self, order, mouse_pos):
        """Dibuja un popup con detalles de un pedido"""
        if not order:
            return
        
        # Contenido del popup
        lines = [
            f"ID: {order.id}",
            f"Recogida: {order.pickup}",
            f"Entrega: {order.dropoff}",
            f"Pago: ${order.payout}",
            f"Peso: {order.weight}kg",
            f"Prioridad: {order.priority}",
            f"Límite: {order.deadline.strftime('%H:%M')}"
        ]
        
        # Calcular tamaño del popup
        max_width = max(self.font_small.get_size(line)[0] for line in lines) + 20
        popup_height = len(lines) * 15 + 10
        
        # Posición del popup (evitar bordes de pantalla)
        popup_x = min(mouse_pos[0] + 10, self.screen_width - max_width - 10)
        popup_y = min(mouse_pos[1] + 10, self.screen_height - popup_height - 10)
        
        # Fondo del popup
        pygame.draw.rect(self.screen, (255, 255, 255), 
                        (popup_x, popup_y, max_width, popup_height))
        pygame.draw.rect(self.screen, (0, 0, 0), 
                        (popup_x, popup_y, max_width, popup_height), 2)
        
        # Dibujar texto
        for i, line in enumerate(lines):
            text_surface = self.font_small.render(line, True, (0, 0, 0))
            self.screen.blit(text_surface, (popup_x + 10, popup_y + 5 + i * 15))
    
    def draw_keyboard_shortcuts(self):
        """Dibuja los atajos de teclado disponibles"""
        shortcuts = [
            "WASD/Flechas: Moverse",
            "E: Interactuar",
            "R: Reiniciar (fin de juego)",
            "Ctrl+S: Guardar",
            "Ctrl+L: Cargar",
            "Ctrl+Z: Deshacer"
        ]
        
        y_start = self.screen_height - len(shortcuts) * 15 - 10
        
        for i, shortcut in enumerate(shortcuts):
            text = self.font_small.render(shortcut, True, (100, 100, 100))
            self.screen.blit(text, (10, y_start + i * 15))
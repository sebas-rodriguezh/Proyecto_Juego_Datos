class Speed_Movement:
    """Sistema que gestiona la velocidad y movimiento del jugador"""
    
    def __init__(self, velocidad_base: float = 3.0):
        self.velocidad_base = velocidad_base  # celdas/segundo
        self.estado_resistencia = 0.0    
        self.reputacion_actual = 0.0
        self.peso_total = 0.0
        self.multiplicador_limite = 1.0
        
        # Definición de pesos de superficie
        self.pesos_superficie = {
            "asfalto": 1.0,
            "parque": 0.95,
            "tierra": 0.85,
            "arena": 0.7,
            "agua": 0.4,
            "nieve": 0.6,
            "hielo": 0.5
        }
        
        
        # Mapa y clima
        
        
        # Multiplicadores de resistencia
        self.multiplicadores_resistencia = {
            "normal": 1.0,
            "tired": 0.8,
            "exhausted": 0.0
        }
    
    def configurar_limite(self, multiplicador: float):
        """Configura el multiplicador de límite (Melima)"""
        self.multiplicador_limite = max(0.0, multiplicador)
    
    def actualizar_reputacion(self, reputacion: float):
        """Actualiza la reputación del jugador"""
        self.reputacion_actual = max(0.0, min(100.0, reputacion))
    
    def actualizar_peso(self, peso: float):
        """Actualiza el peso total que carga el jugador"""
        self.peso_total = max(0.0, peso)
    
    def cambiar_estado_resistencia(self, estado: str):
        """Cambia el estado de resistencia del jugador"""
        if estado in self.multiplicadores_resistencia:
            self.estado_resistencia = estado
        else:
            print(f"Estado de resistencia no válido: {estado}")
    
    def calcular_multiplicador_peso(self) -> float:
        """Calcula Mpeso = max(0.8, 1 - 0.03 * peso_total)"""
        return max(0.8, 1 - 0.03 * self.peso_total)
    
    def calcular_multiplicador_reputacion(self) -> float:
        """Calcula Mrep = 1.03 si reputación ≥ 90, si no 1.0"""
        return 1.03 if self.reputacion_actual >= 90 else 1.0
    
    def obtener_multiplicador_resistencia(self) -> float:
        """Obtiene Mresistencia según el estado actual"""
        return self.multiplicadores_resistencia[self.estado_resistencia]
    
    def obtener_peso_superficie(self, tipo_superficie: str) -> float:
        """Obtiene el surface_weight según el tipo de superficie"""
        return self.pesos_superficie.get(tipo_superficie, 1.0)
    
    def calcular_velocidad_final(self, tipo_superficie: str) -> float:
        #Calcula la velocidad final usando la fórmula completa

        try:
            # Calcular cada componente
            m_peso = self.calcular_multiplicador_peso()
            m_rep = self.calcular_multiplicador_reputacion()
            m_resistencia = self.obtener_multiplicador_resistencia()
            peso_superficie = self.obtener_peso_superficie(tipo_superficie)
            
            # Aplicar fórmula completa
            velocidad_final = (
                self.velocidad_base *
                self.multiplicador_limite *
                m_peso *
                m_rep *
                m_resistencia *
                peso_superficie
            )
            
            # Velocidad nunca puede ser negativa
            return max(0.0, velocidad_final)
            
        except Exception as e:
            print(f"Error al calcular velocidad: {e}")
            return 0.0
    
    def calcular_tiempo_recorrido(self, distancia_celdas: float, tipo_superficie: str) -> float:
        """
        Calcula el tiempo en segundos para recorrer una distancia dada
        """
        velocidad = self.calcular_velocidad_final(tipo_superficie)
        if velocidad <= 0:
            return float('inf')  # No se puede mover
        return distancia_celdas / velocidad
    
    def obtener_estado_movimiento(self, tipo_superficie: str) -> dict:
        """Devuelve un diccionario con toda la información del movimiento"""
        return {
            "velocidad_base": self.velocidad_base,
            "velocidad_final": self.calcular_velocidad_final(tipo_superficie),
            "multiplicador_limite": self.multiplicador_limite,
            "multiplicador_peso": self.calcular_multiplicador_peso(),
            "multiplicador_reputacion": self.calcular_multiplicador_reputacion(),
            "multiplicador_resistencia": self.obtener_multiplicador_resistencia(),
            "peso_superficie": self.obtener_peso_superficie(tipo_superficie),
            "peso_total": self.peso_total,
            "reputacion": self.reputacion_actual,
            "estado_resistencia": self.estado_resistencia,
            "superficie_actual": tipo_superficie
        }

# Ejemplo de uso
if __name__ == "__main__":
    # Crear sistema de movimiento
    sistema_mov = SistemaMovimiento(velocidad_base=3.0)
    
    # Configurar estado del jugador
    sistema_mov.configurar_limite(1.0)  # Sin límite especial
    sistema_mov.actualizar_reputacion(95.0)  # Buena reputación
    sistema_mov.actualizar_peso(5.0)  # 5kg de carga
    sistema_mov.cambiar_estado_resistencia("normal")
    
    # Calcular velocidad en diferentes superficies
    velocidad_asfalto = sistema_mov.calcular_velocidad_final("asfalto")
    velocidad_parque = sistema_mov.calcular_velocidad_final("parque")
    velocidad_arena = sistema_mov.calcular_velocidad_final("arena")
    
    print(f"Velocidad en asfalto: {velocidad_asfalto:.2f} celdas/seg")
    print(f"Velocidad en parque: {velocidad_parque:.2f} celdas/seg")
    print(f"Velocidad en arena: {velocidad_arena:.2f} celdas/seg")
    
    # Obtener estado completo
    estado = sistema_mov.obtener_estado_movimiento("asfalto")
    print(f"\nEstado completo: {estado}")
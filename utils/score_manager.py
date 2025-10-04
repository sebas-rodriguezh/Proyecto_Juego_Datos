
import json
import os
from datetime import datetime
from typing import List, Dict, Any

class ScoreManager:
    """Gestor de puntajes del juego Courier Quest"""
    
    def __init__(self, filename="data/puntajes.json"):
        self.filename = filename
        self.scores = []
        self.initialized = False
        self._ensure_data_directory()
    
    def _ensure_data_directory(self):
        """Asegura que el directorio data existe"""
        try:
            os.makedirs("data", exist_ok=True)
        except Exception as e:
            print(f" Error creando directorio data: {e}")
    
    def initialize_score_system(self) -> bool:
        """Inicializa el sistema de puntuación"""
        try:
            if self.initialized:
                return True
                
            # Verificar/Crear directorio
            self._ensure_data_directory()
            
            # Verificar/Crear archivo si no existe
            if not os.path.exists(self.filename):
                print("Creando nuevo archivo de puntuaciones...")
                self._create_initial_file()
            else:
                print(" Archivo de puntuaciones encontrado, cargando...")
            
            # Cargar puntuaciones existentes
            self.load_scores()
            
            self.initialized = True
            print(f" Sistema de puntuación inicializado. {len(self.scores)} puntuaciones cargadas")
            return True
            
        except Exception as e:
            print(f" Error crítico inicializando sistema de puntuación: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_scores(self) -> None:
        """Carga los puntajes desde el archivo JSON"""
        try:
            if not os.path.exists(self.filename):
                self.scores = []
                print(" Archivo de puntuaciones no existe, usando lista vacía")
                return
            
            with open(self.filename, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                self.scores = []
                print(" Archivo de puntuaciones vacío")
            else:
                self.scores = json.loads(content)
                if not isinstance(self.scores, list):
                    print(" Formato inválido, reiniciando puntuaciones")
                    self.scores = []
                else:
                    print(f" {len(self.scores)} puntuaciones cargadas correctamente")
                    
        except json.JSONDecodeError as e:
            print(f" Error de formato JSON: {e}")
            print(" Creando nuevo archivo de puntuaciones...")
            self.scores = []
            self._create_initial_file()
        except Exception as e:
            print(f" Error cargando puntuaciones: {e}")
            self.scores = []
    
    def _create_initial_file(self):
        """Crea el archivo inicial con array vacío"""
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2, ensure_ascii=False)
            print(" Archivo de puntuaciones inicial creado exitosamente")
        except Exception as e:
            print(f" Error creando archivo de puntuaciones: {e}")
    
    def save_scores(self) -> bool:
        """Guarda los puntajes en el archivo JSON"""
        try:
            if not self.initialized:
                print(" Sistema no inicializado, inicializando...")
                self.initialize_score_system()
            
            self._ensure_data_directory()
            
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.scores, f, indent=2, ensure_ascii=False)
            
            print(f" {len(self.scores)} puntuaciones guardadas correctamente")
            return True
            
        except Exception as e:
            print(f" Error guardando puntuaciones: {e}")
            return False
    
    def add_score(self, game_state, victory: bool, game_duration: float, total_game_duration: float = 900, player_name: str = "Jugador") -> bool:
        """Añade un nuevo puntaje desde GameState"""
        try:
            print(f" Iniciando guardado de puntuación...")
            
            # 1. Verificar inicialización del sistema
            if not self.initialized:
                print(" Sistema no inicializado, inicializando...")
                if not self.initialize_score_system():
                    print(" No se pudo inicializar el sistema de puntuación")
                    return False
            
            # 2. Validaciones del estado del juego
            if not game_state:
                print(" game_state es None")
                return False
                
            if not hasattr(game_state, 'game_over'):
                print(" game_state no tiene atributo game_over")
                return False
                
            if not game_state.game_over:
                print(" El juego no ha terminado, no se puede guardar puntuación")
                return False
            
            # 3. Verificar referencia al jugador
            if not hasattr(game_state, 'player') or game_state.player is None:
                print(" No hay referencia al jugador en game_state")
                return False
            
            # 4. Calcular puntaje final
            final_score = game_state.calculate_final_score(game_duration, total_game_duration)
            print(f" Puntaje calculado: {final_score}")
            
            # 5. Crear entrada de puntuación
            score_entry = {
                "player_name": player_name,
                "score": int(final_score),
                "earnings": int(game_state.total_earnings),
                "orders_cancelled": int(game_state.orders_cancelled),
                "late_deliveries": int(game_state.late_deliveries),
                "best_streak": int(game_state.best_streak),
                "victory": victory,
                "date": datetime.now().isoformat(),
                "game_duration": float(game_duration),
                "final_reputation": int(game_state.player.reputation)
            }
            
            # 6. Añadir y ordenar puntuaciones
            self.scores.append(score_entry)
            self.sort_scores()
            
            # 7. Mantener solo los top 10 puntajes
            if len(self.scores) > 10:
                self.scores = self.scores[:10]
            
            # 8. Guardar en archivo
            success = self.save_scores()
            
            if success:
                pass
            else:
                print(" Error al guardar puntuaciones en archivo")
            
            return success
            
        except Exception as e:
            print(f" Error crítico al añadir puntaje: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def sort_scores(self) -> None:
        """Ordena los puntajes de mayor a menor usando Bubble Sort - Complejidad: O(n²)"""
        n = len(self.scores)
        
        if n <= 1:
            return
        
        for i in range(n - 1):
            swapped = False
            for j in range(0, n - i - 1):
                if self.scores[j].get("score", 0) < self.scores[j + 1].get("score", 0):
                    self.scores[j], self.scores[j + 1] = self.scores[j + 1], self.scores[j]
                    swapped = True
            
            if not swapped:
                break
        
        
    
    def get_top_scores(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene los mejores puntajes"""
        if not self.initialized:
            print("🔄 Sistema no inicializado al obtener puntuaciones")
            self.initialize_score_system()
        
        return self.scores[:limit]
    
    def get_score_count(self) -> int:
        """Retorna la cantidad de puntajes guardados"""
        if not self.initialized:
            return 0
        return len(self.scores)
    
    def get_ranking_position(self, score: int) -> int:
        """Obtiene la posición en el ranking para un puntaje dado"""
        if not self.initialized or not self.scores:
            return 1
            
        for i, entry in enumerate(self.scores):
            if score >= entry.get("score", 0):
                return i + 1
        return len(self.scores) + 1
    
    def debug_info(self):
        """Información de depuración"""
        return {
            "initialized": self.initialized,
            "filename": self.filename,
            "file_exists": os.path.exists(self.filename),
            "scores_count": len(self.scores),
            "top_scores": self.get_top_scores(3)
        }

score_manager = ScoreManager()


def initialize_score_system():
    """Función para inicializar el sistema de puntajes"""
    try:
        print(" Inicializando sistema de puntuación global...")
        success = score_manager.initialize_score_system()
        
        if success:
            print(" Sistema de puntuación global inicializado exitosamente")
        else:
            print(" Falló la inicialización del sistema de puntuación global")
            
        return success
    except Exception as e:
        print(f" Error crítico inicializando sistema de puntuaciones global: {e}")
        return False
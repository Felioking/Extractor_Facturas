"""
Módulo de logging para la aplicación de extracción de facturas
"""
import logging
import sys
from pathlib import Path
import os

# Agregar el directorio raíz al path para importar config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def setup_logging():
    """
    Configurar el sistema de logging de la aplicación
    """
    # Crear directorio de logs si no existe
    config.LOG_FOLDER.mkdir(exist_ok=True)
    
    # Configurar formato del log
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Configurar logging básico
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(config.LOG_FOLDER / 'app.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Logger específico para la aplicación
    logger = logging.getLogger('extractor_facturas')
    logger.setLevel(logging.INFO)
    
    return logger


def get_logger(name):
    """
    Obtener un logger con el nombre especificado
    
    Args:
        name (str): Nombre del logger
        
    Returns:
        logging.Logger: Instancia del logger
    """
    return logging.getLogger(name)


class ProgressLogger:
    """
    Logger especializado para mostrar progreso de operaciones
    """
    
    def __init__(self, operation_name, total_steps=100):
        self.operation_name = operation_name
        self.total_steps = total_steps
        self.current_step = 0
        self.logger = get_logger(f'progress.{operation_name}')
    
    def start(self):
        """Iniciar operación"""
        self.logger.info(f"Iniciando: {self.operation_name}")
        self.current_step = 0
    
    def update(self, message, step_increment=1):
        """Actualizar progreso"""
        self.current_step += step_increment
        progress = (self.current_step / self.total_steps) * 100
        self.logger.info(f"[{progress:.1f}%] {message}")
    
    def complete(self, message="Operación completada"):
        """Completar operación"""
        self.logger.info(f"Completado: {self.operation_name} - {message}")
    
    def error(self, message):
        """Registrar error"""
        self.logger.error(f"Error en {self.operation_name}: {message}")


# Configurar logging al importar el módulo
app_logger = setup_logging()

if __name__ == "__main__":
    # Prueba del módulo
    logger = get_logger('test')
    logger.info("✅ Módulo de logging funcionando correctamente")
    
    # Probar ProgressLogger
    progress = ProgressLogger("Procesamiento de facturas", 5)
    progress.start()
    progress.update("Leyendo archivos")
    progress.update("Extrayendo texto")
    progress.update("Procesando datos")
    progress.update("Guardando en BD")
    progress.update("Generando reporte")
    progress.complete("5 facturas procesadas")
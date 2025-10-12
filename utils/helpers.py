"""
Utilidades y funciones auxiliares
"""

import os
import logging
import logging.handlers
from datetime import datetime
from typing import Any, Dict, List
import sys

class Helpers:
    """Clase con funciones auxiliares"""
    
    @staticmethod
    def setup_logging(log_file: str = "app.log", level=logging.INFO, max_bytes=10*1024*1024, backup_count=5):
        """
        Configura el sistema de logging robusto
        
        Args:
            log_file: Ruta del archivo de log
            level: Nivel de logging
            max_bytes: Tamaño máximo del archivo de log antes de rotar
            backup_count: Número de archivos de backup a mantener
        """
        try:
            # Crear directorio de logs si no existe
            log_dir = os.path.dirname(log_file) if os.path.dirname(log_file) else "logs"
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # Configurar formato
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # Configurar logger raíz
            logger = logging.getLogger()
            logger.setLevel(level)
            
            # Evitar logs duplicados
            if logger.handlers:
                logger.handlers.clear()
            
            # Handler para archivo con rotación
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(level)
            
            # Handler para consola
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.INFO)  # Consola solo muestra INFO y superior
            
            # Agregar handlers
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
            
            # Loggers específicos para diferentes módulos
            Helpers._setup_module_loggers(level, formatter)
            
            logging.info("✓ Sistema de logging configurado correctamente")
            logging.info(f"✓ Logs guardados en: {log_file}")
            
        except Exception as e:
            print(f"✗ Error configurando logging: {e}")
    
    @staticmethod
    def _setup_module_loggers(level, formatter):
        """Configura loggers específicos para diferentes módulos"""
        modules = ['database', 'ocr', 'processing', 'ui']
        
        for module in modules:
            module_logger = logging.getLogger(module)
            module_logger.setLevel(level)
    
    @staticmethod
    def log_function_call(func):
        """Decorator para loggear llamadas a funciones"""
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            logger.debug(f"Llamando {func.__name__} con args: {args}, kwargs: {kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"Función {func.__name__} completada exitosamente")
                return result
            except Exception as e:
                logger.error(f"Error en {func.__name__}: {str(e)}", exc_info=True)
                raise
        return wrapper
    
    @staticmethod
    def format_currency(amount: float) -> str:
        """Formatea un monto como moneda"""
        try:
            return f"RD$ {amount:,.2f}"
        except (ValueError, TypeError):
            return "RD$ 0.00"
    
    @staticmethod
    def safe_float(value: Any, default: float = 0.0) -> float:
        """Convierte seguro a float"""
        try:
            if isinstance(value, (int, float)):
                return float(value)
            elif isinstance(value, str):
                cleaned = ''.join(c for c in value if c.isdigit() or c == '.')
                return float(cleaned) if cleaned else default
            else:
                return default
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def validate_file_path(file_path: str) -> bool:
        """Valida que la ruta de archivo exista"""
        return os.path.exists(file_path) and os.path.isfile(file_path)
    
    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """Obtiene la extensión de un archivo"""
        return os.path.splitext(file_path)[1].lower()
    
    @staticmethod
    def is_image_file(file_path: str) -> bool:
        """Verifica si un archivo es una imagen"""
        valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        return Helpers.get_file_extension(file_path) in valid_extensions
    
    @staticmethod
    def create_backup_filename(original_path: str, suffix: str = "backup") -> str:
        """Crea un nombre de archivo para backup"""
        base, ext = os.path.splitext(original_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base}_{suffix}_{timestamp}{ext}"
    
    @staticmethod
    def dict_to_string(data: Dict[str, Any], separator: str = " | ") -> str:
        """Convierte un diccionario a string legible"""
        parts = []
        for key, value in data.items():
            if value:
                parts.append(f"{key}: {value}")
        return separator.join(parts)
    
    @staticmethod
    def list_to_string(items: List[Any], separator: str = ", ") -> str:
        """Convierte una lista a string"""
        return separator.join(str(item) for item in items if item)
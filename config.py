"""
Configuraciones y constantes de la aplicación
"""

import os
import pytesseract
from utils.constants import *

class Config:
    """Clase de configuración de la aplicación"""
    
    # Configuración de Tesseract
    TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    # Base de datos
    DATABASE_NAME = 'facturas.db'
    
    # Configuración de Logging
    LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FILE = 'logs/app.log'
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Configuración de OCR
    OCR_LANGUAGES = ['spa', 'eng']
    OCR_CONFIG = '--oem 3 --psm 6'
    
    # Patrones regex para extracción
    PATTERNS = {
        'rnc': [
            r'RNC\s*:?\s*(\d{9}|\d{3}-\d{7}-\d{1})',
            r'R\.N\.C\.\s*:?\s*(\d{9}|\d{3}-\d{7}-\d{1})',
            r'IDENTIFICACION\s*:?\s*(\d{9}|\d{3}-\d{7}-\d{1})',
            r'(\d{3}-\d{7}-\d{1})',
            r'(\d{9})'
        ],
        'ncf': [
            r'NCF\s*:?\s*([A-Z]\d{2}\d{11})',
            r'COMPROBANTE\s*:?\s*([A-Z]\d{2}\d{11})',
            r'NO\.?\s*COMPROBANTE\s*:?\s*([A-Z]\d{2}\d{11})',
            r'([A-Z]\d{2}\d{11})'
        ],
        'fecha': [
            r'FECHA\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'EMISION\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'FECHA\s*DE\s*EMISION\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        ]
    }
    
    # Tipos de NCF válidos
    NCF_TIPOS_VALIDOS = ['A', 'B', 'E', 'F', 'G', 'H', 'I', 'J', 'K']
    
    @classmethod
    def initialize(cls):
        """Inicializa la configuración de la aplicación"""
        try:
            # Configurar Tesseract
            pytesseract.pytesseract.tesseract_cmd = cls.TESSERACT_PATH
            
            # Crear directorios necesarios
            os.makedirs('exports', exist_ok=True)
            os.makedirs('temp', exist_ok=True)
            os.makedirs('logs', exist_ok=True)
            
            # Configurar logging
            import logging
            from utils.helpers import Helpers
            
            log_level = getattr(logging, cls.LOG_LEVEL)
            Helpers.setup_logging(
                log_file=cls.LOG_FILE,
                level=log_level,
                max_bytes=cls.LOG_MAX_SIZE,
                backup_count=cls.LOG_BACKUP_COUNT
            )
            
            logging.info("✓ Configuración de la aplicación inicializada")
            logging.info(f"✓ Nivel de log: {cls.LOG_LEVEL}")
            logging.info(f"✓ Base de datos: {cls.DATABASE_NAME}")
            
        except Exception as e:
            print(f"✗ Error inicializando configuración: {e}")
            raise
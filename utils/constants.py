"""
Constantes de la aplicación
"""

# Configuración de la aplicación
APP_NAME = "Extractor Inteligente de Facturas"
APP_VERSION = "3.0.0"
APP_AUTHOR = "Sistema de Procesamiento de Facturas"

# Tamaños de ventana
MAIN_WINDOW_WIDTH = 1400
MAIN_WINDOW_HEIGHT = 900
MIN_WINDOW_WIDTH = 1000
MIN_WINDOW_HEIGHT = 700

# Colores (para temas futuros)
COLORS = {
    'primary': '#2c3e50',
    'secondary': '#34495e',
    'accent': '#3498db',
    'success': '#27ae60',
    'warning': '#f39c12',
    'error': '#e74c3c',
    'background': '#ecf0f1',
    'text': '#2c3e50'
}

# Configuración de OCR
OCR_SETTINGS = {
    'default_language': 'spa',
    'fallback_language': 'eng',
    'timeout': 30,
    'dpi': 300
}

# Configuración de base de datos
DB_SETTINGS = {
    'timeout': 30,
    'detect_types': sqlite3.PARSE_DECLTYPES,
    'check_same_thread': False
}

# Mensajes de la aplicación
MESSAGES = {
    'no_image_loaded': "Primero carga una factura",
    'no_folder_loaded': "Primero carga una carpeta con imágenes",
    'processing_started': "Procesando...",
    'processing_completed': "Procesamiento completado",
    'export_success': "Datos exportados correctamente",
    'export_error': "Error al exportar datos",
    'validation_success': "Validación completada",
    'validation_warning': "Advertencias encontradas durante la validación"
}
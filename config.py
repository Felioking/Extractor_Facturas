"""
Configuración de la aplicación Extractor de Facturas
Usa rutas relativas para ser portable entre diferentes sistemas
"""
import os
from pathlib import Path

# Obtener el directorio base del proyecto (donde está config.py)
BASE_DIR = Path(__file__).parent

# Configuración de rutas
UPLOAD_FOLDER = BASE_DIR / 'uploads'
OUTPUT_FOLDER = BASE_DIR / 'output'
LOG_FOLDER = BASE_DIR / 'logs'
DATABASE_FOLDER = BASE_DIR / 'database'

# Crear directorios si no existen
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, LOG_FOLDER, DATABASE_FOLDER]:
    folder.mkdir(exist_ok=True)

# Configuración de la base de datos
DATABASE_PATH = DATABASE_FOLDER / 'facturas.db'

# Configuración de la aplicación
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# Configuración OCR
OCR_CONFIG = {
    'lang': 'spa',
    'oem': 3,
    'psm': 6
}

# Configuración de la interfaz gráfica
UI_CONFIG = {
    'window_title': 'Extractor de Facturas',
    'window_size': '1000x700',
    'theme': 'clam'
}

# Configuración de exportación
EXPORT_CONFIG = {
    'excel_columns': ['nombre', 'rfc', 'fecha', 'total', 'uuid', 'archivo_origen'],
    'word_template': None  # Puedes agregar una plantilla DOCX después
}

def get_config():
    """Retornar la configuración como diccionario"""
    return {
        'upload_folder': str(UPLOAD_FOLDER),
        'output_folder': str(OUTPUT_FOLDER),
        'log_folder': str(LOG_FOLDER),
        'database_path': str(DATABASE_PATH),
        'allowed_extensions': ALLOWED_EXTENSIONS,
        'max_file_size': MAX_FILE_SIZE,
        'ocr_config': OCR_CONFIG,
        'ui_config': UI_CONFIG,
        'export_config': EXPORT_CONFIG
    }

# Prueba de configuración
if __name__ == "__main__":
    config = get_config()
    print("✅ Configuración cargada correctamente")
    for key, value in config.items():
        if key not in ['ocr_config', 'ui_config', 'export_config']:
            print(f"   {key}: {value}")
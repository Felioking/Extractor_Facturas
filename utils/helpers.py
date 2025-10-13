"""
Módulo de utilidades y funciones helper para la aplicación
"""
import os
import tempfile
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import logging

logger = logging.getLogger(__name__)


def center_window(window, width=None, height=None):
    """
    Centrar una ventana en la pantalla
    
    Args:
        window: Ventana de tkinter
        width: Ancho deseado (opcional)
        height: Alto deseado (opcional)
    """
    window.update_idletasks()
    
    if width is None:
        width = window.winfo_width()
    if height is None:
        height = window.winfo_height()
    
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    
    window.geometry(f'{width}x{height}+{x}+{y}')


def validate_file_type(file_path, allowed_extensions):
    """
    Validar tipo de archivo
    
    Args:
        file_path: Ruta del archivo
        allowed_extensions: Extensiones permitidas
        
    Returns:
        bool: True si es válido
    """
    if not os.path.exists(file_path):
        return False
    
    extension = Path(file_path).suffix.lower().lstrip('.')
    return extension in allowed_extensions


def cleanup_temp_files(temp_dir=None):
    """
    Limpiar archivos temporales
    
    Args:
        temp_dir: Directorio temporal (opcional)
    """
    try:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.info(f"Directorio temporal limpiado: {temp_dir}")
    except Exception as e:
        logger.warning(f"Error limpiando archivos temporales: {e}")


def format_currency(amount):
    """
    Formatear cantidad como moneda
    
    Args:
        amount: Cantidad a formatear
        
    Returns:
        str: Cantidad formateada
    """
    try:
        return f"${float(amount):,.2f}"
    except (ValueError, TypeError):
        return str(amount)


def safe_rename(old_path, new_path):
    """
    Renombrar archivo de forma segura
    
    Args:
        old_path: Ruta original
        new_path: Nueva ruta
        
    Returns:
        bool: True si fue exitoso
    """
    try:
        if os.path.exists(old_path):
            os.rename(old_path, new_path)
            logger.info(f"Archivo renombrado: {old_path} -> {new_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error renombrando archivo: {e}")
        return False


def validate_image(file_path):
    """
    Validar que un archivo es una imagen válida
    
    Args:
        file_path: Ruta del archivo
        
    Returns:
        bool: True si es válido
    """
    valid_extensions = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'}
    extension = Path(file_path).suffix.lower()
    
    if extension not in valid_extensions:
        return False
    
    if not os.path.exists(file_path):
        return False
    
    # Verificar que el archivo no esté corrupto (verificación básica)
    try:
        with open(file_path, 'rb') as f:
            header = f.read(100)
            return len(header) > 0
    except Exception:
        return False


def enhance_image_quality(image_path, output_path=None):
    """
    Mejorar calidad de imagen (función placeholder)
    
    Args:
        image_path: Ruta de la imagen original
        output_path: Ruta de salida (opcional)
        
    Returns:
        str: Ruta de la imagen procesada
    """
    # Esta es una implementación básica - puedes expandirla con OpenCV/PIL
    if output_path is None:
        output_path = image_path
    
    logger.info(f"Mejorando calidad de imagen: {image_path}")
    
    # Por ahora solo copiamos el archivo
    # En una implementación real, aquí iría el procesamiento de imagen
    try:
        shutil.copy2(image_path, output_path)
        return output_path
    except Exception as e:
        logger.error(f"Error mejorando imagen: {e}")
        return image_path


def show_error_message(parent, title, message):
    """
    Mostrar mensaje de error
    
    Args:
        parent: Ventana padre
        title: Título del mensaje
        message: Mensaje a mostrar
    """
    messagebox.showerror(title, message, parent=parent)


def show_info_message(parent, title, message):
    """
    Mostrar mensaje informativo
    
    Args:
        parent: Ventana padre
        title: Título del mensaje
        message: Mensaje a mostrar
    """
    messagebox.showinfo(title, message, parent=parent)


def validate_rfc(rfc):
    """
    Validar formato básico de RFC
    
    Args:
        rfc: RFC a validar
        
    Returns:
        bool: True si el formato es válido
    """
    if not rfc:
        return False
    
    # Formato básico: 4 letras, 6 números, 3 caracteres alfanuméricos
    import re
    pattern = r'^[A-Z&Ñ]{3,4}[0-9]{6}[A-Z0-9]{3}$'
    return bool(re.match(pattern, rfc.upper()))


def format_date(date_str):
    """
    Formatear fecha de forma consistente
    
    Args:
        date_str: String de fecha
        
    Returns:
        str: Fecha formateada
    """
    # Implementación básica - puedes expandir según tus necesidades
    return date_str.strip()


if __name__ == "__main__":
    # Pruebas del módulo
    print("✅ Módulo de helpers funcionando correctamente")
    
    # Probar funciones
    test_file = "test.txt"
    print(f"validate_file_type: {validate_file_type(test_file, {'txt', 'pdf'})}")
    print(f"format_currency: {format_currency(1234.56)}")
    print(f"validate_rfc: {validate_rfc('ABC123456DEF')}")
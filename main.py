#!/usr/bin/env python3
"""
Punto de entrada principal de la aplicación Extractor de Facturas
"""

import tkinter as tk
import logging
import traceback
from ui.main_window import MainWindow
from config import Config

def setup_exception_handling():
    """Configura el manejo global de excepciones"""
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # Permitir Ctrl+C
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logging.critical(
            "Excepción no capturada:",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        
        # Mostrar mensaje de error al usuario
        try:
            tk.messagebox.showerror(
                "Error Crítico",
                f"Ha ocurrido un error inesperado:\n\n{str(exc_value)}\n\n"
                f"Revisa el archivo de logs para más detalles."
            )
        except:
            pass  # Si TK no está disponible, solo loggear
    
    # Configurar handler global de excepciones
    import sys
    sys.excepthook = handle_exception

def main():
    """Función principal de la aplicación"""
    try:
        print("🚀 Iniciando Sistema Avanzado de Extracción de Facturas...")
        
        # Configuración inicial
        Config.initialize()
        
        # Configurar manejo de excepciones
        setup_exception_handling()
        
        logging.info("=" * 60)
        logging.info("INICIANDO APLICACIÓN EXTRACTOR DE FACTURAS")
        logging.info("=" * 60)
        
        # Crear ventana principal
        root = tk.Tk()
        app = MainWindow(root)
        
        logging.info("✓ Aplicación iniciada correctamente")
        
        # Iniciar loop principal
        root.mainloop()
        
        logging.info("Aplicación finalizada correctamente")
        
    except Exception as e:
        logging.critical(f"Error crítico al iniciar la aplicación: {e}", exc_info=True)
        tk.messagebox.showerror(
            "Error Crítico", 
            f"No se pudo iniciar la aplicación:\n\n{str(e)}\n\n"
            f"Revisa el archivo logs/app.log para más detalles."
        )

if __name__ == "__main__":
    main()
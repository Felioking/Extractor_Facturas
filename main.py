# main.py
import tkinter as tk
import logging
import sys
import os

from typing import Any

# Agregar el directorio actual al path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Función principal de la aplicación"""
    print("🚀 Iniciando Sistema Avanzado de Extracción de Facturas...")
    
    try:
        # Importar la interfaz gráfica
        from ui.gui import ExtractorFacturasApp
        
        # Crear ventana principal
        root = tk.Tk()
        
        # Configurar la aplicación
        app = ExtractorFacturasApp(root)
        
        # Iniciar el loop principal
        root.mainloop()
        
    except ImportError as e:
        error_msg = f"Error de importación: {e}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        print("💡 Asegúrate de que todos los módulos estén correctamente instalados")
        
    except Exception as e:
        error_msg = f"Error al iniciar la aplicación: {e}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        
        # Intentar mostrar mensaje de error en GUI si es posible
        try:
            from tkinter import messagebox
            messagebox.showerror("Error Crítico", 
                               f"No se pudo iniciar la aplicación:\n{str(e)}\n\n"
                               f"Revisa el archivo logs/app.log para más detalles.")
        except:
            # Fallback si no se puede mostrar la GUI de error
            print("💡 Revisa el archivo logs/app.log para más detalles")

if __name__ == "__main__":
    main()
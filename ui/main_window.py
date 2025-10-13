"""
Ventana principal de la aplicación de extracción de facturas
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from ui.components.tabs import MainTabs
from utils.helpers import center_window

logger = logging.getLogger(__name__)


class MainWindow:
    """Ventana principal de la aplicación"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.root = None
        self.tabs = None
        
    def _setup_window(self):
        """Configurar la ventana principal"""
        self.root = tk.Tk()
        self.root.title("Extractor de Facturas - Sistema Avanzado")
        self.root.geometry("1200x800")
        
        # Icono de la aplicación (opcional)
        try:
            self.root.iconbitmap("assets/icon.ico")  # Si tienes un icono
        except:
            pass  # Si no hay icono, continuar sin él
        
        # Configurar estilo
        self._setup_styles()
        
        # Centrar ventana
        center_window(self.root, 1200, 800)
        
        # Proteger contra cierre accidental
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _setup_styles(self):
        """Configurar estilos de la interfaz"""
        style = ttk.Style()
        
        # Configurar tema
        try:
            style.theme_use('clam')  # Tema moderno
        except:
            pass  # Usar tema por defecto si 'clam' no está disponible
        
        # Configurar colores y fuentes
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        style.configure('TButton', font=('Arial', 10))
        style.configure('Header.TLabel', font=('Arial', 14, 'bold'))
        
    def _setup_ui(self):
        """Configurar la interfaz de usuario"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill='x', pady=(0, 10))
        
        title_label = ttk.Label(
            header_frame, 
            text="📄 Sistema Avanzado de Extracción de Facturas",
            style='Header.TLabel'
        )
        title_label.pack(pady=10)
        
        # Pestañas principales
        self.tabs = MainTabs(main_frame, self.db_manager)
        
        # Status bar
        self._setup_status_bar(main_frame)
    
    def _setup_status_bar(self, parent):
        """Configurar barra de estado"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill='x', pady=(10, 0))
        
        self.status_var = tk.StringVar(value="Listo")
        status_label = ttk.Label(
            status_frame, 
            textvariable=self.status_var,
            relief='sunken',
            anchor='w'
        )
        status_label.pack(fill='x', padx=5, pady=2)
    
    def update_status(self, message):
        """Actualizar mensaje en la barra de estado"""
        if hasattr(self, 'status_var'):
            self.status_var.set(message)
        logger.info(f"Status: {message}")
    
    def _on_close(self):
        """Manejar cierre de la aplicación"""
        if messagebox.askokcancel("Salir", "¿Estás seguro de que quieres salir?"):
            try:
                # Cerrar conexión a la base de datos
                if self.db_manager:
                    self.db_manager.close()
                
                # Cerrar ventana
                self.root.destroy()
                logger.info("Aplicación cerrada correctamente")
                
            except Exception as e:
                logger.error(f"Error al cerrar aplicación: {e}")
                self.root.destroy()
    
    def show_error(self, title, message):
        """Mostrar mensaje de error"""
        messagebox.showerror(title, message, parent=self.root)
        logger.error(f"{title}: {message}")
    
    def show_info(self, title, message):
        """Mostrar mensaje informativo"""
        messagebox.showinfo(title, message, parent=self.root)
        logger.info(f"{title}: {message}")
    
    def run(self):
        """Ejecutar la aplicación"""
        try:
            self._setup_window()
            self._setup_ui()
            
            # Actualizar estado inicial
            self.update_status("Aplicación iniciada - Lista para usar")
            
            # Mostrar estadísticas iniciales
            self._show_initial_stats()
            
            # Iniciar loop principal
            logger.info("Interfaz gráfica iniciada correctamente")
            self.root.mainloop()
            
        except Exception as e:
            error_msg = f"Error al iniciar interfaz: {str(e)}"
            logger.critical(error_msg)
            messagebox.showerror("Error Crítico", error_msg)
            raise
    
    def _show_initial_stats(self):
        """Mostrar estadísticas iniciales"""
        try:
            stats = self.db_manager.obtener_estadisticas()
            if stats:
                total_facturas = stats.get('total_facturas', 0)
                total_monetario = stats.get('total_monetario', 0)
                
                if total_facturas > 0:
                    self.update_status(
                        f"Base de datos cargada: {total_facturas} facturas, "
                        f"Total: ${total_monetario:,.2f}"
                    )
                else:
                    self.update_status("Base de datos vacía - Comienza agregando facturas")
            else:
                self.update_status("Error al cargar estadísticas")
                
        except Exception as e:
            logger.warning(f"Error obteniendo estadísticas iniciales: {e}")
            self.update_status("Listo - Error cargando estadísticas")


if __name__ == "__main__":
    # Prueba de la ventana principal
    from database.database_manager import DatabaseManager
    
    try:
        db = DatabaseManager()
        app = MainWindow(db)
        app.run()
    except Exception as e:
        print(f"Error en prueba: {e}")
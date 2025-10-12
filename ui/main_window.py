"""
Ventana principal de la aplicación
"""

import tkinter as tk
from tkinter import ttk
import logging
from ui.components.navigation import NavigationPanel
from ui.components.forms import DataForms
from ui.components.tabs import MainTabs
from ui.dialogs import DialogsManager

class MainWindow:
    """Ventana principal de la aplicación"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Extractor Inteligente de Facturas - v3.0")
        self.root.geometry("1400x900")
        
        # Inicializar componentes
        self.setup_ui()
        self.setup_event_handlers()
        
        logging.info("✓ Ventana principal inicializada")
    
    def setup_ui(self):
        """Configura la interfaz de usuario principal"""
        # Frame principal
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Panel de controles superiores
        self.setup_control_panel()
        
        # Frame de contenido principal
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Panel izquierdo - Navegación e imagen
        self.navigation_panel = NavigationPanel(self.content_frame)
        self.navigation_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Panel derecho - Formularios y datos
        self.data_panel = ttk.LabelFrame(self.content_frame, text="Datos de la Factura", padding="10")
        self.data_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        self.data_panel.configure(width=500)
        self.data_panel.pack_propagate(False)
        
        # Notebook para pestañas
        self.setup_tabs()
    
    def setup_control_panel(self):
        """Configura el panel de controles superiores"""
        control_frame = ttk.LabelFrame(self.main_frame, text="Controles Avanzados", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Fila 1: Navegación
        nav_frame = ttk.Frame(control_frame)
        nav_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(nav_frame, text="📁 Cargar Carpeta", 
                  command=self.on_cargar_carpeta).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(nav_frame, text="📄 Cargar Factura", 
                  command=self.on_cargar_imagen).pack(side=tk.LEFT, padx=(0, 10))
        
        # Fila 2: Procesamiento
        process_frame = ttk.Frame(control_frame)
        process_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(process_frame, text="🔍 Extraer Datos", 
                  command=self.on_extraer_datos).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(process_frame, text="🔄 Procesar Lote", 
                  command=self.on_procesar_lote).pack(side=tk.LEFT, padx=(0, 5))
        
        # Fila 3: Exportación
        export_frame = ttk.Frame(control_frame)
        export_frame.pack(fill=tk.X)
        
        ttk.Button(export_frame, text="💾 Guardar JSON", 
                  command=self.on_guardar_json).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(export_frame, text="📊 Exportar Excel", 
                  command=self.on_exportar_excel).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(export_frame, text="🗑️ Limpiar", 
                  command=self.on_limpiar).pack(side=tk.LEFT, padx=(0, 5))
    
    def setup_tabs(self):
        """Configura las pestañas principales"""
        self.tabs_manager = MainTabs(self.data_panel)
        self.tabs_manager.pack(fill=tk.BOTH, expand=True)
    
    def setup_event_handlers(self):
        """Configura los manejadores de eventos"""
        # Conectar eventos entre componentes
        if hasattr(self.navigation_panel, 'on_image_changed'):
            self.navigation_panel.on_image_changed = self.on_image_changed
    
    def on_cargar_carpeta(self):
        """Maneja el evento de cargar carpeta"""
        try:
            from ui.dialogs import DialogsManager
            folder_path = DialogsManager.select_folder()
            if folder_path:
                self.navigation_panel.load_folder(folder_path)
        except Exception as e:
            logging.error(f"Error cargando carpeta: {e}")
            DialogsManager.show_error("Error al cargar carpeta", str(e))
    
    def on_cargar_imagen(self):
        """Maneja el evento de cargar imagen individual"""
        try:
            from ui.dialogs import DialogsManager
            image_path = DialogsManager.select_image()
            if image_path:
                self.navigation_panel.load_single_image(image_path)
        except Exception as e:
            logging.error(f"Error cargando imagen: {e}")
            DialogsManager.show_error("Error al cargar imagen", str(e))
    
    def on_extraer_datos(self):
        """Maneja el evento de extraer datos"""
        try:
            current_image = self.navigation_panel.get_current_image()
            if not current_image:
                DialogsManager.show_warning("Primero carga una factura")
                return
            
            # Aquí integraríamos con el procesamiento OCR
            logging.info(f"Procesando imagen: {current_image}")
            # TODO: Integrar con OCRProcessor
            
        except Exception as e:
            logging.error(f"Error extrayendo datos: {e}")
            DialogsManager.show_error("Error al extraer datos", str(e))
    
    def on_procesar_lote(self):
        """Maneja el evento de procesar lote"""
        try:
            if not self.navigation_panel.has_images():
                DialogsManager.show_warning("Primero carga una carpeta con imágenes")
                return
            
            # TODO: Implementar procesamiento por lote
            logging.info("Iniciando procesamiento por lote...")
            
        except Exception as e:
            logging.error(f"Error en procesamiento por lote: {e}")
            DialogsManager.show_error("Error en procesamiento por lote", str(e))
    
    def on_guardar_json(self):
        """Maneja el evento de guardar JSON"""
        try:
            # TODO: Implementar guardado de JSON
            logging.info("Guardando datos en JSON...")
            
        except Exception as e:
            logging.error(f"Error guardando JSON: {e}")
            DialogsManager.show_error("Error al guardar JSON", str(e))
    
    def on_exportar_excel(self):
        """Maneja el evento de exportar a Excel"""
        try:
            # TODO: Implementar exportación a Excel
            logging.info("Exportando a Excel...")
            
        except Exception as e:
            logging.error(f"Error exportando a Excel: {e}")
            DialogsManager.show_error("Error al exportar a Excel", str(e))
    
    def on_limpiar(self):
        """Maneja el evento de limpiar datos"""
        try:
            self.navigation_panel.clear()
            self.tabs_manager.clear()
            logging.info("Datos limpiados")
            
        except Exception as e:
            logging.error(f"Error limpiando datos: {e}")
            DialogsManager.show_error("Error al limpiar datos", str(e))
    
    def on_image_changed(self, image_path, image_data):
        """Maneja el evento de cambio de imagen"""
        try:
            # Actualizar la interfaz cuando cambia la imagen
            self.tabs_manager.clear()
            logging.info(f"Imagen cambiada: {image_path}")
            
        except Exception as e:
            logging.error(f"Error manejando cambio de imagen: {e}")
    
    def run(self):
        """Inicia la aplicación"""
        try:
            self.root.mainloop()
        except Exception as e:
            logging.error(f"Error ejecutando aplicación: {e}")
            raise
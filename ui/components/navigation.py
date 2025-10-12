"""
Componente de navegación entre imágenes
"""

import tkinter as tk
from tkinter import ttk
import os
import glob
from PIL import Image, ImageTk
import logging

class NavigationPanel(ttk.Frame):
    """Panel de navegación entre imágenes"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        self.current_image_path = None
        self.image_list = []
        self.current_index = -1
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz del panel de navegación"""
        # Frame de imagen principal
        image_frame = ttk.LabelFrame(self, text="Vista Previa", padding="10")
        image_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Información de la imagen
        self.image_info_label = ttk.Label(image_frame, text="No hay imagen cargada", font=("Arial", 10))
        self.image_info_label.pack(pady=(0, 5))
        
        # Label para mostrar imagen
        self.image_label = ttk.Label(image_frame, text="Seleccione una factura para comenzar", 
                                   background="lightgray", justify=tk.CENTER)
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # Controles de navegación
        self.setup_navigation_controls()
        
        # Panel de proveedores frecuentes
        self.setup_providers_panel()
    
    def setup_navigation_controls(self):
        """Configura los controles de navegación"""
        nav_frame = ttk.Frame(self)
        nav_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Botones de navegación
        ttk.Button(nav_frame, text="⏮️ Anterior", 
                  command=self.previous_image).pack(side=tk.LEFT, padx=(0, 5))
        
        self.nav_label = ttk.Label(nav_frame, text="0/0", width=8)
        self.nav_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(nav_frame, text="⏭️ Siguiente", 
                  command=self.next_image).pack(side=tk.LEFT, padx=(5, 0))
    
    def setup_providers_panel(self):
        """Configura el panel de proveedores frecuentes"""
        providers_frame = ttk.LabelFrame(self, text="🏢 Proveedores Frecuentes", padding="10")
        providers_frame.pack(fill=tk.BOTH, expand=False)
        
        self.providers_text = tk.Text(providers_frame, height=6, font=("Arial", 8), wrap=tk.WORD)
        self.providers_text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(providers_frame, orient=tk.VERTICAL, command=self.providers_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.providers_text.configure(yscrollcommand=scrollbar.set)
        
        self.update_providers_list()
    
    def load_folder(self, folder_path):
        """Carga todas las imágenes de una carpeta"""
        try:
            extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.tif']
            self.image_list = []
            
            for extension in extensions:
                self.image_list.extend(glob.glob(os.path.join(folder_path, extension)))
                self.image_list.extend(glob.glob(os.path.join(folder_path, extension.upper())))
            
            if self.image_list:
                self.image_list.sort()
                self.current_index = 0
                self.show_current_image()
                logging.info(f"✓ Carpeta cargada: {len(self.image_list)} imágenes")
                return True
            else:
                logging.warning("No se encontraron imágenes en la carpeta")
                return False
                
        except Exception as e:
            logging.error(f"Error cargando carpeta: {e}")
            return False
    
    def load_single_image(self, image_path):
        """Carga una imagen individual"""
        try:
            self.image_list = [image_path]
            self.current_index = 0
            self.show_current_image()
            logging.info(f"✓ Imagen cargada: {image_path}")
            return True
        except Exception as e:
            logging.error(f"Error cargando imagen: {e}")
            return False
    
    def show_current_image(self):
        """Muestra la imagen actual"""
        if not self.image_list or self.current_index < 0:
            return
        
        self.current_image_path = self.image_list[self.current_index]
        self.display_image(self.current_image_path)
        self.update_navigation_info()
        
        # Disparar evento de cambio de imagen
        if hasattr(self, 'on_image_changed'):
            self.on_image_changed(self.current_image_path, None)
    
    def display_image(self, image_path):
        """Muestra una imagen en el label"""
        try:
            image = Image.open(image_path)
            
            # Redimensionar manteniendo aspecto
            width, height = image.size
            max_width = 600
            max_height = 500
            
            if width > max_width or height > max_height:
                ratio_width = max_width / width
                ratio_height = max_height / height
                ratio = min(ratio_width, ratio_height)
                
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(image)
            self.image_label.configure(image=photo, text="")
            self.image_label.image = photo
            
            # Actualizar información
            filename = os.path.basename(image_path)
            self.image_info_label.configure(text=f"Archivo: {filename}")
            
        except Exception as e:
            self.image_label.configure(image='', text=f"Error al cargar imagen:\n{str(e)}")
            logging.error(f"Error mostrando imagen: {e}")
    
    def previous_image(self):
        """Muestra la imagen anterior"""
        if self.current_index > 0:
            self.current_index -= 1
            self.show_current_image()
    
    def next_image(self):
        """Muestra la siguiente imagen"""
        if self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self.show_current_image()
    
    def update_navigation_info(self):
        """Actualiza la información de navegación"""
        if self.image_list:
            total = len(self.image_list)
            current = self.current_index + 1
            self.nav_label.configure(text=f"{current}/{total}")
        else:
            self.nav_label.configure(text="0/0")
    
    def update_providers_list(self, providers=None):
        """Actualiza la lista de proveedores frecuentes"""
        self.providers_text.delete(1.0, tk.END)
        
        if providers:
            for provider in providers[:8]:  # Mostrar máximo 8
                self.providers_text.insert(tk.END, 
                    f"• {provider.nombre}\n  RNC: {provider.rnc} (Usado {provider.frecuencia} veces)\n\n")
        else:
            self.providers_text.insert(tk.END, "No hay proveedores frecuentes registrados")
    
    def get_current_image(self):
        """Obtiene la ruta de la imagen actual"""
        return self.current_image_path
    
    def has_images(self):
        """Verifica si hay imágenes cargadas"""
        return len(self.image_list) > 0
    
    def clear(self):
        """Limpia el panel de navegación"""
        self.image_list = []
        self.current_index = -1
        self.current_image_path = None
        self.image_label.configure(image='', text="Seleccione una factura para comenzar")
        self.image_info_label.configure(text="No hay imagen cargada")
        self.update_navigation_info()
        self.update_providers_list()
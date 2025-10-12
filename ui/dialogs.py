"""
Módulo de diálogos y ventanas modales
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import logging

class DialogsManager:
    """Gestiona todos los diálogos de la aplicación"""
    
    @staticmethod
    def select_folder(title="Seleccionar carpeta con facturas"):
        """Abre diálogo para seleccionar carpeta"""
        try:
            folder_path = filedialog.askdirectory(title=title)
            return folder_path if folder_path else None
        except Exception as e:
            logging.error(f"Error seleccionando carpeta: {e}")
            return None
    
    @staticmethod
    def select_image(title="Seleccionar factura"):
        """Abre diálogo para seleccionar imagen"""
        try:
            file_types = [
                ("Imágenes", "*.jpg *.jpeg *.png *.bmp *.tiff"),
                ("Todos los archivos", "*.*")
            ]
            file_path = filedialog.askopenfilename(title=title, filetypes=file_types)
            return file_path if file_path else None
        except Exception as e:
            logging.error(f"Error seleccionando imagen: {e}")
            return None
    
    @staticmethod
    def save_file(title="Guardar archivo", default_extension=".json", file_types=None):
        """Abre diálogo para guardar archivo"""
        try:
            if file_types is None:
                file_types = [("Todos los archivos", "*.*")]
            
            file_path = filedialog.asksaveasfilename(
                title=title,
                defaultextension=default_extension,
                filetypes=file_types
            )
            return file_path if file_path else None
        except Exception as e:
            logging.error(f"Error guardando archivo: {e}")
            return None
    
    @staticmethod
    def show_info(title, message):
        """Muestra diálogo de información"""
        messagebox.showinfo(title, message)
    
    @staticmethod
    def show_warning(message):
        """Muestra diálogo de advertencia"""
        messagebox.showwarning("Advertencia", message)
    
    @staticmethod
    def show_error(title, message):
        """Muestra diálogo de error"""
        messagebox.showerror(title, message)
    
    @staticmethod
    def ask_yes_no(title, question):
        """Muestra diálogo de confirmación Sí/No"""
        return messagebox.askyesno(title, question)
    
    @staticmethod
    def show_processing_dialog(parent, title="Procesando", message="Por favor espere..."):
        """Muestra diálogo de procesamiento"""
        dialog = tk.Toplevel(parent)
        dialog.title(title)
        dialog.geometry("300x100")
        dialog.transient(parent)
        dialog.grab_set()
        
        # Centrar diálogo
        dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        ttk.Label(dialog, text=message).pack(expand=True)
        progress = ttk.Progressbar(dialog, mode='indeterminate')
        progress.pack(fill=tk.X, padx=20, pady=10)
        progress.start()
        
        return dialog
    
    @staticmethod
    def close_dialog(dialog):
        """Cierra un diálogo"""
        if dialog and dialog.winfo_exists():
            dialog.destroy()
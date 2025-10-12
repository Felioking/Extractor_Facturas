"""
Módulo para formularios de entrada de datos
"""
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import re


class DataForms:
    """
    Formulario para captura y validación de datos de facturas
    """
    
    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self.create_widgets()
        self.create_validations()
    
    def create_widgets(self):
        """Crear los elementos del formulario"""
        # Título
        title_label = ttk.Label(self.frame, text="Datos de la Factura", 
                               font=('Arial', 12, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Campo Nombre/Proveedor
        ttk.Label(self.frame, text="Proveedor:").grid(
            row=1, column=0, padx=5, pady=5, sticky='w')
        self.nombre_entry = ttk.Entry(self.frame, width=30)
        self.nombre_entry.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        
        # Campo RFC
        ttk.Label(self.frame, text="RFC:").grid(
            row=2, column=0, padx=5, pady=5, sticky='w')
        self.rfc_entry = ttk.Entry(self.frame, width=20)
        self.rfc_entry.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        
        # Campo Fecha
        ttk.Label(self.frame, text="Fecha:").grid(
            row=3, column=0, padx=5, pady=5, sticky='w')
        self.fecha_entry = ttk.Entry(self.frame, width=15)
        self.fecha_entry.grid(row=3, column=1, padx=5, pady=5, sticky='w')
        
        # Campo Total
        ttk.Label(self.frame, text="Total:").grid(
            row=4, column=0, padx=5, pady=5, sticky='w')
        self.total_entry = ttk.Entry(self.frame, width=15)
        self.total_entry.grid(row=4, column=1, padx=5, pady=5, sticky='w')
        
        # Campo UUID
        ttk.Label(self.frame, text="UUID:").grid(
            row=5, column=0, padx=5, pady=5, sticky='w')
        self.uuid_entry = ttk.Entry(self.frame, width=35)
        self.uuid_entry.grid(row=5, column=1, padx=5, pady=5, sticky='ew')
        
        # Configurar peso de columnas para expansión
        self.frame.columnconfigure(1, weight=1)
    
    def create_validations(self):
        """Configurar validaciones para los campos"""
        # Validación para campo total (solo números y punto decimal)
        vcmd = (self.parent.register(self.validate_number), '%P')
        self.total_entry.config(validate='key', validatecommand=vcmd)
        
        # Validación para RFC (solo mayúsculas y números)
        rfc_vcmd = (self.parent.register(self.validate_rfc), '%P')
        self.rfc_entry.config(validate='key', validatecommand=rfc_vcmd)
    
    def validate_number(self, value):
        """Validar que el valor sea un número válido"""
        if value == "":
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def validate_rfc(self, value):
        """Validar formato de RFC"""
        if value == "":
            return True
        # Permitir solo letras mayúsculas, números y guión
        return bool(re.match(r'^[A-Z0-9-]*$', value))
    
    def get_data(self):
        """
        Obtener todos los datos del formulario
        
        Returns:
            dict: Diccionario con los datos de la factura
        """
        return {
            'nombre': self.nombre_entry.get().strip(),
            'rfc': self.rfc_entry.get().strip().upper(),
            'fecha': self.fecha_entry.get().strip(),
            'total': self.total_entry.get().strip(),
            'uuid': self.uuid_entry.get().strip()
        }
    
    def set_data(self, data):
        """
        Establecer datos en el formulario
        
        Args:
            data (dict): Diccionario con datos de factura
        """
        self.clear_data()
        
        if not data:
            return
            
        self.nombre_entry.insert(0, data.get('nombre', ''))
        self.rfc_entry.insert(0, data.get('rfc', ''))
        self.fecha_entry.insert(0, data.get('fecha', ''))
        self.total_entry.insert(0, data.get('total', ''))
        self.uuid_entry.insert(0, data.get('uuid', ''))
    
    def clear_data(self):
        """Limpiar todos los campos del formulario"""
        self.nombre_entry.delete(0, tk.END)
        self.rfc_entry.delete(0, tk.END)
        self.fecha_entry.delete(0, tk.END)
        self.total_entry.delete(0, tk.END)
        self.uuid_entry.delete(0, tk.END)
    
    def validate_form(self):
        """
        Validar que los campos requeridos estén completos
        
        Returns:
            tuple: (bool, str) - (es_válido, mensaje_error)
        """
        data = self.get_data()
        
        if not data['nombre']:
            return False, "El campo Proveedor es requerido"
        
        if not data['rfc']:
            return False, "El campo RFC es requerido"
        
        if not data['total']:
            return False, "El campo Total es requerido"
        
        # Validar formato de total
        try:
            total = float(data['total'])
            if total <= 0:
                return False, "El total debe ser mayor a 0"
        except ValueError:
            return False, "El total debe ser un número válido"
        
        return True, "Formulario válido"


class SearchForm:
    """
    Formulario para búsqueda de facturas
    """
    
    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self.create_widgets()
    
    def create_widgets(self):
        """Crear elementos del formulario de búsqueda"""
        ttk.Label(self.frame, text="Buscar Facturas", 
                 font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=3, pady=5)
        
        # Campo de búsqueda
        ttk.Label(self.frame, text="Buscar:").grid(row=1, column=0, padx=5, pady=2)
        self.search_entry = ttk.Entry(self.frame, width=25)
        self.search_entry.grid(row=1, column=1, padx=5, pady=2)
        
        # Combo para seleccionar campo de búsqueda
        ttk.Label(self.frame, text="En:").grid(row=1, column=2, padx=5, pady=2)
        self.field_combo = ttk.Combobox(self.frame, width=12, 
                                       values=["Todos", "Proveedor", "RFC", "UUID"])
        self.field_combo.set("Todos")
        self.field_combo.grid(row=1, column=3, padx=5, pady=2)
    
    def get_search_data(self):
        """
        Obtener datos de búsqueda
        
        Returns:
            tuple: (campo, valor)
        """
        campo = self.field_combo.get()
        valor = self.search_entry.get().strip()
        
        # Mapear nombres amigables a nombres de campo de BD
        campo_map = {
            "Todos": None,
            "Proveedor": "nombre",
            "RFC": "rfc", 
            "UUID": "uuid"
        }
        
        return campo_map.get(campo), valor
    
    def clear_search(self):
        """Limpiar formulario de búsqueda"""
        self.search_entry.delete(0, tk.END)
        self.field_combo.set("Todos")


# Pruebas simples del módulo
if __name__ == "__main__":
    root = tk.Tk()
    form = DataForms(root)
    form.frame.pack(padx=10, pady=10)
    root.mainloop()
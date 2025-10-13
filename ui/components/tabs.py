"""
Módulo para pestañas principales de la aplicación
"""
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import logging

# Importar componentes
from ui.components.forms import DataForms, SearchForm

logger = logging.getLogger(__name__)

class MainTabs:
    """
    Clase para gestionar las pestañas principales de la aplicación
    """
    
    def __init__(self, parent, db_manager):
        self.parent = parent
        self.db_manager = db_manager
        self.notebook = ttk.Notebook(parent)
        self.tabs = {}
        
        self._create_tabs()
    
    def _create_tabs(self):
        """Crear las pestañas principales"""
        # Pestaña de Extracción
        self.tabs['extraccion'] = ttk.Frame(self.notebook)
        self.notebook.add(self.tabs['extraccion'], text='Extracción')
        
        # Pestaña de Gestión
        self.tabs['gestion'] = ttk.Frame(self.notebook)
        self.notebook.add(self.tabs['gestion'], text='Gestión')
        
        # Pestaña de Búsqueda
        self.tabs['busqueda'] = ttk.Frame(self.notebook)
        self.notebook.add(self.tabs['busqueda'], text='Búsqueda')
        
        # Configurar el contenido de cada pestaña
        self._setup_extraccion_tab()
        self._setup_gestion_tab()
        self._setup_busqueda_tab()
        
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)
    
    def _setup_extraccion_tab(self):
        """Configurar pestaña de extracción"""
        tab = self.tabs['extraccion']
        
        # Frame para subida de archivos
        upload_frame = ttk.LabelFrame(tab, text="Subir Facturas", padding=10)
        upload_frame.pack(fill='x', padx=5, pady=5)
        
        # Botón para seleccionar archivos
        self.upload_btn = ttk.Button(
            upload_frame, 
            text="Seleccionar Archivos", 
            command=self._select_files
        )
        self.upload_btn.pack(pady=5)
        
        # Lista de archivos seleccionados
        self.file_list = tk.Listbox(upload_frame, height=5)
        self.file_list.pack(fill='x', pady=5)
        
        # Botón para procesar
        self.process_btn = ttk.Button(
            upload_frame,
            text="Procesar Facturas",
            command=self._process_files
        )
        self.process_btn.pack(pady=5)
        
        # Área de resultados
        results_frame = ttk.LabelFrame(tab, text="Resultados", padding=10)
        results_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.results_text = tk.Text(results_frame, height=10, wrap='word')
        scrollbar = ttk.Scrollbar(results_frame, orient='vertical', command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        self.results_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
    
    def _setup_gestion_tab(self):
        """Configurar pestaña de gestión de datos"""
        tab = self.tabs['gestion']
        
        # Formulario para datos de factura
        form_frame = ttk.LabelFrame(tab, text="Datos de Factura", padding=10)
        form_frame.pack(fill='x', padx=5, pady=5)
        
        self.data_form = DataForms(form_frame)
        self.data_form.frame.pack(fill='x')
        
        # Botones de acción
        button_frame = ttk.Frame(form_frame)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text="Guardar", command=self._save_data).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Limpiar", command=self._clear_data).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cargar desde BD", command=self._load_from_db).pack(side='left', padx=5)
        
        # Lista de facturas existentes
        list_frame = ttk.LabelFrame(tab, text="Facturas Almacenadas", padding=10)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Treeview para mostrar facturas
        columns = ('ID', 'Proveedor', 'RFC', 'Fecha', 'Total', 'UUID')
        self.facturas_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        # Configurar columnas
        for col in columns:
            self.facturas_tree.heading(col, text=col)
            self.facturas_tree.column(col, width=100)
        
        self.facturas_tree.column('Proveedor', width=150)
        self.facturas_tree.column('UUID', width=200)
        
        # Scrollbar para el treeview
        tree_scroll = ttk.Scrollbar(list_frame, orient='vertical', command=self.facturas_tree.yview)
        self.facturas_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.facturas_tree.pack(side='left', fill='both', expand=True)
        tree_scroll.pack(side='right', fill='y')
        
        # Botones para la lista
        list_buttons = ttk.Frame(list_frame)
        list_buttons.pack(fill='x', pady=5)
        
        ttk.Button(list_buttons, text="Actualizar Lista", command=self._refresh_list).pack(side='left', padx=5)
        ttk.Button(list_buttons, text="Eliminar Seleccionado", command=self._delete_selected).pack(side='left', padx=5)
        
        # Cargar datos iniciales
        self._refresh_list()
    
    def _setup_busqueda_tab(self):
        """Configurar pestaña de búsqueda"""
        tab = self.tabs['busqueda']
        
        # Formulario de búsqueda
        search_frame = ttk.LabelFrame(tab, text="Búsqueda", padding=10)
        search_frame.pack(fill='x', padx=5, pady=5)
        
        self.search_form = SearchForm(search_frame)
        self.search_form.frame.pack(fill='x')
        
        # Botones de búsqueda
        search_buttons = ttk.Frame(search_frame)
        search_buttons.pack(fill='x', pady=10)
        
        ttk.Button(search_buttons, text="Buscar", command=self._perform_search).pack(side='left', padx=5)
        ttk.Button(search_buttons, text="Limpiar Búsqueda", command=self._clear_search).pack(side='left', padx=5)
        
        # Resultados de búsqueda
        results_frame = ttk.LabelFrame(tab, text="Resultados de Búsqueda", padding=10)
        results_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        columns = ('ID', 'Proveedor', 'RFC', 'Fecha', 'Total', 'UUID')
        self.search_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.search_tree.heading(col, text=col)
            self.search_tree.column(col, width=100)
        
        self.search_tree.column('Proveedor', width=150)
        self.search_tree.column('UUID', width=200)
        
        tree_scroll = ttk.Scrollbar(results_frame, orient='vertical', command=self.search_tree.yview)
        self.search_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.search_tree.pack(side='left', fill='both', expand=True)
        tree_scroll.pack(side='right', fill='y')
    
    def _select_files(self):
        """Seleccionar archivos para procesar"""
        # TODO: Implementar selección de archivos
        messagebox.showinfo("Info", "Funcionalidad de selección de archivos por implementar")
    
    def _process_files(self):
        """Procesar archivos seleccionados"""
        # TODO: Implementar procesamiento de archivos
        messagebox.showinfo("Info", "Funcionalidad de procesamiento por implementar")
    
    def _save_data(self):
        """Guardar datos del formulario en la base de datos"""
        try:
            data = self.data_form.get_data()
            is_valid, message = self.data_form.validate_form()
            
            if not is_valid:
                messagebox.showerror("Error", message)
                return
            
            if self.db_manager.insertar_factura(data):
                messagebox.showinfo("Éxito", "Factura guardada correctamente")
                self._clear_data()
                self._refresh_list()
            else:
                messagebox.showerror("Error", "Error al guardar la factura")
                
        except Exception as e:
            logger.error(f"Error guardando datos: {e}")
            messagebox.showerror("Error", f"Error al guardar: {str(e)}")
    
    def _clear_data(self):
        """Limpiar el formulario"""
        self.data_form.clear_data()
    
    def _load_from_db(self):
        """Cargar datos desde la base de datos"""
        # TODO: Implementar carga desde BD al formulario
        messagebox.showinfo("Info", "Funcionalidad de carga desde BD por implementar")
    
    def _refresh_list(self):
        """Actualizar la lista de facturas"""
        try:
            # Limpiar treeview
            for item in self.facturas_tree.get_children():
                self.facturas_tree.delete(item)
            
            # Obtener facturas de la BD
            facturas = self.db_manager.obtener_todas_facturas()
            
            # Agregar al treeview
            for factura in facturas:
                self.facturas_tree.insert('', 'end', values=(
                    factura.get('id', ''),
                    factura.get('nombre', ''),
                    factura.get('rfc', ''),
                    factura.get('fecha', ''),
                    factura.get('total', ''),
                    factura.get('uuid', '')
                ))
                
        except Exception as e:
            logger.error(f"Error actualizando lista: {e}")
            messagebox.showerror("Error", f"Error al cargar facturas: {str(e)}")
    
    def _delete_selected(self):
        """Eliminar factura seleccionada"""
        try:
            selection = self.facturas_tree.selection()
            if not selection:
                messagebox.showwarning("Advertencia", "Selecciona una factura para eliminar")
                return
            
            item = selection[0]
            factura_id = self.facturas_tree.item(item, 'values')[0]
            
            if messagebox.askyesno("Confirmar", "¿Estás seguro de eliminar esta factura?"):
                if self.db_manager.eliminar_factura(int(factura_id)):
                    messagebox.showinfo("Éxito", "Factura eliminada correctamente")
                    self._refresh_list()
                else:
                    messagebox.showerror("Error", "Error al eliminar la factura")
                    
        except Exception as e:
            logger.error(f"Error eliminando factura: {e}")
            messagebox.showerror("Error", f"Error al eliminar: {str(e)}")
    
    def _perform_search(self):
        """Realizar búsqueda"""
        try:
            campo, valor = self.search_form.get_search_data()
            
            # Limpiar resultados anteriores
            for item in self.search_tree.get_children():
                self.search_tree.delete(item)
            
            # Realizar búsqueda
            facturas = self.db_manager.buscar_facturas(campo, valor)
            
            # Mostrar resultados
            for factura in facturas:
                self.search_tree.insert('', 'end', values=(
                    factura.get('id', ''),
                    factura.get('nombre', ''),
                    factura.get('rfc', ''),
                    factura.get('fecha', ''),
                    factura.get('total', ''),
                    factura.get('uuid', '')
                ))
                
            messagebox.showinfo("Búsqueda", f"Encontradas {len(facturas)} facturas")
            
        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            messagebox.showerror("Error", f"Error en búsqueda: {str(e)}")
    
    def _clear_search(self):
        """Limpiar búsqueda"""
        self.search_form.clear_search()
        for item in self.search_tree.get_children():
            self.search_tree.delete(item)

    def get_widget(self):
        """Obtener el widget principal"""
        return self.notebook

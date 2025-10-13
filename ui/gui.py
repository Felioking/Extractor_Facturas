# ui/gui.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import cv2
import os
import logging
from datetime import datetime
import json
import glob
import pandas as pd

# Importar módulos de tu estructura de carpetas
from database.models import DatabaseManager
from ocr.image_preprocessor import ImageProcessor
from ocr.text_extractor import TextExtractor
from processing.data_extractor import DataExtractor
from processing.validator import Validator
from processing.exporter import Exporter
from utils.helpers import setup_logging

# Configurar logging
logger = logging.getLogger(__name__)

class ExtractorFacturasApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Extractor Inteligente de Facturas - v3.0")
        self.root.geometry("1400x900")
        
        # Variables de estado
        self.ruta_imagen = None
        self.datos_extraidos = {}
        self.lista_imagenes = []
        self.indice_actual = -1
        self.proveedores_frecuentes = []
        
        # Inicializar módulos
        self.db_manager = DatabaseManager()
        self.image_processor = ImageProcessor()
        self.data_extractor = DataExtractor()
        
        # Cargar proveedores frecuentes
        self.cargar_proveedores_frecuentes()
        
        # Configurar interfaz
        self.setup_ui()
        logger.info("Sistema inicializado correctamente")
    
    def cargar_proveedores_frecuentes(self):
        """Carga los proveedores más frecuentes de la base de datos"""
        try:
            self.proveedores_frecuentes = self.db_manager.obtener_proveedores_frecuentes(limite=8)
        except Exception as e:
            logger.error(f"Error cargando proveedores: {e}")
            self.proveedores_frecuentes = []
    
    def setup_ui(self):
        """Configura la interfaz de usuario con pestañas avanzadas"""
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame superior para controles
        frame_controles = ttk.LabelFrame(main_frame, text="Controles Avanzados", padding="10")
        frame_controles.pack(fill=tk.X, pady=(0, 10))
        
        # Primera fila - Navegación básica
        frame_navegacion = ttk.Frame(frame_controles)
        frame_navegacion.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(frame_navegacion, text="📁 Cargar Carpeta", 
                  command=self.cargar_carpeta).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(frame_navegacion, text="📄 Cargar Factura", 
                  command=self.cargar_imagen).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(frame_navegacion, text="⏮️", 
                  command=self.imagen_anterior).pack(side=tk.LEFT, padx=(0, 2))
        self.label_navegacion = ttk.Label(frame_navegacion, text="0/0", width=8)
        self.label_navegacion.pack(side=tk.LEFT, padx=2)
        ttk.Button(frame_navegacion, text="⏭️", 
                  command=self.imagen_siguiente).pack(side=tk.LEFT, padx=(2, 10))
        
        # Segunda fila - Procesamiento
        frame_procesamiento = ttk.Frame(frame_controles)
        frame_procesamiento.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(frame_procesamiento, text="🔍 Extraer Datos", 
                  command=self.extraer_datos_factura).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(frame_procesamiento, text="🔄 Procesar Lote", 
                  command=self.procesar_lote).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(frame_procesamiento, text="⚙️ Preprocesar", 
                  command=self.mostrar_opciones_preprocesamiento).pack(side=tk.LEFT, padx=(0, 10))
        
        # Tercera fila - Exportación y BD
        frame_export = ttk.Frame(frame_controles)
        frame_export.pack(fill=tk.X)
        
        ttk.Button(frame_export, text="💾 Guardar JSON", 
                  command=self.guardar_datos).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(frame_export, text="📊 Exportar Excel", 
                  command=self.exportar_excel).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(frame_export, text="🗃️ Ver Base Datos", 
                  command=self.mostrar_base_datos).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(frame_export, text="🗑️ Limpiar", 
                  command=self.limpiar_datos).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(frame_export, text="📈 Estadísticas", 
                  command=self.mostrar_estadisticas).pack(side=tk.LEFT)
        
        # Frame para contenido principal
        frame_contenido = ttk.Frame(main_frame)
        frame_contenido.pack(fill=tk.BOTH, expand=True)
        
        # Panel izquierdo - Imagen y proveedores
        frame_izquierdo = ttk.Frame(frame_contenido)
        frame_izquierdo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Frame de imagen
        frame_imagen = ttk.LabelFrame(frame_izquierdo, text="Vista Previa", padding="10")
        frame_imagen.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.label_info_imagen = ttk.Label(frame_imagen, text="No hay imagen cargada", font=("Arial", 10))
        self.label_info_imagen.pack(pady=(0, 5))
        
        self.label_imagen = ttk.Label(frame_imagen, text="Seleccione una factura para comenzar", 
                                    background="lightgray", justify=tk.CENTER)
        self.label_imagen.pack(fill=tk.BOTH, expand=True)
        
        # Frame de proveedores frecuentes
        frame_proveedores = ttk.LabelFrame(frame_izquierdo, text="🏢 Proveedores Frecuentes", padding="10")
        frame_proveedores.pack(fill=tk.BOTH, expand=False)
        
        self.lista_proveedores = scrolledtext.ScrolledText(frame_proveedores, height=6, font=("Arial", 8))
        self.lista_proveedores.pack(fill=tk.BOTH, expand=True)
        self.actualizar_lista_proveedores()
        
        # Panel derecho - Datos y resultados
        frame_datos = ttk.LabelFrame(frame_contenido, text="Datos de la Factura", padding="10")
        frame_datos.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        
        # Configurar un ancho mínimo para el frame de datos
        frame_datos.configure(width=500)
        frame_datos.pack_propagate(False)
        
        # Notebook para pestañas
        self.notebook = ttk.Notebook(frame_datos)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Pestaña de información fiscal
        frame_fiscal = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame_fiscal, text="📄 Información Fiscal")
        self.crear_formulario_fiscal(frame_fiscal)
        
        # Pestaña de montos
        frame_montos = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame_montos, text="💰 Montos")
        self.crear_formulario_montos(frame_montos)
        
        # Pestaña de texto completo
        frame_texto = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame_texto, text="📝 Texto Completo")
        
        self.texto_completo = scrolledtext.ScrolledText(frame_texto, wrap=tk.WORD, font=("Consolas", 8))
        self.texto_completo.pack(fill=tk.BOTH, expand=True)
        
        # Pestaña de validación
        frame_validacion = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame_validacion, text="✅ Validación")
        self.crear_pestana_validacion(frame_validacion)
    
    def crear_formulario_fiscal(self, parent):
        """Crea el formulario de información fiscal"""
        campos_fiscal = [
            ("RNC Emisor:", "rnc_emisor"),
            ("Nombre Emisor:", "nombre_emisor"),
            ("Comprobante/NCF:", "comprobante"),
            ("Fecha Emisión:", "fecha_emision"),
            ("Fecha Vencimiento:", "fecha_vencimiento")
        ]
        
        self.entries_fiscal = {}
        
        for i, (label, key) in enumerate(campos_fiscal):
            ttk.Label(parent, text=label, font=("Arial", 9, "bold")).grid(row=i, column=0, sticky=tk.W, pady=3)
            entry = ttk.Entry(parent, width=35, font=("Arial", 9))
            entry.grid(row=i, column=1, sticky=tk.EW, pady=3, padx=(5, 0))
            self.entries_fiscal[key] = entry
        
        parent.columnconfigure(1, weight=1)
    
    def crear_formulario_montos(self, parent):
        """Crea el formulario de montos"""
        campos_montos = [
            ("Subtotal:", "subtotal"),
            ("ITBIS/Impuestos:", "impuestos"),
            ("Descuentos:", "descuentos"),
            ("Total:", "total"),
            ("Total a Pagar:", "total_pagar")
        ]
        
        self.entries_montos = {}
        
        for i, (label, key) in enumerate(campos_montos):
            ttk.Label(parent, text=label, font=("Arial", 9, "bold")).grid(row=i, column=0, sticky=tk.W, pady=3)
            entry = ttk.Entry(parent, width=30, font=("Arial", 9))
            entry.grid(row=i, column=1, sticky=tk.EW, pady=3, padx=(5, 0))
            self.entries_montos[key] = entry
        
        parent.columnconfigure(1, weight=1)
    
    def crear_pestana_validacion(self, parent):
        """Crea la pestaña de validación"""
        ttk.Label(parent, text="Estado de Validación:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.label_estado_validacion = ttk.Label(parent, text="No validado", foreground="red", font=("Arial", 10, "bold"))
        self.label_estado_validacion.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        ttk.Label(parent, text="Detalles de Validación:", font=("Arial", 9, "bold")).grid(row=1, column=0, sticky=tk.W, pady=2)
        
        self.texto_validacion = scrolledtext.ScrolledText(parent, height=8, font=("Consolas", 8))
        self.texto_validacion.grid(row=2, column=0, columnspan=2, sticky=tk.NSEW, pady=5)
        
        ttk.Button(parent, text="Validar NCF", command=self.validar_ncf).grid(row=3, column=0, pady=5, sticky=tk.W)
        ttk.Button(parent, text="Verificar en BD", command=self.verificar_base_datos).grid(row=3, column=1, pady=5, sticky=tk.E)
        
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(2, weight=1)

    # ========== MÉTODOS DE NAVEGACIÓN ==========
    
    def cargar_carpeta(self):
        """Carga todas las imágenes de una carpeta"""
        carpeta = filedialog.askdirectory(title="Seleccionar carpeta con facturas")
        
        if carpeta:
            # Buscar imágenes en formatos comunes
            extensiones = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.tif']
            self.lista_imagenes = []
            
            for extension in extensiones:
                self.lista_imagenes.extend(glob.glob(os.path.join(carpeta, extension)))
                self.lista_imagenes.extend(glob.glob(os.path.join(carpeta, extension.upper())))
            
            if self.lista_imagenes:
                self.lista_imagenes.sort()  # Ordenar alfabéticamente
                self.indice_actual = 0
                self.mostrar_imagen_actual()
                messagebox.showinfo("Éxito", f"Se cargaron {len(self.lista_imagenes)} imágenes")
            else:
                messagebox.showwarning("Advertencia", "No se encontraron imágenes en la carpeta seleccionada")
    
    def cargar_imagen(self):
        """Carga una imagen individual"""
        ruta = filedialog.askopenfilename(
            title="Seleccionar factura",
            filetypes=[
                ("Imágenes", "*.jpg *.jpeg *.png *.bmp *.tiff"),
                ("Todos los archivos", "*.*")
            ]
        )
        
        if ruta:
            self.lista_imagenes = [ruta]
            self.indice_actual = 0
            self.mostrar_imagen_actual()
            self.limpiar_formularios()
    
    def imagen_anterior(self):
        """Muestra la imagen anterior en la lista"""
        if self.lista_imagenes and self.indice_actual > 0:
            self.indice_actual -= 1
            self.mostrar_imagen_actual()
    
    def imagen_siguiente(self):
        """Muestra la siguiente imagen en la lista"""
        if self.lista_imagenes and self.indice_actual < len(self.lista_imagenes) - 1:
            self.indice_actual += 1
            self.mostrar_imagen_actual()
    
    def mostrar_imagen_actual(self):
        """Muestra la imagen actual en la interfaz"""
        if self.lista_imagenes and 0 <= self.indice_actual < len(self.lista_imagenes):
            self.ruta_imagen = self.lista_imagenes[self.indice_actual]
            self.mostrar_imagen(self.ruta_imagen)
            self.actualizar_navegacion()
            self.limpiar_formularios()
    
    def actualizar_navegacion(self):
        """Actualiza la información de navegación"""
        if self.lista_imagenes:
            total = len(self.lista_imagenes)
            actual = self.indice_actual + 1
            nombre_archivo = os.path.basename(self.ruta_imagen)
            
            self.label_navegacion.config(text=f"{actual}/{total}")
            self.label_info_imagen.config(text=f"Archivo: {nombre_archivo}")
        else:
            self.label_navegacion.config(text="0/0")
            self.label_info_imagen.config(text="No hay imagen cargada")
    
    def mostrar_imagen(self, ruta):
        """Muestra la imagen en el label"""
        try:
            imagen = Image.open(ruta)
            # Redimensionar manteniendo aspecto
            ancho, alto = imagen.size
            max_ancho = 600
            max_alto = 500
            
            if ancho > max_ancho or alto > max_alto:
                ratio_ancho = max_ancho / ancho
                ratio_alto = max_alto / alto
                ratio = min(ratio_ancho, ratio_alto)
                
                nuevo_ancho = int(ancho * ratio)
                nuevo_alto = int(alto * ratio)
                imagen = imagen.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)
            
            foto = ImageTk.PhotoImage(imagen)
            self.label_imagen.configure(image=foto, text="")
            self.label_imagen.image = foto
            
            logger.info(f"Imagen cargada: {os.path.basename(ruta)}")
            
        except Exception as e:
            self.label_imagen.configure(image='', text=f"Error al cargar imagen:\n{str(e)}")
            logger.error(f"Error cargando imagen: {e}")
    
    def actualizar_lista_proveedores(self):
        """Actualiza la lista de proveedores frecuentes"""
        self.lista_proveedores.delete(1.0, tk.END)
        if self.proveedores_frecuentes:
            for proveedor in self.proveedores_frecuentes:
                self.lista_proveedores.insert(tk.END, 
                    f"• {proveedor['nombre']}\n  RNC: {proveedor['rnc']} (Usado {proveedor['frecuencia']} veces)\n\n")
        else:
            self.lista_proveedores.insert(tk.END, "No hay proveedores frecuentes registrados")

    # ========== MÉTODOS DE PROCESAMIENTO ==========
    
    def extraer_datos_factura(self):
        """Extrae datos de la factura actual"""
        if not self.ruta_imagen:
            messagebox.showwarning("Advertencia", "Primero carga una factura")
            return
        
        try:
            logger.info("Iniciando extracción de datos avanzada...")
            self.root.config(cursor="watch")
            self.root.update()
            
            # Preprocesar imagen y extraer texto
            imagen_procesada, texto = self.image_processor.preprocess_image(self.ruta_imagen)
            
            self.texto_completo.delete(1.0, tk.END)
            self.texto_completo.insert(tk.END, texto)
            
            # Extraer datos estructurados
            self.datos_extraidos = self.data_extractor.extract_data_from_text(texto, self.ruta_imagen)
            
            # Llenar formularios
            self.llenar_formularios()
            
            # Validación automática
            self.validar_y_mostrar_resultados()
            
            # Guardar en base de datos automáticamente
            if self.datos_extraidos.get('comprobante'):
                resultado, mensaje = self.db_manager.guardar_factura(self.datos_extraidos)
                if resultado:
                    logger.info("Datos guardados en base de datos")
                    # Actualizar lista de proveedores
                    self.cargar_proveedores_frecuentes()
                    self.actualizar_lista_proveedores()
                else:
                    logger.warning(f"No se pudo guardar en BD: {mensaje}")
            
            messagebox.showinfo("Éxito", "Datos extraídos y procesados correctamente")
            
        except Exception as e:
            logger.error(f"Error al extraer datos: {e}")
            messagebox.showerror("Error", f"Error al extraer datos: {str(e)}")
        finally:
            self.root.config(cursor="")
    
    def llenar_formularios(self):
        """Llena los formularios con los datos extraídos"""
        for key, entry in self.entries_fiscal.items():
            valor = self.datos_extraidos.get(key, "")
            entry.delete(0, tk.END)
            entry.insert(0, str(valor))
        
        for key, entry in self.entries_montos.items():
            valor = self.datos_extraidos.get(key, "")
            entry.delete(0, tk.END)
            if isinstance(valor, (int, float)):
                entry.insert(0, f"RD$ {valor:,.2f}")
            else:
                entry.insert(0, str(valor))
    
    def limpiar_formularios(self):
        """Limpia todos los formularios"""
        for entry in self.entries_fiscal.values():
            entry.delete(0, tk.END)
        
        for entry in self.entries_montos.values():
            entry.delete(0, tk.END)
        
        self.texto_completo.delete(1.0, tk.END)
        self.texto_validacion.delete(1.0, tk.END)
        self.datos_extraidos = {}
        self.label_estado_validacion.config(text="No validado", foreground="red")
    
    # ========== MÉTODOS DE VALIDACIÓN ==========
    
    def validar_ncf(self):
        """Valida el NCF actual"""
        ncf = self.datos_extraidos.get('comprobante', '')
        if not ncf:
            messagebox.showwarning("Advertencia", "No hay NCF para validar")
            return
        
        valido, mensaje = self.data_extractor.validar_ncf_formato(ncf)
        
        self.texto_validacion.delete(1.0, tk.END)
        self.texto_validacion.insert(tk.END, f"Validación NCF: {ncf}\n\n")
        
        if valido:
            self.texto_validacion.insert(tk.END, f"✅ {mensaje}\n")
            self.label_estado_validacion.config(text="VÁLIDO", foreground="green")
        else:
            self.texto_validacion.insert(tk.END, f"❌ {mensaje}\n")
            self.label_estado_validacion.config(text="INVÁLIDO", foreground="red")
        
        if self.db_manager.verificar_comprobante_existente(ncf):
            self.texto_validacion.insert(tk.END, "\n⚠️ ADVERTENCIA: Este comprobante ya existe en la base de datos")
    
    def verificar_base_datos(self):
        """Verifica si el comprobante existe en la base de datos"""
        ncf = self.datos_extraidos.get('comprobante', '')
        if not ncf:
            messagebox.showwarning("Advertencia", "No hay comprobante para verificar")
            return
        
        duplicado = self.db_manager.verificar_comprobante_existente(ncf)
        
        self.texto_validacion.delete(1.0, tk.END)
        self.texto_validacion.insert(tk.END, f"Verificación en Base de Datos:\n\n")
        
        if duplicado:
            self.texto_validacion.insert(tk.END, f"❌ El comprobante {ncf} ya existe en la base de datos")
            self.label_estado_validacion.config(text="DUPLICADO", foreground="orange")
        else:
            self.texto_validacion.insert(tk.END, f"✅ El comprobante {ncf} no existe en la base de datos")
            self.label_estado_validacion.config(text="NUEVO", foreground="green")
    
    def validar_y_mostrar_resultados(self):
        """Realiza validaciones y muestra resultados"""
        self.texto_validacion.delete(1.0, tk.END)
        
        ncf = self.datos_extraidos.get('comprobante', '')
        if ncf:
            ncf_valido, mensaje_ncf = self.data_extractor.validar_ncf_formato(ncf)
            self.texto_validacion.insert(tk.END, f"✅ NCF: {mensaje_ncf}\n\n")
            
            if ncf_valido:
                self.label_estado_validacion.config(text="VÁLIDO", foreground="green")
            else:
                self.label_estado_validacion.config(text="INVÁLIDO", foreground="red")
        else:
            self.texto_validacion.insert(tk.END, "❌ No se encontró NCF\n\n")
            self.label_estado_validacion.config(text="INCOMPLETO", foreground="orange")
        
        if ncf and self.db_manager.verificar_comprobante_existente(ncf):
            self.texto_validacion.insert(tk.END, "⚠️ ADVERTENCIA: Este comprobante ya existe en la base de datos\n\n")
        
        rnc = self.datos_extraidos.get('rnc_emisor', '')
        if rnc:
            if len(rnc) in [9, 11]:
                self.texto_validacion.insert(tk.END, f"✅ RNC: Formato válido ({len(rnc)} dígitos)\n\n")
            else:
                self.texto_validacion.insert(tk.END, f"⚠️ RNC: Longitud inusual ({len(rnc)} dígitos)\n\n")

    # ========== MÉTODOS ADICIONALES ==========
    
    def mostrar_opciones_preprocesamiento(self):
        """Muestra ventana de opciones de preprocesamiento"""
        ventana = tk.Toplevel(self.root)
        ventana.title("Opciones de Preprocesamiento")
        ventana.geometry("400x300")
        
        ttk.Label(ventana, text="Configuración de Procesamiento", font=("Arial", 12, "bold")).pack(pady=10)
        
        ttk.Button(ventana, text="Aplicar Configuración por Defecto", 
                  command=lambda: messagebox.showinfo("Info", "Configuración aplicada")).pack(pady=20)
        ttk.Button(ventana, text="Cerrar", command=ventana.destroy).pack(pady=10)
    
    def mostrar_base_datos(self):
        """Muestra ventana con los datos de la base de datos"""
        ventana = tk.Toplevel(self.root)
        ventana.title("Base de Datos - Facturas Registradas")
        ventana.geometry("1000x600")
        
        try:
            facturas = self.db_manager.obtener_todas_facturas(limite=100)
            
            frame = ttk.Frame(ventana)
            frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Crear un texto para mostrar los datos
            texto_bd = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=("Consolas", 8))
            texto_bd.pack(fill=tk.BOTH, expand=True)
            
            # Mostrar datos en formato legible
            texto_bd.insert(tk.END, "FACTURAS REGISTRADAS EN LA BASE DE DATOS\n")
            texto_bd.insert(tk.END, "=" * 50 + "\n\n")
            
            for factura in facturas:
                texto_bd.insert(tk.END, f"ID: {factura['id']}\n")
                texto_bd.insert(tk.END, f"RNC: {factura['rnc_emisor']}\n")
                texto_bd.insert(tk.END, f"Nombre: {factura['nombre_emisor']}\n")
                texto_bd.insert(tk.END, f"Comprobante: {factura['comprobante']}\n")
                texto_bd.insert(tk.END, f"Fecha: {factura['fecha_emision']}\n")
                texto_bd.insert(tk.END, f"Total: RD$ {factura['total'] or 0:,.2f}\n")
                texto_bd.insert(tk.END, f"Procesado: {factura['fecha_procesamiento']}\n")
                texto_bd.insert(tk.END, "-" * 30 + "\n\n")
            
            texto_bd.config(state=tk.DISABLED)
            
            stats = self.db_manager.obtener_estadisticas()
            
            ttk.Label(ventana, text=f"Total de facturas: {stats['total_facturas']} | Suma total: RD$ {stats['suma_total']:,.2f}", 
                     font=("Arial", 10, "bold")).pack(pady=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error mostrando base de datos: {str(e)}")
    
    def mostrar_estadisticas(self):
        """Muestra estadísticas del sistema"""
        try:
            stats = self.db_manager.obtener_estadisticas()
            
            ventana = tk.Toplevel(self.root)
            ventana.title("Estadísticas del Sistema")
            ventana.geometry("400x300")
            
            ttk.Label(ventana, text="📊 Estadísticas Generales", font=("Arial", 14, "bold")).pack(pady=10)
            
            frame_stats = ttk.Frame(ventana)
            frame_stats.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            estadisticas = [
                f"Total de Facturas Procesadas: {stats['total_facturas']}",
                f"Proveedores Únicos: {stats['total_proveedores']}",
                f"Suma Total de Facturas: RD$ {stats['suma_total']:,.2f}",
                f"Promedio por Factura: RD$ {stats['promedio_factura']:,.2f}",
                f"Factura Más Alta: RD$ {stats['factura_maxima']:,.2f}",
                f"Factura Más Baja: RD$ {stats['factura_minima']:,.2f}"
            ]
            
            for stat in estadisticas:
                ttk.Label(frame_stats, text=stat, font=("Arial", 10)).pack(anchor=tk.W, pady=2)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error generando estadísticas: {str(e)}")
    
    def procesar_lote(self):
        """Procesa todas las imágenes en la carpeta"""
        if not self.lista_imagenes:
            messagebox.showwarning("Advertencia", "Primero carga una carpeta con imágenes")
            return
        
        archivo_salida = filedialog.asksaveasfilename(
            title="Guardar resultados del lote",
            defaultextension=".json",
            filetypes=[("Archivo JSON", "*.json")]
        )
        
        if not archivo_salida:
            return
        
        try:
            self.root.config(cursor="watch")
            resultados = []
            
            for i, ruta_imagen in enumerate(self.lista_imagenes):
                logger.info(f"Procesando {i+1}/{len(self.lista_imagenes)}: {os.path.basename(ruta_imagen)}")
                
                self.label_info_imagen.config(text=f"Procesando: {i+1}/{len(self.lista_imagenes)}")
                self.root.update()
                
                try:
                    # Procesar imagen y extraer texto
                    _, texto = self.image_processor.preprocess_image(ruta_imagen)
                    
                    # Extraer datos
                    datos = self.data_extractor.extract_data_from_text(texto, ruta_imagen)
                    datos['archivo'] = ruta_imagen
                    datos['fecha_procesamiento'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    resultados.append(datos)
                    
                    # Guardar en base de datos si tiene comprobante
                    if datos.get('comprobante'):
                        self.db_manager.guardar_factura(datos)
                    
                except Exception as e:
                    logger.error(f"Error procesando {ruta_imagen}: {e}")
                    continue
            
            # Guardar resultados en archivo JSON
            with open(archivo_salida, 'w', encoding='utf-8') as f:
                json.dump(resultados, f, indent=2, ensure_ascii=False)
            
            # Actualizar proveedores
            self.cargar_proveedores_frecuentes()
            self.actualizar_lista_proveedores()
            
            messagebox.showinfo("Éxito", f"Procesamiento completado\n{len(resultados)} facturas procesadas")
            
        except Exception as e:
            logger.error(f"Error en procesamiento por lote: {e}")
            messagebox.showerror("Error", f"Error en procesamiento por lote: {str(e)}")
        finally:
            self.root.config(cursor="")
            self.actualizar_navegacion()
    
    def exportar_excel(self):
        """Exporta todas las facturas a Excel"""
        try:
            facturas = self.db_manager.obtener_todas_facturas()
            
            if not facturas:
                messagebox.showwarning("Advertencia", "No hay datos para exportar")
                return
            
            # Crear DataFrame
            df = pd.DataFrame(facturas)
            
            # Seleccionar y renombrar columnas relevantes
            columnas_exportar = [
                'rnc_emisor', 'nombre_emisor', 'comprobante', 'fecha_emision',
                'subtotal', 'impuestos', 'descuentos', 'total', 'fecha_procesamiento'
            ]
            
            # Filtrar columnas existentes
            columnas_existentes = [col for col in columnas_exportar if col in df.columns]
            df_export = df[columnas_existentes].copy()
            
            # Renombrar columnas
            nombres_spanish = {
                'rnc_emisor': 'RNC Emisor',
                'nombre_emisor': 'Nombre Emisor',
                'comprobante': 'Comprobante',
                'fecha_emision': 'Fecha Emisión',
                'subtotal': 'Subtotal',
                'impuestos': 'Impuestos',
                'descuentos': 'Descuentos',
                'total': 'Total',
                'fecha_procesamiento': 'Fecha Procesamiento'
            }
            df_export.rename(columns=nombres_spanish, inplace=True)
            
            archivo = filedialog.asksaveasfilename(
                title="Exportar a Excel",
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            
            if archivo:
                with pd.ExcelWriter(archivo, engine='openpyxl') as writer:
                    df_export.to_excel(writer, sheet_name='Facturas', index=False)
                    
                    # Crear hoja de resumen
                    resumen = pd.DataFrame({
                        'Métrica': ['Total Facturas', 'Suma Total', 'Promedio Factura', 'Factura Más Alta', 'Factura Más Baja'],
                        'Valor': [
                            len(df_export),
                            f"RD$ {df_export['Total'].sum():,.2f}",
                            f"RD$ {df_export['Total'].mean():,.2f}",
                            f"RD$ {df_export['Total'].max():,.2f}",
                            f"RD$ {df_export['Total'].min():,.2f}"
                        ]
                    })
                    resumen.to_excel(writer, sheet_name='Resumen', index=False)
                
                messagebox.showinfo("Éxito", f"Datos exportados a:\n{archivo}")
                
        except ImportError:
            messagebox.showerror("Error", "Para exportar a Excel, instala: pip install pandas openpyxl")
        except Exception as e:
            messagebox.showerror("Error", f"Error exportando a Excel: {str(e)}")
    
    def guardar_datos(self):
        """Guarda los datos extraídos en un archivo JSON"""
        if not self.datos_extraidos:
            messagebox.showwarning("Advertencia", "No hay datos para guardar")
            return
        
        datos_guardar = {
            'fecha_procesamiento': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'archivo_origen': self.ruta_imagen,
            'datos_factura': self.datos_extraidos
        }
        
        ruta = filedialog.asksaveasfilename(
            title="Guardar datos de factura",
            defaultextension=".json",
            filetypes=[("Archivo JSON", "*.json"), ("Todos los archivos", "*.*")]
        )
        
        if ruta:
            try:
                with open(ruta, 'w', encoding='utf-8') as archivo:
                    json.dump(datos_guardar, archivo, indent=2, ensure_ascii=False)
                logger.info(f"Datos guardados en: {ruta}")
                messagebox.showinfo("Éxito", f"Datos guardados en:\n{ruta}")
            except Exception as e:
                logger.error(f"Error guardando datos: {e}")
                messagebox.showerror("Error", f"No se pudo guardar: {str(e)}")
    
    def limpiar_datos(self):
        """Limpia todos los datos"""
        self.limpiar_formularios()
        self.label_imagen.configure(image='', text="Factura no cargada")
        self.ruta_imagen = None
        self.lista_imagenes = []
        self.indice_actual = -1
        self.actualizar_navegacion() 

# ui/gui.py - VERSIÓN COMPLETA CORREGIDA
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
        try:
            from database.models import DatabaseManager
            from ocr.image_preprocessor import ImageProcessor
            from processing.data_extractor import DataExtractor
            
            self.db_manager = DatabaseManager()
            self.image_processor = ImageProcessor()
            self.data_extractor = DataExtractor()
            
        except ImportError as e:
            logger.error(f"Error importando módulos: {e}")
            messagebox.showerror("Error", f"No se pudieron cargar los módulos:\n{e}")
            return
        
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
            ("Comprobante:", "comprobante"),
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
        
        ttk.Button(parent, text="Validar Comprobante", command=self.validar_comprobante).grid(row=3, column=0, pady=5, sticky=tk.W)
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

    # ========== MÉTODOS DE PROCESAMIENTO CON DEBUG MEJORADO ==========
    
    def extraer_datos_factura(self):
        """Extrae datos de la factura actual - CON DEBUG MEJORADO"""
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
            
            print("\n" + "="*80)
            print("🚀 INICIANDO EXTRACCIÓN DESDE GUI")
            print("="*80)
            print(f"📁 Archivo: {os.path.basename(self.ruta_imagen)}")
            print(f"📝 Texto OCR: {len(texto)} caracteres")
            
            # Usar el nuevo método de extracción
            self.datos_extraidos = self.data_extractor.extraer_datos(texto)
            
            # 🔥 DEBUG MEJORADO: Mostrar estructura completa
            print("\n🎯 ESTRUCTURA COMPLETA RECIBIDA EN GUI:")
            print("-" * 50)
            for key, value in self.datos_extraidos.items():
                print(f"   📬 '{key}': {value}")
            print(f"Total campos recibidos: {len(self.datos_extraidos)}")
            
            # Llenar formularios
            self.llenar_formularios()
            
            # Validación automática
            self.validar_y_mostrar_resultados()
            
            # Guardar en base de datos automáticamente
            comprobante = self._obtener_comprobante_apropiado()
            if comprobante:
                # Preparar datos para la base de datos
                datos_db = {
                    'rnc_emisor': self._obtener_valor_mapeado(['rnc_emisor', 'nit', 'rnc', 'numero_documento']),
                    'nombre_emisor': self._obtener_valor_mapeado(['nombre_emisor', 'razon_social', 'nombre_empresa', 'empresa']),
                    'comprobante': comprobante,
                    'fecha_emision': self._obtener_valor_mapeado(['fecha', 'fecha_emision']),
                    'total': self._obtener_valor_mapeado(['total', 'monto_total', 'importe']),
                    'subtotal': self._obtener_valor_mapeado(['subtotal']),
                    'impuestos': self._obtener_valor_mapeado(['itbis', 'impuestos', 'iva']),
                    'tipo_factura': self.datos_extraidos.get('tipo_factura', 'general')
                }
                
                resultado, mensaje = self.db_manager.guardar_factura(datos_db)
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
    
    def _obtener_comprobante_apropiado(self):
        """Obtiene el comprobante apropiado según el tipo de factura - VERSIÓN CORREGIDA"""
        tipo_factura = self.datos_extraidos.get('tipo_factura', 'general')
        
        # ✅ CORRECCIÓN: Para facturas dominicanas, priorizar NCF sobre número de factura
        if tipo_factura == 'peaje':
            # Para peaje, usar número de ticket
            return self._obtener_valor_mapeado(['numero_factura', 'ticket', 'numero'])
        else:
            # ✅ CORRECCIÓN: Para facturas dominicanas, buscar NCF primero aunque haya número de factura
            ncf = self._obtener_valor_mapeado(['ncf'])
            if ncf and ncf != 'False':
                print(f"🎯 Usando NCF como comprobante: {ncf}")
                return ncf
            else:
                # Solo si no hay NCF válido, usar número de factura
                numero_factura = self._obtener_valor_mapeado(['numero_factura', 'numero_comprobante', 'ticket'])
                if numero_factura:
                    print(f"🎯 Usando número de factura como comprobante: {numero_factura}")
                return numero_factura
    
    def llenar_formularios(self):
        """Llena los formularios con los datos extraídos - VERSIÓN CORREGIDA"""
        
        print("\n🔄 INICIANDO MAPEO A GUI...")
        
        # 🔥 MAPEO CORREGIDO - Sin typos
        mapeo_campos = {
            # Información Fiscal
            'rnc_emisor': ['rnc_emisor', 'nit', 'rnc', 'numero_documento'],
            'nombre_emisor': ['nombre_emisor', 'razon_social', 'nombre_empresa', 'empresa'],
            'comprobante': ['ncf', 'numero_factura', 'comprobante'],  # ✅ CORREGIDO: Sin typo
            'fecha_emision': ['fecha', 'fecha_emision'],
            'fecha_vencimiento': ['fecha_vencimiento'],
            
            # Montos
            'subtotal': ['subtotal'],
            'impuestos': ['itbis', 'impuestos', 'iva'],
            'descuentos': ['descuentos'],
            'total': ['total', 'monto_total', 'importe'],
            'total_pagar': ['total_pagar', 'total']
        }
        
        # DEBUG: Mostrar qué campos tenemos disponibles
        print("📦 CAMPOS DISPONIBLES EN datos_extraidos:")
        for key, value in self.datos_extraidos.items():
            if value and str(value).strip() and value != 'False':  # ✅ CORRECCIÓN: Ignorar "False"
                print(f"   ✅ '{key}': {value}")
            else:
                print(f"   ❌ '{key}': VACÍO O FALSE")
        
        # Llenar campos fiscales
        print("\n🖊️  LLENANDO CAMPOS FISCALES:")
        for campo_ui, posibles_campos in mapeo_campos.items():
            if campo_ui in self.entries_fiscal:
                valor = self._obtener_valor_mapeado(posibles_campos)
                self.entries_fiscal[campo_ui].delete(0, tk.END)
                self.entries_fiscal[campo_ui].insert(0, str(valor))
                print(f"   📝 {campo_ui}: '{valor}'")
        
        # Llenar campos de montos
        print("\n💰 LLENANDO CAMPOS DE MONTOS:")
        for campo_ui, posibles_campos in mapeo_campos.items():
            if campo_ui in self.entries_montos:
                valor = self._obtener_valor_mapeado(posibles_campos)
                self.entries_montos[campo_ui].delete(0, tk.END)
                if isinstance(valor, (int, float)):
                    self.entries_montos[campo_ui].insert(0, f"RD$ {valor:,.2f}")
                    print(f"   💰 {campo_ui}: RD$ {valor:,.2f}")
                else:
                    self.entries_montos[campo_ui].insert(0, str(valor))
                    print(f"   💰 {campo_ui}: '{valor}'")
        
        print("✅ MAPEO A GUI COMPLETADO\n")
    
    def _obtener_valor_mapeado(self, posibles_campos):
        """Obtiene el valor del primer campo que exista en la lista - VERSIÓN CORREGIDA"""
        for campo in posibles_campos:
            if campo in self.datos_extraidos and self.datos_extraidos[campo]:
                valor = self.datos_extraidos[campo]
                # ✅ CORRECCIÓN: Ignorar valores "False"
                if str(valor).strip() and valor != 'False' and valor is not False:
                    print(f"   🔍 Encontrado '{campo}': {valor}")
                    return valor
                else:
                    print(f"   ❌ Campo '{campo}' tiene valor inválido: {valor}")
            else:
                print(f"   ❌ Campo '{campo}' no encontrado o vacío")
        
        print(f"   ⚠️  Ninguno de los campos {posibles_campos} fue encontrado")
        return ""
    
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
    
    def validar_comprobante(self):
        """Valida el comprobante actual - VERSIÓN CORREGIDA"""
        tipo_factura = self.datos_extraidos.get('tipo_factura', 'general')
        comprobante = self._obtener_comprobante_apropiado()
        
        if not comprobante:
            messagebox.showwarning("Advertencia", "No hay comprobante para validar")
            return
        
        self.texto_validacion.delete(1.0, tk.END)
        
        # ✅ CORRECCIÓN: Manejo diferenciado por tipo de factura
        if tipo_factura == 'peaje':
            self.texto_validacion.insert(tk.END, f"🎫 VALIDACIÓN FACTURA DE PEAJE\n")
            self.texto_validacion.insert(tk.END, "=" * 40 + "\n\n")
            self.texto_validacion.insert(tk.END, f"📄 Ticket: {comprobante}\n")
            self.texto_validacion.insert(tk.END, f"✅ Válido para factura de peaje\n")
            self.texto_validacion.insert(tk.END, f"ℹ️  Las facturas de peaje no requieren NCF\n")
            self.label_estado_validacion.config(text="VÁLIDO", foreground="green")
        else:
            # Para otros tipos de factura, validar NCF
            ncf_valido = self.data_extractor.validar_ncf_formato(comprobante)
            
            self.texto_validacion.insert(tk.END, f"📄 VALIDACIÓN NCF\n")
            self.texto_validacion.insert(tk.END, "=" * 40 + "\n\n")
            self.texto_validacion.insert(tk.END, f"Comprobante: {comprobante}\n\n")
            
            if ncf_valido:
                self.texto_validacion.insert(tk.END, f"✅ NCF VÁLIDO\n")
                self.texto_validacion.insert(tk.END, f"El formato del NCF es correcto\n")
                self.label_estado_validacion.config(text="VÁLIDO", foreground="green")
            else:
                self.texto_validacion.insert(tk.END, f"❌ NCF INVÁLIDO\n")
                self.texto_validacion.insert(tk.END, f"El formato del NCF no es válido\n")
                self.texto_validacion.insert(tk.END, f"ℹ️  Formato esperado: E310000000001, B0100000001, etc.\n")
                self.label_estado_validacion.config(text="INVÁLIDO", foreground="red")
            
            # Verificar duplicados solo para facturas con NCF válido
            if ncf_valido and self.db_manager.verificar_comprobante_existente(comprobante):
                self.texto_validacion.insert(tk.END, f"\n⚠️  ADVERTENCIA: Este comprobante ya existe en la base de datos")
    
    def verificar_base_datos(self):
        """Verifica si el comprobante existe en la base de datos"""
        comprobante = self._obtener_comprobante_apropiado()
        tipo_factura = self.datos_extraidos.get('tipo_factura', 'general')
        
        if not comprobante:
            messagebox.showwarning("Advertencia", "No hay comprobante para verificar")
            return
        
        duplicado = self.db_manager.verificar_comprobante_existente(comprobante)
        
        self.texto_validacion.delete(1.0, tk.END)
        
        if tipo_factura == 'peaje':
            self.texto_validacion.insert(tk.END, f"🎫 VERIFICACIÓN FACTURA DE PEAJE\n")
            self.texto_validacion.insert(tk.END, "=" * 40 + "\n\n")
            self.texto_validacion.insert(tk.END, f"📄 Ticket: {comprobante}\n\n")
        else:
            self.texto_validacion.insert(tk.END, f"📄 VERIFICACIÓN EN BASE DE DATOS\n")
            self.texto_validacion.insert(tk.END, "=" * 40 + "\n\n")
            self.texto_validacion.insert(tk.END, f"Comprobante: {comprobante}\n\n")
        
        if duplicado:
            self.texto_validacion.insert(tk.END, f"❌ Este comprobante ya existe en la base de datos\n")
            self.texto_validacion.insert(tk.END, f"ℹ️  Posible duplicado\n")
            self.label_estado_validacion.config(text="DUPLICADO", foreground="orange")
        else:
            self.texto_validacion.insert(tk.END, f"✅ Este comprobante no existe en la base de datos\n")
            self.texto_validacion.insert(tk.END, f"ℹ️  Puede proceder con el registro\n")
            self.label_estado_validacion.config(text="NUEVO", foreground="green")
    
    def validar_y_mostrar_resultados(self):
        """Realiza validaciones y muestra resultados - VERSIÓN MEJORADA"""
        self.texto_validacion.delete(1.0, tk.END)
        
        # Obtener datos
        comprobante = self._obtener_comprobante_apropiado()
        rnc = self._obtener_valor_mapeado(['rnc_emisor', 'nit', 'rnc', 'numero_documento'])
        tipo_factura = self.datos_extraidos.get('tipo_factura', 'general')
        
        self.texto_validacion.insert(tk.END, "🔍 RESULTADOS DE VALIDACIÓN\n")
        self.texto_validacion.insert(tk.END, "=" * 40 + "\n\n")
        
        # ✅ CORRECCIÓN: Manejo diferenciado por tipo de factura
        if tipo_factura == 'peaje':
            self.texto_validacion.insert(tk.END, f"🎫 FACTURA DE PEAJE\n")
            self.texto_validacion.insert(tk.END, f"   No requiere NCF\n\n")
            
            if comprobante:
                self.texto_validacion.insert(tk.END, f"📄 Ticket: {comprobante}\n")
                self.texto_validacion.insert(tk.END, f"   ✅ Válido para factura de peaje\n\n")
            else:
                self.texto_validacion.insert(tk.END, f"❌ No se encontró número de ticket\n\n")
            self.label_estado_validacion.config(text="VÁLIDO", foreground="green")
            
        else:
            # Para otros tipos de factura, validar NCF
            if comprobante:
                ncf_valido = self.data_extractor.validar_ncf_formato(comprobante)
                mensaje_ncf = "✅ NCF válido" if ncf_valido else "❌ NCF no válido"
                
                self.texto_validacion.insert(tk.END, f"📄 COMPROBANTE: {comprobante}\n")
                self.texto_validacion.insert(tk.END, f"   {mensaje_ncf}\n\n")
                
                if ncf_valido:
                    self.label_estado_validacion.config(text="VÁLIDO", foreground="green")
                else:
                    self.label_estado_validacion.config(text="INVÁLIDO", foreground="red")
            else:
                self.texto_validacion.insert(tk.END, "❌ No se encontró comprobante\n\n")
                self.label_estado_validacion.config(text="INCOMPLETO", foreground="orange")
        
        # Validación de RNC (común para todos los tipos)
        if rnc:
            if len(str(rnc)) in [9, 11]:
                self.texto_validacion.insert(tk.END, f"🏢 RNC: {rnc} (Formato válido - {len(str(rnc))} dígitos)\n\n")
            else:
                self.texto_validacion.insert(tk.END, f"⚠️ RNC: {rnc} (Longitud inusual - {len(str(rnc))} dígitos)\n\n")
        else:
            self.texto_validacion.insert(tk.END, "❌ No se encontró RNC\n\n")
        
        # Verificar duplicados (solo si es factura con NCF válido)
        if tipo_factura != 'peaje' and comprobante and self.data_extractor.validar_ncf_formato(comprobante):
            if self.db_manager.verificar_comprobante_existente(comprobante):
                self.texto_validacion.insert(tk.END, "🚨 ADVERTENCIA: Este comprobante ya existe en la base de datos\n\n")
        
        # Mostrar calidad de extracción
        if 'calidad_texto' in self.datos_extraidos:
            calidad = self.datos_extraidos['calidad_texto']
            puntuacion = self.datos_extraidos.get('puntuacion_calidad_texto', 'N/A')
            self.texto_validacion.insert(tk.END, f"📊 Calidad de extracción: {calidad} ({puntuacion}/10)\n")
        
        if 'confianza_clasificacion' in self.datos_extraidos:
            confianza = self.datos_extraidos['confianza_clasificacion']
            self.texto_validacion.insert(tk.END, f"🎯 Confianza de clasificación: {confianza:.2f}\n")
        
        # Mostrar tipo de factura detectado
        self.texto_validacion.insert(tk.END, f"📋 Tipo de factura: {tipo_factura}\n")

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
                texto_bd.insert(tk.END, f"Tipo: {factura.get('tipo_factura', 'N/A')}\n")
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
                    datos = self.data_extractor.extraer_datos(texto)
                    datos['archivo'] = ruta_imagen
                    datos['fecha_procesamiento'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    resultados.append(datos)
                    
                    # Guardar en base de datos si tiene comprobante
                    comprobante = self._obtener_comprobante_apropiado()
                    if comprobante:
                        datos_db = {
                            'rnc_emisor': self._obtener_valor_mapeado(['rnc_emisor', 'nit', 'rnc', 'numero_documento']),
                            'nombre_emisor': self._obtener_valor_mapeado(['nombre_emisor', 'razon_social', 'nombre_empresa', 'empresa']),
                            'comprobante': comprobante,
                            'fecha_emision': self._obtener_valor_mapeado(['fecha', 'fecha_emision']),
                            'total': self._obtener_valor_mapeado(['total', 'monto_total', 'importe']),
                            'tipo_factura': datos.get('tipo_factura', 'general')
                        }
                        self.db_manager.guardar_factura(datos_db)
                    
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
                'rnc_emisor', 'nombre_emisor', 'comprobante', 'tipo_factura', 'fecha_emision',
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
                'tipo_factura': 'Tipo Factura',
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

def main():
    root = tk.Tk()
    app = ExtractorFacturasApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
# processing/data_extractor.py
import re
import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DataExtractor:
    def __init__(self):
        self.proveedores_frecuentes = {}
        
    def extract_data_from_text(self, text: str, image_path: str = None) -> Dict[str, Any]:
        """
        Extrae datos estructurados de una factura desde el texto OCR
        """
        logger.info("Iniciando extracción de datos desde texto...")
        
        datos_extraidos = {
            'rnc_emisor': '',
            'nombre_emisor': '',
            'comprobante': '',
            'fecha_emision': '',
            'subtotal': None,
            'impuestos': None,
            'descuentos': None,
            'total': None,
            'total_pagar': None,
            'archivo_origen': image_path,
            'fecha_procesamiento': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'confianza': 0,
            'texto_completo': text
        }
        
        try:
            # Extraer RNC
            datos_extraidos['rnc_emisor'] = self.buscar_rnc(text)
            
            # Extraer Comprobante/NCF
            datos_extraidos['comprobante'] = self.buscar_comprobante(text)
            
            # Extraer Fecha de Emisión
            datos_extraidos['fecha_emision'] = self.buscar_fecha_emision(text)
            
            # Extraer montos
            self.extraer_montos_desde_texto(text, datos_extraidos)
            
            # Extraer nombre del emisor
            datos_extraidos['nombre_emisor'] = self.extraer_nombre_emisor(text)
            
            # Calcular montos faltantes
            self.calcular_montos_faltantes(datos_extraidos)
            
            # Calcular confianza
            datos_extraidos['confianza'] = self.calcular_confianza_extraccion(datos_extraidos)
            
            logger.info("Extracción de datos completada")
            self.log_datos_extraidos(datos_extraidos)
            
        except Exception as e:
            logger.error(f"Error en extracción de datos: {e}")
            
        return datos_extraidos
    
    def buscar_rnc(self, texto: str) -> str:
        """
        Busca RNC en el texto con múltiples patrones
        """
        patrones_rnc = [
            r'RNC\s*:?\s*(\d{9}|\d{3}-\d{7}-\d{1})',
            r'R\.N\.C\.\s*:?\s*(\d{9}|\d{3}-\d{7}-\d{1})',
            r'IDENTIFICACION\s*:?\s*(\d{9}|\d{3}-\d{7}-\d{1})',
            r'REGISTRO\s*NACIONAL\s*:?\s*(\d{9}|\d{3}-\d{7}-\d{1})',
            r'(\d{3}-\d{7}-\d{1})',  # Formato con guiones
            r'(\d{9})'  # Formato sin guiones
        ]
        
        for patron in patrones_rnc:
            matches = re.findall(patron, texto, re.IGNORECASE)
            if matches:
                rnc_encontrado = matches[0]
                # Limpiar formato
                rnc_limpio = re.sub(r'[^\d]', '', rnc_encontrado)
                logger.debug(f"RNC encontrado: {rnc_limpio} (patrón: {patron})")
                return rnc_limpio
        
        logger.debug("No se encontró RNC en el texto")
        return ""
    
    def buscar_comprobante(self, texto: str) -> str:
        """
        Busca NCF/Comprobante en el texto
        """
        patrones_ncf = [
            r'NCF\s*:?\s*([A-Z]\d{2}\d{11})',
            r'COMPROBANTE\s*:?\s*([A-Z]\d{2}\d{11})',
            r'NO\.?\s*COMPROBANTE\s*:?\s*([A-Z]\d{2}\d{11})',
            r'COMPROBANTE\s*FISCAL\s*:?\s*([A-Z]\d{2}\d{11})',
            r'NUMERO\s*DE\s*COMPROBANTE\s*:?\s*([A-Z]\d{2}\d{11})',
            r'([A-Z]\d{2}\d{11})'  # Solo el formato NCF
        ]
        
        for patron in patrones_ncf:
            matches = re.findall(patron, texto, re.IGNORECASE)
            if matches:
                ncf_encontrado = matches[0].upper()
                logger.debug(f"NCF encontrado: {ncf_encontrado} (patrón: {patron})")
                return ncf_encontrado
        
        logger.debug("No se encontró NCF en el texto")
        return ""
    
    def buscar_fecha_emision(self, texto: str) -> str:
        """
        Busca fecha de emisión en el texto
        """
        patrones_fecha = [
            r'FECHA\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'EMISION\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'FECHA\s*DE\s*EMISION\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'FECHA\s*FACTURA\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        ]
        
        for patron in patrones_fecha:
            matches = re.findall(patron, texto, re.IGNORECASE)
            if matches:
                fecha_encontrada = matches[0]
                # Estandarizar formato
                fecha_limpia = self.limpiar_fecha(fecha_encontrada)
                logger.debug(f"Fecha encontrada: {fecha_limpia} (patrón: {patron})")
                return fecha_limpia
        
        logger.debug("No se encontró fecha de emisión en el texto")
        return ""
    
    def extraer_montos_desde_texto(self, texto: str, datos: Dict[str, Any]):
        """
        Extrae montos y los agrega al diccionario datos
        """
        patrones_montos = {
            'subtotal': [
                r'SUBTOTAL\s*[\$RD\s]*([0-9,]+\.?[0-9]*)',
                r'SUB-TOTAL\s*[\$RD\s]*([0-9,]+\.?[0-9]*)',
                r'BASE\s*IMPONIBLE\s*[\$RD\s]*([0-9,]+\.?[0-9]*)'
            ],
            'impuestos': [
                r'ITBIS\s*[\$RD\s]*([0-9,]+\.?[0-9]*)',
                r'IMPUESTOS?\s*[\$RD\s]*([0-9,]+\.?[0-9]*)',
                r'IVA\s*[\$RD\s]*([0-9,]+\.?[0-9]*)',
                r'IMPUESTO\s*[\$RD\s]*([0-9,]+\.?[0-9]*)'
            ],
            'descuentos': [
                r'DESCUENTO\s*[\$RD\s]*([0-9,]+\.?[0-9]*)',
                r'DESC\.\s*[\$RD\s]*([0-9,]+\.?[0-9]*)',
                r'REBAJA\s*[\$RD\s]*([0-9,]+\.?[0-9]*)',
                r'DISCOUNT\s*[\$RD\s]*([0-9,]+\.?[0-9]*)'
            ],
            'total': [
                r'TOTAL\s*[\$RD\s]*([0-9,]+\.?[0-9]*)',
                r'TOTAL\s*A\s*PAGAR\s*[\$RD\s]*([0-9,]+\.?[0-9]*)',
                r'MONTO\s*TOTAL\s*[\$RD\s]*([0-9,]+\.?[0-9]*)',
                r'IMPORTE\s*TOTAL\s*[\$RD\s]*([0-9,]+\.?[0-9]*)'
            ],
            'total_pagar': [
                r'TOTAL\s*A\s*PAGAR\s*[\$RD\s]*([0-9,]+\.?[0-9]*)',
                r'MONTO\s*A\s*PAGAR\s*[\$RD\s]*([0-9,]+\.?[0-9]*)',
                r'PAGAR\s*[\$RD\s]*([0-9,]+\.?[0-9]*)'
            ]
        }
        
        for key, patrones in patrones_montos.items():
            for patron in patrones:
                matches = re.findall(patron, texto, re.IGNORECASE)
                if matches:
                    monto = self.limpiar_monto(matches[0])
                    if monto is not None:
                        datos[key] = monto
                        logger.debug(f"Monto {key}: {monto} (patrón: {patron})")
                        break
    
    def calcular_montos_faltantes(self, datos: Dict[str, Any]):
        """
        Calcula montos que no se pudieron extraer directamente
        """
        total = datos.get('total')
        subtotal = datos.get('subtotal')
        impuestos = datos.get('impuestos')
        descuentos = datos.get('descuentos', 0)
        
        # Si tenemos total e impuestos pero no subtotal
        if total is not None and impuestos is not None and subtotal is None:
            datos['subtotal'] = total - impuestos
            logger.debug(f"Subtotal calculado: {datos['subtotal']}")
        
        # Si tenemos total y subtotal pero no impuestos
        if total is not None and subtotal is not None and impuestos is None:
            datos['impuestos'] = total - subtotal
            logger.debug(f"Impuestos calculados: {datos['impuestos']}")
        
        # Si tenemos subtotal e impuestos pero no total
        if subtotal is not None and impuestos is not None and total is None:
            datos['total'] = subtotal + impuestos
            logger.debug(f"Total calculado: {datos['total']}")
        
        # Si tenemos total pero no total_pagar
        if 'total' in datos and 'total_pagar' not in datos:
            datos['total_pagar'] = datos['total']
    
    def extraer_nombre_emisor(self, texto: str) -> str:
        """
        Intenta extraer el nombre del emisor del texto
        """
        lineas = texto.split('\n')
        
        palabras_clave = [
            'EMISOR', 'PROVEEDOR', 'COMPAÑIA', 'COMPANY', 
            'NOMBRE', 'RAZON SOCIAL', 'VENDEDOR', 'ESTABLECIMIENTO',
            'BUSINESS', 'COMPANY', 'CORPORATION'
        ]
        
        for i, linea in enumerate(lineas):
            linea_upper = linea.upper().strip()
            
            # Buscar líneas que contengan palabras clave
            for palabra in palabras_clave:
                if palabra in linea_upper:
                    # Buscar en las siguientes líneas el nombre
                    for j in range(1, 4):  # Buscar en las 3 líneas siguientes
                        if i + j < len(lineas):
                            nombre_candidato = lineas[i + j].strip()
                            
                            # Validar que sea un nombre válido
                            if (nombre_candidato and 
                                len(nombre_candidato) > 3 and 
                                not re.match(r'^\d', nombre_candidato) and
                                not any(clave in nombre_candidato.upper() for clave in palabras_clave) and
                                not re.match(r'^[^a-zA-Z]*$', nombre_candidato)):
                                
                                logger.debug(f"Nombre emisor encontrado: {nombre_candidato}")
                                return nombre_candidato
        
        logger.debug("No se pudo extraer nombre del emisor")
        return ""
    
    def limpiar_monto(self, monto_str: str) -> Optional[float]:
        """
        Convierte string de monto a float
        """
        try:
            if not monto_str:
                return None
                
            # Remover símbolos de moneda, comas y espacios
            monto_limpio = re.sub(r'[^\d.]', '', monto_str.replace(',', ''))
            
            if not monto_limpio:
                return None
                
            return float(monto_limpio)
            
        except (ValueError, TypeError) as e:
            logger.debug(f"Error limpiando monto '{monto_str}': {e}")
            return None
    
    def limpiar_fecha(self, fecha_str: str) -> str:
        """
        Estandariza el formato de fecha
        """
        try:
            # Reemplazar separadores inconsistentes
            fecha_limpia = fecha_str.replace('-', '/')
            
            # Asegurar formato dd/mm/yyyy
            partes = fecha_limpia.split('/')
            if len(partes) == 3:
                dia = partes[0].zfill(2)
                mes = partes[1].zfill(2)
                año = partes[2]
                
                # Ajustar año si es de dos dígitos
                if len(año) == 2:
                    año = '20' + año
                
                return f"{dia}/{mes}/{año}"
            
            return fecha_limpia
            
        except Exception as e:
            logger.debug(f"Error limpiando fecha '{fecha_str}': {e}")
            return fecha_str
    
    def calcular_confianza_extraccion(self, datos: Dict[str, Any]) -> float:
        """
        Calcula un score de confianza para la extracción
        """
        campos_obligatorios = ['rnc_emisor', 'comprobante', 'total']
        campos_importantes = ['fecha_emision', 'nombre_emisor', 'subtotal']
        
        puntaje = 0
        max_puntaje = len(campos_obligatorios) * 2 + len(campos_importantes)
        
        # Campos obligatorios (2 puntos cada uno)
        for campo in campos_obligatorios:
            if datos.get(campo):
                puntaje += 2
        
        # Campos importantes (1 punto cada uno)
        for campo in campos_importantes:
            if datos.get(campo):
                puntaje += 1
        
        # Puntos adicionales por validación de formato
        if datos.get('comprobante'):
            valido, _ = self.validar_ncf_formato(datos['comprobante'])
            if valido:
                puntaje += 1
        
        if datos.get('rnc_emisor'):
            if len(datos['rnc_emisor']) in [9, 11]:
                puntaje += 1
        
        confianza = (puntaje / max_puntaje) * 100
        return round(confianza, 2)
    
    def validar_ncf_formato(self, ncf: str) -> Tuple[bool, str]:
        """
        Valida el formato del NCF según normativa dominicana
        """
        if not ncf:
            return False, "NCF vacío"
        
        # Patrón básico: Letra + 13 dígitos
        patron = r'^[A-Z]\d{13}$'
        if not re.match(patron, ncf):
            return False, "Formato inválido. Debe ser: Letra + 13 dígitos"
        
        # Tipos de comprobantes válidos según DGII
        tipo_comprobante = ncf[0]
        tipos_validos = ['A', 'B', 'E', 'F', 'G', 'H', 'I', 'J', 'K']
        
        if tipo_comprobante not in tipos_validos:
            return False, f"Tipo de comprobante '{tipo_comprobante}' no válido"
        
        # Validar secuencia numérica
        secuencia = ncf[1:]
        if not secuencia.isdigit():
            return False, "La secuencia debe ser numérica"
        
        # Descripción del tipo de comprobante
        descripciones = {
            'A': 'Factura de Crédito Fiscal',
            'B': 'Factura de Consumo',
            'E': 'Factura de Exportación',
            'F': 'Factura de Importación',
            'G': 'Comprobante Gubernamental',
            'H': 'Factura de Sujeto Excluido',
            'I': 'Comprobante para Gastos Menores',
            'J': 'Comprobante para Régimen Especial',
            'K': 'Comprobante para Régimen Agrícola'
        }
        
        descripcion = descripciones.get(tipo_comprobante, 'Tipo desconocido')
        return True, f"NCF válido - {descripcion}"
    
    def log_datos_extraidos(self, datos: Dict[str, Any]):
        """
        Log de los datos extraídos para debugging
        """
        logger.info("=== DATOS EXTRAÍDOS ===")
        for key, value in datos.items():
            if key != 'texto_completo' and value:  # No loguear el texto completo
                logger.info(f"  {key}: {value}")
        logger.info(f"  Confianza: {datos.get('confianza', 0)}%")
        logger.info("========================")
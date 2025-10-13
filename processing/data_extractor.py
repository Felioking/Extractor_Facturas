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
        Extrae datos estructurados de facturas - VERSIÓN OPTIMIZADA
        """
        print("🔧 [EXTRACTOR] Iniciando extracción optimizada...")
        
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
            # 1. EXTRAER RNC
            datos_extraidos['rnc_emisor'] = self.buscar_rnc(text)
            if datos_extraidos['rnc_emisor']:
                print(f"✅ [EXTRACTOR] RNC encontrado: {datos_extraidos['rnc_emisor']}")
            
            # 2. EXTRAER NOMBRE EMISOR
            datos_extraidos['nombre_emisor'] = self.extraer_nombre_emisor(text)
            if datos_extraidos['nombre_emisor']:
                print(f"✅ [EXTRACTOR] Emisor: {datos_extraidos['nombre_emisor']}")
            
            # 3. EXTRAER FECHA
            datos_extraidos['fecha_emision'] = self.buscar_fecha_emision(text)
            if datos_extraidos['fecha_emision']:
                print(f"✅ [EXTRACTOR] Fecha: {datos_extraidos['fecha_emision']}")
            
            # 4. EXTRAER MONTOS
            self.extraer_montos_desde_texto(text, datos_extraidos)
            
            # Mostrar montos encontrados
            montos_encontrados = []
            for key in ['subtotal', 'impuestos', 'total', 'total_pagar']:
                if datos_extraidos.get(key):
                    montos_encontrados.append(f"{key}: {datos_extraidos[key]}")
            
            if montos_encontrados:
                print(f"✅ [EXTRACTOR] Montos: {', '.join(montos_encontrados)}")
            
            # 5. CALCULAR CONFIANZA
            datos_extraidos['confianza'] = self.calcular_confianza_extraccion(datos_extraidos)
            print(f"📊 [EXTRACTOR] Confianza: {datos_extraidos['confianza']}%")
            
            logger.info("Extracción de datos completada")
            
        except Exception as e:
            logger.error(f"Error en extracción de datos: {e}")
            print(f"❌ [EXTRACTOR] Error: {e}")
            
        return datos_extraidos
    
    def buscar_rnc(self, texto: str) -> str:
        """Busca RNC con múltiples patrones"""
        patrones_rnc = [
            r'RNC[\s:]*([0-9]{9}|[0-9]{3}-[0-9]{7}-[0-9]{1})',
            r'R\.N\.C\.[\s:]*([0-9]{9}|[0-9]{3}-[0-9]{7}-[0-9]{1})',
            r'IDENTIFICACION[\s:]*([0-9]{9}|[0-9]{3}-[0-9]{7}-[0-9]{1})',
        ]
        
        for patron in patrones_rnc:
            match = re.search(patron, texto, re.IGNORECASE)
            if match:
                rnc = re.sub(r'[^\\d]', '', match.group(1))
                return rnc
        return ""
    
    def extraer_nombre_emisor(self, texto: str) -> str:
        """Extrae nombre del emisor"""
        lineas = texto.split('\\n')
        
        # Buscar después de palabras clave
        palabras_clave = ['Fideicomiso', 'Empresa', 'Compañía', 'S.A.', 'S.R.L.']
        
        for i, linea in enumerate(lineas):
            linea_limpia = linea.strip()
            if any(palabra in linea_limpia for palabra in palabras_clave) and len(linea_limpia) > 5:
                return linea_limpia
        
        # Si no encuentra, tomar primera línea significativa
        for linea in lineas:
            linea_limpia = linea.strip()
            if len(linea_limpia) > 10 and not re.match(r'^[0-9\s\W]+$', linea_limpia):
                return linea_limpia
        
        return ""
    
    def buscar_fecha_emision(self, texto: str) -> str:
        """Busca fecha de emisión"""
        patrones_fecha = [
            r'Fecha[\s:/]*([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})',
            r'Emision[\s:/]*([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})',
            r'([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})'
        ]
        
        for patron in patrones_fecha:
            match = re.search(patron, texto, re.IGNORECASE)
            if match:
                return match.group(1)
        return ""
    
    def extraer_montos_desde_texto(self, texto: str, datos: Dict[str, Any]):
        """Extrae montos del texto"""
        patrones_montos = {
            'subtotal': [
                r'Subtotal[\s\\$RD]*([0-9,]+\\.?[0-9]*)',
                r'SUB-TOTAL[\s\\$RD]*([0-9,]+\\.?[0-9]*)'
            ],
            'impuestos': [
                r'ITBIS[\s\\$RD]*([0-9,]+\\.?[0-9]*)',
                r'IMPUESTO[\s\\$RD]*([0-9,]+\\.?[0-9]*)'
            ],
            'total': [
                r'Total[\s\\$RD]*([0-9,]+\\.?[0-9]*)',
                r'IMPORTE[\s\\$RD]*([0-9,]+\\.?[0-9]*)',
                r'MONTO[\s\\$RD]*([0-9,]+\\.?[0-9]*)'
            ]
        }
        
        for campo, patrones in patrones_montos.items():
            for patron in patrones:
                match = re.search(patron, texto, re.IGNORECASE)
                if match:
                    try:
                        monto_limpio = re.sub(r'[^0-9.]', '', match.group(1).replace(',', ''))
                        datos[campo] = float(monto_limpio)
                        break
                    except (ValueError, TypeError):
                        pass
    
    def calcular_confianza_extraccion(self, datos: Dict[str, Any]) -> float:
        """Calcula confianza de la extracción"""
        campos = ['rnc_emisor', 'nombre_emisor', 'fecha_emision', 'total']
        campos_encontrados = sum(1 for campo in campos if datos.get(campo))
        
        confianza = (campos_encontrados / len(campos)) * 100
        return round(confianza, 2)

# Instancia global
data_extractor = DataExtractor()

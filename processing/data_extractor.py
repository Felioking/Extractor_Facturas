"""
Módulo de extracción de datos estructurados desde texto OCR
"""

import re
import logging
from typing import Dict, Any, List, Optional
from config import Config

class DataExtractor:
    """Extrae datos estructurados de facturas desde texto OCR"""
    
    def __init__(self):
        self.patterns = Config.PATTERNS
    
    def extract_invoice_data(self, text: str) -> Dict[str, Any]:
        """
        Extrae todos los datos de una factura del texto OCR
        
        Args:
            text: Texto extraído por OCR
            
        Returns:
            Diccionario con datos estructurados de la factura
        """
        try:
            data = {}
            
            # Extraer información fiscal
            data['rnc_emisor'] = self._extract_rnc(text)
            data['comprobante'] = self._extract_ncf(text)
            data['fecha_emision'] = self._extract_fecha_emision(text)
            data['nombre_emisor'] = self._extract_nombre_emisor(text)
            
            # Extraer montos
            montos = self._extract_montos(text)
            data.update(montos)
            
            # Calcular montos faltantes
            self._calcular_montos_faltantes(data)
            
            logging.info("✓ Datos de factura extraídos correctamente")
            return data
            
        except Exception as e:
            logging.error(f"Error extrayendo datos de factura: {e}")
            return {}
    
    def _extract_rnc(self, text: str) -> str:
        """Extrae RNC del emisor"""
        for pattern in self.patterns['rnc']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        return ""
    
    def _extract_ncf(self, text: str) -> str:
        """Extrae NCF/Comprobante"""
        for pattern in self.patterns['ncf']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        return ""
    
    def _extract_fecha_emision(self, text: str) -> str:
        """Extrae fecha de emisión"""
        for pattern in self.patterns['fecha']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        return ""
    
    def _extract_nombre_emisor(self, text: str) -> str:
        """Intenta extraer el nombre del emisor"""
        lines = text.split('\n')
        palabras_clave = ['EMISOR', 'PROVEEDOR', 'COMPAÑIA', 'COMPANY', 'NOMBRE', 'RAZON SOCIAL']
        
        for i, linea in enumerate(lines):
            linea_upper = linea.upper().strip()
            for palabra in palabras_clave:
                if palabra in linea_upper:
                    # Buscar en las siguientes 3 líneas
                    for j in range(1, 4):
                        if i + j < len(lines):
                            nombre_candidato = lines[i + j].strip()
                            if (nombre_candidato and 
                                len(nombre_candidato) > 3 and 
                                not re.match(r'^\d', nombre_candidato) and
                                not any(clave in nombre_candidato.upper() for clave in palabras_clave)):
                                return nombre_candidato
        return ""
    
    def _extract_montos(self, text: str) -> Dict[str, float]:
        """Extrae montos de la factura"""
        montos = {}
        
        patrones_montos = {
            'subtotal': [
                r'SUBTOTAL\s*[\$RD\s]*([0-9,]+\.?[0-9]*)',
                r'SUB-TOTAL\s*[\$RD\s]*([0-9,]+\.?[0-9]*)'
            ],
            'impuestos': [
                r'ITBIS\s*[\$RD\s]*([0-9,]+\.?[0-9]*)',
                r'IMPUESTOS?\s*[\$RD\s]*([0-9,]+\.?[0-9]*)',
                r'IVA\s*[\$RD\s]*([0-9,]+\.?[0-9]*)'
            ],
            'descuentos': [
                r'DESCUENTO\s*[\$RD\s]*([0-9,]+\.?[0-9]*)',
                r'DESC\.\s*[\$RD\s]*([0-9,]+\.?[0-9]*)',
                r'REBAJA\s*[\$RD\s]*([0-9,]+\.?[0-9]*)'
            ],
            'total': [
                r'TOTAL\s*[\$RD\s]*([0-9,]+\.?[0-9]*)',
                r'TOTAL\s*A\s*PAGAR\s*[\$RD\s]*([0-9,]+\.?[0-9]*)',
                r'MONTO\s*TOTAL\s*[\$RD\s]*([0-9,]+\.?[0-9]*)'
            ]
        }
        
        for key, patrones in patrones_montos.items():
            for patron in patrones:
                matches = re.findall(patron, text, re.IGNORECASE)
                if matches:
                    monto = self._limpiar_monto(matches[0])
                    if monto is not None:
                        montos[key] = monto
                        break
        
        return montos
    
    def _limpiar_monto(self, monto_str: str) -> Optional[float]:
        """Convierte string de monto a float"""
        try:
            monto_limpio = re.sub(r'[^\d.]', '', monto_str.replace(',', ''))
            return float(monto_limpio)
        except (ValueError, TypeError):
            return None
    
    def _calcular_montos_faltantes(self, data: Dict[str, Any]):
        """Calcula montos que no se pudieron extraer directamente"""
        total = data.get('total')
        subtotal = data.get('subtotal')
        impuestos = data.get('impuestos')
        
        # Si tenemos total e impuestos pero no subtotal
        if total is not None and impuestos is not None and subtotal is None:
            data['subtotal'] = total - impuestos
        
        # Si tenemos total y subtotal pero no impuestos
        if total is not None and subtotal is not None and impuestos is None:
            data['impuestos'] = total - subtotal
        
        # Total a pagar es generalmente el mismo que total
        if 'total' in data and 'total_pagar' not in data:
            data['total_pagar'] = data['total']
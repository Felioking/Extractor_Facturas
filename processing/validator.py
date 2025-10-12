"""
Módulo de validación de datos de facturas
"""

import re
import logging
from typing import Tuple, Dict, Any
from config import Config

class InvoiceValidator:
    """Valida los datos extraídos de las facturas"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.ncf_tipos_validos = Config.NCF_TIPOS_VALIDOS
    
    def validate_ncf(self, ncf: str) -> Tuple[bool, str]:
        """
        Valida el formato del NCF según normativa dominicana
        
        Args:
            ncf: Número de Comprobante Fiscal
            
        Returns:
            Tupla (es_valido, mensaje)
        """
        if not ncf:
            return False, "NCF vacío"
        
        # Patrón básico de NCF: Letra + 13 dígitos
        patron = r'^[A-Z]\d{13}$'
        if not re.match(patron, ncf):
            return False, "Formato inválido. Debe ser: Letra + 13 dígitos"
        
        # Validar tipo de comprobante
        tipo_comprobante = ncf[0]
        if tipo_comprobante not in self.ncf_tipos_validos:
            return False, f"Tipo de comprobante '{tipo_comprobante}' no válido"
        
        # Validar secuencia numérica
        secuencia = ncf[1:]
        if not secuencia.isdigit():
            return False, "La secuencia debe ser numérica"
        
        return True, f"NCF válido - Tipo: {tipo_comprobante}"
    
    def validate_rnc(self, rnc: str) -> Tuple[bool, str]:
        """
        Valida el formato del RNC
        
        Args:
            rnc: RNC a validar
            
        Returns:
            Tupla (es_valido, mensaje)
        """
        if not rnc:
            return False, "RNC vacío"
        
        # Remover guiones para validación
        rnc_limpio = rnc.replace('-', '')
        
        if not rnc_limpio.isdigit():
            return False, "RNC debe contener solo dígitos"
        
        if len(rnc_limpio) not in [9, 11]:
            return False, f"Longitud de RNC inválida: {len(rnc_limpio)} dígitos"
        
        return True, f"RNC válido - {len(rnc_limpio)} dígitos"
    
    def check_duplicate(self, comprobante: str) -> bool:
        """
        Verifica si el comprobante ya existe en la base de datos
        
        Args:
            comprobante: NCF a verificar
            
        Returns:
            True si es duplicado, False si no
        """
        if not self.db_manager or not comprobante:
            return False
        
        try:
            return self.db_manager.factura_existe(comprobante)
        except Exception as e:
            logging.error(f"Error verificando duplicado: {e}")
            return False
    
    def validate_amounts(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Valida la coherencia de los montos
        
        Args:
            data: Datos de la factura
            
        Returns:
            Tupla (es_valido, mensaje)
        """
        total = data.get('total')
        subtotal = data.get('subtotal')
        impuestos = data.get('impuestos')
        
        if not total:
            return False, "No se encontró monto total"
        
        if subtotal and impuestos:
            calculado = subtotal + impuestos
            diferencia = abs(total - calculado)
            
            if diferencia > 0.01:  # Tolerancia pequeña para decimales
                return False, f"Inconsistencia en montos: diferencia de RD$ {diferencia:.2f}"
        
        return True, "Montos coherentes"
    
    def comprehensive_validation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Realiza una validación completa de todos los datos
        
        Args:
            data: Datos de la factura a validar
            
        Returns:
            Diccionario con resultados de validación
        """
        resultados = {
            'valido_general': True,
            'errores': [],
            'advertencias': [],
            'detalles': {}
        }
        
        # Validar NCF
        ncf = data.get('comprobante', '')
        if ncf:
            ncf_valido, mensaje_ncf = self.validate_ncf(ncf)
            resultados['detalles']['ncf'] = {
                'valido': ncf_valido,
                'mensaje': mensaje_ncf
            }
            if not ncf_valido:
                resultados['valido_general'] = False
                resultados['errores'].append(f"NCF: {mensaje_ncf}")
        else:
            resultados['valido_general'] = False
            resultados['errores'].append("No se encontró NCF")
        
        # Validar RNC
        rnc = data.get('rnc_emisor', '')
        if rnc:
            rnc_valido, mensaje_rnc = self.validate_rnc(rnc)
            resultados['detalles']['rnc'] = {
                'valido': rnc_valido,
                'mensaje': mensaje_rnc
            }
            if not rnc_valido:
                resultados['advertencias'].append(f"RNC: {mensaje_rnc}")
        else:
            resultados['advertencias'].append("No se encontró RNC")
        
        # Verificar duplicados
        if ncf and self.check_duplicate(ncf):
            resultados['advertencias'].append("Este comprobante ya existe en la base de datos")
        
        # Validar montos
        montos_valido, mensaje_montos = self.validate_amounts(data)
        resultados['detalles']['montos'] = {
            'valido': montos_valido,
            'mensaje': mensaje_montos
        }
        if not montos_valido:
            resultados['advertencias'].append(f"Montos: {mensaje_montos}")
        
        return resultados
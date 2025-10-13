# processing/validator.py
import re
import logging
from typing import Dict, Any, Tuple, List

logger = logging.getLogger(__name__)

class Validator:
    def __init__(self):
        pass
    
    def validar_factura_completa(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Realiza validación completa de los datos de la factura
        """
        validaciones = {
            'ncf_valido': False,
            'rnc_valido': False,
            'montos_coherentes': False,
            'campos_obligatorios': False,
            'errores': [],
            'advertencias': []
        }
        
        # Validar NCF
        if datos.get('comprobante'):
            valido, mensaje = self.validar_ncf_formato(datos['comprobante'])
            validaciones['ncf_valido'] = valido
            if not valido:
                validaciones['errores'].append(f"NCF: {mensaje}")
        else:
            validaciones['errores'].append("NCF no encontrado")
        
        # Validar RNC
        if datos.get('rnc_emisor'):
            valido, mensaje = self.validar_rnc_formato(datos['rnc_emisor'])
            validaciones['rnc_valido'] = valido
            if not valido:
                validaciones['advertencias'].append(f"RNC: {mensaje}")
        else:
            validaciones['advertencias'].append("RNC no encontrado")
        
        # Validar coherencia de montos
        if datos.get('subtotal') and datos.get('impuestos') and datos.get('total'):
            calculado = datos['subtotal'] + datos['impuestos']
            if abs(calculado - datos['total']) < 0.01:  # Tolerancia para decimales
                validaciones['montos_coherentes'] = True
            else:
                validaciones['advertencias'].append(
                    f"Montos incoherentes: Subtotal + Impuestos ({calculado:.2f}) ≠ Total ({datos['total']:.2f})"
                )
        
        # Validar campos obligatorios
        campos_presentes = sum(1 for campo in ['rnc_emisor', 'comprobante', 'total'] if datos.get(campo))
        if campos_presentes >= 2:
            validaciones['campos_obligatorios'] = True
        else:
            validaciones['errores'].append("Faltan campos obligatorios")
        
        return validaciones
    
    def validar_ncf_formato(self, ncf: str) -> Tuple[bool, str]:
        """
        Valida el formato del NCF según normativa dominicana
        """
        if not ncf:
            return False, "NCF vacío"
        
        patron = r'^[A-Z]\d{13}$'
        if not re.match(patron, ncf):
            return False, "Formato inválido. Debe ser: Letra + 13 dígitos"
        
        tipo_comprobante = ncf[0]
        tipos_validos = ['A', 'B', 'E', 'F', 'G', 'H', 'I', 'J', 'K']
        
        if tipo_comprobante not in tipos_validos:
            return False, f"Tipo de comprobante '{tipo_comprobante}' no válido"
        
        return True, f"NCF válido - Tipo: {tipo_comprobante}"
    
    def validar_rnc_formato(self, rnc: str) -> Tuple[bool, str]:
        """
        Valida el formato del RNC
        """
        if not rnc:
            return False, "RNC vacío"
        
        # Limpiar formato
        rnc_limpio = re.sub(r'[^\d]', '', rnc)
        
        if len(rnc_limpio) == 9:
            return True, "RNC válido (9 dígitos)"
        elif len(rnc_limpio) == 11:
            return True, "RNC válido (11 dígitos - formato con guiones)"
        else:
            return False, f"Longitud inválida: {len(rnc_limpio)} dígitos"
    
    def validar_fecha_formato(self, fecha: str) -> Tuple[bool, str]:
        """
        Valida el formato de fecha
        """
        if not fecha:
            return False, "Fecha vacía"
        
        patron = r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$'
        if not re.match(patron, fecha):
            return False, "Formato de fecha inválido"
        
        return True, "Fecha válida"
"""
Modelos de datos para la aplicación
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Factura:
    """Modelo de datos para facturas"""
    id: Optional[int] = None
    rnc_emisor: str = ""
    nombre_emisor: str = ""
    comprobante: str = ""
    fecha_emision: str = ""
    subtotal: float = 0.0
    impuestos: float = 0.0
    descuentos: float = 0.0
    total: float = 0.0
    archivo_origen: str = ""
    fecha_procesamiento: str = ""
    confianza: float = 0.0
    
    def to_dict(self):
        """Convierte el objeto a diccionario"""
        return {
            'rnc_emisor': self.rnc_emisor,
            'nombre_emisor': self.nombre_emisor,
            'comprobante': self.comprobante,
            'fecha_emision': self.fecha_emision,
            'subtotal': self.subtotal,
            'impuestos': self.impuestos,
            'descuentos': self.descuentos,
            'total': self.total,
            'archivo_origen': self.archivo_origen,
            'fecha_procesamiento': self.fecha_procesamiento or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'confianza': self.confianza
        }

@dataclass
class Proveedor:
    """Modelo de datos para proveedores"""
    id: Optional[int] = None
    rnc: str = ""
    nombre: str = ""
    frecuencia: int = 1
    ultima_vez: str = ""
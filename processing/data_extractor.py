# processing/data_extractor.py
import re
from typing import Dict, List, Optional
from processing.validator import ValidadorDatos

class ExtractorDatos:
    def __init__(self):
        self.validador = ValidadorDatos()
        self.patrones = self._construir_patrones()
    
    def _construir_patrones(self) -> Dict[str, List[Dict]]:
        return {
            'nit': [
                {
                    'patron': r'(NIT|Nit|nit)[\s:]*([0-9.,-]+)',
                    'grupo': 2,
                    'palabras_contexto': ['NIT', 'Nit', 'nit', 'identificación']
                },
                {
                    'patron': r'(\d{5,15})',
                    'grupo': 1,
                    'palabras_contexto': ['NIT', 'Nit', 'IDENTIF'],
                    'validar_contexto': True
                }
            ],
            'fecha': [
                {
                    'patron': r'(Fecha|FECHA|fecha)[\s:]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                    'grupo': 2
                },
                {
                    'patron': r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                    'grupo': 1,
                    'palabras_contexto': ['Fecha', 'Emisión', 'Factura']
                }
            ],
            'total': [
                {
                    'patron': r'(Total|TOTAL|total)[\s:]*[\$]?\s*([0-9.,]+)',
                    'grupo': 2
                },
                {
                    'patron': r'(Gran Total|TOTAL GENERAL)[\s:]*[\$]?\s*([0-9.,]+)',
                    'grupo': 2
                }
            ],
            'subtotal': [
                {
                    'patron': r'(Subtotal|SUBOTAL|subtotal)[\s:]*[\$]?\s*([0-9.,]+)',
                    'grupo': 2
                }
            ],
            'numero_factura': [
                {
                    'patron': r'(No\.?|Número|NUMERO)[\s:]*([0-9-]+)',
                    'grupo': 2
                },
                {
                    'patron': r'(Factura|FACTURA)[\s:]*([0-9-]+)',
                    'grupo': 2
                }
            ]
        }
    
    def extraer_datos(self, texto: str) -> Dict[str, Any]:
        datos_extraidos = {}
        
        for campo, patrones in self.patrones.items():
            for config_patron in patrones:
                valor = self._extraer_con_patron(texto, config_patron)
                if valor:
                    valor_validado = self._validar_campo(campo, valor)
                    if valor_validado:
                        datos_extraidos[campo] = valor_validado
                        break
        
        return datos_extraidos
    
    def _extraer_con_patron(self, texto: str, config_patron: Dict) -> Optional[str]:
        coincidencias = re.finditer(config_patron['patron'], texto, re.IGNORECASE | re.MULTILINE)
        
        for coincidencia in coincidencias:
            valor = coincidencia.group(config_patron['grupo'])
            
            if config_patron.get('validar_contexto'):
                if not self._tiene_contexto_valido(texto, coincidencia.start(), config_patron.get('palabras_contexto', [])):
                    continue
            
            return valor
            
        return None
    
    def _tiene_contexto_valido(self, texto: str, posicion: int, palabras_contexto: List[str]) -> bool:
        inicio = max(0, posicion - 100)
        fin = min(len(texto), posicion + 100)
        area_contexto = texto[inicio:fin]
        
        return any(palabra.lower() in area_contexto.lower() for palabra in palabras_contexto)
    
    def _validar_campo(self, campo: str, valor: str) -> Any:
        validadores = {
            'nit': self.validador.validar_y_corregir_nit,
            'fecha': self.validador.validar_y_corregir_fecha,
            'total': self.validador.validar_y_corregir_monto,
            'subtotal': self.validador.validar_y_corregir_monto,
            'numero_factura': lambda x: x.strip() if x.strip() else None
        }
        
        validador = validadores.get(campo)
        return validador(valor) if validador else valor
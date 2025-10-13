# processing/confidence_analyzer.py
from typing import Dict, Any

class AnalizadorConfianza:
    @staticmethod
    def calcular_confianza(datos_extraidos: Dict[str, Any], texto: str) -> Dict[str, Any]:
        puntajes_confianza = {}
        
        for campo, valor in datos_extraidos.items():
            if valor is None:
                puntajes_confianza[campo] = {'puntaje': 0, 'estado': 'faltante'}
                continue
                
            puntaje = 0
            puntaje += 20
            
            if campo in ['nit', 'fecha', 'total']:
                puntaje += 30
            
            if AnalizadorConfianza._tiene_contexto_apropiado(campo, texto):
                puntaje += 30
                
            if AnalizadorConfianza._tiene_posicion_esperada(campo, texto, valor):
                puntaje += 20
                
            puntajes_confianza[campo] = {
                'puntaje': min(puntaje, 100),
                'estado': AnalizadorConfianza._obtener_estado(puntaje)
            }
        
        return puntajes_confianza
    
    @staticmethod
    def _tiene_contexto_apropiado(campo: str, texto: str) -> bool:
        mapa_contexto = {
            'nit': ['NIT', 'IDENTIF', 'IDENTIFICACIÓN'],
            'fecha': ['FECHA', 'EMISIÓN', 'FACTURA'],
            'total': ['TOTAL', 'PAGAR', 'IMPORTE'],
            'numero_factura': ['FACTURA', 'NO.', 'NÚMERO']
        }
        
        palabras_contexto = mapa_contexto.get(campo, [])
        return any(palabra.lower() in texto.lower() for palabra in palabras_contexto)
    
    @staticmethod
    def _tiene_posicion_esperada(campo: str, texto: str, valor: str) -> bool:
        posicion = texto.find(str(valor))
        if posicion == -1:
            return False
            
        posicion_normalizada = (posicion / len(texto)) * 100
        
        posiciones_esperadas = {
            'nit': (0, 40),
            'fecha': (0, 50),
            'numero_factura': (0, 40),
            'total': (60, 100)
        }
        
        min_pos, max_pos = posiciones_esperadas.get(campo, (0, 100))
        return min_pos <= posicion_normalizada <= max_pos
    
    @staticmethod
    def _obtener_estado(puntaje: int) -> str:
        if puntaje >= 80:
            return 'alto'
        elif puntaje >= 60:
            return 'medio'
        elif puntaje >= 40:
            return 'bajo'
        else:
            return 'muy_bajo'
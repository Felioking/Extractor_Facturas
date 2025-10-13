# debug_ui_fields.py
"""
Script para diagnosticar qué campos espera la UI
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from processing.data_extractor import DataExtractor

def test_ui_fields():
    """Prueba qué campos se muestran en la UI"""
    print("🧪 INICIANDO PRUEBA DE CAMPOS UI")
    print("=" * 50)
    
    # Texto de ejemplo de factura de peaje
    texto_ejemplo = """Fideicomiso RD Vial
RNC: 131092659
Operador: Vianca Rondón Polanco
Estacion de Peaje Guaraguao

Ticket Nro: 1701-000001
Vehiculo: LIVIANO
Sentido: ASCENDENTE
Fecha/Hora:08/10/2025 10:13:59
Importe: RD$ : 200.00

Para Asist.Vial MOPC llamar a:
Tel 511

No olvide usar el cinturon de seguridad"""
    
    extractor = DataExtractor()
    resultado = extractor.extraer_datos(texto_ejemplo)
    
    print("\n" + "=" * 50)
    print("📊 RESUMEN FINAL:")
    print(f"Total de campos extraídos: {len(resultado)}")
    print("Campos disponibles para UI:")
    
    for campo, valor in resultado.items():
        if not campo.startswith('confianza_') and campo not in ['calidad_texto', 'estado_calidad', 'metodo_extraccion']:
            print(f"   📌 {campo}: {valor}")
    
    print("\n💡 Si la UI no muestra todos los campos, revisa:")
    print("   1. Los nombres de campos en ui/gui.py")
    print("   2. El mapeo de datos en la interfaz")
    print("   3. Los widgets específicos para cada campo")

if __name__ == "__main__":
    test_ui_fields()
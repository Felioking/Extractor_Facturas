# ml/training_manager.py
import os
import json
from typing import List, Tuple, Dict, Any
from datetime import datetime

class TrainingManager:
    def __init__(self, data_path: str = "ml/training_data"):
        self.data_path = data_path
        os.makedirs(self.data_path, exist_ok=True)
    
    def save_training_example(self, text: str, invoice_type: str, extracted_data: Dict[str, Any]):
        """Guarda un ejemplo para entrenamiento futuro"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"training_{timestamp}.json"
        filepath = os.path.join(self.data_path, filename)
        
        example = {
            'timestamp': timestamp,
            'invoice_type': invoice_type,
            'text_sample': text[:1000] + "..." if len(text) > 1000 else text,
            'extracted_data': extracted_data,
            'text_length': len(text),
            'fields_found': list(extracted_data.keys())
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(example, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Ejemplo guardado: {filename}")
    
    def load_training_data(self) -> List[Tuple[str, str]]:
        """Carga datos de entrenamiento existentes"""
        training_data = []
        
        for filename in os.listdir(self.data_path):
            if filename.endswith('.json'):
                filepath = os.path.join(self.data_path, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    training_data.append((data['text_sample'], data['invoice_type']))
                    
                except Exception as e:
                    print(f"⚠️  Error cargando {filename}: {e}")
        
        print(f"📚 Cargados {len(training_data)} ejemplos de entrenamiento")
        return training_data
    
    def generate_synthetic_data(self) -> List[Tuple[str, str]]:
        """Genera datos sintéticos para entrenamiento inicial"""
        synthetic_data = []
        
        # Ejemplos de facturas dominicanas
        dominican_examples = [
            """COMPROBANTE FISCAL
RNC: 123456789
NCF: B0123456789
Fecha: 15/01/2024
Subtotal: 1,000.00
ITBIS: 180.00
Total: 1,180.00 RD$""",
            
            """FACTURA
Registro Nacional: 987654321
NCF: E0123456789
Fecha Emisión: 20/02/2024
Total ITBIS: 150.00
Total a Pagar: 1,150.00 RD$"""
        ]
        
        # Ejemplos de facturas internacionales
        international_examples = [
            """INVOICE #001
NIT: 800123456
DATE: 2024-03-10
SUBOTAL: 500.00
IVA: 95.00
TOTAL: 595.00 USD""",
            
            """FACTURA COMERCIAL
IDENTIFICACIÓN: 900987654
FECHA: 10/03/2024
IMPUESTO: 120.00
TOTAL: 1,620.00 $"""
        ]
        
        # Ejemplos de facturas de peaje
        peaje_examples = [
            """Fideicomiso RD Vial
RNC: 131092659
Operador: Vianca Rondón Polanco
Estacion de Peaje Guaraguao

Ticket Nro: 1701-000001
Vehiculo: LIVIANO
Sentido: ASCENDENTE
Fecha/Hora:08/10/2025 10:13:59
Importe: RD$ : 200.00""",
            
            """Ticket de Peaje
RNC: 112233445
Estacion: Peaje Duarte

Ticket: 2024-001234
Vehiculo: PESADO
Fecha: 15/03/2024 14:30:00
Importe: 350.00 RD$"""
        ]
        
        for example in dominican_examples:
            synthetic_data.append((example, 'dominican'))
        
        for example in international_examples:
            synthetic_data.append((example, 'international'))
            
        for example in peaje_examples:
            synthetic_data.append((example, 'peaje'))
        
        return synthetic_data
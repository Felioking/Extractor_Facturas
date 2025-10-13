# processing/data_extractor.py
import re
from typing import Dict, List, Optional, Any
from processing.validator import ValidadorDatos
from processing.confidence_analyzer import AnalizadorConfianza
from ml.invoice_classifier import InvoiceClassifier
from ml.field_extractor_ml import MLFieldExtractor
from ml.training_manager import TrainingManager

class DataExtractor:
    def __init__(self):
        self.validador = ValidadorDatos()
        self.analizador_confianza = AnalizadorConfianza()
        self.classifier = InvoiceClassifier()
        self.ml_extractor = MLFieldExtractor()
        self.training_manager = TrainingManager()
        self.patrones = self._construir_patrones()
        
        # Cargar modelo ML si existe
        self.classifier.load_model()
        
        # Entrenar con datos sintéticos si no hay modelo
        if not self.classifier.classifier:
            self._train_with_synthetic_data()
    
    def _train_with_synthetic_data(self):
        """Entrena con datos sintéticos si no hay modelo real"""
        synthetic_data = self.training_manager.generate_synthetic_data()
        self.classifier.train(synthetic_data)
        print("🤖 Modelo entrenado con datos sintéticos")
    
    def extraer_datos(self, texto: str) -> Dict[str, Any]:
        """Extrae datos usando enfoque híbrido (Regex + ML)"""
        print("🔍 Iniciando extracción híbrida...")
        
        # Análisis de calidad del texto
        quality_analysis = self.ml_extractor.analyze_text_quality(texto)
        print(f"📊 Calidad texto: {quality_analysis['calidad']} ({quality_analysis['puntuacion_calidad']}/10)")
        
        # Paso 1: Clasificar tipo de factura
        invoice_type, confidence = self.classifier.get_prediction_confidence(texto)
        print(f"📋 Tipo de factura: {invoice_type} (confianza: {confidence:.2f})")
        
        # Paso 2: Extracción con Regex (método tradicional)
        datos_regex = self._extraer_con_regex(texto, invoice_type)
        print(f"🔄 Regex extrajo {len(datos_regex)} campos")
        
        # Paso 3: Extracción con ML
        datos_ml = self.ml_extractor.extract_with_ml(texto, invoice_type)
        
        # Paso 4: Combinar resultados inteligentemente
        datos_combinados = self._combinar_resultados(datos_regex, datos_ml, texto, invoice_type)
        
        # Paso 5: Validar y calcular confianza
        datos_validados = self._validar_datos(datos_combinados)
        resultado_final = self._agregar_metadatos(datos_validados, texto, invoice_type, confidence, quality_analysis)
        
        # Guardar para entrenamiento futuro
        self.training_manager.save_training_example(texto, invoice_type, datos_validados)
        
        print(f"✅ Extracción completada. Campos encontrados: {len(datos_validados)} campos")
        return resultado_final
    
    def _construir_patrones(self) -> Dict[str, List[Dict]]:
        """Construye patrones de extracción por campo"""
        return {
            'rnc': [
                {'patron': r'RNC[:\s]*(\d{9,11})', 'grupo': 1, 'contexto': ['RNC']},
                {'patron': r'Registro Nacional[:\s]*(\d{9,11})', 'grupo': 1, 'contexto': ['Registro Nacional']},
                {'patron': r'RNC\s*(\d{9,11})', 'grupo': 1, 'contexto': ['RNC']}
            ],
            'fecha': [
                {'patron': r'Fecha/Hora[:\s]*(\d{1,2}/\d{1,2}/\d{4})', 'grupo': 1, 'contexto': ['Fecha/Hora']},
                {'patron': r'Fecha[:\s]*(\d{1,2}/\d{1,2}/\d{4})', 'grupo': 1, 'contexto': ['Fecha']},
                {'patron': r'(\d{1,2}/\d{1,2}/\d{4})', 'grupo': 1, 'contexto': ['Fecha']}
            ],
            'total': [
                {'patron': r'Importe[:\s]*RD\$[:\s]*([0-9.,]+)', 'grupo': 1, 'contexto': ['Importe']},
                {'patron': r'Total[:\s]*RD\$[:\s]*([0-9.,]+)', 'grupo': 1, 'contexto': ['Total']},
                {'patron': r'Importe[:\s]*([0-9.,]+)', 'grupo': 1, 'contexto': ['Importe']},
                {'patron': r'RD\$[:\s]*([0-9.,]+)', 'grupo': 1, 'contexto': ['RD$']}
            ],
            'numero_factura': [
                {'patron': r'Ticket Nro[:\s]*([0-9-]+)', 'grupo': 1, 'contexto': ['Ticket Nro']},
                {'patron': r'Factura[:\s]*([0-9-]+)', 'grupo': 1, 'contexto': ['Factura']},
                {'patron': r'Nro[:\s]*([0-9-]+)', 'grupo': 1, 'contexto': ['Nro']}
            ],
            'razon_social': [
                {'patron': r'^(.*?)\nRNC', 'grupo': 1, 'contexto': ['RNC']},
                {'patron': r'Operador[:\s]*([^\n]+)', 'grupo': 1, 'contexto': ['Operador']},
                {'patron': r'Fideicomiso[^\n]+', 'grupo': 0, 'contexto': ['Fideicomiso']}
            ],
            'vehiculo': [
                {'patron': r'Vehiculo[:\s]*([^\n]+)', 'grupo': 1, 'contexto': ['Vehiculo']}
            ],
            'estacion': [
                {'patron': r'Estacion[^\n]+', 'grupo': 0, 'contexto': ['Estacion']}
            ],
            'hora': [
                {'patron': r'(\d{1,2}:\d{2}:\d{2})', 'grupo': 1, 'contexto': ['Hora']},
                {'patron': r'Fecha/Hora[:\s]*\d{1,2}/\d{1,2}/\d{4}\s*(\d{1,2}:\d{2}:\d{2})', 'grupo': 1, 'contexto': ['Fecha/Hora']}
            ]
        }
    
    def _extraer_con_regex(self, texto: str, invoice_type: str) -> Dict[str, Any]:
        """Extracción tradicional con regex mejorada"""
        datos = {}
        
        for campo, patrones in self.patrones.items():
            for config_patron in patrones:
                valor = self._extraer_con_patron(texto, config_patron)
                if valor:
                    if config_patron['grupo'] == 0:
                        valor = self._limpiar_valor_especial(valor, campo)
                    
                    datos[campo] = valor
                    print(f"   ✅ Regex encontró {campo}: {valor}")
                    break
        
        return datos
    
    def _limpiar_valor_especial(self, valor: str, campo: str) -> str:
        """Limpia valores especiales para patrones con grupo 0"""
        if campo == 'razon_social':
            return valor.split('\n')[0].strip()
        elif campo == 'estacion':
            return valor.replace('Estacion de ', '').strip()
        return valor.strip()
    
    def _extraer_con_patron(self, texto: str, config_patron: Dict) -> Optional[str]:
        """Extrae valor usando un patrón específico"""
        try:
            matches = re.finditer(config_patron['patron'], texto, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                if config_patron['grupo'] == 0:
                    valor = match.group(0)
                else:
                    valor = match.group(config_patron['grupo'])
                
                if config_patron.get('contexto'):
                    if not self._tiene_contexto_valido(texto, match.start(), config_patron['contexto']):
                        continue
                
                if valor and valor.strip():
                    return valor.strip()
                    
        except Exception as e:
            print(f"❌ Error en patrón {config_patron['patron']}: {e}")
            
        return None
    
    def _tiene_contexto_valido(self, texto: str, posicion: int, palabras_contexto: List[str]) -> bool:
        """Verifica si hay palabras de contexto cerca"""
        contexto_radio = 100
        inicio = max(0, posicion - contexto_radio)
        fin = min(len(texto), posicion + contexto_radio)
        area_contexto = texto[inicio:fin].lower()
        
        return any(contexto.lower() in area_contexto for contexto in palabras_contexto)
    
    def _combinar_resultados(self, datos_regex: Dict, datos_ml: Dict, texto: str, invoice_type: str) -> Dict[str, Any]:
        """Combina resultados de regex y ML inteligentemente"""
        resultados = datos_regex.copy()
        
        campos_ml_preferidos = ['total', 'subtotal', 'itbis', 'fecha', 'fecha_emision', 'fecha_vencimiento']
        campos_regex_preferidos = ['rnc', 'nit', 'ncf', 'numero_factura', 'vehiculo', 'estacion']
        
        for campo, valor_ml in datos_ml.items():
            campo_normalizado = self._normalizar_nombre_campo(campo)
            
            if campo_normalizado in campos_ml_preferidos:
                if campo_normalizado not in resultados or self._es_mejor_valor(valor_ml, resultados[campo_normalizado], texto, campo_normalizado):
                    resultados[campo_normalizado] = valor_ml
                    print(f"   🤖 ML mejoró {campo_normalizado}: {valor_ml}")
            
            elif campo_normalizado not in resultados:
                resultados[campo_normalizado] = valor_ml
        
        return resultados
    
    def _normalizar_nombre_campo(self, campo: str) -> str:
        """Normaliza nombres de campos de diferentes fuentes"""
        mapeo = {
            'fecha_detectada': 'fecha',
            'monto_detectado': 'total',
            'empresa_detectada': 'razon_social',
            'numero_documento': 'rnc'
        }
        return mapeo.get(campo, campo)
    
    def _es_mejor_valor(self, valor_ml: str, valor_regex: str, texto: str, campo: str) -> bool:
        """Determina qué valor es mejor"""
        if campo in ['razon_social']:
            return len(str(valor_ml)) > len(str(valor_regex))
        
        if campo in ['total', 'subtotal', 'itbis']:
            return self._tiene_mejor_formato_monto(valor_ml)
        
        return False
    
    def _tiene_mejor_formato_monto(self, valor: str) -> bool:
        """Verifica si el valor tiene buen formato de monto"""
        return bool(re.match(r'^\d+[.,]\d{2}$', str(valor)))
    
    def _validar_datos(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica validación a todos los datos"""
        datos_validados = {}
        
        for campo, valor in datos.items():
            valor_validado = self._validar_campo(campo, valor)
            if valor_validado is not None and str(valor_validado).strip():
                datos_validados[campo] = valor_validado
                print(f"   ✅ Campo {campo} validado: {valor_validado}")
            else:
                print(f"   ⚠️  Campo {campo} descartado: {valor}")
        
        print(f"📊 Total de campos válidos: {len(datos_validados)}")
        return datos_validados
    
    def _validar_campo(self, campo: str, valor: str) -> Any:
        """Aplica validación específica por campo"""
        validadores = {
            'nit': self.validador.validar_y_corregir_nit,
            'rnc': self.validador.validar_y_corregir_nit,
            'fecha': self.validador.validar_y_corregir_fecha,
            'total': self.validador.validar_y_corregir_monto,
            'subtotal': self.validador.validar_y_corregir_monto,
            'itbis': self.validador.validar_y_corregir_monto,
            'ncf': lambda x: x.strip() if x.strip() else None,
            'fecha_emision': self.validador.validar_y_corregir_fecha,
            'fecha_vencimiento': self.validador.validar_y_corregir_fecha,
            'razon_social': lambda x: x.strip() if x.strip() and len(x.strip()) > 2 else None,
            'vehiculo': lambda x: x.strip() if x.strip() else None,
            'estacion': lambda x: x.strip() if x.strip() else None,
            'numero_factura': lambda x: x.strip() if x.strip() else None,
            'hora': lambda x: x.strip() if x.strip() else None,
            'operador': lambda x: x.strip() if x.strip() else None,
            'empresa_detectada': lambda x: x.strip() if x.strip() else None,
            'monto_detectado': self.validador.validar_y_corregir_monto,
            'fecha_detectada': self.validador.validar_y_corregir_fecha,
            'numero_documento': self.validador.validar_y_corregir_nit
        }
        
        validador = validadores.get(campo)
        return validador(valor) if validador else valor
    
    def _agregar_metadatos(self, datos: Dict[str, Any], texto: str, invoice_type: str, 
                          confidence: float, quality_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Agrega metadatos de calidad - ENVÍA TODOS LOS CAMPOS POSIBLES"""
        
        # Crear una copia con TODOS los nombres posibles
        resultado_completo = {}
        
        # 🔥 ENVIAR TODAS LAS VARIANTES POSIBLES
        variantes = {
            # NIT/RNC
            'nit': datos.get('rnc') or datos.get('nit'),
            'numero_documento': datos.get('rnc') or datos.get('nit'),
            'identificacion': datos.get('rnc') or datos.get('nit'),
            'documento': datos.get('rnc') or datos.get('nit'),
            'rnc': datos.get('rnc'),
            
            # Fechas
            'fecha': datos.get('fecha'),
            'fecha_emision': datos.get('fecha'),
            'fecha_documento': datos.get('fecha'),
            
            # Montos
            'total': datos.get('total'),
            'monto_total': datos.get('total'),
            'importe': datos.get('total'),
            'monto': datos.get('total'),
            'valor': datos.get('total'),
            
            # Numeración
            'numero_factura': datos.get('numero_factura'),
            'numero_comprobante': datos.get('numero_factura'),
            'ticket': datos.get('numero_factura'),
            'numero': datos.get('numero_factura'),
            
            # Empresa
            'razon_social': datos.get('razon_social'),
            'nombre_empresa': datos.get('razon_social'),
            'empresa': datos.get('razon_social'),
            'cliente': datos.get('razon_social'),
            'operador': datos.get('razon_social'),
            
            # Campos peaje
            'vehiculo': datos.get('vehiculo'),
            'tipo_vehiculo': datos.get('vehiculo'),
            'estacion': datos.get('estacion'),
            'lugar': datos.get('estacion'),
            'hora': datos.get('hora'),
            'hora_emision': datos.get('hora')
        }
        
        # Agregar solo campos con valor
        for campo, valor in variantes.items():
            if valor is not None:
                resultado_completo[campo] = valor
                print(f"   🔥 Enviando: {campo} = {valor}")
        
        # Agregar metadatos
        resultado_completo.update({
            'tipo_factura': invoice_type,
            'confianza_clasificacion': round(confidence, 2),
            'calidad_texto': quality_analysis['calidad'],
            'total_campos_encontrados': len([v for v in variantes.values() if v is not None]),
            'metodo_extraccion': 'HIBRIDO_ML'
        })
        
        print(f"🎯 ENVIANDO {len(resultado_completo)} CAMPOS A LA UI")
        print("🔍 ESTRUCTURA COMPLETA:")
        for key, value in resultado_completo.items():
            print(f"   🏷️  {key}: {value}")
        
        return resultado_completo
    
    def extract_data_from_text(self, texto: str, use_advanced: bool = False) -> Dict[str, Any]:
        """
        Método de compatibilidad - extrae datos del texto
        Args:
            texto: Texto a procesar
            use_advanced: Parámetro adicional para compatibilidad
        """
        return self.extraer_datos(texto)
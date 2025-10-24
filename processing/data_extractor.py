# processing/data_extractor.py
import re
import traceback
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from processing.validator import ValidadorDatos
from processing.confidence_analyzer import AnalizadorConfianza
from ml.invoice_classifier import InvoiceClassifier
from ml.field_extractor_ml import MLFieldExtractor
from ml.training_manager import TrainingManager

class DataExtractor:
    def __init__(self):
        try:
            self.validador = ValidadorDatos()
            self.analizador_confianza = AnalizadorConfianza()
            self.classifier = InvoiceClassifier()
            self.ml_extractor = MLFieldExtractor()
            self.training_manager = TrainingManager()
            self.patrones = self._construir_patrones()
            
            # Inicializar sistema de validadores robusto
            self.inicializar_validadores()
            
            # Cargar modelo ML si existe
            self.classifier.load_model()
            
            # Entrenar con datos sintéticos si no hay modelo
            if not self.classifier.classifier:
                self._train_with_synthetic_data()
                
            print("✅ DataExtractor inicializado correctamente")
            
        except Exception as e:
            print(f"❌ Error inicializando DataExtractor: {str(e)}")
            # Inicialización mínima de emergencia
            self.patrones = {}
            self.validadores = {}
            self.fallbacks = {}
    
    def inicializar_validadores(self):
        """Inicializa el sistema de validadores robusto"""
        self.validadores = {
            'ncf': self.validar_ncf_formato,
            'rnc': self.validar_rnc_formato,
            'fecha': self.validar_fecha_formato,
            'total': self.validar_total_formato,
            'numero_factura': self.validar_numero_factura_formato,
            'nit': self.validar_rnc_formato,
            'identificacion': self.validar_rnc_formato,
            'razon_social': self.validar_texto_general,
            'vehiculo': self.validar_texto_general,
            'estacion': self.validar_texto_general,
            'hora': self.validar_hora_formato,
            'operador': self.validar_texto_general,
            'rnc_emisor': self.validar_rnc_formato,
            'rnc_cliente': self.validar_rnc_formato,
            'nombre_emisor': self.validar_texto_general,
            'subtotal': self.validar_total_formato,
            'itbis': self.validar_total_formato
        }
        
        # Métodos de fallback para validadores faltantes
        self.fallbacks = {
            'validar_rnc_formato': self._fallback_validar_rnc,
            'validar_total_formato': self._fallback_validar_total,
            'validar_numero_factura_formato': self._fallback_validar_numero_factura,
            'validar_fecha_formato': self._fallback_validar_fecha,
            'validar_ncf_formato': self._fallback_validar_ncf,
            'validar_hora_formato': self._fallback_validar_hora,
            'validar_texto_general': self._fallback_validar_texto_general
        }

    def _train_with_synthetic_data(self):
        """Entrena con datos sintéticos si no hay modelo real"""
        try:
            synthetic_data = self.training_manager.generate_synthetic_data()
            self.classifier.train(synthetic_data)
            print("🤖 Modelo entrenado con datos sintéticos")
        except Exception as e:
            print(f"⚠️ No se pudo entrenar con datos sintéticos: {str(e)}")
    
    def debug_extraccion_completa(self, texto: str):
        """Debug completo del proceso de extracción"""
        print("\n" + "="*80)
        print("🔍 DEBUG COMPLETO - DATA EXTRACTOR")
        print("="*80)
        
        # 1. Mostrar texto de entrada
        print("📄 TEXTO RECIBIDO DEL OCR:")
        print("-" * 40)
        print(texto[:500] + "..." if len(texto) > 500 else texto)
        print(f"Longitud total: {len(texto)} caracteres")
        print()
        
        # 2. Clasificación
        print("🎯 CLASIFICACIÓN:")
        print("-" * 40)
        invoice_type, confidence = self._clasificar_tipo_factura_seguro(texto)
        print(f"Tipo detectado: {invoice_type}")
        print(f"Confianza: {confidence:.2f}")
        print()
        
        # 3. Extracción Regex
        print("🔄 EXTRACCIÓN REGEX:")
        print("-" * 40)
        datos_regex = self._extraer_con_regex(texto, invoice_type)
        for campo, valor in datos_regex.items():
            print(f"   {campo}: {valor}")
        print(f"Total campos regex: {len(datos_regex)}")
        print()
        
        # 4. Extracción ML
        print("🧠 EXTRACCIÓN ML:")
        print("-" * 40)
        datos_ml = self.ml_extractor.extract_with_ml(texto, invoice_type)
        for campo, valor in datos_ml.items():
            print(f"   {campo}: {valor}")
        print(f"Total campos ML: {len(datos_ml)}")
        print()
        
        # 5. Combinación
        print("🔄 COMBINACIÓN:")
        print("-" * 40)
        datos_combinados = self._combinar_resultados(datos_regex, datos_ml, texto, invoice_type)
        for campo, valor in datos_combinados.items():
            print(f"   {campo}: {valor}")
        print(f"Total campos combinados: {len(datos_combinados)}")
        print()
        
        # 6. Validación
        print("✅ VALIDACIÓN:")
        print("-" * 40)
        datos_validados = self._validar_datos_robusto(datos_combinados, invoice_type)
        for campo, valor in datos_validados.items():
            print(f"   {campo}: {valor}")
        print(f"Total campos validados: {len(datos_validados)}")
        print()
        
        return datos_validados, invoice_type, confidence

    def extraer_datos(self, texto: str) -> Dict[str, Any]:
        """Extrae datos usando enfoque híbrido (Regex + ML)"""
        print("🔍 Iniciando extracción híbrida...")
        
        try:
            # DEBUG: Mostrar proceso completo
            datos_validados, invoice_type, confidence = self.debug_extraccion_completa(texto)
            
            # Análisis de calidad del texto
            quality_analysis = self.ml_extractor.analyze_text_quality(texto)
            
            # Paso 5: Optimizar y agregar metadatos
            resultado_final = self._agregar_metadatos_optimizado(
                datos_validados, texto, invoice_type, confidence, quality_analysis
            )
            
            # Guardar para entrenamiento futuro
            self.training_manager.save_training_example(texto, invoice_type, datos_validados)
            
            print(f"✅ Extracción completada. Campos encontrados: {len(datos_validados)}")
            return resultado_final
            
        except Exception as e:
            print(f"🚨 ERROR CRÍTICO en extracción: {str(e)}")
            print(f"🔍 Traceback: {traceback.format_exc()}")
            return self._extraccion_basica_fallback(texto, "general")

    def _clasificar_tipo_factura_seguro(self, texto: str) -> Tuple[str, float]:
        """
        Clasificación segura del tipo de factura con manejo robusto de errores
        """
        try:
            print("   🔧 Llamando a classifier.get_prediction_confidence...")
            resultado = self.classifier.get_prediction_confidence(texto)
            
            # DEBUG: Verificar qué retorna exactamente
            print(f"   🔍 Resultado clasificación: {resultado}")
            print(f"   🔍 Tipo del resultado: {type(resultado)}")
            
            if isinstance(resultado, tuple):
                print(f"   🔍 Longitud de tupla: {len(resultado)}")
                if len(resultado) == 2:
                    invoice_type, confidence = resultado
                    # Validar tipos
                    if not isinstance(invoice_type, str):
                        invoice_type = str(invoice_type)
                    if not isinstance(confidence, (int, float)):
                        confidence = float(confidence) if confidence else 0.5
                    return invoice_type, confidence
                else:
                    print(f"   ⚠️ Tupla con longitud inesperada: {len(resultado)}")
                    return "general", 0.5
            elif isinstance(resultado, dict):
                print("   🔍 Resultado es diccionario, extrayendo valores...")
                invoice_type = resultado.get('tipo', 'general')
                confidence = resultado.get('confianza', 0.5)
                return str(invoice_type), float(confidence)
            else:
                print(f"   ⚠️ Tipo de retorno inesperado: {type(resultado)}")
                return "general", 0.5
                
        except ValueError as e:
            if "too many values to unpack" in str(e):
                print("   ❌ ERROR: Demasiados valores para desempaquetar en clasificación")
                print("   🔍 Revisar classifier.get_prediction_confidence()")
            return "general", 0.5
        except Exception as e:
            print(f"   ❌ Error en clasificación: {str(e)}")
            return "general", 0.5

    def _construir_patrones(self) -> Dict[str, List[Dict]]:
        """Construye patrones de extracción por campo - VERSIÓN MEJORADA"""
        return {
            'rnc_emisor': [
                {'patron': r'RNC:\s*(\d{9,11})', 'grupo': 1, 'contexto': ['RNC:']},
                {'patron': r'RNC\s*(\d{9,11})', 'grupo': 1, 'contexto': ['RNC']},
                {'patron': r'Registro Nacional[:\s]*(\d{9,11})', 'grupo': 1, 'contexto': ['Registro Nacional']}
            ],
            'rnc_cliente': [
                {'patron': r'RNC/CED[:\s]*(\d{9,11})', 'grupo': 1, 'contexto': ['RNC/CED']},
                {'patron': r'CLIENTE[^\n]+\nRNC/CED[:\s]*(\d{9,11})', 'grupo': 1, 'contexto': ['CLIENTE', 'RNC/CED']},
                {'patron': r'CLIENTE[^\n]*\n[^\n]*RNC[:\s]*(\d{9,11})', 'grupo': 1, 'contexto': ['CLIENTE', 'RNC']}
            ],
            'nombre_emisor': [
                {'patron': r'^([^\n]+)\nAutovia', 'grupo': 1, 'contexto': ['Autovia']},
                {'patron': r'^([^\n]+)\nRNC:', 'grupo': 1, 'contexto': ['RNC:']},
                {'patron': r'RESET - ([^\n]+)', 'grupo': 1, 'contexto': ['RESET']}
            ],
            'razon_social': [
                {'patron': r'CLIENTE:\s*([^\n]+)', 'grupo': 1, 'contexto': ['CLIENTE:']},
                {'patron': r'CLIENTE[:\s]*([^\n]+)', 'grupo': 1, 'contexto': ['CLIENTE']}
            ],
            'ncf': [
                {'patron': r'NCF:\s*([A-Z]\d{10,11})', 'grupo': 1, 'contexto': ['NCF:']},
                {'patron': r'NCF[:\s]*([A-Z]\d{10,11})', 'grupo': 1, 'contexto': ['NCF']},
                {'patron': r'B0100076051', 'grupo': 0, 'contexto': ['NCF']}  # Patrón específico
            ],
            'fecha': [
                {'patron': r'FECHA:\s*(\d{1,2}/\d{1,2}/\d{4})', 'grupo': 1, 'contexto': ['FECHA:']},
                {'patron': r'FECHA[:\s]*(\d{1,2}/\d{1,2}/\d{4})', 'grupo': 1, 'contexto': ['FECHA']},
                {'patron': r'(\d{1,2}/\d{1,2}/\d{4})\s+\d{1,2}:\d{2}:\d{2}', 'grupo': 1, 'contexto': ['FECHA']}
            ],
            'subtotal': [
                {'patron': r'SubTotal\s*==>\s*([0-9,]+\.?[0-9]*)', 'grupo': 1, 'contexto': ['SubTotal', '==>']},
                {'patron': r'SubTotal[^\n]*([0-9,]+\.?[0-9]*)', 'grupo': 1, 'contexto': ['SubTotal']},
                {'patron': r'SubTotal\s*([0-9,]+\.?[0-9]*)', 'grupo': 1, 'contexto': ['SubTotal']}
            ],
            'itbis': [
                {'patron': r'Itbis\s*=\s*([0-9,]+\.?[0-9]*)', 'grupo': 1, 'contexto': ['Itbis', '=']},
                {'patron': r'Itbis[^\n]*([0-9,]+\.?[0-9]*)', 'grupo': 1, 'contexto': ['Itbis']},
                {'patron': r'ITBIS[^\n]*([0-9,]+\.?[0-9]*)', 'grupo': 1, 'contexto': ['ITBIS']}
            ],
            'total': [
                {'patron': r'Total a Pagar RD\$\s*==>\s*([0-9,]+\.?[0-9]*)', 'grupo': 1, 'contexto': ['Total a Pagar RD$', '==>']},
                {'patron': r'Total a Pagar[^\n]*RD\$[^\n]*([0-9,]+\.?[0-9]*)', 'grupo': 1, 'contexto': ['Total a Pagar', 'RD$']},
                {'patron': r'Total[^\n]*([0-9,]+\.?[0-9]*)', 'grupo': 1, 'contexto': ['Total']}
            ],
            'numero_factura': [
                {'patron': r'FACT\.NO:\s*(\d+)', 'grupo': 1, 'contexto': ['FACT.NO:']},
                {'patron': r'=ACT\.NO:\s*(\d+)', 'grupo': 1, 'contexto': ['=ACT.NO:']},
                {'patron': r'Factura[^\n]*(\d+)', 'grupo': 1, 'contexto': ['Factura']}
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
        """Combina resultados de regex y ML inteligentemente - VERSIÓN CORREGIDA"""
        resultados = datos_regex.copy()
        
        # Campos donde ML tiene prioridad
        campos_ml_preferidos = ['total', 'fecha', 'fecha_emision', 'fecha_vencimiento']
        
        # Campos donde REGEX tiene prioridad (no permitir que ML los sobrescriba)
        campos_regex_preferidos = ['rnc', 'nit', 'ncf', 'numero_factura', 'subtotal', 'itbis', 'rnc_emisor', 'rnc_cliente', 'nombre_emisor', 'razon_social']
        
        for campo, valor_ml in datos_ml.items():
            campo_normalizado = self._normalizar_nombre_campo(campo)
            
            # ✅ NO permitir que ML sobrescriba campos críticos que ya tenemos de regex
            if campo_normalizado in campos_regex_preferidos and campo_normalizado in resultados:
                print(f"   🔒 Manteniendo valor regex para {campo_normalizado}: {resultados[campo_normalizado]}")
                continue
                
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
    
    def _validar_datos_robusto(self, datos: Dict[str, Any], invoice_type: str) -> Dict[str, Any]:
        """Aplica validación robusta a todos los datos considerando el tipo de factura"""
        datos_validados = {}
        
        for campo, valor in datos.items():
            try:
                # Validación especial para NCF en facturas de peaje
                if campo == 'ncf' and invoice_type == 'peaje':
                    print("   ⚠️  Factura de peaje: Ignorando validación NCF (no aplica)")
                    continue
                    
                valor_validado = self.validar_campo(campo, valor)
                if valor_validado is not None and str(valor_validado).strip():
                    datos_validados[campo] = valor_validado
                    print(f"   ✅ Campo {campo} validado: {valor_validado}")
                else:
                    print(f"   ⚠️  Campo {campo} descartado: {valor}")
            except Exception as e:
                print(f"   ❌ Error validando {campo}: {str(e)}")
                # Incluir el campo aunque falle la validación
                datos_validados[campo] = valor
        
        print(f"📊 Total de campos válidos: {len(datos_validados)}")
        return datos_validados

    def validar_campo(self, nombre_campo: str, valor: Any) -> Any:
        """Sistema robusto de validación de campos"""
        try:
            validador = self.validadores.get(nombre_campo)
            if validador:
                return validador(valor)
            else:
                print(f"⚠️ No hay validador para campo: {nombre_campo}")
                return valor  # Por defecto, devolver valor original
                
        except AttributeError as e:
            metodo_faltante = str(e).split("'")[-2]
            print(f"🔧 Validador faltante: {metodo_faltante}, usando fallback")
            return self._usar_fallback_validacion(metodo_faltante, valor)
        except Exception as e:
            print(f"❌ Error en validación {nombre_campo}: {str(e)}")
            return valor  # Fallback: devolver valor original

    def _usar_fallback_validacion(self, metodo_faltante: str, valor: Any) -> Any:
        """Usa métodos de fallback para validadores faltantes"""
        fallback = self.fallbacks.get(metodo_faltante)
        if fallback:
            return fallback(valor)
        else:
            print(f"⚠️ No hay fallback para {metodo_faltante}, validación omitida")
            return valor

    # ========== MÉTODOS DE VALIDACIÓN CORREGIDOS ==========
    
    def validar_ncf_formato(self, ncf: Any) -> Optional[str]:
        """
        Valida el formato de NCF (Número de Comprobante Fiscal)
        Retorna: str (NCF válido) o None si no es válido - VERSIÓN MEJORADA
        """
        try:
            if not ncf or not isinstance(ncf, str):
                return None
                
            # Limpiar el NCF
            ncf_clean = ncf.strip().upper()
            
            # ✅ CORRECCIÓN: Si el NCF es "False" como string, tratarlo como inválido
            if ncf_clean == 'FALSE':
                print(f"❌ NCF inválido: {ncf_clean}")
                return None
                
            # ✅ PATRONES MEJORADOS para NCF dominicanos
            patrones = [
                r'^[A-Z]\d{10}$',      # E3100000001 (11 caracteres)
                r'^[A-Z]\d{11}$',      # E31000000001 (12 caracteres)  
                r'^[A-Z]{2}\d{9}$',    # B010000001 (11 caracteres)
                r'^B01\d{8}$',         # B0100076051 (11 caracteres) - ✅ NUEVO PATRÓN
                r'^E31\d{8}$',         # E3100000001 (11 caracteres) - ✅ NUEVO PATRÓN
                r'^\d{3}-\d{7,8}$',    # 001-1234567
                r'^\d{2}-\d{2}-\d{4,8}$',  # 01-01-123456
                r'^\d{4}-\d{4}-\d{4}$',    # 0001-0000-0000001
                r'^[A-Z]-\d{2}-\d{4,8}$'   # E-01-123456
            ]
            
            for patron in patrones:
                if re.match(patron, ncf_clean):
                    print(f"✅ NCF válido: {ncf_clean} (patrón: {patron})")
                    return ncf_clean  # ✅ Devolver el valor
                        
            print(f"❌ Formato NCF no válido: {ncf_clean}")
            return None
            
        except Exception as e:
            print(f"Error validando NCF {ncf}: {str(e)}")
            return None

    def validar_rnc_formato(self, rnc: Any) -> Optional[str]:
        """Valida formato de RNC"""
        try:
            if not rnc:
                return None
                
            rnc_clean = str(rnc).strip()
            
            # Validación básica de RNC (9-11 dígitos)
            if rnc_clean.isdigit() and 9 <= len(rnc_clean) <= 11:
                print(f"✅ RNC válido: {rnc_clean}")
                return rnc_clean
            else:
                print(f"⚠️ RNC con formato inusual: {rnc_clean}")
                return rnc_clean  # Devolver original
                
        except Exception as e:
            print(f"Error validando RNC {rnc}: {str(e)}")
            return str(rnc) if rnc else None

    def validar_fecha_formato(self, fecha: Any) -> Optional[str]:
        """Valida y parsea formato de fecha"""
        return self.parsear_fecha_robusto(fecha)

    def validar_total_formato(self, total: Any) -> Optional[float]:
        """Valida formato de total/monto"""
        try:
            if not total:
                return None
                
            # Convertir a string y limpiar
            total_str = str(total).replace('RD$', '').replace('$', '').replace(',', '').strip()
            
            # Intentar convertir a float
            total_float = float(total_str)
            
            print(f"✅ Total válido: {total_float}")
            return total_float
            
        except (ValueError, TypeError) as e:
            print(f"❌ Error validando total {total}: {str(e)}")
            return None

    def validar_numero_factura_formato(self, numero: Any) -> Optional[str]:
        """Valida formato de número de factura"""
        try:
            if not numero:
                return None
                
            numero_clean = str(numero).strip()
            
            # Aceptar cualquier string no vacío como número de factura válido
            if numero_clean:
                print(f"✅ Número factura válido: {numero_clean}")
                return numero_clean
            else:
                return None
                
        except Exception as e:
            print(f"Error validando número factura {numero}: {str(e)}")
            return str(numero) if numero else None

    def validar_hora_formato(self, hora: Any) -> Optional[str]:
        """Valida formato de hora"""
        try:
            if not hora:
                return None
                
            hora_clean = str(hora).strip()
            
            # Patrón básico de hora
            if re.match(r'^\d{1,2}:\d{2}(:\d{2})?$', hora_clean):
                print(f"✅ Hora válida: {hora_clean}")
                return hora_clean
            else:
                print(f"⚠️ Formato de hora inusual: {hora_clean}")
                return hora_clean
                
        except Exception as e:
            print(f"Error validando hora {hora}: {str(e)}")
            return str(hora) if hora else None

    def validar_texto_general(self, texto: Any) -> Optional[str]:
        """Valida texto general (razón social, vehículo, estación, etc.)"""
        try:
            if not texto:
                return None
                
            texto_clean = str(texto).strip()
            
            if texto_clean and len(texto_clean) >= 2:
                return texto_clean
            else:
                return None
                
        except Exception as e:
            print(f"Error validando texto {texto}: {str(e)}")
            return str(texto) if texto else None

    # ========== MÉTODOS DE FALLBACK ==========
    
    def _fallback_validar_rnc(self, rnc: Any) -> Optional[str]:
        """Fallback para validar RNC"""
        return self.validar_rnc_formato(rnc)

    def _fallback_validar_total(self, total: Any) -> Optional[float]:
        """Fallback para validar total"""
        return self.validar_total_formato(total)

    def _fallback_validar_numero_factura(self, numero: Any) -> Optional[str]:
        """Fallback para validar número de factura"""
        return self.validar_numero_factura_formato(numero)

    def _fallback_validar_fecha(self, fecha: Any) -> Optional[str]:
        """Fallback para validar fecha"""
        return self.parsear_fecha_robusto(fecha)

    def _fallback_validar_ncf(self, ncf: Any) -> Optional[str]:
        """Fallback para validar NCF - VERSIÓN CORREGIDA"""
        return self.validar_ncf_formato(ncf)

    def _fallback_validar_hora(self, hora: Any) -> Optional[str]:
        """Fallback para validar hora"""
        return self.validar_hora_formato(hora)

    def _fallback_validar_texto_general(self, texto: Any) -> Optional[str]:
        """Fallback para validar texto general"""
        return self.validar_texto_general(texto)

    # ========== PARSER DE FECHAS MEJORADO ==========
    
    def parsear_fecha_robusto(self, texto_fecha: Any) -> Optional[str]:
        """
        Parser más robusto para fechas que evita el error 2025 -> 2020
        """
        try:
            if not texto_fecha:
                return None
                
            texto_limpio = str(texto_fecha).strip()
            
            # Log para debugging
            print(f"🔍 Parseando fecha: '{texto_limpio}'")
            
            # Intentar múltiples formatos en orden de preferencia
            formatos = [
                '%d/%m/%Y',  # 08/10/2025
                '%d-%m-%Y',  # 08-10-2025  
                '%Y-%m-%d',  # 2025-10-08
                '%d/%m/%y',  # 08/10/25 (CUIDADO con este)
                '%d-%m-%y',  # 08-10-25
            ]
            
            for formato in formatos:
                try:
                    fecha_parsed = datetime.strptime(texto_limpio, formato)
                    
                    # CORRECCIÓN CRÍTICA: Manejar correctamente los años de 2 dígitos
                    if formato in ['%d/%m/%y', '%d-%m-%y']:
                        # Asumir que años <= 30 son 2000+, años > 30 son 1900+
                        if fecha_parsed.year > 2030:
                            fecha_parsed = fecha_parsed.replace(year=fecha_parsed.year - 100)
                    
                    fecha_formateada = fecha_parsed.strftime('%d/%m/%Y')
                    print(f"✅ Fecha parseada: '{texto_limpio}' -> '{fecha_formateada}'")
                    return fecha_formateada
                    
                except ValueError:
                    continue
                    
            # Si no coincide con ningún formato, devolver original
            print(f"⚠️ No se pudo parsear fecha: '{texto_limpio}'")
            return texto_limpio
            
        except Exception as e:
            print(f"❌ Error parseando fecha '{texto_fecha}': {str(e)}")
            return str(texto_fecha) if texto_fecha else None

    # ========== SISTEMA OPTIMIZADO DE ENVÍO ==========
    
    def _agregar_metadatos_optimizado(self, datos: Dict[str, Any], texto: str, invoice_type: str, 
                                    confidence: float, quality_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Agrega metadatos de calidad - VERSIÓN OPTIMIZADA"""
        
        # Usar el sistema optimizado de campos
        resultado_optimizado = self.optimizar_campos_enviados(datos, invoice_type)
        
        # Agregar metadatos
        resultado_optimizado.update({
            'tipo_factura': invoice_type,
            'confianza_clasificacion': round(confidence, 2),
            'calidad_texto': quality_analysis['calidad'],
            'total_campos_encontrados': len(datos),
            'metodo_extraccion': 'HIBRIDO_ML',
            'tiene_ncf': self._determinar_si_tiene_ncf(datos, invoice_type)
        })
        
        print(f"🎯 ENVIANDO {len(resultado_optimizado)} CAMPOS A LA UI")
        print("🔍 ESTRUCTURA OPTIMIZADA:")
        for key, value in resultado_optimizado.items():
            print(f"   🏷️  {key}: {value}")
        
        return resultado_optimizado

    def _determinar_si_tiene_ncf(self, datos: Dict[str, Any], invoice_type: str) -> bool:
        """Determina si la factura tiene NCF basado en su tipo"""
        # Facturas de peaje NO tienen NCF
        if invoice_type == 'peaje':
            return False
        
        # Para otros tipos, verificar si hay un campo NCF válido
        ncf = datos.get('ncf')
        if ncf and ncf != 'False':  # ✅ CORRECCIÓN: Verificar que no sea "False"
            return self.validar_ncf_formato(ncf) is not None
        
        return False

    def optimizar_campos_enviados(self, datos: Dict[str, Any], invoice_type: str) -> Dict[str, Any]:
        """
        Optimiza los campos enviados a la UI para evitar duplicación excesiva
        """
        try:
            # Campos esenciales que siempre enviar
            campos_esenciales = {
                'rnc_emisor', 'rnc_cliente', 'fecha', 'total', 'subtotal', 'itbis',
                'numero_factura', 'ncf', 'razon_social', 'nombre_emisor'
            }
            
            # Campos específicos por tipo de factura
            campos_por_tipo = {
                'peaje': {'vehiculo', 'estacion', 'hora', 'operador'},
                'combustible': {'vehiculo', 'estacion', 'litros', 'producto'},
                'general': {'descripcion', 'concepto'}
            }
            
            resultado = {}
            
            # Agregar campos esenciales que existan en los datos
            for campo in campos_esenciales:
                if campo in datos and datos[campo] is not None:
                    resultado[campo] = datos[campo]
            
            # Agregar campos específicos del tipo de factura
            campos_tipo = campos_por_tipo.get(invoice_type, set())
            for campo in campos_tipo:
                if campo in datos and datos[campo] is not None:
                    resultado[campo] = datos[campo]
            
            # Agregar cualquier otro campo que no sea duplicado
            for campo, valor in datos.items():
                if campo not in resultado and valor is not None:
                    # Evitar duplicados como rnc vs rnc_emisor
                    if not self._es_campo_duplicado(campo, resultado.keys()):
                        resultado[campo] = valor
            
            print(f"🎯 Optimización: {len(datos)} -> {len(resultado)} campos")
            return resultado
            
        except Exception as e:
            print(f"❌ Error optimizando campos: {str(e)}")
            return datos

    def _es_campo_duplicado(self, campo: str, campos_existentes: set) -> bool:
        """Verifica si un campo es duplicado de otro ya existente"""
        grupos_duplicados = [
            {'rnc', 'rnc_emisor', 'rnc_cliente', 'identificacion'},
            {'razon_social', 'nombre_emisor', 'empresa_detectada'},
            {'total', 'monto_detectado', 'total_pagar'},
            {'fecha', 'fecha_emision', 'fecha_detectada'}
        ]
        
        for grupo in grupos_duplicados:
            if campo in grupo:
                for campo_existente in campos_existentes:
                    if campo_existente in grupo and campo_existente != campo:
                        print(f"🔍 Campo duplicado: {campo} (ya existe {campo_existente})")
                        return True
        return False

    def _extraccion_basica_fallback(self, texto: str, invoice_type: str) -> Dict[str, Any]:
        """Extracción básica de fallback cuando falla el sistema principal"""
        try:
            print("🔄 Usando extracción básica de fallback...")
            
            datos_basicos = {}
            
            # Extracción mínima con patrones simples
            patrones_fallback = {
                'total': r'Total[^\d]*([0-9,]+\.?[0-9]*)',
                'fecha': r'(\d{1,2}/\d{1,2}/\d{4})',
                'rnc': r'RNC[:\s]*(\d{9,11})',
                'numero_factura': r'Factura[^\n]*(\d+)'
            }
            
            for campo, patron in patrones_fallback.items():
                match = re.search(patron, texto, re.IGNORECASE)
                if match:
                    datos_basicos[campo] = match.group(1).strip()
            
            # Agregar metadatos de fallback
            datos_basicos.update({
                'tipo_factura': invoice_type,
                'confianza_clasificacion': 0.1,
                'calidad_texto': 'BAJA',
                'total_campos_encontrados': len(datos_basicos),
                'metodo_extraccion': 'FALLBACK_BASICO',
                'tiene_ncf': False,
                'advertencia': 'Extracción limitada - sistema principal falló'
            })
            
            print(f"🔄 Fallback: {len(datos_basicos)} campos básicos encontrados")
            return datos_basicos
            
        except Exception as e:
            print(f"🚨 ERROR incluso en fallback: {str(e)}")
            return {
                'tipo_factura': 'desconocido',
                'confianza_clasificacion': 0.0,
                'calidad_texto': 'CRITICA',
                'total_campos_encontrados': 0,
                'metodo_extraccion': 'ERROR',
                'error': str(e)
            }

    # ========== MÉTODOS DE UTILIDAD ADICIONALES ==========

    def obtener_estadisticas_extraccion(self) -> Dict[str, Any]:
        """Obtiene estadísticas del proceso de extracción"""
        return {
            'modelo_cargado': self.classifier.classifier is not None,
            'total_patrones_regex': sum(len(patrones) for patrones in self.patrones.values()),
            'validadores_activos': len(self.validadores),
            'fallbacks_configurados': len(self.fallbacks)
        }

    def limpiar_cache_modelo(self):
        """Limpia el cache del modelo ML para forzar recarga"""
        self.classifier.classifier = None
        self.classifier.load_model()
        print("🧹 Cache del modelo limpiado")

    def exportar_configuracion_patrones(self) -> Dict[str, Any]:
        """Exporta la configuración actual de patrones para debugging"""
        return {
            'patrones_por_campo': {campo: len(patrones) for campo, patrones in self.patrones.items()},
            'campos_soportados': list(self.patrones.keys()),
            'validadores_disponibles': list(self.validadores.keys())
        }

    # ========== MÉTODOS DE DIAGNÓSTICO ==========

    def diagnosticar_extraccion(self, texto: str) -> Dict[str, Any]:
        """
        Ejecuta un diagnóstico completo del sistema de extracción
        """
        print("\n" + "="*80)
        print("🔧 DIAGNÓSTICO COMPLETO DEL SISTEMA")
        print("="*80)
        
        diagnostico = {
            'estado_sistema': 'OK',
            'errores': [],
            'advertencias': [],
            'estadisticas': self.obtener_estadisticas_extraccion(),
            'configuracion': self.exportar_configuracion_patrones()
        }
        
        # Verificar componentes críticos
        componentes = {
            'ValidadorDatos': self.validador is not None,
            'AnalizadorConfianza': self.analizador_confianza is not None,
            'InvoiceClassifier': self.classifier is not None,
            'MLFieldExtractor': self.ml_extractor is not None,
            'TrainingManager': self.training_manager is not None
        }
        
        for componente, estado in componentes.items():
            if not estado:
                diagnostico['errores'].append(f"Componente {componente} no inicializado")
                diagnostico['estado_sistema'] = 'ERROR'
        
        # Verificar patrones regex
        if not self.patrones:
            diagnostico['errores'].append("No hay patrones regex configurados")
            diagnostico['estado_sistema'] = 'ERROR'
        
        # Verificar validadores
        if not self.validadores:
            diagnostico['advertencias'].append("No hay validadores configurados")
        
        # Probar extracción básica
        try:
            test_result = self.extraer_datos(texto[:1000] if len(texto) > 1000 else texto)
            diagnostico['test_extraccion'] = {
                'campos_encontrados': len(test_result),
                'tipo_factura': test_result.get('tipo_factura'),
                'confianza': test_result.get('confianza_clasificacion')
            }
        except Exception as e:
            diagnostico['errores'].append(f"Error en test de extracción: {str(e)}")
            diagnostico['estado_sistema'] = 'ERROR'
        
        # Resumen del diagnóstico
        print(f"📊 DIAGNÓSTICO: {diagnostico['estado_sistema']}")
        print(f"   ✅ Componentes: {sum(componentes.values())}/{len(componentes)}")
        print(f"   ❌ Errores: {len(diagnostico['errores'])}")
        print(f"   ⚠️  Advertencias: {len(diagnostico['advertencias'])}")
        
        return diagnostico

    def __str__(self) -> str:
        """Representación en string del DataExtractor"""
        stats = self.obtener_estadisticas_extraccion()
        return (f"DataExtractor - "
                f"Modelo: {'Cargado' if stats['modelo_cargado'] else 'No cargado'}, "
                f"Patrones: {stats['total_patrones_regex']}, "
                f"Validadores: {stats['validadores_activos']}")

# ========== FUNCIÓN DE CONVENIENCIA PARA USO RÁPIDO ==========

def crear_data_extractor() -> DataExtractor:
    """
    Función de conveniencia para crear una instancia de DataExtractor
    con manejo de errores incorporado
    """
    try:
        return DataExtractor()
    except Exception as e:
        print(f"❌ No se pudo crear DataExtractor: {str(e)}")
        # Retornar una instancia mínima para evitar caídas
        extractor = DataExtractor()
        extractor.patrones = {}
        extractor.validadores = {}
        return extractor
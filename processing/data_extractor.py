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
            'operador': self.validar_texto_general
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
        synthetic_data = self.training_manager.generate_synthetic_data()
        self.classifier.train(synthetic_data)
        print("🤖 Modelo entrenado con datos sintéticos")
    
    def extraer_datos(self, texto: str) -> Dict[str, Any]:
        """Extrae datos usando enfoque híbrido (Regex + ML)"""
        print("🔍 Iniciando extracción híbrida...")
        
        try:
            # Análisis de calidad del texto
            quality_analysis = self.ml_extractor.analyze_text_quality(texto)
            print(f"📊 Calidad texto: {quality_analysis['calidad']} ({quality_analysis['puntuacion_calidad']}/10)")
            
            # Paso 1: Clasificar tipo de factura - CON DEBUG DETALLADO
            print("🎯 Iniciando clasificación de tipo de factura...")
            invoice_type, confidence = self._clasificar_tipo_factura_seguro(texto)
            print(f"📋 Tipo de factura: {invoice_type} (confianza: {confidence:.2f})")
            
            # Paso 2: Extracción con Regex (método tradicional)
            datos_regex = self._extraer_con_regex(texto, invoice_type)
            print(f"🔄 Regex extrajo {len(datos_regex)} campos")
            
            # Paso 3: Extracción con ML
            datos_ml = self.ml_extractor.extract_with_ml(texto, invoice_type)
            print(f"🧠 ML extrajo {len(datos_ml)} campos")
            
            # Paso 4: Combinar resultados inteligentemente
            datos_combinados = self._combinar_resultados(datos_regex, datos_ml, texto, invoice_type)
            
            # Paso 5: Validar y calcular confianza
            datos_validados = self._validar_datos_robusto(datos_combinados, invoice_type)
            resultado_final = self._agregar_metadatos_optimizado(datos_validados, texto, invoice_type, confidence, quality_analysis)
            
            # Guardar para entrenamiento futuro
            self.training_manager.save_training_example(texto, invoice_type, datos_validados)
            
            print(f"✅ Extracción completada. Campos encontrados: {len(datos_validados)} campos")
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

    # ========== MÉTODOS DE VALIDACIÓN NUEVOS ==========
    
    def validar_ncf_formato(self, ncf: Any) -> bool:
        """
        Valida el formato de NCF (Número de Comprobante Fiscal)
        Retorna: bool (True si es válido, False si no)
        """
        try:
            if not ncf or not isinstance(ncf, str):
                return False
                
            # Limpiar el NCF
            ncf_clean = ncf.strip().upper()
            
            # ✅ CORRECCIÓN: Facturas de peaje NO tienen NCF, solo número de ticket
            # No tratamos tickets de peaje como NCF válidos
            
            # Patrones comunes de NCF en República Dominicana (para facturas fiscales)
            patrones = [
                r'^[A-Z]\d{11}$',  # E310000000001
                r'^[A-Z]{2}\d{9}$',  # B0100000001
                r'^\d{3}-\d{7,8}$',  # 001-1234567
                r'^\d{2}-\d{2}-\d{4,8}$',  # 01-01-123456
                r'^\d{4}-\d{4}-\d{4}$',  # 0001-0000-0000001
                r'^[A-Z]-\d{2}-\d{4,8}$'  # E-01-123456
            ]
            
            for patron in patrones:
                if re.match(patron, ncf_clean):
                    print(f"✅ NCF válido: {ncf_clean} (patrón: {patron})")
                    return True
                    
            print(f"❌ Formato NCF no válido: {ncf_clean}")
            return False  # No cumple con ningún patrón de NCF fiscal
            
        except Exception as e:
            print(f"Error validando NCF {ncf}: {str(e)}")
            return False

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

    def _fallback_validar_ncf(self, ncf: Any) -> bool:
        """Fallback para validar NCF"""
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
        ncf = datos.get('ncf') or datos.get('numero_factura')
        if ncf:
            return self.validar_ncf_formato(ncf)
        
        return False

    def optimizar_campos_enviados(self, datos: Dict[str, Any], invoice_type: str) -> Dict[str, Any]:
        """
        Optimiza los campos enviados a la UI para evitar duplicación excesiva
        """
        try:
            # Campos esenciales que siempre enviar
            campos_esenciales = {
                'rnc', 'fecha', 'total', 'numero_factura', 
                'razon_social', 'tipo_factura', 'confianza_clasificacion',
                'calidad_texto', 'total_campos_encontrados', 'metodo_extraccion',
                'tiene_ncf'
            }
            
            # Campos adicionales específicos por tipo de factura
            campos_por_tipo = {
                'peaje': {'vehiculo', 'estacion', 'hora', 'operador', 'ticket'},
                'supermercado': {'cajero', 'itbis', 'subtotal', 'ncf'},
                'restaurante': {'propina', 'mesa', 'servicio', 'ncf'},
                'combustible': {'litros', 'producto', 'estacion_servicio', 'ncf'},
                'general': {'nit', 'fecha_emision', 'monto_total', 'ncf'}
            }
            
            campos_tipo_especifico = campos_por_tipo.get(invoice_type, campos_por_tipo['general'])
            
            # Combinar todos los campos a enviar
            campos_a_enviar = campos_esenciales.union(campos_tipo_especifico)
            
            # Filtrar y mantener solo los campos necesarios
            datos_optimizados = {}
            for campo in campos_a_enviar:
                if campo in datos:
                    datos_optimizados[campo] = datos[campo]
            
            # Log de optimización
            original_count = len(datos)
            optimizado_count = len(datos_optimizados)
            print(f"📦 Optimización campos: {original_count} → {optimizado_count} (-{original_count - optimizado_count})")
            
            return datos_optimizados
            
        except Exception as e:
            print(f"❌ Error optimizando campos: {str(e)}")
            return datos  # Fallback a datos completos

    def extract_data_from_text(self, texto: str, use_advanced: bool = False) -> Dict[str, Any]:
        """
        Método de compatibilidad - extrae datos del texto
        Args:
            texto: Texto a procesar
            use_advanced: Parámetro adicional para compatibilidad
        """
        return self.extraer_datos(texto)

    # ========== MÉTODO DE EXTRACCIÓN ROBUSTO ==========
    
    def extraer_datos_avanzados(self, texto: str, tipo_factura: str, confianza: float) -> Dict[str, Any]:
        """Método robusto para extracción avanzada con manejo de errores"""
        try:
            # Análisis de calidad del texto
            quality_analysis = self.ml_extractor.analyze_text_quality(texto)
            
            # Extracción con Regex
            datos_regex = self._extraer_con_regex(texto, tipo_factura)
            
            # Extracción con ML
            datos_ml = self.ml_extractor.extract_with_ml(texto, tipo_factura)
            
            # Combinar resultados
            datos_combinados = self._combinar_resultados(datos_regex, datos_ml, texto, tipo_factura)
            
            # Validar datos
            datos_validados = self._validar_datos_robusto(datos_combinados, tipo_factura)
            
            # Optimizar y retornar
            return self._agregar_metadatos_optimizado(
                datos_validados, texto, tipo_factura, confianza, quality_analysis
            )
            
        except Exception as e:
            print(f"🚨 Error en extracción avanzada: {str(e)}")
            return self._extraccion_basica_fallback(texto, tipo_factura)

    def _extraccion_basica_fallback(self, texto: str, tipo_factura: str) -> Dict[str, Any]:
        """Extracción básica como fallback cuando falla la avanzada"""
        print("🔄 Usando extracción básica (fallback)")
        
        datos_basicos = {
            'texto_extraido': texto[:500] + "..." if len(texto) > 500 else texto,
            'tipo_factura': tipo_factura,
            'confianza_clasificacion': 0.5,
            'calidad_texto': 'MEDIA',
            'metodo_extraccion': 'FALLBACK_BASICO',
            'total_campos_encontrados': 0,
            'tiene_ncf': False
        }
        
        return datos_basicos
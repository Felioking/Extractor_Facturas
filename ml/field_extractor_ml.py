# ml/field_extractor_ml.py
import re
import spacy
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

class MLFieldExtractor:
    def __init__(self):
        self.nlp = None
        self._load_models()
    
    def _load_models(self):
        """Carga modelos de spaCy"""
        try:
            self.nlp = spacy.load("es_core_news_sm")
            print("✅ Modelo spaCy cargado exitosamente")
        except OSError as e:
            print(f"⚠️  Error cargando spaCy: {e}")
            print("💡 Intentando descargar modelo...")
            try:
                import subprocess
                import sys
                subprocess.check_call([sys.executable, "-m", "spacy", "download", "es_core_news_sm"])
                self.nlp = spacy.load("es_core_news_sm")
                print("✅ Modelo spaCy descargado y cargado")
            except Exception as e2:
                print(f"❌ No se pudo cargar spaCy: {e2}")
                self.nlp = None
    
    def extract_with_ml(self, text: str, invoice_type: str) -> Dict[str, Any]:
        """Extrae campos usando técnicas de ML/NLP"""
        print(f"🧠 Aplicando ML avanzado para tipo: {invoice_type}")
        
        if self.nlp is None:
            print("   ⚠️  spaCy no disponible, usando ML básico")
            return self._extract_with_advanced_heuristics(text, invoice_type)
        
        try:
            # Enfoque híbrido: NLP + reglas
            doc = self.nlp(text)
            results = {
                **self._extract_entities_spacy(doc),
                **self._extract_with_contextual_rules(doc, invoice_type),
                **self._extract_with_advanced_heuristics(text, invoice_type)
            }
            
            # Filtrar y limpiar resultados
            cleaned_results = {}
            for key, value in results.items():
                if value and str(value).strip():
                    cleaned_results[key] = value
            
            print(f"📊 ML avanzado extrajo {len(cleaned_results)} campos: {list(cleaned_results.keys())}")
            return cleaned_results
            
        except Exception as e:
            print(f"❌ Error en ML avanzado: {e}. Usando ML básico.")
            return self._extract_with_advanced_heuristics(text, invoice_type)
    
    def _extract_entities_spacy(self, doc) -> Dict[str, str]:
        """Extrae entidades usando spaCy"""
        entities = {}
        
        for ent in doc.ents:
            if ent.label_ == "MONEY" and len(ent.text) > 3:
                entities['monto_detectado'] = ent.text
                print(f"   💰 spaCy detectó monto: {ent.text}")
            elif ent.label_ == "DATE":
                if 'fecha' not in entities:
                    entities['fecha_detectada'] = ent.text
                    print(f"   📅 spaCy detectó fecha: {ent.text}")
            elif ent.label_ == "ORG" and len(ent.text) > 3:
                entities['empresa_detectada'] = ent.text
                print(f"   🏢 spaCy detectó empresa: {ent.text}")
            elif ent.label_ == "CARDINAL" and len(ent.text) > 5:
                # Podría ser un NIT/RNC
                if ent.text.replace('-', '').replace('.', '').isdigit():
                    entities['numero_documento'] = ent.text
                    print(f"   🔢 spaCy detectó documento: {ent.text}")
        
        return entities
    
    def _extract_with_contextual_rules(self, doc, invoice_type: str) -> Dict[str, str]:
        """Extrae campos usando reglas contextuales con spaCy"""
        results = {}
        text = doc.text
        
        # Análisis de dependencias para montos
        for token in doc:
            if token.like_num and token.text.replace(',', '').replace('.', '').isdigit():
                # Buscar hijos que puedan ser símbolos de moneda
                for child in token.children:
                    if child.text in ['RD$', '$', 'USD', '€']:
                        # Buscar cabeza que indique el tipo de monto
                        head_text = token.head.text.lower()
                        if 'total' in head_text:
                            results['total'] = token.text
                        elif 'subtotal' in head_text:
                            results['subtotal'] = token.text
                        elif 'itbis' in head_text or 'impuesto' in head_text:
                            results['itbis'] = token.text
        
        return results
    
    def _extract_with_advanced_heuristics(self, text: str, invoice_type: str) -> Dict[str, str]:
        """Heurísticas avanzadas para extracción (sin spaCy)"""
        results = {}
        lines = text.split('\n')
        text_lower = text.lower()
        
        print("   🔍 Aplicando heurísticas avanzadas...")
        
        # Análisis de líneas para encontrar patrones específicos
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            # Detectar RNC con contexto mejorado
            if 'rnc' in line.lower():
                rnc_candidates = re.findall(r'\d{9,11}', line_clean)
                if rnc_candidates:
                    results['rnc'] = rnc_candidates[0]
                    print(f"   🔍 RNC detectado: {rnc_candidates[0]}")
            
            # Detectar NCF con diferentes formatos
            if 'ncf' in line.lower():
                ncf_patterns = [
                    r'[A-E]\d{10,11}',  # Formato estándar
                    r'[A-Z]\d{2}-\d{2}-\d{4}-\d{2}'  # Formato con guiones
                ]
                for pattern in ncf_patterns:
                    ncf_match = re.search(pattern, line_clean)
                    if ncf_match:
                        results['ncf'] = ncf_match.group()
                        print(f"   📄 NCF detectado: {ncf_match.group()}")
                        break
            
            # Detectar montos con contexto mejorado
            amount_matches = re.finditer(r'(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})', line_clean)
            for match in amount_matches:
                amount = match.group(1)
                context = self._get_line_context(lines, i, window=3)
                
                if any(term in context.lower() for term in ['total', 'pagar', 'importe', 'final']):
                    if 'total' not in results or self._is_better_amount(amount, results.get('total')):
                        results['total'] = amount
                        print(f"   💰 Total detectado: {amount}")
                
                elif any(term in context.lower() for term in ['subtotal', 'gravado', 'base']):
                    if 'subtotal' not in results or self._is_better_amount(amount, results.get('subtotal')):
                        results['subtotal'] = amount
                        print(f"   📊 Subtotal detectado: {amount}")
                
                elif any(term in context.lower() for term in ['itbis', 'impuesto', 'iva', 'tax']):
                    if 'itbis' not in results or self._is_better_amount(amount, results.get('itbis')):
                        results['itbis'] = amount
                        print(f"   🏛️  ITBIS detectado: {amount}")
        
        # Búsqueda de fechas con contexto
        date_matches = re.finditer(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', text)
        for match in date_matches:
            date = match.group(1)
            context_start = max(0, match.start() - 50)
            context_end = min(len(text), match.end() + 30)
            context = text[context_start:context_end].lower()
            
            if 'vencim' in context and 'fecha_vencimiento' not in results:
                results['fecha_vencimiento'] = date
                print(f"   📅 Fecha vencimiento: {date}")
            elif 'emis' in context and 'fecha_emision' not in results:
                results['fecha_emision'] = date
                print(f"   📅 Fecha emisión: {date}")
            elif 'fecha' in context and 'fecha' not in results:
                results['fecha'] = date
                print(f"   📅 Fecha general: {date}")
        
        return results
    
    def _is_better_amount(self, new_amount: str, old_amount: str) -> bool:
        """Determina si un monto es mejor que otro"""
        if not old_amount:
            return True
        
        # Preferir montos más grandes (probablemente totales)
        try:
            new_val = float(new_amount.replace(',', ''))
            old_val = float(old_amount.replace(',', ''))
            return new_val > old_val
        except:
            return len(new_amount) > len(old_amount)
    
    def _get_line_context(self, lines: List[str], current_index: int, window: int = 2) -> str:
        """Obtiene contexto alrededor de una línea"""
        start = max(0, current_index - window)
        end = min(len(lines), current_index + window + 1)
        return ' '.join(lines[start:end])
    
    def analyze_text_quality(self, text: str) -> Dict[str, Any]:
        """Analiza la calidad del texto extraído por OCR"""
        analysis = {
            'total_caracteres': len(text),
            'total_lineas': len(text.split('\n')),
            'total_palabras': len(text.split()),
            'densidad_numeros': len(re.findall(r'\d', text)) / max(1, len(text)),
            'densidad_monetaria': len(re.findall(r'\d+[.,]\d{2}', text)) / max(1, len(text.split('\n'))),
            'tiene_fechas': len(re.findall(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', text)) > 0,
            'tiene_montos': len(re.findall(r'\d+[.,]\d{2}', text)) > 0,
            'tiene_identificadores': len(re.findall(r'(RNC|NCF|NIT|ID)', text, re.IGNORECASE)) > 0
        }
        
        # Calcular puntuación de calidad
        quality_score = (
            (1.0 if analysis['tiene_fechas'] else 0.0) +
            (1.0 if analysis['tiene_montos'] else 0.0) +
            (1.0 if analysis['tiene_identificadores'] else 0.0) +
            min(analysis['densidad_numeros'] * 10, 2.0) +
            min(analysis['densidad_monetaria'] * 20, 2.0)
        ) / 7.0 * 10.0
        
        analysis['puntuacion_calidad'] = round(quality_score, 2)
        analysis['calidad'] = 'ALTA' if quality_score >= 7 else 'MEDIA' if quality_score >= 4 else 'BAJA'
        
        return analysis
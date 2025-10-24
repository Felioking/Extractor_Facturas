import cv2
import logging
from typing import Tuple, List, Dict, Any
import os
import re
from paddleocr import PaddleOCR
import numpy as np

logger = logging.getLogger(__name__)

class ImageProcessor:
    def __init__(self):
        """Inicializa PaddleOCR con la versión correcta"""
        print("🔄 Inicializando PaddleOCR...")
        try:
            # Usar la misma configuración que en tu prueba funcional
            self.ocr = PaddleOCR(lang='es')
            print("✅ PaddleOCR inicializado correctamente")
        except Exception as e:
            print(f"❌ Error inicializando PaddleOCR: {e}")
            raise

    def preprocess_image(self, image_path: str, technique: str = 'direct') -> Tuple:
        """OCR usando la versión correcta de PaddleOCR"""
        print(f"🎯 [PADDLEOCR] Iniciando: {os.path.basename(image_path)}")
        
        try:
            # 1. Cargar imagen
            image = cv2.imread(image_path)
            if image is None:
                print("❌ No se pudo cargar imagen")
                return None, ""
            
            print(f"📏 Imagen: {image.shape}")
            
            # 2. OCR CON PADDLEOCR - Usando la versión correcta
            print("🔍 Ejecutando PaddleOCR...")
            
            # Usar el mismo método que en tu prueba funcional
            resultado = self.ocr.predict(image_path)
            
            texto = self._procesar_resultado_paddleocr(resultado)
            texto = texto.strip()
            
            print(f"✅ EXTRACCIÓN EXITOSA: {len(texto)} caracteres")
            
            # MOSTRAR DATOS ENCONTRADOS
            if texto:
                self._analizar_texto_detectado(texto)
            
            return image, texto
            
        except Exception as e:
            print(f"💥 ERROR en PaddleOCR: {e}")
            return None, ""

    def _procesar_resultado_paddleocr(self, resultado) -> str:
        """Procesa el resultado de PaddleOCR usando la estructura correcta"""
        try:
            if not resultado:
                return ""
            
            ocr_result = resultado[0]
            
            # Usar las claves correctas según tu prueba
            textos = ocr_result.get('rec_texts', [])
            confianzas = ocr_result.get('rec_scores', [])
            
            print(f"🔍 PaddleOCR encontró {len(textos)} elementos de texto")
            
            textos_filtrados = []
            
            for i, (texto, confianza) in enumerate(zip(textos, confianzas)):
                if texto and texto.strip() and confianza > 0.5:
                    textos_filtrados.append(texto.strip())
                    print(f"   📄 [{i+1}] '{texto}' (confianza: {confianza:.3f})")
            
            if textos_filtrados:
                # Unir todos los textos filtrados
                texto_completo = "\n".join(textos_filtrados)
                return texto_completo
            else:
                print("⚠️ No se encontró texto con suficiente confianza")
                # Devolver todo el texto encontrado (sin filtrar) como fallback
                texto_fallback = " ".join([t.strip() for t in textos if t and t.strip()])
                return texto_fallback
                
        except Exception as e:
            print(f"❌ Error procesando resultado PaddleOCR: {e}")
            return ""

    def _analizar_texto_detectado(self, texto: str):
        """Analiza el texto extraído para datos específicos"""
        print("📊 DATOS IDENTIFICADOS:")
        
        # Buscar RNC
        rnc_match = re.search(r'RNC[\s:]*([0-9-]+)', texto, re.IGNORECASE)
        if rnc_match:
            print(f"   ✅ RNC: {rnc_match.group(1)}")
        
        # Buscar NCF
        ncf_match = re.search(r'([A-Z]\d{13})', texto)
        if ncf_match:
            print(f"   ✅ NCF: {ncf_match.group(1)}")
        
        # Buscar Fecha
        fecha_match = re.search(r'(\d{1,2}/\d{1,2}/\d{2,4})', texto)
        if fecha_match:
            print(f"   ✅ FECHA: {fecha_match.group(1)}")
        
        # Buscar Total
        total_match = re.search(r'TOTAL[\s\$RD]*([0-9,]+\.?[0-9]*)', texto, re.IGNORECASE)
        if total_match:
            print(f"   ✅ TOTAL: {total_match.group(1)}")
        
        # Mostrar primeras líneas limpias
        lines = [line for line in texto.split('\n') if line.strip()]
        print("\n📄 TEXTO EXTRAÍDO (primeras 10 líneas):")
        for i, line in enumerate(lines[:10]):
            print(f"   {i+1:2d}. {line}")

    def extract_detailed_data(self, image_path: str) -> Dict[str, Any]:
        """Extrae datos detallados con información de confianza y posición"""
        try:
            resultado = self.ocr.predict(image_path)
            
            detailed_data = {
                'full_text': '',
                'text_blocks': [],
                'confidence_avg': 0.0
            }
            
            if resultado:
                ocr_result = resultado[0]
                textos = ocr_result.get('rec_texts', [])
                confianzas = ocr_result.get('rec_scores', [])
                
                confidences_list = []
                text_lines = []
                
                for i, (texto, confianza) in enumerate(zip(textos, confianzas)):
                    if texto and texto.strip() and confianza > 0.5:
                        confidences_list.append(confianza)
                        text_lines.append(texto)
                        
                        detailed_data['text_blocks'].append({
                            'text': texto,
                            'confidence': confianza,
                            'position': i
                        })
                
                if confidences_list:
                    detailed_data['confidence_avg'] = sum(confidences_list) / len(confidences_list)
                    detailed_data['full_text'] = '\n'.join(text_lines)
            
            return detailed_data
            
        except Exception as e:
            print(f"❌ Error en extracción detallada: {e}")
            return {}

# Instancia global
image_processor = ImageProcessor()
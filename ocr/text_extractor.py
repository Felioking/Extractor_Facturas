"""
Módulo de extracción de texto usando Tesseract OCR con logging
"""

import pytesseract
import cv2
import logging
from typing import Tuple, Dict, Any
from config import Config

# Logger específico para OCR
logger = logging.getLogger('ocr')

class TextExtractor:
    """Clase para extracción de texto usando OCR con logging completo"""
    
    @staticmethod
    def extract_text(image_path: str, preprocess: bool = True) -> Tuple[str, Dict[str, Any]]:
        """
        Extrae texto de una imagen usando OCR con logging detallado
        
        Args:
            image_path: Ruta a la imagen
            preprocess: Si aplicar preprocesamiento
            
        Returns:
            Tupla con (texto_extraido, metadatos)
        """
        logger.info(f"Iniciando extracción de texto de: {image_path}")
        logger.debug(f"Preprocesamiento: {preprocess}")
        
        try:
            # Cargar y preprocesar imagen
            if preprocess:
                from ocr.image_preprocessor import ImagePreprocessor
                logger.debug("Aplicando preprocesamiento avanzado")
                image = ImagePreprocessor.preprocess_image(image_path)
            else:
                logger.debug("Cargando imagen sin preprocesamiento")
                image = cv2.imread(image_path)
                if image is None:
                    raise ValueError("No se pudo cargar la imagen")
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Configuración de Tesseract
            custom_config = Config.OCR_CONFIG
            logger.debug(f"Configuración Tesseract: {custom_config}")
            
            # Intentar con español primero, luego inglés
            text = ""
            confidence = 0
            best_language = ""
            
            for lang in Config.OCR_LANGUAGES:
                try:
                    logger.debug(f"Probando OCR con idioma: {lang}")
                    
                    # Extraer texto
                    current_text = pytesseract.image_to_string(image, lang=lang, config=custom_config)
                    
                    # Extraer datos de confianza
                    data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT, config=custom_config)
                    current_confidence = TextExtractor._calculate_confidence(data)
                    
                    logger.debug(f"Idioma {lang}: {len(current_text)} caracteres, confianza: {current_confidence:.1f}%")
                    
                    # Seleccionar el mejor resultado
                    if current_confidence > confidence:
                        text = current_text
                        confidence = current_confidence
                        best_language = lang
                        
                except Exception as e:
                    logger.warning(f"OCR con idioma {lang} falló: {e}")
                    continue
            
            if not text.strip():
                logger.warning("No se pudo extraer texto de la imagen")
            else:
                logger.info(f"✓ Texto extraído exitosamente con idioma {best_language}")
                logger.info(f"  - Caracteres: {len(text)}")
                logger.info(f"  - Confianza: {confidence:.1f}%")
            
            # Metadatos
            metadata = {
                'confidence': confidence,
                'characters_extracted': len(text),
                'preprocessed': preprocess,
                'language_used': best_language
            }
            
            return text, metadata
            
        except Exception as e:
            logger.error(f"✗ Error extrayendo texto de {image_path}: {e}", exc_info=True)
            raise
    
    @staticmethod
    def _calculate_confidence(data: Dict[str, Any]) -> float:
        """Calcula la confianza promedio del OCR"""
        try:
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            if not confidences:
                return 0.0
            
            confidence_avg = sum(confiances) / len(confiances)
            return confidence_avg
            
        except Exception as e:
            logger.warning(f"Error calculando confianza OCR: {e}")
            return 0.0
    
    @staticmethod
    def extract_with_details(image_path: str) -> Dict[str, Any]:
        """
        Extrae texto con información detallada
        """
        logger.info(f"Extrayendo texto con detalles de: {image_path}")
        
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("No se pudo cargar la imagen")
            
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Extraer datos detallados
            data = pytesseract.image_to_data(
                image_rgb, 
                lang='spa', 
                output_type=pytesseract.Output.DICT,
                config=Config.OCR_CONFIG
            )
            
            # Filtrar por confianza
            filtered_text = ""
            high_confidence_words = 0
            
            for i, word in enumerate(data['text']):
                if int(data['conf'][i]) > 30 and word.strip():
                    filtered_text += word + " "
                    high_confidence_words += 1
            
            result = {
                'full_text': pytesseract.image_to_string(image_rgb, lang='spa'),
                'filtered_text': filtered_text.strip(),
                'detailed_data': data,
                'word_count': len([w for w in data['text'] if w.strip()]),
                'confidence_words': high_confidence_words
            }
            
            logger.info(f"✓ Extracción detallada completada:")
            logger.info(f"  - Palabras totales: {result['word_count']}")
            logger.info(f"  - Palabras alta confianza: {high_confidence_words}")
            
            return result
            
        except Exception as e:
            logger.error(f"✗ Error en extracción detallada: {e}", exc_info=True)
            return {}
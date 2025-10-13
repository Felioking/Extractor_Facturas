# ocr/image_preprocessor.py
import cv2
import numpy as np
import logging
from PIL import Image, ImageEnhance
import pytesseract
from typing import Tuple, List, Dict, Any
import os

logger = logging.getLogger(__name__)

class ImageProcessor:
    def __init__(self):
        self.tecnicas_aplicadas = []
        
    def preprocess_image(self, image_path: str, technique: str = 'auto') -> Tuple[np.ndarray, str]:
        """
        Preprocesa una imagen para mejorar la calidad del OCR
        """
        logger.info(f"Preprocesando imagen: {os.path.basename(image_path)}")
        
        try:
            # Cargar imagen
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"No se pudo cargar la imagen: {image_path}")
            
            if technique == 'auto':
                imagen_procesada, texto = self._preprocesamiento_automatico(image)
            else:
                imagen_procesada = self._aplicar_tecnica_especifica(image, technique)
                texto = self._ejecutar_ocr(imagen_procesada)
            
            logger.info(f"Preprocesamiento completado. Técnicas: {self.tecnicas_aplicadas}")
            return imagen_procesada, texto
            
        except Exception as e:
            logger.error(f"Error en preprocesamiento: {e}")
            # Fallback: devolver imagen original
            image = cv2.imread(image_path)
            texto = pytesseract.image_to_string(image, lang='spa')
            return image, texto
    
    def _preprocesamiento_automatico(self, image: np.ndarray) -> Tuple[np.ndarray, str]:
        """
        Aplica múltiples técnicas de preprocesamiento y selecciona la mejor
        """
        mejores_resultados = ""
        mejor_confianza = 0
        mejor_imagen = image
        mejor_tecnica = "original"
        
        # Definir técnicas a probar
        tecnicas = {
            'original': self._aplicar_original,
            'gaussian': self._aplicar_gaussian,
            'median': self._aplicar_median,
            'adaptive_threshold': self._aplicar_adaptive_threshold,
            'clahe': self._aplicar_clahe,
            'morphological': self._aplicar_morphological,
            'combined': self._aplicar_combinado
        }
        
        for nombre_tecnica, tecnica_func in tecnicas.items():
            try:
                logger.debug(f"Probando técnica: {nombre_tecnica}")
                
                # Aplicar técnica
                imagen_procesada = tecnica_func(image)
                
                # Ejecutar OCR y obtener confianza
                texto, confianza_promedio = self._ejecutar_ocr_con_confianza(imagen_procesada)
                
                logger.debug(f"Técnica {nombre_tecnica} - Confianza: {confianza_promedio:.2f}%")
                
                # Actualizar mejor resultado
                if confianza_promedio > mejor_confianza:
                    mejor_confianza = confianza_promedio
                    mejores_resultados = texto
                    mejor_imagen = imagen_procesada
                    mejor_tecnica = nombre_tecnica
                    
            except Exception as e:
                logger.warning(f"Error en técnica {nombre_tecnica}: {e}")
                continue
        
        self.tecnicas_aplicadas = [mejor_tecnica]
        logger.info(f"Mejor técnica: {mejor_tecnica} (Confianza: {mejor_confianza:.2f}%)")
        
        return mejor_imagen, mejores_resultados
    
    def _aplicar_tecnica_especifica(self, image: np.ndarray, technique: str) -> np.ndarray:
        """
        Aplica una técnica específica de preprocesamiento
        """
        tecnicas = {
            'original': self._aplicar_original,
            'gaussian': self._aplicar_gaussian,
            'median': self._aplicar_median,
            'adaptive_threshold': self._aplicar_adaptive_threshold,
            'clahe': self._aplicar_clahe,
            'morphological': self._aplicar_morphological,
            'combined': self._aplicar_combinado,
        }
        
        if technique in tecnicas:
            self.tecnicas_aplicadas = [technique]
            return tecnicas[technique](image)
        else:
            logger.warning(f"Técnica {technique} no encontrada. Usando original.")
            return self._aplicar_original(image)
    
    def _aplicar_original(self, image: np.ndarray) -> np.ndarray:
        """Imagen original en escala de grises"""
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    def _aplicar_gaussian(self, image: np.ndarray) -> np.ndarray:
        """Aplica desenfoque gaussiano"""
        gris = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.GaussianBlur(gris, (3, 3), 0)
    
    def _aplicar_median(self, image: np.ndarray) -> np.ndarray:
        """Aplica filtro mediano"""
        gris = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.medianBlur(gris, 3)
    
    def _aplicar_adaptive_threshold(self, image: np.ndarray) -> np.ndarray:
        """Aplica umbral adaptativo"""
        gris = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.adaptiveThreshold(
            gris, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
    
    def _aplicar_clahe(self, image: np.ndarray) -> np.ndarray:
        """Aplica CLAHE para mejorar contraste"""
        gris = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(gris)
    
    def _aplicar_morphological(self, image: np.ndarray) -> np.ndarray:
        """Aplica operaciones morfológicas"""
        gris = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Umbral adaptativo
        umbral = cv2.adaptiveThreshold(
            gris, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Operaciones morfológicas para limpiar ruido
        kernel = np.ones((1, 1), np.uint8)
        limpia = cv2.morphologyEx(umbral, cv2.MORPH_CLOSE, kernel)
        limpia = cv2.medianBlur(limpia, 3)
        
        return limpia
    
    def _aplicar_combinado(self, image: np.ndarray) -> np.ndarray:
        """Combina múltiples técnicas avanzadas"""
        gris = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Paso 1: Denoising
        denoised = cv2.fastNlMeansDenoising(gris)
        
        # Paso 2: CLAHE para contraste
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contrast_enhanced = clahe.apply(denoised)
        
        # Paso 3: Umbral adaptativo
        umbral = cv2.adaptiveThreshold(
            contrast_enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Paso 4: Operaciones morfológicas
        kernel = np.ones((1, 1), np.uint8)
        morphological = cv2.morphologyEx(umbral, cv2.MORPH_CLOSE, kernel)
        morphological = cv2.medianBlur(morphological, 3)
        
        return morphological
    
    def _ejecutar_ocr(self, image: np.ndarray) -> str:
        """Ejecuta OCR en la imagen procesada"""
        try:
            # Configuración de Tesseract para mejor precisión
            config = '--oem 3 --psm 6'
            
            texto = pytesseract.image_to_string(image, lang='spa', config=config)
            return texto.strip()
            
        except Exception as e:
            logger.error(f"Error en OCR: {e}")
            return ""
    
    def _ejecutar_ocr_con_confianza(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Ejecuta OCR y retorna texto junto con confianza promedio
        """
        try:
            config = '--oem 3 --psm 6'
            
            # Obtener datos detallados incluyendo confianza
            datos = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, lang='spa')
            
            # Calcular confianza promedio (excluyendo -1 que indica no texto)
            confianzas = [int(conf) for conf in datos['conf'] if int(conf) > 0]
            confianza_promedio = sum(confianzas) / len(confianzas) if confianzas else 0
            
            texto = " ".join([word for word, conf in zip(datos['text'], datos['conf']) 
                            if int(conf) > 0 and word.strip()])
            
            return texto, confianza_promedio
            
        except Exception as e:
            logger.error(f"Error en OCR con confianza: {e}")
            return "", 0
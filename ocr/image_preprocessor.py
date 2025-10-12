"""
Módulo de preprocesamiento de imágenes para mejorar OCR
"""

import cv2
import numpy as np
import logging
from typing import Tuple

class ImagePreprocessor:
    """Clase para preprocesamiento avanzado de imágenes"""
    
    @staticmethod
    def preprocess_image(image_path: str) -> np.ndarray:
        """
        Preprocesa una imagen para mejorar el reconocimiento OCR
        
        Args:
            image_path: Ruta a la imagen
            
        Returns:
            Imagen preprocesada
        """
        try:
            # Cargar imagen
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("No se pudo cargar la imagen")
            
            # Convertir a escala de grises
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Aplicar diferentes técnicas y seleccionar la mejor
            processed_image = ImagePreprocessor._apply_best_preprocessing(gray)
            
            logging.info("✓ Imagen preprocesada correctamente")
            return processed_image
            
        except Exception as e:
            logging.error(f"Error preprocesando imagen: {e}")
            raise
    
    @staticmethod
    def _apply_best_preprocessing(gray_image: np.ndarray) -> np.ndarray:
        """
        Aplica múltiples técnicas de preprocesamiento y selecciona la mejor
        """
        techniques = {
            'adaptive_threshold': ImagePreprocessor._adaptive_threshold,
            'contrast_enhancement': ImagePreprocessor._contrast_enhancement,
            'noise_reduction': ImagePreprocessor._noise_reduction,
            'combined': ImagePreprocessor._combined_processing
        }
        
        best_image = gray_image
        best_score = 0
        
        for name, technique in techniques.items():
            try:
                processed = technique(gray_image)
                score = ImagePreprocessor._evaluate_image_quality(processed)
                
                if score > best_score:
                    best_score = score
                    best_image = processed
                    
            except Exception as e:
                logging.warning(f"Técnica {name} falló: {e}")
                continue
        
        return best_image
    
    @staticmethod
    def _adaptive_threshold(image: np.ndarray) -> np.ndarray:
        """Aplica umbral adaptativo"""
        return cv2.adaptiveThreshold(
            image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
    
    @staticmethod
    def _contrast_enhancement(image: np.ndarray) -> np.ndarray:
        """Mejora el contraste"""
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(image)
    
    @staticmethod
    def _noise_reduction(image: np.ndarray) -> np.ndarray:
        """Reduce el ruido"""
        # Reducción de ruido con filtro mediano
        denoised = cv2.medianBlur(image, 3)
        
        # Operaciones morfológicas para limpiar la imagen
        kernel = np.ones((1, 1), np.uint8)
        cleaned = cv2.morphologyEx(denoised, cv2.MORPH_CLOSE, kernel)
        
        return cleaned
    
    @staticmethod
    def _combined_processing(image: np.ndarray) -> np.ndarray:
        """Combina múltiples técnicas de procesamiento"""
        # Mejorar contraste
        contrast_enhanced = ImagePreprocessor._contrast_enhancement(image)
        
        # Reducir ruido
        noise_reduced = ImagePreprocessor._noise_reduction(contrast_enhanced)
        
        # Aplicar umbral adaptativo
        thresholded = ImagePreprocessor._adaptive_threshold(noise_reduced)
        
        return thresholded
    
    @staticmethod
    def _evaluate_image_quality(image: np.ndarray) -> float:
        """
        Evalúa la calidad de la imagen procesada
        (métrica simple basada en varianza)
        """
        return float(np.var(image))
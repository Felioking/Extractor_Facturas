import cv2
import pytesseract
import logging
from typing import Tuple
import os

logger = logging.getLogger(__name__)

class ImageProcessor:
    def preprocess_image(self, image_path: str, technique: str = 'direct') -> Tuple:
        """OCR DIRECTO - SIN PREPROCESAMIENTO"""
        print(f"🎯 [OCR-DIRECTO] Iniciando: {os.path.basename(image_path)}")
        
        try:
            # 1. Cargar imagen
            image = cv2.imread(image_path)
            if image is None:
                print("❌ No se pudo cargar imagen")
                return None, ""
            
            print(f"📏 Imagen: {image.shape}")
            
            # 2. OCR DIRECTAMENTE SIN PROCESAMIENTO
            print("🔍 Ejecutando Tesseract...")
            
            # Método 1: Imagen original a color
            texto_color = pytesseract.image_to_string(image, lang='spa')
            
            # Método 2: Solo escala de grises
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            texto_gray = pytesseract.image_to_string(gray, lang='spa')
            
            # Elegir el mejor texto
            if len(texto_color) > len(texto_gray):
                texto = texto_color
                metodo = "COLOR"
            else:
                texto = texto_gray  
                metodo = "GRIS"
            
            texto = texto.strip()
            
            print(f"✅ EXTRACCIÓN EXITOSA ({metodo}): {len(texto)} caracteres")
            
            # MOSTRAR DATOS ENCONTRADOS
            if texto:
                print("📊 DATOS IDENTIFICADOS:")
                
                # Buscar RNC
                import re
                rnc_match = re.search(r'RNC[\s:]*([0-9-]+)', texto, re.IGNORECASE)
                if rnc_match:
                    print(f"   ✅ RNC: {rnc_match.group(1)}")
                
                # Buscar NCF
                ncf_match = re.search(r'([A-Z]\\d{13})', texto)
                if ncf_match:
                    print(f"   ✅ NCF: {ncf_match.group(1)}")
                
                # Buscar Fecha
                fecha_match = re.search(r'(\\d{1,2}/\\d{1,2}/\\d{2,4})', texto)
                if fecha_match:
                    print(f"   ✅ FECHA: {fecha_match.group(1)}")
                
                # Buscar Total
                total_match = re.search(r'TOTAL[\\s\\$RD]*([0-9,]+\\.?[0-9]*)', texto, re.IGNORECASE)
                if total_match:
                    print(f"   ✅ TOTAL: {total_match.group(1)}")
                
                # Mostrar primeras líneas limpias
                lines = [line for line in texto.split('\\n') if line.strip()]
                print("\\n📄 TEXTO EXTRAÍDO (primeras 10 líneas):")
                for i, line in enumerate(lines[:10]):
                    print(f"   {i+1:2d}. {line}")
            
            return image, texto
            
        except Exception as e:
            print(f"💥 ERROR: {e}")
            return None, ""

# Instancia global
image_processor = ImageProcessor()

# implement_smart_preprocessing.py
import os

print("🎯 IMPLEMENTANDO PREPROCESAMIENTO INTELIGENTE...")

smart_preprocessor_content = '''import cv2
import numpy as np
import pytesseract
import logging
from typing import Tuple
import os
import re

logger = logging.getLogger(__name__)

class SmartImageProcessor:
    def __init__(self):
        self.tecnicas_aplicadas = []
        self.quality_metrics = {}
        
    def preprocess_image(self, image_path: str, technique: str = 'auto') -> Tuple:
        """PREPROCESAMIENTO INTELIGENTE - SE ADAPTA A CADA FACTURA"""
        print(f"🎯 [SMART-OCR] Analizando: {os.path.basename(image_path)}")
        
        try:
            # 1. CARGAR IMAGEN
            image = cv2.imread(image_path)
            if image is None:
                print("❌ No se pudo cargar la imagen")
                return None, ""
            
            original_shape = image.shape
            print(f"📏 Dimensiones originales: {original_shape}")
            
            # 2. ANALIZAR TIPO DE IMAGEN
            image_analysis = self.analyze_image_characteristics(image)
            print(f"🔍 Análisis: {image_analysis['type']} | Brillo: {image_analysis['brightness']:.1f} | Contraste: {image_analysis['contrast']:.1f}")
            
            # 3. APLICAR ESTRATEGIA ESPECÍFICA
            if image_analysis['type'] == "documento_oscuro":
                processed, texto, method = self.process_dark_document(image)
            elif image_analysis['type'] == "documento_claro":
                processed, texto, method = self.process_light_document(image) 
            elif image_analysis['type'] == "foto_baja_calidad":
                processed, texto, method = self.process_low_quality_photo(image)
            elif image_analysis['needs_rotation']:
                processed, texto, method = self.process_rotated_document(image)
            else:
                processed, texto, method = self.process_standard_document(image)
            
            # 4. EVALUAR RESULTADOS Y MEJORAR SI ES NECESARIO
            if not texto or len(texto.strip()) < 50:
                print("🔄 Resultado pobre, intentando método alternativo...")
                processed, texto, method = self.fallback_processing(image)
            
            # 5. ANALIZAR CALIDAD DE EXTRACCIÓN
            quality_score = self.analyze_extraction_quality(texto)
            self.quality_metrics = {
                'score': quality_score,
                'method': method,
                'text_length': len(texto),
                'image_type': image_analysis['type']
            }
            
            print(f"📊 CALIDAD FINAL: {quality_score}/10 | Método: {method}")
            
            if quality_score >= 7:
                print("✅ EXTRACCIÓN EXCELENTE")
            elif quality_score >= 5:
                print("⚠️ EXTRACCIÓN ACEPTABLE") 
            else:
                print("❌ EXTRACCIÓN DEFICIENTE - Considerar nueva imagen")
            
            return processed, texto
            
        except Exception as e:
            print(f"💥 ERROR en procesamiento inteligente: {e}")
            import traceback
            traceback.print_exc()
            return None, ""
    
    def analyze_image_characteristics(self, image):
        """Analiza características de la imagen para decidir estrategia"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Métricas básicas
        brightness = np.mean(gray)
        contrast = np.std(gray)
        
        # Detectar si necesita rotación (basado en bordes)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        needs_rotation = False
        if lines is not None:
            angles = []
            for rho, theta in lines[:10]:
                angle = np.degrees(theta) - 90
                if abs(angle) > 5:  # Si hay ángulos significativos
                    angles.append(angle)
            
            if angles and np.std(angles) < 10:  # Si hay consistencia en ángulos
                needs_rotation = True
        
        # Clasificar tipo de imagen
        if brightness < 80:
            image_type = "documento_oscuro"
        elif brightness > 180:
            image_type = "documento_claro"
        elif contrast < 35:
            image_type = "foto_baja_calidad"
        else:
            image_type = "documento_estándar"
        
        return {
            'type': image_type,
            'brightness': brightness,
            'contrast': contrast,
            'needs_rotation': needs_rotation
        }
    
    def process_dark_document(self, image):
        """Procesa documentos oscuros o sombreados"""
        print("   🌙 Aplicando mejora para documento OSCURO...")
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 1. Mejorar brillo y contraste agresivamente
        alpha = 1.5  # Factor de contraste
        beta = 60    # Factor de brillo
        enhanced = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
        
        # 2. CLAHE para contraste local
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
        clahe_applied = clahe.apply(enhanced)
        
        # 3. Umbral adaptativo con parámetros optimizados
        thresh = cv2.adaptiveThreshold(clahe_applied, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY, 21, 10)
        
        # 4. Reducir ruido
        denoised = cv2.medianBlur(thresh, 3)
        
        texto = pytesseract.image_to_string(denoised, lang='spa', config='--oem 3 --psm 6')
        return denoised, texto.strip(), "dark_document_enhancement"
    
    def process_light_document(self, image):
        """Procesa documentos muy claros o sobreexpuestos"""
        print("   ☀️ Aplicando mejora para documento CLARO...")
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 1. Reducir brillo y aumentar contraste
        alpha = 1.3  # Aumentar contraste
        beta = -40   # Reducir brillo
        adjusted = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
        
        # 2. Umbral invertido para texto oscuro sobre fondo claro
        _, thresh = cv2.threshold(adjusted, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # 3. Operaciones morfológicas para limpiar
        kernel = np.ones((2,2), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        texto = pytesseract.image_to_string(cleaned, lang='spa', config='--oem 3 --psm 6')
        return cleaned, texto.strip(), "light_document_inversion"
    
    def process_low_quality_photo(self, image):
        """Procesa fotos de documentos con baja calidad"""
        print("   📷 Aplicando mejora para FOTO de baja calidad...")
        
        # 1. Reducir ruido preservando bordes
        denoised = cv2.fastNlMeansDenoisingColored(image, None, 15, 15, 7, 21)
        
        # 2. Mejorar contraste en espacio LAB
        lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l)
        lab_enhanced = cv2.merge([l_enhanced, a, b])
        contrast_enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
        
        # 3. Enfoque suave
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(contrast_enhanced, -1, kernel)
        
        # 4. Escala de grises final
        gray = cv2.cvtColor(sharpened, cv2.COLOR_BGR2GRAY)
        
        texto = pytesseract.image_to_string(gray, lang='spa', config='--oem 3 --psm 6')
        return gray, texto.strip(), "photo_enhancement"
    
    def process_rotated_document(self, image):
        """Procesa documentos que necesitan corrección de rotación"""
        print("   📐 Corrigiendo ROTACIÓN de documento...")
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detectar ángulo de rotación usando Hough Transform
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        if lines is not None:
            angles = []
            for rho, theta in lines[:20]:
                angle = np.degrees(theta) - 90
                if -45 < angle < 45:  # Filtrar ángulos razonables
                    angles.append(angle)
            
            if angles:
                median_angle = np.median(angles)
                print(f"   🔄 Rotación detectada: {median_angle:.1f}°")
                
                # Corregir rotación
                (h, w) = gray.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                rotated = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, 
                                       borderMode=cv2.BORDER_REPLICATE)
                
                texto = pytesseract.image_to_string(rotated, lang='spa', config='--oem 3 --psm 6')
                return rotated, texto.strip(), f"rotation_correction_{median_angle:.1f}deg"
        
        # Fallback si no se detecta rotación
        return self.process_standard_document(image)
    
    def process_standard_document(self, image):
        """Procesamiento para documentos estándar"""
        print("   📄 Procesamiento ESTÁNDAR...")
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Mejorar contraste local
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Umbral adaptativo
        thresh = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY, 11, 2)
        
        texto = pytesseract.image_to_string(thresh, lang='spa', config='--oem 3 --psm 6')
        return thresh, texto.strip(), "standard_processing"
    
    def fallback_processing(self, image):
        """Método de respaldo cuando los otros fallan"""
        print("   🆘 ACTIVANDO MODO RESPUESTA...")
        
        # Intentar OCR directo sin procesamiento
        texto_directo = pytesseract.image_to_string(image, lang='spa', config='--oem 3 --psm 6')
        
        if texto_directo.strip():
            return image, texto_directo.strip(), "direct_fallback"
        
        # Último intento con diferentes configuraciones PSM
        configs = [
            '--oem 3 --psm 4',  # Asume un único bloque de texto
            '--oem 3 --psm 8',  # Palabra única
            '--oem 3 --psm 13'  # Línea de texto cruda
        ]
        
        for config in configs:
            try:
                texto = pytesseract.image_to_string(image, lang='spa', config=config)
                if texto.strip():
                    return image, texto.strip(), f"psm_fallback_{config}"
            except:
                continue
        
        return image, "", "all_methods_failed"
    
    def analyze_extraction_quality(self, texto):
        """Analiza la calidad de la extracción con puntuación 0-10"""
        if not texto:
            return 0
        
        lines = [line for line in texto.split('\\\\n') if line.strip()]
        
        # Factores de calidad
        factors = {
            'line_count': min(len(lines) / 10, 2),  # Máximo 2 puntos
            'has_currency': 2 if any('RD$' in line or '$' in line for line in lines) else 0,
            'has_dates': 2 if any(re.search(r'\\\\d{1,2}/\\\\d{1,2}/\\\\d{2,4}', line) for line in lines) else 0,
            'has_numbers': 1 if any(re.search(r'\\\\d+', line) for line in lines) else 0,
            'has_rnc_pattern': 2 if re.search(r'RNC[\\\\s:]*[0-9-]+', texto, re.IGNORECASE) else 0,
            'has_total': 2 if re.search(r'TOTAL[\\\\s\\\\$RD]*[0-9,]', texto, re.IGNORECASE) else 0,
            'text_length': min(len(texto) / 200, 1)  # Máximo 1 punto
        }
        
        score = sum(factors.values())
        return min(score, 10)  # Máximo 10 puntos

# Instancia global del procesador inteligente
image_processor = SmartImageProcessor()
'''

# Aplicar el preprocesamiento inteligente
print("1. 🔧 Implementando SmartImageProcessor...")
with open('ocr/image_preprocessor.py', 'w', encoding='utf-8') as f:
    f.write(smart_preprocessor_content)

print("2. ✅ PREPROCESAMIENTO INTELIGENTE IMPLEMENTADO")
print("3. 🎯 El sistema ahora:")
print("   • Analiza automáticamente el tipo de imagen")
print("   • Aplica estrategias específicas para cada caso") 
print("   • Detecta y corrige rotación")
print("   • Evalúa la calidad de extracción")
print("   • Tiene métodos de respaldo automáticos")

print("4. 🚀 EJECUTA: python main.py")
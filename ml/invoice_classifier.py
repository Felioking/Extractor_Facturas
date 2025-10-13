# ml/invoice_classifier.py
import os
import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from typing import Dict, List, Optional, Tuple, Any
import re
import json

class InvoiceClassifier:
    def __init__(self, model_path: str = "ml/models"):
        self.model_path = model_path
        self.vectorizer = None
        self.classifier = None
        self.classes = []
        
        # Patrones comunes por tipo de factura
        self.invoice_patterns = {
            'dominican': ['RNC', 'NCF', 'ITBIS', 'RD$', 'COMPROBANTE FISCAL', 'DGII'],
            'international': ['NIT', 'IVA', 'USD', 'TAX', 'INVOICE', 'VAT'],
            'peaje': ['Ticket', 'Peaje', 'Vehiculo', 'Importe', 'Estacion', 'Vial'],
            'simple': ['Factura', 'Total', 'Fecha', 'Cliente', 'Producto'],
            'detailed': ['Subtotal', 'Descuento', 'Impuesto', 'Items', 'Cantidad', 'Precio']
        }
        
        os.makedirs(self.model_path, exist_ok=True)
    
    def extract_features(self, text: str) -> Dict[str, float]:
        """Extrae características del texto para clasificación"""
        features = {}
        text_lower = text.lower()
        
        # Características basadas en patrones
        for invoice_type, patterns in self.invoice_patterns.items():
            features[f'pattern_{invoice_type}'] = sum(
                1 for pattern in patterns if pattern.lower() in text_lower
            )
        
        # Características estructurales
        lines = text.split('\n')
        features['line_count'] = len(lines)
        features['word_count'] = len(text.split())
        features['has_dates'] = len(re.findall(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', text))
        features['has_amounts'] = len(re.findall(r'\$?\d+[.,]\d{2}', text))
        features['has_numbers'] = len(re.findall(r'\d+', text))
        features['has_currency_rd'] = int('rd$' in text_lower)
        features['has_currency_usd'] = int('usd' in text_lower or '$' in text)
        
        # Características específicas de facturas
        features['has_tax_terms'] = int(any(term in text_lower for term in ['itbis', 'iva', 'impuesto', 'tax']))
        features['has_invoice_terms'] = int(any(term in text_lower for term in ['factura', 'invoice', 'comprobante']))
        features['has_peaje_terms'] = int(any(term in text_lower for term in ['ticket', 'peaje', 'vehiculo', 'estacion', 'vial']))
        
        return features
    
    def train(self, training_data: List[Tuple[str, str]]):
        """Entrena el clasificador con datos etiquetados"""
        if not training_data:
            print("⚠️  No hay datos de entrenamiento. Usando clasificador por reglas.")
            return
        
        texts, labels = zip(*training_data)
        
        # Extraer características
        features_list = []
        for text in texts:
            features = self.extract_features(text)
            features_list.append(list(features.values()))
        
        # Entrenar modelo
        X = np.array(features_list)
        y = np.array(labels)
        
        self.classifier = RandomForestClassifier(
            n_estimators=100, 
            random_state=42,
            max_depth=10,
            min_samples_split=5
        )
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.classifier.fit(X_train, y_train)
        self.classes = self.classifier.classes_
        
        # Calcular precisión
        accuracy = self.classifier.score(X_test, y_test)
        print(f"✅ Modelo entrenado. Precisión: {accuracy:.2f}")
        
        # Guardar modelo
        model_data = {
            'classifier': self.classifier,
            'classes': self.classes,
            'features': list(self.extract_features(texts[0]).keys())
        }
        
        with open(os.path.join(self.model_path, 'invoice_classifier.pkl'), 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"✅ Modelo guardado en {self.model_path}")
    
    def predict(self, text: str) -> str:
        """Predice el tipo de factura"""
        # Si no hay modelo entrenado, usar reglas
        if self.classifier is None:
            return self._predict_by_rules(text)
        
        try:
            features = list(self.extract_features(text).values())
            prediction = self.classifier.predict([features])[0]
            confidence = np.max(self.classifier.predict_proba([features]))
            
            print(f"🔮 Predicción ML: {prediction} (confianza: {confidence:.2f})")
            
            if confidence > 0.6:
                return prediction
            else:
                return self._predict_by_rules(text)
                
        except Exception as e:
            print(f"⚠️  Error en predicción ML: {e}. Usando reglas.")
            return self._predict_by_rules(text)
    
    def _predict_by_rules(self, text: str) -> str:
        """Clasificación basada en reglas cuando no hay ML"""
        text_lower = text.lower()
        
        scores = {
            'dominican': 0,
            'international': 0,
            'peaje': 0,
            'simple': 0,
            'detailed': 0
        }
        
        # Puntuar por patrones
        for pattern_type, patterns in self.invoice_patterns.items():
            for pattern in patterns:
                if pattern.lower() in text_lower:
                    scores[pattern_type] += 1
        
        # Reglas específicas
        if 'rnc' in text_lower:
            scores['dominican'] += 2
        if 'ticket' in text_lower and 'peaje' in text_lower:
            scores['peaje'] += 3
        if 'vehiculo' in text_lower and 'importe' in text_lower:
            scores['peaje'] += 2
        if 'estacion' in text_lower:
            scores['peaje'] += 1
        if 'fideicomiso' in text_lower and 'vial' in text_lower:
            scores['peaje'] += 2
        if 'operador' in text_lower and 'peaje' in text_lower:
            scores['peaje'] += 1
        
        # Determinar el tipo con mayor puntuación
        predicted_type = max(scores.items(), key=lambda x: x[1])
        print(f"🔧 Predicción por reglas: {predicted_type[0]} (puntuación: {predicted_type[1]})")
        
        return predicted_type[0]
    
    def load_model(self):
        """Carga modelo pre-entrenado"""
        try:
            model_path = os.path.join(self.model_path, 'invoice_classifier.pkl')
            if os.path.exists(model_path):
                with open(model_path, 'rb') as f:
                    model_data = pickle.load(f)
                
                self.classifier = model_data['classifier']
                self.classes = model_data['classes']
                print("✅ Modelo ML cargado exitosamente")
                return True
                
        except Exception as e:
            print(f"⚠️  Error cargando modelo: {e}")
        
        print("ℹ️  No se encontró modelo ML. Usando clasificador por reglas.")
        return False
    
    def get_prediction_confidence(self, text: str) -> Tuple[str, float]:
        """Obtiene predicción y confianza"""
        if self.classifier is None:
            return self._predict_by_rules(text), 0.8
        
        try:
            features = list(self.extract_features(text).values())
            prediction = self.classifier.predict([features])[0]
            confidence = np.max(self.classifier.predict_proba([features]))
            return prediction, confidence
        except:
            return self._predict_by_rules(text), 0.7
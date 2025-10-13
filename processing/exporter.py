# processing/exporter.py
import json
import pandas as pd
import logging
from typing import List, Dict, Any
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class Exporter:
    def __init__(self):
        pass
    
    def exportar_a_json(self, datos: Dict[str, Any], ruta_salida: str) -> bool:
        """
        Exporta datos a archivo JSON
        """
        try:
            datos_exportar = {
                'fecha_exportacion': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'datos_factura': datos
            }
            
            with open(ruta_salida, 'w', encoding='utf-8') as f:
                json.dump(datos_exportar, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Datos exportados a JSON: {ruta_salida}")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando a JSON: {e}")
            return False
    
    def exportar_a_excel(self, facturas: List[Dict[str, Any]], ruta_salida: str) -> bool:
        """
        Exporta múltiples facturas a archivo Excel
        """
        try:
            if not facturas:
                logger.warning("No hay datos para exportar a Excel")
                return False
            
            # Crear DataFrame
            df = pd.DataFrame(facturas)
            
            # Seleccionar columnas relevantes
            columnas_exportar = [
                'rnc_emisor', 'nombre_emisor', 'comprobante', 'fecha_emision',
                'subtotal', 'impuestos', 'descuentos', 'total', 'fecha_procesamiento'
            ]
            
            # Filtrar columnas existentes
            columnas_existentes = [col for col in columnas_exportar if col in df.columns]
            df_export = df[columnas_existentes].copy()
            
            # Renombrar columnas
            nombres_spanish = {
                'rnc_emisor': 'RNC Emisor',
                'nombre_emisor': 'Nombre Emisor',
                'comprobante': 'Comprobante',
                'fecha_emision': 'Fecha Emisión',
                'subtotal': 'Subtotal',
                'impuestos': 'Impuestos',
                'descuentos': 'Descuentos',
                'total': 'Total',
                'fecha_procesamiento': 'Fecha Procesamiento'
            }
            df_export.rename(columns=nombres_spanish, inplace=True)
            
            with pd.ExcelWriter(ruta_salida, engine='openpyxl') as writer:
                # Hoja de facturas
                df_export.to_excel(writer, sheet_name='Facturas', index=False)
                
                # Hoja de resumen
                resumen = self._crear_resumen(df_export)
                resumen.to_excel(writer, sheet_name='Resumen', index=False)
            
            logger.info(f"Datos exportados a Excel: {ruta_salida}")
            return True
            
        except ImportError:
            logger.error("Para exportar a Excel, instala: pip install pandas openpyxl")
            return False
        except Exception as e:
            logger.error(f"Error exportando a Excel: {e}")
            return False
    
    def _crear_resumen(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Crea DataFrame de resumen para exportación
        """
        try:
            resumen = pd.DataFrame({
                'Métrica': [
                    'Total de Facturas',
                    'Suma Total',
                    'Promedio por Factura', 
                    'Factura Más Alta',
                    'Factura Más Baja',
                    'Total Impuestos',
                    'Total Descuentos'
                ],
                'Valor': [
                    len(df),
                    f"RD$ {df['Total'].sum():,.2f}",
                    f"RD$ {df['Total'].mean():,.2f}",
                    f"RD$ {df['Total'].max():,.2f}",
                    f"RD$ {df['Total'].min():,.2f}",
                    f"RD$ {df['Impuestos'].sum():,.2f}" if 'Impuestos' in df.columns else "N/A",
                    f"RD$ {df['Descuentos'].sum():,.2f}" if 'Descuentos' in df.columns else "N/A"
                ]
            })
            return resumen
        except Exception as e:
            logger.error(f"Error creando resumen: {e}")
            return pd.DataFrame()
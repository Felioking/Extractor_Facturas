"""
Módulo de exportación de datos a diferentes formatos
"""

import pandas as pd
import json
import logging
from typing import List, Dict, Any
from datetime import datetime
from database.models import Factura

class DataExporter:
    """Exporta datos a diferentes formatos (Excel, JSON, etc.)"""
    
    @staticmethod
    def export_to_excel(facturas: List[Dict[str, Any]], file_path: str) -> bool:
        """
        Exporta facturas a archivo Excel
        
        Args:
            facturas: Lista de facturas a exportar
            file_path: Ruta del archivo de salida
            
        Returns:
            True si la exportación fue exitosa
        """
        try:
            if not facturas:
                logging.warning("No hay datos para exportar a Excel")
                return False
            
            # Crear DataFrame principal
            df_facturas = pd.DataFrame(facturas)
            
            # Crear DataFrame de resumen
            resumen_data = DataExporter._create_summary_data(facturas)
            df_resumen = pd.DataFrame(resumen_data)
            
            # Crear DataFrame de proveedores
            proveedores_data = DataExporter._create_providers_data(facturas)
            df_proveedores = pd.DataFrame(proveedores_data)
            
            # Exportar a Excel con múltiples hojas
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # Hoja de facturas
                df_facturas.to_excel(writer, sheet_name='Facturas', index=False)
                
                # Hoja de resumen
                df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
                
                # Hoja de proveedores
                df_proveedores.to_excel(writer, sheet_name='Proveedores', index=False)
                
                # Ajustar automáticamente el ancho de las columnas
                DataExporter._auto_adjust_columns(writer)
            
            logging.info(f"✓ Datos exportados a Excel: {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error exportando a Excel: {e}")
            return False
    
    @staticmethod
    def _create_summary_data(facturas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Crea datos de resumen para exportación"""
        if not facturas:
            return []
        
        totals = [f.get('total', 0) for f in facturas if f.get('total')]
        
        return [
            {'Métrica': 'Total Facturas', 'Valor': len(facturas)},
            {'Métrica': 'Suma Total', 'Valor': f"RD$ {sum(totals):,.2f}"},
            {'Métrica': 'Promedio Factura', 'Valor': f"RD$ {sum(totals)/len(totals):,.2f}" if totals else "N/A"},
            {'Métrica': 'Factura Más Alta', 'Valor': f"RD$ {max(totals):,.2f}" if totals else "N/A"},
            {'Métrica': 'Factura Más Baja', 'Valor': f"RD$ {min(totals):,.2f}" if totals else "N/A"},
            {'Métrica': 'Fecha Exportación', 'Valor': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        ]
    
    @staticmethod
    def _create_providers_data(facturas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Crea datos de proveedores para exportación"""
        if not facturas:
            return []
        
        providers = {}
        for factura in facturas:
            rnc = factura.get('rnc_emisor')
            nombre = factura.get('nombre_emisor', 'Desconocido')
            total = factura.get('total', 0)
            
            if rnc:
                if rnc not in providers:
                    providers[rnc] = {
                        'nombre': nombre,
                        'cantidad_facturas': 0,
                        'total_facturado': 0
                    }
                
                providers[rnc]['cantidad_facturas'] += 1
                providers[rnc]['total_facturado'] += total
        
        return [
            {
                'RNC': rnc,
                'Nombre': data['nombre'],
                'Cantidad Facturas': data['cantidad_facturas'],
                'Total Facturado': f"RD$ {data['total_facturado']:,.2f}"
            }
            for rnc, data in providers.items()
        ]
    
    @staticmethod
    def _auto_adjust_columns(writer):
        """Ajusta automáticamente el ancho de las columnas en Excel"""
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
    
    @staticmethod
    def export_to_json(facturas: List[Dict[str, Any]], file_path: str) -> bool:
        """
        Exporta facturas a archivo JSON
        
        Args:
            facturas: Lista de facturas a exportar
            file_path: Ruta del archivo de salida
            
        Returns:
            True si la exportación fue exitosa
        """
        try:
            if not facturas:
                logging.warning("No hay datos para exportar a JSON")
                return False
            
            export_data = {
                'metadata': {
                    'fecha_exportacion': datetime.now().isoformat(),
                    'total_facturas': len(facturas),
                    'version': '1.0'
                },
                'facturas': facturas
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logging.info(f"✓ Datos exportados a JSON: {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error exportando a JSON: {e}")
            return False
    
    @staticmethod
    def export_single_invoice(invoice_data: Dict[str, Any], file_path: str) -> bool:
        """
        Exporta una sola factura a JSON
        
        Args:
            invoice_data: Datos de la factura
            file_path: Ruta del archivo de salida
            
        Returns:
            True si la exportación fue exitosa
        """
        try:
            export_data = {
                'metadata': {
                    'fecha_exportacion': datetime.now().isoformat(),
                    'tipo': 'factura_individual',
                    'version': '1.0'
                },
                'factura': invoice_data
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logging.info(f"✓ Factura individual exportada: {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error exportando factura individual: {e}")
            return False
# processing/validator.py
import re
from datetime import datetime
from typing import Dict, Any, Optional

class ValidadorDatos:
    @staticmethod
    def validar_y_corregir_nit(nit: str) -> Optional[str]:
        """Valida y corrige formato de NIT"""
        if not nit:
            return None
            
        nit_limpio = re.sub(r'[^\d]', '', nit)
        
        if len(nit_limpio) < 5 or len(nit_limpio) > 15:
            return None
            
        return nit_limpio

    @staticmethod
    def validar_y_corregir_fecha(fecha_str: str) -> Optional[str]:
        """Valida y corrige fechas"""
        if not fecha_str:
            return None
            
        patrones = [
            r'(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})',
            r'(\d{2,4})[-/](\d{1,2})[-/](\d{1,2})',
        ]
        
        for patron in patrones:
            coincidencia = re.search(patron, fecha_str)
            if coincidencia:
                grupos = coincidencia.groups()
                try:
                    if len(grupos[2]) == 4:
                        año, mes, dia = int(grupos[0]), int(grupos[1]), int(grupos[2])
                    else:
                        dia, mes, año = int(grupos[0]), int(grupos[1]), int(grupos[2])
                        año = 2000 + año if año < 100 else año
                    
                    if 1900 <= año <= 2100 and 1 <= mes <= 12 and 1 <= dia <= 31:
                        return f"{dia:02d}/{mes:02d}/{año}"
                except (ValueError, IndexError):
                    continue
                    
        return None

    @staticmethod
    def validar_y_corregir_monto(monto_str: str) -> Optional[float]:
        """Valida y corrige montos monetarios"""
        if not monto_str:
            return None
            
        monto_limpio = re.sub(r'[^\d.,]', '', monto_str)
        
        if ',' in monto_limpio and '.' in monto_limpio:
            monto_limpio = monto_limpio.replace('.', '').replace(',', '.')
        elif ',' in monto_limpio:
            if monto_limpio.count(',') == 1 and len(monto_limpio.split(',')[1]) == 2:
                monto_limpio = monto_limpio.replace(',', '.')
            else:
                monto_limpio = monto_limpio.replace(',', '')
        
        try:
            monto = float(monto_limpio)
            if 0 <= monto <= 10000000:
                return round(monto, 2)
        except ValueError:
            pass
            
        return None
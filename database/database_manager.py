"""
Gestión de base de datos SQLite con logging
"""

import sqlite3
import logging
from typing import List, Optional, Dict, Any
from database.models import Factura, Proveedor
from config import Config

# Logger específico para base de datos
logger = logging.getLogger('database')

class DatabaseManager:
    """Gestiona todas las operaciones de base de datos con logging completo"""
    
    def __init__(self, db_name: str = Config.DATABASE_NAME):
        self.db_name = db_name
        self.connection = None
        logger.info(f"Inicializando DatabaseManager con base de datos: {db_name}")
        self.connect()
        self.initialize_tables()
    
    def connect(self):
        """Establece conexión con la base de datos"""
        try:
            self.connection = sqlite3.connect(self.db_name)
            self.connection.row_factory = sqlite3.Row
            logger.info("✓ Conexión a BD establecida correctamente")
        except Exception as e:
            logger.error(f"✗ Error conectando a BD: {e}", exc_info=True)
            raise
    
    def initialize_tables(self):
        """Inicializa las tablas de la base de datos"""
        try:
            cursor = self.connection.cursor()
            
            # Tabla de facturas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS facturas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rnc_emisor TEXT,
                    nombre_emisor TEXT,
                    comprobante TEXT UNIQUE,
                    fecha_emision TEXT,
                    subtotal REAL,
                    impuestos REAL,
                    descuentos REAL,
                    total REAL,
                    archivo_origen TEXT,
                    fecha_procesamiento TEXT,
                    confianza REAL
                )
            ''')
            
            # Tabla de proveedores
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS proveedores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rnc TEXT UNIQUE,
                    nombre TEXT,
                    frecuencia INTEGER DEFAULT 1,
                    ultima_vez TEXT
                )
            ''')
            
            self.connection.commit()
            logger.info("✓ Tablas de BD inicializadas correctamente")
            
        except Exception as e:
            logger.error(f"✗ Error inicializando tablas: {e}", exc_info=True)
            raise
    
    def guardar_factura(self, factura: Factura) -> tuple[bool, str]:
        """Guarda una factura en la base de datos con logging detallado"""
        try:
            cursor = self.connection.cursor()
            
            # Verificar si ya existe
            if factura.comprobante and self.factura_existe(factura.comprobante):
                logger.warning(f"Factura con comprobante {factura.comprobante} ya existe en BD")
                return False, "Comprobante ya existe en la base de datos"
            
            logger.debug(f"Guardando factura en BD: {factura.comprobante}")
            
            cursor.execute('''
                INSERT INTO facturas 
                (rnc_emisor, nombre_emisor, comprobante, fecha_emision, 
                 subtotal, impuestos, descuentos, total, archivo_origen, 
                 fecha_procesamiento, confianza)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', tuple(factura.to_dict().values()))
            
            # Actualizar proveedor
            if factura.rnc_emisor and factura.nombre_emisor:
                self.actualizar_proveedor(factura.rnc_emisor, factura.nombre_emisor)
            
            self.connection.commit()
            logger.info(f"✓ Factura guardada exitosamente: {factura.comprobante}")
            return True, "Factura guardada correctamente"
            
        except sqlite3.IntegrityError as e:
            logger.error(f"Error de integridad al guardar factura {factura.comprobante}: {e}")
            return False, f"Error de integridad: {str(e)}"
        except Exception as e:
            logger.error(f"Error guardando factura {factura.comprobante}: {e}", exc_info=True)
            return False, f"Error guardando en BD: {str(e)}"
    
    def factura_existe(self, comprobante: str) -> bool:
        """Verifica si una factura ya existe"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM facturas WHERE comprobante = ?", (comprobante,))
            existe = cursor.fetchone()[0] > 0
            logger.debug(f"Verificando existencia de comprobante {comprobante}: {existe}")
            return existe
        except Exception as e:
            logger.error(f"Error verificando factura {comprobante}: {e}")
            return False
    
    def actualizar_proveedor(self, rnc: str, nombre: str):
        """Actualiza la frecuencia de un proveedor"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("SELECT frecuencia FROM proveedores WHERE rnc = ?", (rnc,))
            resultado = cursor.fetchone()
            
            if resultado:
                nueva_frecuencia = resultado[0] + 1
                cursor.execute(
                    "UPDATE proveedores SET frecuencia = ?, ultima_vez = datetime('now') WHERE rnc = ?",
                    (nueva_frecuencia, rnc)
                )
                logger.debug(f"Proveedor actualizado: {rnc} - Frecuencia: {nueva_frecuencia}")
            else:
                cursor.execute(
                    "INSERT INTO proveedores (rnc, nombre, ultima_vez) VALUES (?, ?, datetime('now'))",
                    (rnc, nombre)
                )
                logger.info(f"✓ Nuevo proveedor registrado: {nombre} ({rnc})")
            
            self.connection.commit()
            
        except Exception as e:
            logger.error(f"Error actualizando proveedor {rnc}: {e}")
    
    def obtener_proveedores_frecuentes(self, limite: int = 10) -> List[Proveedor]:
        """Obtiene los proveedores más frecuentes"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT rnc, nombre, frecuencia, ultima_vez 
                FROM proveedores 
                ORDER BY frecuencia DESC 
                LIMIT ?
            ''', (limite,))
            
            proveedores = [Proveedor(rnc=row[0], nombre=row[1], frecuencia=row[2], ultima_vez=row[3]) 
                          for row in cursor.fetchall()]
            
            logger.debug(f"Obtenidos {len(proveedores)} proveedores frecuentes")
            return proveedores
            
        except Exception as e:
            logger.error(f"Error obteniendo proveedores: {e}")
            return []
    
    def obtener_todas_facturas(self) -> List[Dict[str, Any]]:
        """Obtiene todas las facturas para exportación"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT rnc_emisor, nombre_emisor, comprobante, fecha_emision, 
                       subtotal, impuestos, descuentos, total, fecha_procesamiento 
                FROM facturas 
                ORDER BY fecha_procesamiento DESC
            ''')
            
            facturas = [dict(row) for row in cursor.fetchall()]
            logger.info(f"Obtenidas {len(facturas)} facturas para exportación")
            return facturas
            
        except Exception as e:
            logger.error(f"Error obteniendo facturas: {e}")
            return []
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM facturas")
            total_facturas = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT rnc_emisor) FROM facturas")
            total_proveedores = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(total) FROM facturas")
            suma_total = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT AVG(total) FROM facturas")
            promedio = cursor.fetchone()[0] or 0
            
            stats = {
                'total_facturas': total_facturas,
                'total_proveedores': total_proveedores,
                'suma_total': suma_total,
                'promedio': promedio
            }
            
            logger.debug(f"Estadísticas obtenidas: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def close(self):
        """Cierra la conexión a la base de datos"""
        if self.connection:
            self.connection.close()
            logger.info("✓ Conexión a BD cerrada correctamente")
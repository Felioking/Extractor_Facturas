# database/models.py
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = 'facturas.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.initialize_database()
    
    def initialize_database(self):
        """Inicializa la base de datos con todas las tablas necesarias"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            
            # Crear tabla de facturas (expandida)
            self.cursor.execute('''
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
                    confianza REAL,
                    estado_validacion TEXT DEFAULT 'PENDIENTE'
                )
            ''')
            
            # Crear tabla de proveedores (nueva)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS proveedores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rnc TEXT UNIQUE,
                    nombre TEXT,
                    frecuencia INTEGER DEFAULT 1,
                    ultima_vez TEXT,
                    fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.conn.commit()
            logger.info("Base de datos inicializada correctamente")
            
        except Exception as e:
            logger.error(f"Error inicializando base de datos: {e}")
            raise
    
    def guardar_factura(self, datos_factura: Dict[str, Any]) -> tuple[bool, str]:
        """Guarda una factura en la base de datos"""
        try:
            # Verificar si el comprobante ya existe
            if datos_factura.get('comprobante'):
                existe = self.verificar_comprobante_existente(datos_factura['comprobante'])
                if existe:
                    return False, "El comprobante ya existe en la base de datos"
            
            # Insertar factura
            self.cursor.execute('''
                INSERT INTO facturas 
                (rnc_emisor, nombre_emisor, comprobante, fecha_emision, 
                 subtotal, impuestos, descuentos, total, archivo_origen, 
                 fecha_procesamiento, confianza, estado_validacion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datos_factura.get('rnc_emisor'),
                datos_factura.get('nombre_emisor'),
                datos_factura.get('comprobante'),
                datos_factura.get('fecha_emision'),
                datos_factura.get('subtotal'),
                datos_factura.get('impuestos'),
                datos_factura.get('descuentos'),
                datos_factura.get('total'),
                datos_factura.get('archivo_origen'),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                datos_factura.get('confianza', 0),
                datos_factura.get('estado_validacion', 'PENDIENTE')
            ))
            
            # Actualizar proveedor si hay RNC y nombre
            if datos_factura.get('rnc_emisor') and datos_factura.get('nombre_emisor'):
                self.actualizar_proveedor(
                    datos_factura['rnc_emisor'], 
                    datos_factura['nombre_emisor']
                )
            
            self.conn.commit()
            logger.info(f"Factura guardada: {datos_factura.get('comprobante', 'N/A')}")
            return True, "Factura guardada correctamente"
            
        except Exception as e:
            logger.error(f"Error guardando factura: {e}")
            return False, f"Error guardando factura: {str(e)}"
    
    def actualizar_proveedor(self, rnc: str, nombre: str):
        """Actualiza o crea un proveedor en la base de datos"""
        try:
            # Verificar si el proveedor existe
            self.cursor.execute(
                "SELECT frecuencia FROM proveedores WHERE rnc = ?", 
                (rnc,)
            )
            resultado = self.cursor.fetchone()
            
            if resultado:
                # Actualizar frecuencia
                nueva_frecuencia = resultado[0] + 1
                self.cursor.execute('''
                    UPDATE proveedores 
                    SET frecuencia = ?, ultima_vez = ?, nombre = ?
                    WHERE rnc = ?
                ''', (
                    nueva_frecuencia, 
                    datetime.now().strftime("%Y-%m-%d"),
                    nombre,
                    rnc
                ))
            else:
                # Insertar nuevo proveedor
                self.cursor.execute('''
                    INSERT INTO proveedores (rnc, nombre, ultima_vez)
                    VALUES (?, ?, ?)
                ''', (
                    rnc, 
                    nombre, 
                    datetime.now().strftime("%Y-%m-%d")
                ))
            
            self.conn.commit()
            logger.debug(f"Proveedor actualizado: {nombre} ({rnc})")
            
        except Exception as e:
            logger.error(f"Error actualizando proveedor: {e}")
    
    def obtener_proveedores_frecuentes(self, limite: int = 10) -> List[Dict]:
        """Obtiene los proveedores más frecuentes"""
        try:
            self.cursor.execute('''
                SELECT rnc, nombre, frecuencia, ultima_vez
                FROM proveedores 
                ORDER BY frecuencia DESC 
                LIMIT ?
            ''', (limite,))
            
            proveedores = []
            for row in self.cursor.fetchall():
                proveedores.append({
                    'rnc': row[0],
                    'nombre': row[1],
                    'frecuencia': row[2],
                    'ultima_vez': row[3]
                })
            
            return proveedores
            
        except Exception as e:
            logger.error(f"Error obteniendo proveedores frecuentes: {e}")
            return []
    
    def verificar_comprobante_existente(self, comprobante: str) -> bool:
        """Verifica si un comprobante ya existe en la base de datos"""
        try:
            self.cursor.execute(
                "SELECT COUNT(*) FROM facturas WHERE comprobante = ?", 
                (comprobante,)
            )
            resultado = self.cursor.fetchone()
            return resultado[0] > 0
            
        except Exception as e:
            logger.error(f"Error verificando comprobante: {e}")
            return False
    
    def obtener_todas_facturas(self, limite: int = 100) -> List[Dict]:
        """Obtiene todas las facturas de la base de datos"""
        try:
            self.cursor.execute('''
                SELECT * FROM facturas 
                ORDER BY fecha_procesamiento DESC 
                LIMIT ?
            ''', (limite,))
            
            facturas = []
            column_names = [description[0] for description in self.cursor.description]
            
            for row in self.cursor.fetchall():
                factura = dict(zip(column_names, row))
                facturas.append(factura)
            
            return facturas
            
        except Exception as e:
            logger.error(f"Error obteniendo facturas: {e}")
            return []
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la base de datos"""
        try:
            stats = {}
            
            # Total de facturas
            self.cursor.execute("SELECT COUNT(*) FROM facturas")
            stats['total_facturas'] = self.cursor.fetchone()[0]
            
            # Total de proveedores únicos
            self.cursor.execute("SELECT COUNT(DISTINCT rnc_emisor) FROM facturas")
            stats['total_proveedores'] = self.cursor.fetchone()[0]
            
            # Suma total
            self.cursor.execute("SELECT SUM(total) FROM facturas")
            stats['suma_total'] = self.cursor.fetchone()[0] or 0
            
            # Promedio
            self.cursor.execute("SELECT AVG(total) FROM facturas")
            stats['promedio_factura'] = self.cursor.fetchone()[0] or 0
            
            # Factura más alta y más baja
            self.cursor.execute("SELECT MAX(total), MIN(total) FROM facturas")
            max_min = self.cursor.fetchone()
            stats['factura_maxima'] = max_min[0] or 0
            stats['factura_minima'] = max_min[1] or 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def close(self):
        """Cierra la conexión a la base de datos"""
        if self.conn:
            self.conn.close()
            logger.info("Conexión a base de datos cerrada")
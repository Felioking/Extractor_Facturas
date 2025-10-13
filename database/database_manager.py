"""
Módulo de base de datos seguro para el extractor de facturas
Protege contra inyección SQL usando parámetros preparados
"""
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import sys
import os

# Agregar el directorio raíz al path para importar config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gestor seguro de base de datos para facturas"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_PATH
        self.conn = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Inicializar la base de datos y crear tablas si no existen"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Para acceso por nombre de columna
            self._create_tables()
            logger.info(f"Base de datos inicializada: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Error inicializando base de datos: {e}")
            raise
    
    def _create_tables(self):
        """Crear las tablas necesarias si no existen"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            rfc TEXT NOT NULL,
            fecha TEXT,
            total REAL NOT NULL,
            uuid TEXT UNIQUE,
            archivo_origen TEXT,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(create_table_query)
            self.conn.commit()
            logger.info("Tabla 'facturas' verificada/creada correctamente")
        except sqlite3.Error as e:
            logger.error(f"Error creando tabla: {e}")
            raise
    
    def insertar_factura(self, factura_data: Dict) -> bool:
        """
        Insertar una nueva factura de forma segura
        
        Args:
            factura_data: Diccionario con datos de la factura
            
        Returns:
            bool: True si fue exitoso, False si hubo error
        """
        required_fields = ['nombre', 'rfc', 'total']
        for field in required_fields:
            if field not in factura_data or not factura_data[field]:
                logger.error(f"Campo requerido faltante: {field}")
                return False
        
        query = """
        INSERT OR REPLACE INTO facturas 
        (nombre, rfc, fecha, total, uuid, archivo_origen)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, (
                factura_data.get('nombre', '').strip(),
                factura_data.get('rfc', '').strip().upper(),
                factura_data.get('fecha', '').strip(),
                float(factura_data.get('total', 0)),
                factura_data.get('uuid', '').strip(),
                factura_data.get('archivo_origen', '').strip()
            ))
            self.conn.commit()
            logger.info(f"Factura insertada: {factura_data.get('uuid', 'N/A')}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error insertando factura: {e}")
            return False
        except ValueError as e:
            logger.error(f"Error en formato de datos: {e}")
            return False
    
    def buscar_facturas(self, campo: str = None, valor: str = None) -> List[Dict]:
        """
        Buscar facturas de forma segura usando parámetros preparados
        
        Args:
            campo: Campo por el cual buscar (nombre, rfc, uuid)
            valor: Valor a buscar
            
        Returns:
            List[Dict]: Lista de facturas encontradas
        """
        # Campos permitidos para búsqueda (prevenir inyección SQL)
        campos_permitidos = ['nombre', 'rfc', 'uuid', 'fecha']
        
        if campo and valor:
            if campo not in campos_permitidos:
                logger.warning(f"Campo no permitido para búsqueda: {campo}")
                return []
            
            query = f"SELECT * FROM facturas WHERE {campo} LIKE ? ORDER BY fecha_creacion DESC"
            params = (f'%{valor}%',)
        else:
            query = "SELECT * FROM facturas ORDER BY fecha_creacion DESC"
            params = ()
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convertir sqlite3.Row a dict
            facturas = [dict(row) for row in rows]
            logger.info(f"Búsqueda encontrada: {len(facturas)} facturas")
            return facturas
        except sqlite3.Error as e:
            logger.error(f"Error buscando facturas: {e}")
            return []
    
    def obtener_todas_facturas(self) -> List[Dict]:
        """Obtener todas las facturas de forma segura"""
        return self.buscar_facturas()
    
    def obtener_factura_por_id(self, factura_id: int) -> Optional[Dict]:
        """Obtener una factura por ID de forma segura"""
        query = "SELECT * FROM facturas WHERE id = ?"
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, (factura_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error obteniendo factura por ID {factura_id}: {e}")
            return None
    
    def actualizar_factura(self, factura_id: int, factura_data: Dict) -> bool:
        """
        Actualizar una factura existente de forma segura
        
        Args:
            factura_id: ID de la factura a actualizar
            factura_data: Nuevos datos de la factura
            
        Returns:
            bool: True si fue exitoso
        """
        # Solo permitir actualizar campos específicos
        campos_permitidos = ['nombre', 'rfc', 'fecha', 'total', 'uuid']
        update_fields = []
        params = []
        
        for campo in campos_permitidos:
            if campo in factura_data:
                update_fields.append(f"{campo} = ?")
                params.append(factura_data[campo])
        
        if not update_fields:
            logger.warning("No hay campos válidos para actualizar")
            return False
        
        params.append(factura_id)
        query = f"UPDATE facturas SET {', '.join(update_fields)} WHERE id = ?"
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            logger.info(f"Factura {factura_id} actualizada correctamente")
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error actualizando factura {factura_id}: {e}")
            return False
    
    def eliminar_factura(self, factura_id: int) -> bool:
        """Eliminar una factura de forma segura"""
        query = "DELETE FROM facturas WHERE id = ?"
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, (factura_id,))
            self.conn.commit()
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Factura {factura_id} eliminada")
            else:
                logger.warning(f"Factura {factura_id} no encontrada para eliminar")
            return deleted
        except sqlite3.Error as e:
            logger.error(f"Error eliminando factura {factura_id}: {e}")
            return False
    
    def obtener_estadisticas(self) -> Dict:
        """Obtener estadísticas de la base de datos"""
        try:
            cursor = self.conn.cursor()
            
            # Total de facturas
            cursor.execute("SELECT COUNT(*) FROM facturas")
            total_facturas = cursor.fetchone()[0]
            
            # Total monetario
            cursor.execute("SELECT SUM(total) FROM facturas")
            total_monetario = cursor.fetchone()[0] or 0
            
            # Proveedores únicos
            cursor.execute("SELECT COUNT(DISTINCT nombre) FROM facturas")
            proveedores_unicos = cursor.fetchone()[0]
            
            return {
                'total_facturas': total_facturas,
                'total_monetario': round(total_monetario, 2),
                'proveedores_unicos': proveedores_unicos
            }
        except sqlite3.Error as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def close(self):
        """Cerrar conexión a la base de datos"""
        if self.conn:
            self.conn.close()
            logger.info("Conexión a base de datos cerrada")
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support"""
        self.close()


# Función de conveniencia para uso rápido
def get_database_manager():
    """Obtener una instancia del gestor de base de datos"""
    return DatabaseManager()


# Pruebas del módulo
if __name__ == "__main__":
    # Configurar logging básico para pruebas
    logging.basicConfig(level=logging.INFO)
    
    # Probar la base de datos
    with DatabaseManager() as db:
        print("✅ Base de datos inicializada correctamente")
        
        # Probar inserción
        test_data = {
            'nombre': 'Proveedor Test',
            'rfc': 'TEST123456789',
            'fecha': '2024-01-01',
            'total': '1000.50',
            'uuid': 'TEST-UUID-123'
        }
        
        if db.insertar_factura(test_data):
            print("✅ Inserción de prueba exitosa")
        
        # Probar búsqueda
        facturas = db.buscar_facturas('nombre', 'Test')
        print(f"✅ Búsqueda encontrada: {len(facturas)} facturas")
        
        # Probar estadísticas
        stats = db.obtener_estadisticas()
        print(f"✅ Estadísticas: {stats}")
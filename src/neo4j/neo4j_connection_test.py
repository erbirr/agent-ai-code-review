"""
neo4j_connection_test.py - Utilidad para verificar la conexión con Neo4j

Este script realiza una serie de pruebas para comprobar que la conexión
con Neo4j funciona correctamente: establecer conexión, crear nodos,
realizar consultas y gestionar transacciones.
"""

import os
import sys
import uuid
from datetime import datetime

from neo4j import GraphDatabase
from neo4j.exceptions import AuthError, ServiceUnavailable


class Neo4jConnectionTester:
    """Clase para probar la conexión y funcionalidades básicas de Neo4j."""

    def __init__(self, uri=None, user=None, password=None):
        """
        Inicializa el tester con los parámetros de conexión.
        
        Args:
            uri: URI de conexión a Neo4j (por defecto: desde variable de entorno NEO4J_URI)
            user: Usuario de Neo4j (por defecto: desde variable de entorno NEO4J_USER)
            password: Contraseña de Neo4j (por defecto: desde variable de entorno NEO4J_PASSWORD)
        """
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "agenteai")
        self.driver = None
        self.test_id = str(uuid.uuid4())[:8]  # Identificador único para los nodos de prueba

    def connect(self):
        """Establece la conexión con Neo4j."""
        try:
            self.driver = GraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
            # Verificar que la conexión es válida
            self.driver.verify_connectivity()
            print(f"✅ Conexión establecida con éxito a {self.uri}")
            return True
        except AuthError:
            print(f"❌ Error de autenticación. Verifica usuario y contraseña.")
            return False
        except ServiceUnavailable:
            print(f"❌ No se puede conectar a Neo4j en {self.uri}. ¿Está el servidor activo?")
            return False
        except Exception as e:
            print(f"❌ Error inesperado al conectar: {str(e)}")
            return False

    def test_create_node(self):
        """Prueba la creación de un nodo de prueba."""
        query = """
        CREATE (t:TestNode {
            id: $id,
            name: $name,
            created_at: $timestamp
        })
        RETURN t
        """
        params = {
            "id": self.test_id,
            "name": f"Test Node {self.test_id}",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            with self.driver.session() as session:
                result = session.run(query, params)
                node = result.single()
                if node:
                    print(f"✅ Nodo de prueba creado con ID: {self.test_id}")
                    return True
                else:
                    print("❌ No se pudo crear el nodo de prueba")
                    return False
        except Exception as e:
            print(f"❌ Error al crear nodo: {str(e)}")
            return False

    def test_read_node(self):
        """Prueba la lectura del nodo creado anteriormente."""
        query = """
        MATCH (t:TestNode {id: $id})
        RETURN t.name AS name
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query, {"id": self.test_id})
                record = result.single()
                if record and record["name"]:
                    print(f"✅ Nodo leído correctamente: {record['name']}")
                    return True
                else:
                    print("❌ No se pudo leer el nodo de prueba")
                    return False
        except Exception as e:
            print(f"❌ Error al leer nodo: {str(e)}")
            return False

    def test_transaction(self):
        """Prueba la ejecución de transacciones."""
        try:
            with self.driver.session() as session:
                # Definimos una función de transacción
                def create_test_relationship(tx, node_id):
                    query = """
                    MATCH (t:TestNode {id: $id})
                    CREATE (t)-[:HAS_TEST {timestamp: $timestamp}]->(m:TestMetadata {status: 'OK'})
                    RETURN m.status as status
                    """
                    result = tx.run(query, {"id": node_id, "timestamp": datetime.now().isoformat()})
                    return result.single()["status"]
                
                # Ejecutamos la transacción
                status = session.write_transaction(create_test_relationship, self.test_id)
                print(f"✅ Transacción ejecutada con éxito. Status: {status}")
                return True
        except Exception as e:
            print(f"❌ Error en transacción: {str(e)}")
            return False

    def cleanup(self):
        """Elimina los nodos de prueba para no dejar residuos."""
        query = """
        MATCH (t:TestNode {id: $id})-[r]-(m)
        DETACH DELETE t, m
        """
        
        try:
            with self.driver.session() as session:
                session.run(query, {"id": self.test_id})
                print("✅ Limpieza completada. Nodos de prueba eliminados.")
                return True
        except Exception as e:
            print(f"❌ Error en limpieza: {str(e)}")
            return False

    def close(self):
        """Cierra la conexión con Neo4j."""
        if self.driver:
            self.driver.close()
            print("✅ Conexión cerrada correctamente")

    def run_all_tests(self):
        """Ejecuta todas las pruebas en secuencia."""
        print("\n🔍 INICIANDO PRUEBAS DE CONEXIÓN A NEO4J\n")
        print(f"URI: {self.uri}")
        print(f"Usuario: {self.user}")
        print(f"ID de prueba: {self.test_id}\n")
        
        test_results = []
        
        # Conectar
        if not self.connect():
            print("\n❌ PRUEBA FALLIDA: No se pudo establecer conexión. Abortando tests.")
            return False
        
        # Ejecutar pruebas
        test_results.append(("Crear nodo", self.test_create_node()))
        test_results.append(("Leer nodo", self.test_read_node()))
        test_results.append(("Ejecutar transacción", self.test_transaction()))
        test_results.append(("Limpiar datos de prueba", self.cleanup()))
        
        # Cerrar conexión
        self.close()
        
        # Mostrar resumen
        print("\n📊 RESUMEN DE PRUEBAS:")
        all_passed = True
        for name, result in test_results:
            status = "✅ PASÓ" if result else "❌ FALLÓ"
            if not result:
                all_passed = False
            print(f"{status} - {name}")
        
        print(f"\n{'🎉 TODAS LAS PRUEBAS PASARON' if all_passed else '❌ ALGUNAS PRUEBAS FALLARON'}")
        return all_passed


if __name__ == "__main__":
    # Se pueden proporcionar credenciales como argumentos de línea de comandos
    uri = sys.argv[1] if len(sys.argv) > 1 else None
    user = sys.argv[2] if len(sys.argv) > 2 else None
    password = sys.argv[3] if len(sys.argv) > 3 else None
    
    tester = Neo4jConnectionTester(uri, user, password)
    success = tester.run_all_tests()
    
    # Código de salida para uso en scripts
    sys.exit(0 if success else 1)
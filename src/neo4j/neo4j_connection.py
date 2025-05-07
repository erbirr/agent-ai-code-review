# src/neo4j/neo4j_connection.py
import logging
import os
import time

from neo4j import GraphDatabase
from neo4j.exceptions import AuthError, ServiceUnavailable


class Neo4jConnection:
    def __init__(self, uri=None, user=None, password=None, max_retry=3, retry_delay=2):
        # Usar variables de entorno si no se proporcionan parámetros
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "agenteai")
        self.driver = None
        self.max_retry = max_retry
        self.retry_delay = retry_delay
        self._connect_with_retry()
        
    def _connect_with_retry(self):
        """Intenta conectar a Neo4j con reintentos en caso de fallos"""
        retry_count = 0
        while retry_count < self.max_retry:
            try:
                self.driver = GraphDatabase.driver(
                    self.uri, 
                    auth=(self.user, self.password),
                    max_connection_lifetime=3600
                )
                # Verificar conexión
                self.driver.verify_connectivity()
                logging.info(f"Conexión exitosa a Neo4j en {self.uri}")
                return
            except (ServiceUnavailable, AuthError) as e:
                retry_count += 1
                if retry_count >= self.max_retry:
                    logging.error(f"Error al conectar a Neo4j: {str(e)}")
                    raise
                logging.warning(f"Intento {retry_count} fallido. Reintentando en {self.retry_delay} segundos...")
                time.sleep(self.retry_delay)
        
    def close(self):
        """Cierra la conexión al driver de Neo4j"""
        if self.driver:
            self.driver.close()
            
    def execute_query(self, query, parameters=None):
        """Ejecuta una consulta Cypher y devuelve los resultados"""
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record for record in result]
        except Exception as e:
            logging.error(f"Error al ejecutar consulta: {str(e)}")
            raise
            
    def execute_write_transaction(self, tx_function, *args, **kwargs):
        """Ejecuta una transacción de escritura"""
        with self.driver.session() as session:
            return session.write_transaction(tx_function, *args, **kwargs)
            
    def execute_read_transaction(self, tx_function, *args, **kwargs):
        """Ejecuta una transacción de lectura"""
        with self.driver.session() as session:
            return session.read_transaction(tx_function, *args, **kwargs)
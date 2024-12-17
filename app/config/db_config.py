import mysql.connector
import cx_Oracle
import logging
from app.config.env import DB_CONFIG, ORACLE_CONFIG

logging.basicConfig(level=logging.INFO)

import mysql.connector
from app.config.env import DB_CONFIG
import logging

def create_verzo_connection():
    """
    Cria uma conexão específica com o banco MySQL 'verzo'.
    """
    try:
        logging.info("Tentando conectar ao banco Verzo...")
        conn = mysql.connector.connect(
            host="10.27.254.161",
            port=3307,            
            user="root",           
            password="Kora@2024",  
            database="verzo"  
        )
        logging.info("Conexão bem-sucedida com o banco Verzo.")
        return conn
    except mysql.connector.Error as e:
        logging.error(f"Erro ao conectar ao banco Verzo: {e}")
        raise ConnectionError(f"Erro ao conectar ao banco Verzo: {e}")

def create_db_connection_mysql():
    """
    Cria uma conexão com o banco MySQL usando as configurações definidas no env.py.
    """
    try:
        logging.info("Tentando conectar ao banco MySQL...")
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"]
        )
        logging.info("Conexão bem-sucedida com o banco MySQL.")
        return conn
    except mysql.connector.Error as e:
        logging.error(f"Erro ao conectar ao banco MySQL: {e}")
        raise ConnectionError(f"Erro ao conectar ao banco MySQL: {e}")

def create_mysql_connection():
    try:
        logging.info("Tentando conectar ao banco MySQL...")
        connection = mysql.connector.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"]
        )
        logging.info("Conexão bem-sucedida com o banco MySQL.")
        return connection
    except mysql.connector.Error as e:
        logging.error(f"Erro ao conectar ao MySQL: {e}")
        raise ConnectionError(f"Erro ao conectar ao MySQL: {e}")

def create_db_connection_mv(database):
    db_config = ORACLE_CONFIG.get(database)
    if not db_config:
        raise ValueError(f"Banco de dados '{database}' não configurado para MV.")

    dsn = cx_Oracle.makedsn(
        db_config['host'],
        db_config.get('port', 1521),
        service_name=db_config['service_name']
    )

    try:
        logging.info(f"Tentando conectar ao banco MV: {database}...")
        connection = cx_Oracle.connect(
            user=db_config['user'],
            password=db_config['password'],
            dsn=dsn,
            encoding="UTF-8"
        )
        logging.info(f"Conexão bem-sucedida com o banco MV: {database}.")
        return connection
    except cx_Oracle.DatabaseError as e:
        logging.error(f"Erro ao conectar ao banco MV '{database}': {e}")
        raise

def create_db_connection_tasy(database):
    db_config = ORACLE_CONFIG.get(database)
    if not db_config:
        raise ValueError(f"Banco de dados '{database}' não configurado para TASY.")

    dsn = cx_Oracle.makedsn(
        db_config['host'],
        db_config.get('port', 1521),
        service_name=db_config['service_name']
    )

    try:
        logging.info(f"Tentando conectar ao banco TASY: {database}...")
        connection = cx_Oracle.connect(
            user=db_config['user'],
            password=db_config['password'],
            dsn=dsn,
            encoding="UTF-8"
        )
        logging.info(f"Conexão bem-sucedida com o banco TASY: {database}.")
        return connection
    except cx_Oracle.DatabaseError as e:
        logging.error(f"Erro ao conectar ao banco TASY '{database}': {e}")
        raise

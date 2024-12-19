import mysql.connector
import cx_Oracle
import logging

# Configuração do logger
logging.basicConfig(level=logging.INFO)

def create_mysql_connection(host, port, user, password, database):
    """
    Cria uma conexão MySQL.
    """
    try:
        logging.info("Conectando ao banco MySQL...")
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        logging.info("Conexão com MySQL estabelecida com sucesso.")
        return connection
    except mysql.connector.Error as e:
        logging.error(f"Erro ao conectar ao MySQL: {e}")
        raise ConnectionError(f"Erro ao conectar ao MySQL: {e}")


def create_oracle_connection(host, port, user, password, service_name):
    """
    Cria uma conexão Oracle.
    """
    try:
        logging.info("Conectando ao banco Oracle...")
        dsn = cx_Oracle.makedsn(host, port, service_name=service_name)
        connection = cx_Oracle.connect(
            user=user,
            password=password,
            dsn=dsn
        )
        logging.info("Conexão com Oracle estabelecida com sucesso.")
        return connection
    except cx_Oracle.DatabaseError as e:
        logging.error(f"Erro ao conectar ao Oracle: {e}")
        raise ConnectionError(f"Erro ao conectar ao Oracle: {e}")

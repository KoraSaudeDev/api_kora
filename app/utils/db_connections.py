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

def create_oracle_connection(host, port, user, password, service_name=None, sid=None):
    """
    Cria uma conexão Oracle, suportando service_name ou SID.
    """
    try:
        logging.info("Conectando ao banco Oracle...")

        # Constrói o DSN com base no service_name ou sid
        if service_name:
            dsn = cx_Oracle.makedsn(host, port, service_name=service_name)
        elif sid:
            dsn = cx_Oracle.makedsn(host, port, sid=sid)
        else:
            raise ValueError("É necessário fornecer 'service_name' ou 'sid' para conexões Oracle.")

        # Estabelece a conexão
        connection = cx_Oracle.connect(
            user=user,
            password=password,
            dsn=dsn
        )
        logging.info("Conexão com Oracle estabelecida com sucesso.")
        return connection
    except cx_Oracle.DatabaseError as e:
        error_obj, = e.args
        logging.error(f"Erro ao conectar ao Oracle: Código={error_obj.code}, Mensagem={error_obj.message}")
        raise ConnectionError(f"Erro ao conectar ao Oracle: {error_obj.message}")
    except ValueError as ve:
        logging.error(f"Erro de validação: {ve}")
        raise

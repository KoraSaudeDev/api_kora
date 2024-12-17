# app/config/oracle_config.py
import cx_Oracle
from app.config.env import ORACLE_CONFIG

def create_oracle_connection(database):
    db_config = ORACLE_CONFIG.get(database)
    if not db_config:
        raise ValueError(f"Configuração do banco Oracle para '{database}' não encontrada.")

    dsn = cx_Oracle.makedsn(db_config['host'], db_config['port'], service_name=db_config['service_name'])

    try:
        return cx_Oracle.connect(
            user=db_config['user'],
            password=db_config['password'],
            dsn=dsn,
            encoding="UTF-8"
        )
    except cx_Oracle.DatabaseError as e:
        raise ConnectionError(f"Erro ao conectar ao Oracle ({database}): {e}")
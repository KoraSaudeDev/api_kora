from cryptography.fernet import Fernet
from sqlalchemy import create_engine
import cx_Oracle
import os
import logging

# Inicialize o objeto de criptografia com a chave secreta
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY não está definido no arquivo .env")
cipher = Fernet(SECRET_KEY.encode())

def decrypt_password(encrypted_password):
    """
    Descriptografa uma senha criptografada.
    """
    try:
        decrypted_password = cipher.decrypt(encrypted_password.encode()).decode()
        logging.debug(f"Senha descriptografada com sucesso.")
        return decrypted_password
    except Exception as e:
        logging.error(f"Erro ao descriptografar a senha: {e}")
        raise RuntimeError(f"Erro ao descriptografar a senha: {e}")

def connect_to_database(db_type, connection_data):
    """
    Conecta ao banco de dados com base no tipo especificado.
    """
    try:
        # Descriptografar a senha
        encrypted_password = connection_data.get("password")
        password = decrypt_password(encrypted_password)
        print(f"Senha descriptografada: {password}")

        # Dados da conexão
        host = connection_data.get("host")
        port = connection_data.get("port")
        username = connection_data.get("username")
        database_name = connection_data.get("database_name")  # Não utilizado para Oracle
        service_name = connection_data.get("service_name")
        sid = connection_data.get("sid")

        if db_type == "oracle":
            if service_name:
                dsn = cx_Oracle.makedsn(host, port, service_name=service_name)
            elif sid:
                dsn = cx_Oracle.makedsn(host, port, sid=sid)
            else:
                raise ValueError("Para conexões Oracle, 'service_name' ou 'sid' deve ser fornecido.")

            return create_engine(f"oracle+cx_oracle://{username}:{password}@{dsn}")

        # Outras conexões já existentes
        if db_type == "mysql":
            return create_engine(f"mysql+pymysql://{username}:{password}@{host}:{port}/{database_name}")
        elif db_type == "mariadb":
            return create_engine(f"mariadb+pymysql://{username}:{password}@{host}:{port}/{database_name}")
        elif db_type == "postgres":
            return create_engine(f"postgresql://{username}:{password}@{host}:{port}/{database_name}")
        elif db_type == "sqlite":
            return create_engine(f"sqlite:///{database_name}")
        # Adicione outros bancos conforme necessário
        else:
            raise ValueError(f"Tipo de banco de dados '{db_type}' não é suportado.")
    except Exception as e:
        raise RuntimeError(f"Erro ao conectar ao banco de dados '{db_type}': {e}")

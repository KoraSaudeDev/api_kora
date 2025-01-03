import jwt
from datetime import datetime, timedelta
from app.config.env import SECRET_KEY
from app.config.db_config import create_db_connection_mysql
from cryptography.fernet import Fernet
import os
from sqlalchemy import create_engine
import re
import unidecode
import logging

# Verifica se SECRET_KEY está configurada
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY não está definido no arquivo .env")

# Inicializa o objeto de criptografia
cipher = Fernet(SECRET_KEY.encode())

def create_token(payload):
    """
    Gera um token JWT com um payload específico.
    """
    try:
        payload["exp"] = datetime.utcnow() + timedelta(hours=1)  # Adiciona expiração
        return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    except Exception as e:
        raise ValueError(f"Erro ao criar token: {e}")

def check_user_permission(user_id, slug):
    """
    Verifica se um usuário possui permissão para acessar um slug específico.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 1 
            FROM user_access ua
            JOIN route_access ra ON ua.access_id = ra.access_id
            JOIN routes r ON ra.route_id = r.id
            WHERE ua.user_id = %s AND r.slug = %s
        """
        cursor.execute(query, (user_id, slug))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        return result is not None
    except Exception as e:
        raise RuntimeError(f"Erro ao verificar permissões: {e}")

def encrypt_password(password):
    """
    Criptografa uma senha.
    """
    return cipher.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password):
    """
    Descriptografa uma senha criptografada.
    """
    return cipher.decrypt(encrypted_password.encode()).decode()

def create_db_engine(db_type, host, port, username, password, database_name, service_name=None, sid=None):
    """
    Cria uma conexão com o banco de dados usando SQLAlchemy.
    """
    try:
        if db_type.lower() == "mysql":
            return create_engine(f"mysql+pymysql://{username}:{password}@{host}:{port}/{database_name}")
        elif db_type.lower() == "mariadb":
            return create_engine(f"mariadb+pymysql://{username}:{password}@{host}:{port}/{database_name}")
        elif db_type.lower() == "sqlite":
            return create_engine(f"sqlite:///{database_name}")
        elif db_type.lower() == "postgres":
            return create_engine(f"postgresql://{username}:{password}@{host}:{port}/{database_name}")
        elif db_type.lower() == "oracle":
            return create_engine(f"oracle+cx_oracle://{username}:{password}@{host}:{port}/{service_name}")
        elif db_type.lower() == "sap":
            raise NotImplementedError("SAP connection not yet supported via SQLAlchemy.")
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    except Exception as e:
        raise RuntimeError(f"Erro ao criar conexão: {e}")

def generate_slug(name):
    """
    Gera um slug a partir de um nome.
    - Remove caracteres especiais.
    - Substitui espaços por '_'.
    - Converte para minúsculas.
    """
    if not name:
        raise ValueError("O nome não pode estar vazio para gerar um slug.")

    # Remove acentos e converte para caracteres ASCII
    name = unidecode.unidecode(name)

    # Remove caracteres não alfanuméricos exceto espaços
    name = re.sub(r'[^a-zA-Z0-9\s]', '', name)

    # Substitui espaços por '_'
    slug = name.strip().replace(' ', '_').lower()

    return slug
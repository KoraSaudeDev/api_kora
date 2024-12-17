import jwt
from datetime import datetime, timedelta
from app.config.env import SECRET_KEY
from app.config.db_config import create_db_connection_mysql
from cryptography.fernet import Fernet
import os

def create_token(payload):
    """
    Gera um token JWT com um payload específico.
    """
    try:
        # Adicionar data de expiração ao payload
        payload["exp"] = datetime.utcnow() + timedelta(hours=1)
        # Gerar o token JWT
        return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    except Exception as e:
        raise ValueError(f"Erro ao criar token: {e}")


def check_user_permission(user_id, route_prefix):
    """
    Verifica se um usuário possui permissão para acessar uma rota específica.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Query para verificar permissões
        query = """
            SELECT 1 
            FROM user_routes up
            JOIN routes r ON up.route_id = r.id
            WHERE up.user_id = %s AND r.route_prefix = %s
        """
        cursor.execute(query, (user_id, route_prefix))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        return result is not None
    except Exception as e:
        raise RuntimeError(f"Erro ao verificar permissões: {e}")  

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise ValueError("SECRET_KEY não está definido no arquivo .env")

cipher = Fernet(SECRET_KEY.encode())

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

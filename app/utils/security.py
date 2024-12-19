from cryptography.fernet import Fernet, InvalidToken
import logging
import os

def decrypt_password(encrypted_password):
    """
    Descriptografa uma senha usando a SECRET_KEY do ambiente.
    """
    try:
        # Obter a SECRET_KEY do ambiente
        secret_key = os.getenv("SECRET_KEY")
        if not secret_key:
            raise ValueError("SECRET_KEY não definida nas variáveis de ambiente.")

        # Inicializar o cifrador Fernet
        cipher = Fernet(secret_key)
        decrypted_password = cipher.decrypt(encrypted_password.encode()).decode()
        return decrypted_password
    except InvalidToken:
        logging.error("Erro ao descriptografar a senha. Token inválido.")
        raise ValueError("Erro ao descriptografar a senha.")
    except Exception as e:
        logging.error(f"Erro desconhecido ao descriptografar a senha: {e}")
        raise ValueError("Erro desconhecido ao descriptografar a senha.")

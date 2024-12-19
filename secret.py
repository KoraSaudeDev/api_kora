from cryptography.fernet import Fernet

# Gera uma nova chave secreta
secret_key = Fernet.generate_key()

# Exibe a chave secreta gerada
print("Sua SECRET_KEY gerada é:")
print(secret_key.decode())

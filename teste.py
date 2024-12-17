from cryptography.fernet import Fernet

# Gera uma chave válida
key = Fernet.generate_key()
print(key.decode())  # Imprime a chave em formato de string

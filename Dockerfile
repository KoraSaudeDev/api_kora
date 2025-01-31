# Usar uma imagem base oficial do Python
FROM python:3.10-slim

# Configurar o diretório de trabalho dentro do container
WORKDIR /app

# Instalar dependências do sistema operacional e o pip
RUN apt-get update && apt-get install -y \
    unixodbc \
    unixodbc-dev \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar os arquivos de dependências para o container
COPY requirements.txt .

# Instalar as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante da aplicação para o diretório de trabalho do container
COPY . .

# Expor a porta na qual a aplicação será executada
EXPOSE 3792

# Comando para rodar a aplicação
CMD ["python", "main.py"]

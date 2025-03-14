# Usar uma imagem base oficial do Python
FROM python:3.10-slim

# Definir o diretório de trabalho dentro do container
WORKDIR /app

# Instalar pacotes necessários para o Oracle Client
RUN apt-get update && apt-get install -y \
    libaio1 unzip && \
    rm -rf /var/lib/apt/lists/*

# Copiar o Oracle Instant Client para dentro do container
COPY instantclient-basic-linux.zip /opt/oracle/

# Instalar o Oracle Instant Client
RUN mkdir -p /opt/oracle && \
    cd /opt/oracle && \
    unzip instantclient-basic-linux.zip && \
    rm instantclient-basic-linux.zip && \
    ln -s /opt/oracle/instantclient_23_6 /opt/oracle/instantclient && \
    echo "/opt/oracle/instantclient" > /etc/ld.so.conf.d/oracle-instantclient.conf && \
    ldconfig

# Definir variáveis de ambiente do Oracle Client
ENV LD_LIBRARY_PATH=/opt/oracle/instantclient
ENV PATH="$PATH:/opt/oracle/instantclient"
ENV TNS_ADMIN=/opt/oracle/instantclient

# Definir a versão do Instant Client para `oracledb` (caso esteja usando)
ENV ORACLE_CLIENT_VERSION=23.6

# Copiar os arquivos de dependências para o container
COPY requirements.txt .

# Instalar as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante da aplicação para o diretório de trabalho do container
COPY . .

# Expor a porta correta
EXPOSE 5000

# Comando para rodar a aplicação
CMD ["python", "main.py"]

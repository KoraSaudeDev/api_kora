# Usar uma imagem base oficial do Python (Debian 13/trixie)
FROM python:3.10-slim

WORKDIR /app

# Instalar deps do Oracle Instant Client no trixie (t64)
RUN apt-get update && apt-get install -y \
    libaio1t64 libnsl2 unzip \
    && rm -rf /var/lib/apt/lists/*

# Copiar o zip do Instant Client (garanta que o nome bate!)
COPY instantclient-basic-linux.zip /opt/oracle/
COPY itsmkora-account-file.json .

# Instalar o Oracle Instant Client
RUN mkdir -p /opt/oracle && \
    cd /opt/oracle && \
    unzip instantclient-basic-linux.zip && \
    rm instantclient-basic-linux.zip && \
    ln -s /opt/oracle/instantclient_23_6 /opt/oracle/instantclient && \
    echo "/opt/oracle/instantclient" > /etc/ld.so.conf.d/oracle-instantclient.conf && \
    ldconfig

ENV LD_LIBRARY_PATH=/opt/oracle/instantclient
ENV PATH="$PATH:/opt/oracle/instantclient"
ENV TNS_ADMIN=/opt/oracle/instantclient
ENV ORACLE_CLIENT_VERSION=23.6

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 5000
CMD ["python", "main.py"]

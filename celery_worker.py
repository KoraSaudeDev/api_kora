from celery import Celery
import sys
import os
import logging
import pymysql
import cx_Oracle

from app.config.db_config import (
    create_db_connection_mysql,
    create_db_connection_mv,
    create_db_connection_tasy
)

# Certifique-se de adicionar o diretório atual ao path para imports relativos funcionarem
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Importa a função central de execução
from app.services.integration_service import executar_job

# Cria a instância Celery corretamente
app = Celery("verzo_logger", broker="amqp://user:password@rabbitmq:5672//")

@app.task
def log_request_to_db(username, endpoint, status_code, requested_at, ip_address):
    try:
        conn = create_db_connection_mysql()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO request_logs
                  (username, endpoint, status_code, requested_at, ip_address)
                VALUES
                  (%s, %s, %s, %s, %s)
            """, (username, endpoint, status_code, requested_at, ip_address))
            conn.commit()
    except Exception:
        logging.exception("Falha ao gravar log de requisição em background")
    finally:
        if 'conn' in locals():
            conn.close()

@app.task(name="celery_worker.execute_integration_job")
def execute_integration_job(job_id: int):
    try:
        logging.info(f"🚀 Iniciando execução do job #{job_id} via Celery")
        resultado = executar_job(job_id)
        logging.info(f"✅ Job {job_id} finalizado: {resultado}")
        return resultado
    except Exception as e:
        logging.error(f"❌ Erro no job {job_id}: {e}")
        raise
from celery import Celery
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

celery_app = Celery("verzo_logger", broker="redis://redis:6379/0")

@celery_app.task
def log_request_to_db(username, endpoint, status_code, requested_at, ip_address):
    from app.config.db_config import create_db_connection_mysql
    import logging
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
        conn.close()
    except Exception:
        logging.exception("Falha ao gravar log de requisição em background")

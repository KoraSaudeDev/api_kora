import threading
import time
import logging
from datetime import datetime, timedelta
from app.config.db_config import create_db_connection_mysql
from app.services.integration_service import executar_job, get_job_by_id

def job_worker(job_id, schedule_seconds):
    logging.info(f"🚀 Thread de job #{job_id} iniciada (cada {schedule_seconds}s)")
    while True:
        try:
            # Verifica se job ainda está ativo
            conn = create_db_connection_mysql()
            with conn.cursor(dictionary=True) as cur:
                cur.execute("SELECT is_active, last_run FROM integration_jobs WHERE id = %s", (job_id,))
                job_status = cur.fetchone()

            if not job_status or job_status["is_active"] != 1:
                logging.info(f"⏹️ Job #{job_id} desativado. Encerrando thread.")
                break

            now = datetime.utcnow()
            last_run = job_status["last_run"] or datetime.min
            next_run = last_run + timedelta(seconds=schedule_seconds)

            if now >= next_run:
                logging.info(f"⏱️ Executando job automático #{job_id}")
                job_data = get_job_by_id(job_id)
                executar_job(job_id, job_data)

                # Atualiza o campo last_run
                with create_db_connection_mysql() as conn_update:
                    with conn_update.cursor() as cur_update:
                        cur_update.execute("""
                            UPDATE integration_jobs
                            SET last_run = %s
                            WHERE id = %s
                        """, (now, job_id))
                        conn_update.commit()

            time.sleep(1)

        except Exception as e:
            logging.exception(f"❌ Erro ao executar job automático {job_id}: {e}")
            time.sleep(5)

def start_scheduler():
    logging.info("🧠 Iniciando agendador de jobs com threads por job...")

    try:
        conn = create_db_connection_mysql()
        with conn.cursor(dictionary=True) as cur:
            cur.execute("""
                SELECT id, schedule_seconds
                FROM integration_jobs
                WHERE is_active = 1 AND schedule_seconds IS NOT NULL
            """)
            jobs = cur.fetchall()

        for job in jobs:
            job_id = job["id"]
            interval = job["schedule_seconds"]

            t = threading.Thread(target=job_worker, args=(job_id, interval), daemon=True)
            t.start()
            logging.info(f"🧵 Thread iniciada para job #{job_id} (intervalo: {interval}s)")

    except Exception as e:
        logging.exception("❌ Erro ao iniciar agendador")
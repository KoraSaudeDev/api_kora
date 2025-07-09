from flask import Blueprint, jsonify, request
from app.config.db_config import create_db_connection_mysql
from celery_worker import execute_integration_job
from app.utils.security import decrypt_password
import cx_Oracle
import mysql.connector
import logging

integration_bp = Blueprint('integration', __name__, url_prefix='/integration')

def get_connection_by_id(conn_id):
    conn = create_db_connection_mysql()
    try:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT * FROM connections WHERE id = %s", (conn_id,))
            return cur.fetchone()
    finally:
        conn.close()
    
@integration_bp.route('/<int:job_id>', methods=['GET'])
def buscar_integracao(job_id):
    try:
        conn = create_db_connection_mysql()
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT * FROM integration_jobs WHERE id = %s", (job_id,))
            job = cur.fetchone()

        if not job:
            return jsonify({"error": "Job não encontrado"}), 404

        return jsonify(job), 200

    except Exception as e:
        logging.exception("Erro ao buscar integração")
        return jsonify({"error": str(e)}), 500

    finally:
        if conn:
            conn.close()
            
@integration_bp.route('/', methods=['GET'])
def listar_integracoes():
    try:
        conn = create_db_connection_mysql()
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT * FROM integration_jobs ORDER BY id DESC")
            jobs = cur.fetchall()
        return jsonify(jobs), 200

    except Exception as e:
        logging.exception("Erro ao listar integrações")
        return jsonify({"error": str(e)}), 500

    finally:
        if conn:
            conn.close()


@integration_bp.route('/<int:job_id>/executar', methods=['POST'])
def executar_integracao(job_id):
    try:
        logging.info(f"📨 Enviando job {job_id} para execução via Celery")
        execute_integration_job.delay(job_id)
        return jsonify({"message": f"Job {job_id} enviado para execução em background."}), 202

    except Exception as e:
        logging.exception(f"❌ Erro ao enviar job {job_id}")
        return jsonify({"error": str(e)}), 500

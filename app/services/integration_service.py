
import logging
import cx_Oracle
import mysql.connector
from app.utils.notify_chat_error_job import notificar_erro_chat
from app.config.db_config import create_db_connection_mysql
from app.utils.security import decrypt_password

def get_connection_by_id(conn_id):
    conn = create_db_connection_mysql()
    try:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT * FROM connections WHERE id = %s", (conn_id,))
            return cur.fetchone()
    finally:
        conn.close()

def connect_to_database(conf, job=None):
    db_type = conf["db_type"]
    host = conf["host"]
    port = conf["port"]
    user = conf["username"]
    password = decrypt_password(conf["password"])

    database = conf.get("database_name")
    if not database and isinstance(job, dict):
        database = job.get("target_database")

    logging.info(f"🔍 Conectando ao banco ({db_type}) em {host}:{port} com user={user}")
    logging.info(f"📦 Nome do banco a ser usado: {database}")

    if db_type == "oracle":
        dsn = cx_Oracle.makedsn(host, port, service_name=conf["service_name"])
        return cx_Oracle.connect(user=user, password=password, dsn=dsn, encoding="UTF-8")

    elif db_type in ["mysql", "mariadb"]:
        if not database:
            raise ValueError("⚠️ Conexão MySQL/MariaDB sem 'database_name' ou 'target_database'.")
        return mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )

    else:
        raise ValueError("❌ Tipo de banco de dados não suportado: " + db_type)

def generate_sql_statement(mode, table, columns, where_key="id"):
    cols = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))

    if mode == "insert":
        return f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
    elif mode == "replace":
        return f"REPLACE INTO {table} ({cols}) VALUES ({placeholders})"
    elif mode == "update":
        set_clause = ", ".join([f"{col} = %s" for col in columns])
        return f"UPDATE {table} SET {set_clause} WHERE {where_key} = %s"
    elif mode == "upsert":
        update_clause = ", ".join([f"{col}=VALUES({col})" for col in columns])
        return f"""INSERT INTO {table} ({cols}) VALUES ({placeholders})
                   ON DUPLICATE KEY UPDATE {update_clause}"""
    else:
        raise ValueError("Modo de operação não suportado")

def get_job_by_id(job_id):
    conn = create_db_connection_mysql()
    try:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT * FROM integration_jobs WHERE id = %s", (job_id,))
            return cur.fetchone()
    finally:
        conn.close()

def executar_job(job_id, job=None):
    conn = origem_conn = destino_conn = None
    try:
        logging.info(f"🔁 Executando job #{job_id}")
        if not job:
            job = get_job_by_id(job_id)
        if not job:
            raise Exception(f"Job ID {job_id} não encontrado")

        origem_conf = get_connection_by_id(job["source_connection_id"])
        destino_conf = get_connection_by_id(job["destination_connection_id"])
        origem_conn = connect_to_database(origem_conf, job)
        destino_conn = connect_to_database(destino_conf, job)

        # 🔸 Tenta executar a query de origem
        try:
            with origem_conn.cursor() as cur:
                cur.execute(job["source_query"])
                dados = cur.fetchall()
                colunas_origem = [desc[0] for desc in cur.description]
        except Exception as e:
            msg = f"Erro na origem ao executar query: {e}"
            logging.error(msg)
            registrar_erro_critico(job_id, msg)
            raise

        if not dados:
            logging.info("Nenhum dado retornado pela origem.")
            return "Nenhum dado retornado."

        colunas_destino = [col.strip() for col in job["target_columns"].split(",")]
        sql = generate_sql_statement(job["mode"], job["target_table"], colunas_destino, job.get("where_key", "id"))

        with destino_conn.cursor() as cur:
            for row in dados:
                try:
                    valores = [row[colunas_origem.index(col)] for col in colunas_destino]
                    if job["mode"] == "update":
                        valores.append(row[colunas_origem.index(job.get("where_key", "id"))])
                    cur.execute(sql, valores)
                except Exception as err:
                    snapshot = str(dict(zip(colunas_origem, row)))
                    msg = f"Erro ao inserir linha no destino: {err}"
                    logging.error(msg)
                    registrar_erro_critico(job_id, msg, snapshot)
                    raise

            destino_conn.commit()

        logging.info(f"✅ {len(dados)} registros processados.")
        return f"{len(dados)} registros processados com sucesso."

    except Exception as e:
        logging.exception("Erro ao executar job")
        raise

    finally:
        for c in [conn, origem_conn, destino_conn]:
            try:
                if c:
                    c.close()
            except:
                pass


from app.utils.notify_chat_error_job import notificar_erro_chat

def registrar_erro_critico(job_id, mensagem, snapshot=None):
    # Notifica no Chat
    notificar_erro_chat(job_id, mensagem, snapshot)

    # Grava no banco
    try:
        with create_db_connection_mysql() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO integration_errors (job_id, error_message, data_snapshot)
                    VALUES (%s, %s, %s)
                """, (job_id, mensagem, snapshot))
                conn.commit()
    except Exception as e:
        logging.exception("Erro ao registrar falha no banco de log.")

    # Desativa o job
    try:
        with create_db_connection_mysql() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE integration_jobs SET is_active = 0 WHERE id = %s", (job_id,))
                conn.commit()
        logging.warning(f"🚫 Job #{job_id} desativado após erro crítico.")
    except Exception as e:
        logging.exception("Falha ao desativar job.")

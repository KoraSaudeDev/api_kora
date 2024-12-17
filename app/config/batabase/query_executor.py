from app.config.db_config import create_db_connection_mv, create_db_connection_tasy
import logging

def execute_query_with_pagination(system, database, query, limit=None, offset=None):
    """
    Executa uma query com paginação no sistema especificado (MV ou TASY),
    adicionando um número de linha (ROWNUM) a cada registro.
    """
    try:
        if system == "mv":
            connection = create_db_connection_mv(database)
        elif system == "tasy":
            connection = create_db_connection_tasy(database)
        else:
            raise ValueError("Sistema inválido. Use 'mv' ou 'tasy'.")

        logging.info(f"Conexão bem-sucedida com o sistema '{system}' no banco '{database}'.")
        cursor = connection.cursor()
        cursor.execute(query)

        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        for idx, result in enumerate(results, start=1):
            result["ROWNUM"] = idx

        cursor.close()
        connection.close()
        return {"status": "success", "data": results}
    except Exception as e:
        logging.error(f"Erro ao executar query no banco '{database}': {e}")
        return {"status": "error", "message": str(e)}

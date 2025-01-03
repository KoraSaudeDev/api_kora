import logging
from app.utils.db_connection_util import connect_to_database
from app.config.db_config import create_db_connection_mysql

def execute_query_with_parameters(slug, parameters):
    try:
        # Buscar a rota e as conexões associadas
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Obter detalhes da rota
        query_route = "SELECT query FROM routes WHERE slug = %s"
        cursor.execute(query_route, (slug,))
        route = cursor.fetchone()

        if not route:
            raise ValueError(f"Rota com slug '{slug}' não encontrada.")

        query = route["query"]

        # Obter as conexões associadas
        query_connections = """
            SELECT c.*
            FROM route_connections rc
            JOIN connections c ON rc.connection_id = c.id
            WHERE rc.route_id = (SELECT id FROM routes WHERE slug = %s)
        """
        cursor.execute(query_connections, (slug,))
        connections = cursor.fetchall()

        if not connections:
            raise ValueError(f"Nenhuma conexão associada à rota com slug '{slug}'.")

        # Fechar cursor e conexão MySQL
        cursor.close()
        conn.close()

        # Substituir parâmetros na query
        param_dict = {f":{param['name']}": param["value"] for param in parameters}
        query = query.format(**param_dict)

        # Executar a query em todas as conexões associadas
        results = {}
        for connection in connections:
            try:
                logging.info(f"Tentando conectar ao banco com os seguintes dados: {connection}")
                
                db_conn = connect_to_database(
                    db_type=connection["db_type"],
                    connection_data=connection
                )

                with db_conn.cursor() as db_cursor:
                    db_cursor.execute(query)
                    rows = db_cursor.fetchall()
                    columns = [desc[0] for desc in db_cursor.description]
                    results[connection["name"]] = [dict(zip(columns, row)) for row in rows]

            except Exception as e:
                logging.error(f"Erro ao executar query na conexão '{connection['name']}': {e}")
                results[connection["name"]] = str(e)

        return results

    except Exception as e:
        logging.error(f"Erro ao executar query da rota: {e}")
        raise
import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from app.utils.decorators import token_required, admin_required, permission_required
from app.config.db_config import create_db_connection_mysql
from app.utils.db_connections import create_oracle_connection, create_mysql_connection
from app.utils.security import decrypt_password

executor_bp = Blueprint('executors', __name__, url_prefix='/executors')

@executor_bp.route('/create', methods=['POST'])
@token_required
@admin_required
@permission_required(route_prefix='/executors')
def create_executor(user_data):
    """
    Cria um executor e salva a query em um arquivo .sql.
    """
    try:
        data = request.json
        system_id = data.get("system_id")
        connection_ids = data.get("connection_ids")
        name = data.get("name")
        query = data.get("query")
        parameters = data.get("parameters", [])  # Lista de parâmetros

        if not all([system_id, connection_ids, name, query]):
            return jsonify({"status": "error", "message": "Todos os campos são obrigatórios."}), 400

        # Remove o ';' do final da query, se existir
        query = query.rstrip(';')

        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT name FROM systems WHERE id = %s", (system_id,))
        system = cursor.fetchone()

        if not system:
            return jsonify({"status": "error", "message": "System não encontrado."}), 404

        system_name = system["name"]

        # Criar a pasta se não existir
        system_folder = os.path.join("app", "queries", system_name)
        os.makedirs(system_folder, exist_ok=True)

        # Caminho completo do arquivo
        file_path = os.path.join(system_folder, f"{name}.sql")

        # Salvar o arquivo
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(query)

        # Salvar no banco de dados
        connection_ids_str = ",".join(map(str, connection_ids))
        query_insert = """
            INSERT INTO executors (system_id, connection_ids, name, file_path)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query_insert, (system_id, connection_ids_str, name, file_path))
        executor_id = cursor.lastrowid  # Obter o ID do executor criado

        # Salvar parâmetros no banco
        if parameters:
            parameter_query = """
                INSERT INTO executor_parameters (executor_id, name, type, value)
                VALUES (%s, %s, %s, %s)
            """
            for param in parameters:
                cursor.execute(parameter_query, (executor_id, param["name"], param["type"], param["value"]))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": "Executor criado com sucesso.", "executor_id": executor_id}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@executor_bp.route('/execute/<int:executor_id>', methods=['POST'])
@token_required
@admin_required
@permission_required(route_prefix='/executors')
def execute_query(user_data, executor_id):
    """
    Executa a query salva em um executor para múltiplas conexões, com suporte à paginação.
    ---
    tags:
      - Executors
    parameters:
      - name: executor_id
        in: path
        required: true
        type: integer
        description: ID do executor a ser executado.
      - name: page
        in: query
        required: false
        type: integer
        description: Página atual para a paginação. Default: 1
      - name: limit
        in: query
        required: false
        type: integer
        description: Número de registros por página. Default: 1000
    responses:
      200:
        description: Resultado da execução da query.
      404:
        description: Executor não encontrado.
      500:
        description: Erro ao executar a query.
    """
    try:
        # Obter parâmetros de paginação da URL
        page = int(request.args.get("page", 1))  # Página atual (default: 1)
        limit = int(request.args.get("limit", 1000))  # Tamanho do limite (default: 1000)
        offset = (page - 1) * limit  # Calcular o deslocamento (offset)

        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Buscar informações do executor
        cursor.execute("SELECT * FROM executors WHERE id = %s", (executor_id,))
        executor = cursor.fetchone()

        if not executor:
            return jsonify({"status": "error", "message": "Executor não encontrado."}), 404

        connection_ids = executor["connection_ids"].split(",")
        file_path = executor["file_path"]

        # Ler a query do arquivo
        with open(file_path, "r", encoding="utf-8") as file:
            query = file.read()

        # Remover qualquer ";" do final da query
        query = query.rstrip(";")

        # Adicionar limites de paginação à query
        paginated_query_mysql = f"{query} LIMIT {limit} OFFSET {offset}"
        paginated_query_oracle = f"""
        SELECT * FROM (
            SELECT a.*, ROWNUM rnum FROM ({query}) a
            WHERE ROWNUM <= {offset + limit}
        )
        WHERE rnum > {offset}
        """

        results = {}
        for connection_id in connection_ids:
            cursor.execute("SELECT * FROM connections WHERE id = %s", (connection_id,))
            connection_data = cursor.fetchone()

            if not connection_data:
                results[f"connection_{connection_id}"] = "Conexão não encontrada."
                continue

            # Abrir a conexão com o banco
            db_type = connection_data["db_type"]
            host = connection_data["host"]
            port = connection_data["port"]
            username = connection_data["username"]
            encrypted_password = connection_data["password"]  # A senha ainda criptografada
            database_name = connection_data["database_name"]
            service_name = connection_data.get("service_name", None)
            sid = connection_data.get("sid", None)

            try:
                # Descriptografar a senha
                password = decrypt_password(encrypted_password)

                if db_type == "mysql":
                    db_conn = create_mysql_connection(host, port, username, password, database_name)
                    final_query = paginated_query_mysql
                elif db_type == "oracle":
                    db_conn = create_oracle_connection(
                        host=host, port=port, username=username, password=password,
                        service_name=service_name, sid=sid
                    )
                    final_query = paginated_query_oracle
                else:
                    results[f"connection_{connection_id}"] = "Tipo de banco desconhecido."
                    continue

                db_cursor = db_conn.cursor()
                db_cursor.execute(final_query)

                columns = [col[0] for col in db_cursor.description]
                rows = [dict(zip(columns, row)) for row in db_cursor.fetchall()]

                results[f"connection_{connection_id}"] = rows

                db_cursor.close()
                db_conn.close()
            except Exception as e:
                results[f"connection_{connection_id}"] = str(e)

        # Atualizar o campo executed_at
        update_query = "UPDATE executors SET executed_at = %s WHERE id = %s"
        cursor.execute(update_query, (datetime.now(), executor_id))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"status": "success", "data": results}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@executor_bp.route('/list', methods=['GET'])
@token_required
@admin_required
@permission_required(route_prefix='/executors')
def list_executors(user_data):
    """
    Lista todos os executores com detalhes, incluindo nomes de sistemas e conexões, com suporte à paginação.
    ---
    tags:
      - Executors
    parameters:
      - name: page
        in: query
        required: false
        type: integer
        description: Número da página para a paginação. Default: 1
        example: 1
      - name: limit
        in: query
        required: false
        type: integer
        description: Número de registros por página. Default: 10
        example: 10
    responses:
      200:
        description: Lista de executores com detalhes.
        schema:
          type: object
          properties:
            status:
              type: string
              example: "success"
            page:
              type: integer
              example: 1
            limit:
              type: integer
              example: 10
            total:
              type: integer
              example: 50
            executors:
              type: array
              items:
                type: object
                properties:
                  executor_id:
                    type: integer
                    example: 1
                  executor_name:
                    type: string
                    example: "Executor 1"
                  system_name:
                    type: string
                    example: "Sistema X"
                  connections:
                    type: array
                    items:
                      type: string
                      example: "Conexão 1"
                  file_path:
                    type: string
                    example: "/path/to/file.sql"
                  created_at:
                    type: string
                    example: "2024-01-01 00:00:00"
                  executed_at:
                    type: string
                    example: "2024-01-02 00:00:00"
      500:
        description: Erro ao buscar os dados.
    """
    try:
        # Obter os parâmetros de paginação
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
        offset = (page - 1) * limit

        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Buscar informações dos executores com paginação
        query = f"""
            SELECT 
                e.id AS executor_id,
                e.name AS executor_name,
                e.file_path,
                e.created_at,
                e.executed_at,
                s.name AS system_name,
                GROUP_CONCAT(c.name) AS connection_names
            FROM executors e
            LEFT JOIN systems s ON e.system_id = s.id
            LEFT JOIN connections c ON FIND_IN_SET(c.id, e.connection_ids)
            GROUP BY e.id
            ORDER BY e.created_at DESC
            LIMIT {limit} OFFSET {offset}
        """
        cursor.execute(query)
        executors = cursor.fetchall()

        # Contar o total de executores
        count_query = "SELECT COUNT(*) AS total FROM executors"
        cursor.execute(count_query)
        total_count = cursor.fetchone()["total"]

        cursor.close()
        conn.close()

        # Organizar os dados
        response = []
        for executor in executors:
            response.append({
                "executor_id": executor["executor_id"],
                "executor_name": executor["executor_name"],
                "system_name": executor["system_name"],
                "connections": executor["connection_names"].split(",") if executor["connection_names"] else [],
                "file_path": executor["file_path"],
                "created_at": executor["created_at"],
                "executed_at": executor["executed_at"] if executor["executed_at"] else "Nunca executado"
            })

        return jsonify({
            "status": "success",
            "page": page,
            "limit": limit,
            "total": total_count,
            "executors": response
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

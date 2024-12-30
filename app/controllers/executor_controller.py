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
        # Obter os dados da requisição
        data = request.json
        system_id = data.get("system_id")
        connection_ids = data.get("connection_ids")
        name = data.get("name")
        query = data.get("query")
        parameters = data.get("parameters", [])  # Lista de parâmetros

        # Log dos dados recebidos
        print("Dados recebidos:", json.dumps(data, indent=4))

        # Validar campos obrigatórios
        if not all([system_id, connection_ids, name, query]):
            print("Erro: Campos obrigatórios ausentes.")
            return jsonify({"status": "error", "message": "Todos os campos são obrigatórios."}), 400

        # Substituir os placeholders de parâmetros de '@nome' para ':nome'
        for param in parameters:
            placeholder = f"@{param['name']}"
            new_placeholder = f":{param['name']}"
            query = query.replace(placeholder, new_placeholder)

        # Remove o ';' do final da query, se existir
        query = query.rstrip(';')
        print("Query ajustada:", query)

        # Conexão com o banco de dados
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Verificar se o sistema existe
        cursor.execute("SELECT name FROM systems WHERE id = %s", (system_id,))
        system = cursor.fetchone()
        print("Sistema encontrado:", system)

        if not system:
            print("Erro: Sistema não encontrado.")
            return jsonify({"status": "error", "message": "System não encontrado."}), 404

        system_name = system["name"]

        # Criar a pasta do sistema se não existir
        system_folder = os.path.join("app", "queries", system_name)
        if not os.path.exists(system_folder):
            os.makedirs(system_folder)
            print("Pasta do sistema criada:", system_folder)
        else:
            print("Pasta do sistema já existe:", system_folder)

        # Caminho completo do arquivo
        file_path = os.path.join(system_folder, f"{name}.sql")
        print("Caminho do arquivo SQL:", file_path)

        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(query)
            print("Arquivo SQL salvo com sucesso.")

            # Verificar se o arquivo foi criado
            if os.path.exists(file_path):
                print(f"Arquivo criado com sucesso: {file_path}")
            else:
                print(f"Erro: Arquivo não foi encontrado após tentativa de criação: {file_path}")
        except Exception as e:
            print("Erro ao salvar o arquivo SQL:", e)
            return jsonify({"status": "error", "message": f"Erro ao salvar o arquivo SQL: {e}"}), 500

        # Salvar o executor no banco de dados
        connection_ids_str = ",".join(map(str, connection_ids))
        query_insert = """
            INSERT INTO executors (system_id, connection_ids, name, file_path)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query_insert, (system_id, connection_ids_str, name, file_path))
        executor_id = cursor.lastrowid  # Obter o ID do executor criado
        print("Executor salvo no banco de dados. ID:", executor_id)

        # Salvar parâmetros no banco
        if parameters:
            parameter_query = """
                INSERT INTO executor_parameters (executor_id, name, type, value)
                VALUES (%s, %s, %s, %s)
            """
            for param in parameters:
                cursor.execute(parameter_query, (executor_id, param["name"], param["type"], param["value"]))
            print("Parâmetros do executor salvos no banco de dados.")

        # Confirmar as alterações no banco
        conn.commit()
        print("Alterações confirmadas no banco de dados.")

        cursor.close()
        conn.close()

        print("Executor criado com sucesso.")
        return jsonify({"status": "success", "message": "Executor criado com sucesso.", "executor_id": executor_id}), 201
    except Exception as e:
        print("Erro durante a criação do executor:", e)
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

@executor_bp.route('/list/<int:system_id>', methods=['GET'])
@token_required
@admin_required
@permission_required(route_prefix='/executors')
def list_executors_by_system(user_data, system_id):
    """
    Lista todos os executores associados a um sistema específico.
    ---
    tags:
      - Executors
    parameters:
      - name: system_id
        in: path
        required: true
        type: integer
        description: ID do sistema para buscar os executores.
        example: 1
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
      404:
        description: Sistema não encontrado ou sem executores associados.
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

        # Buscar informações dos executores associados ao sistema com paginação
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
            WHERE e.system_id = %s
            GROUP BY e.id
            ORDER BY e.created_at DESC
            LIMIT {limit} OFFSET {offset}
        """
        cursor.execute(query, (system_id,))
        executors = cursor.fetchall()

        # Contar o total de executores associados ao sistema
        count_query = "SELECT COUNT(*) AS total FROM executors WHERE system_id = %s"
        cursor.execute(count_query, (system_id,))
        total_count = cursor.fetchone()["total"]

        cursor.close()
        conn.close()

        if not executors:
            return jsonify({"status": "error", "message": "Sistema não encontrado ou sem executores associados."}), 404

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

@executor_bp.route('/validate/<int:executor_id>', methods=['GET'])
@token_required
@admin_required
@permission_required(route_prefix='/executors')
def validate_executor_parameters_route(user_data, executor_id):
    """
    Valida os parâmetros de um executor antes da execução.
    ---
    tags:
      - Executors
    parameters:
      - name: executor_id
        in: path
        required: true
        type: integer
        description: ID do executor para validar os parâmetros.
        example: 1
    responses:
      200:
        description: Parâmetros validados.
        schema:
          type: object
          properties:
            status:
              type: string
              example: "pending"
            message:
              type: string
              example: "Alguns parâmetros precisam ser corrigidos."
            parameters:
              type: array
              items:
                type: object
                properties:
                  name:
                    type: string
                    example: "P_DATA_INI"
                  type:
                    type: string
                    example: "string"
                  value:
                    type: string
                    example: ""
                  is_valid:
                    type: boolean
                    example: false
                  error:
                    type: string
                    example: "O parâmetro 'P_DATA_INI' está vazio e é obrigatório."
    """
    try:
        parameters = validate_executor_parameters(executor_id)

        # Filtrar parâmetros inválidos
        invalid_parameters = [param for param in parameters if not param["is_valid"]]

        if invalid_parameters:
            return jsonify({
                "status": "pending",
                "message": "Alguns parâmetros precisam ser corrigidos.",
                "parameters": invalid_parameters
            }), 200

        return jsonify({
            "status": "success",
            "message": "Todos os parâmetros estão válidos."
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Erro ao validar parâmetros: {e}"
        }), 500

def validate_executor_parameters(executor_id):
    """
    Valida os parâmetros de um executor.
    Retorna uma lista de objetos detalhando a validação de cada parâmetro.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Buscar parâmetros do executor
        query = "SELECT name, type, value FROM executor_parameters WHERE executor_id = %s"
        cursor.execute(query, (executor_id,))
        parameters = cursor.fetchall()

        cursor.close()
        conn.close()

        validation_results = []
        for param in parameters:
            param_result = {
                "name": param["name"],
                "type": param["type"],
                "value": param["value"],
                "is_valid": True,
                "error": None
            }

            # Validar se o valor está vazio
            if param["value"] in (None, ""):
                param_result["is_valid"] = False
                param_result["error"] = f"O parâmetro '{param['name']}' está vazio e é obrigatório."
            
            # Validar tipos
            elif param["type"].lower() == "integer":
                if not str(param["value"]).isdigit():
                    param_result["is_valid"] = False
                    param_result["error"] = f"O parâmetro '{param['name']}' deve ser um número inteiro."
            
            elif param["type"].lower() == "string":
                if not isinstance(param["value"], str):
                    param_result["is_valid"] = False
                    param_result["error"] = f"O parâmetro '{param['name']}' deve ser uma string."
            
            elif param["type"].lower() == "date":
                try:
                    # Validar formato de data
                    datetime.strptime(param["value"], "%Y-%m-%d")
                except ValueError:
                    param_result["is_valid"] = False
                    param_result["error"] = f"O parâmetro '{param['name']}' deve estar no formato 'YYYY-MM-DD'."

            validation_results.append(param_result)

        return validation_results
    except Exception as e:
        return [{
            "name": "unknown",
            "type": "unknown",
            "value": None,
            "is_valid": False,
            "error": f"Erro ao validar parâmetros: {e}"
        }]

@executor_bp.route('/execute/<int:executor_id>', methods=['POST'])
@token_required
@admin_required
@permission_required(route_prefix='/executors')
def execute_query(user_data, executor_id):
    """
    Executa a query salva em um executor para múltiplas conexões, com suporte a parâmetros enviados na requisição.
    """
    try:
        # Obter parâmetros enviados pelo usuário
        request_data = request.json or {}
        user_parameters = request_data.get("parameters", {})

        # Validar os parâmetros
        parameters = validate_executor_parameters_with_user_input(executor_id, user_parameters)
        invalid_parameters = [param for param in parameters if not param["is_valid"]]

        if invalid_parameters:
            return jsonify({
                "status": "error",
                "message": "Erro de validação nos parâmetros.",
                "parameters": invalid_parameters
            }), 400

        # Obter parâmetros de paginação da URL
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 1000))
        offset = (page - 1) * limit

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
            query = file.read().rstrip(";")  # Remove qualquer ";" no final

        # Substituir parâmetros na query com base na validação
        param_dict = {f":{param['name']}": param["value"] for param in parameters}
        print(f"Parâmetros aplicados na query: {param_dict}")

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
            # Buscar detalhes da conexão e garantir que 'db_type' esteja presente
            cursor.execute("""
                SELECT name, db_type, host, port, username, password, database_name, service_name, sid
                FROM connections WHERE id = %s
            """, (connection_id,))
            connection_data = cursor.fetchone()

            if not connection_data:
                results[f"connection_{connection_id}"] = "Conexão não encontrada."
                continue

            connection_name = connection_data["name"]
            db_type = connection_data["db_type"]
            host = connection_data["host"]
            port = connection_data["port"]
            user = connection_data["username"]
            encrypted_password = connection_data["password"]
            database_name = connection_data.get("database_name")
            service_name = connection_data.get("service_name")
            sid = connection_data.get("sid")

            try:
                # Descriptografar a senha
                password = decrypt_password(encrypted_password)

                if db_type == "mysql":
                    db_conn = create_mysql_connection(host, port, user, password, database_name)
                    final_query = paginated_query_mysql
                elif db_type == "oracle":
                    db_conn = create_oracle_connection(
                        host=host, port=port, user=user, password=password,
                        service_name=service_name, sid=sid
                    )
                    final_query = paginated_query_oracle
                else:
                    results[connection_name] = "Tipo de banco desconhecido."
                    continue

                print(f"Executando a query na conexão '{connection_name}' com os parâmetros: {param_dict}")

                db_cursor = db_conn.cursor()
                db_cursor.execute(final_query, param_dict)

                columns = [col[0] for col in db_cursor.description]
                rows = [dict(zip(columns, row)) for row in db_cursor.fetchall()]

                results[connection_name] = rows

                db_cursor.close()
                db_conn.close()
            except Exception as e:
                print(f"Erro ao executar a query na conexão '{connection_name}':", e)
                results[connection_name] = str(e)

        # Atualizar o campo executed_at
        update_query = "UPDATE executors SET executed_at = %s WHERE id = %s"
        cursor.execute(update_query, (datetime.now(), executor_id))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"status": "success", "data": results}), 200
    except Exception as e:
        print("Erro durante a execução da query:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


def validate_executor_parameters_with_user_input(executor_id, user_parameters):
    """
    Valida os parâmetros de um executor considerando valores fornecidos pelo usuário.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Buscar parâmetros do executor
        query = "SELECT name, type, value FROM executor_parameters WHERE executor_id = %s"
        cursor.execute(query, (executor_id,))
        parameters = cursor.fetchall()

        cursor.close()
        conn.close()

        validation_results = []
        for param in parameters:
            param_name = param["name"]
            param_value = user_parameters.get(param_name, param["value"])  # Priorizar valor enviado pelo usuário

            param_result = {
                "name": param_name,
                "type": param["type"],
                "value": param_value,
                "is_valid": True,
                "error": None
            }

            # Validar se o valor está vazio somente se o parâmetro foi declarado
            if param["value"] in (None, "") and param_value in (None, ""):
                param_result["is_valid"] = False
                param_result["error"] = f"O parâmetro '{param_name}' está vazio e é obrigatório."
            
            # Validar tipos
            elif param["type"].lower() == "integer":
                if not str(param_value).isdigit():
                    param_result["is_valid"] = False
                    param_result["error"] = f"O parâmetro '{param_name}' deve ser um número inteiro."
            
            elif param["type"].lower() == "string":
                if not isinstance(param_value, str):
                    param_result["is_valid"] = False
                    param_result["error"] = f"O parâmetro '{param_name}' deve ser uma string."
            
            elif param["type"].lower() == "date":
                try:
                    # Validar formato de data
                    datetime.strptime(param_value, "%Y-%m-%d")
                except ValueError:
                    param_result["is_valid"] = False
                    param_result["error"] = f"O parâmetro '{param_name}' deve estar no formato 'YYYY-MM-DD'."

            validation_results.append(param_result)

        return validation_results
    except Exception as e:
        return [{
            "name": "unknown",
            "type": "unknown",
            "value": None,
            "is_valid": False,
            "error": f"Erro ao validar parâmetros: {e}"
        }]

import os
from flask import Blueprint, request, jsonify
from app.utils.decorators import token_required, admin_required, permission_required
from app.config.db_config import create_db_connection_mysql
from datetime import datetime
from app.utils.db_connection_util import connect_to_database
import json
import logging
import unidecode
import re
from sqlalchemy.sql import text
from app.utils.db_connections import create_oracle_connection, create_mysql_connection
from app.utils.security import decrypt_password

# Blueprint para rotas
route_bp = Blueprint('routes', __name__, url_prefix='/routes')

# Caminho base para as pastas de queries
BASE_QUERIES_PATH = os.path.join("app", "queries")

def generate_slug(name):
    """
    Gera um slug a partir de um nome.
    """
    if not name:
        raise ValueError("O campo 'name' não pode estar vazio para gerar um slug.")
    name = unidecode.unidecode(name)  # Remove acentos
    name = re.sub(r'[^a-zA-Z0-9\s]', '', name)  # Remove caracteres especiais
    return name.strip().replace(' ', '_').lower()

@route_bp.route('/create', methods=['POST'])
@token_required
@permission_required(route_prefix='/routes')
def create_route(user_data):
    """
    Cria uma nova rota, salva no banco e opcionalmente em arquivos, e relaciona com sistemas e conexões.
    """
    try:
        # Obter os dados da requisição
        data = request.json
        name = data.get("name")
        query = data.get("query")
        parameters = data.get("parameters", [])
        system_ids = data.get("system_id", [])  # Pode ser uma lista ou único ID
        connection_ids = data.get("connection_ids", [])

        # Validar campos obrigatórios
        if not name or not query:
            return jsonify({"status": "error", "message": "Os campos 'name' e 'query' são obrigatórios."}), 400

        # Gerar slug para a rota
        slug = generate_slug(name)

        # Substituir placeholders de parâmetros na query
        for param in parameters:
            placeholder = f"@{param['name']}"
            new_placeholder = f":{param['name']}"
            query = query.replace(placeholder, new_placeholder)

        # Inicializar `query_path` como None (opcional)
        query_path = None

        # Salvar a query em um arquivo, se necessário
        save_query_to_file = data.get("save_query_to_file", False)  # Flag opcional
        if save_query_to_file:
            system_folder = os.path.join("app", "queries", slug)
            if not os.path.exists(system_folder):
                os.makedirs(system_folder)
            query_path = os.path.join(system_folder, f"{slug}.sql")
            with open(query_path, "w", encoding="utf-8") as file:
                file.write(query)

        # Conectar ao banco de dados
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Inserir a rota na tabela 'routes'
        query_insert_route = """
            INSERT INTO routes (name, slug, query, query_path, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """
        cursor.execute(query_insert_route, (name, slug, query, query_path))
        route_id = cursor.lastrowid

        # Relacionar com sistemas na tabela 'route_systems'
        if system_ids:
            if not isinstance(system_ids, list):
                system_ids = [system_ids]
            query_insert_systems = """
                INSERT INTO route_systems (route_id, system_id)
                VALUES (%s, %s)
            """
            for system_id in system_ids:
                cursor.execute(query_insert_systems, (route_id, system_id))

        # Relacionar com conexões na tabela 'route_connections'
        if connection_ids:
            query_insert_connections = """
                INSERT INTO route_connections (route_id, connection_id)
                VALUES (%s, %s)
            """
            for connection_id in connection_ids:
                cursor.execute(query_insert_connections, (route_id, connection_id))

        # Inserir parâmetros na tabela 'route_parameters'
        if parameters:
            query_insert_parameters = """
                INSERT INTO route_parameters (route_id, name, type, value)
                VALUES (%s, %s, %s, %s)
            """
            for param in parameters:
                cursor.execute(query_insert_parameters, (route_id, param['name'], param['type'], param['value']))

        # Confirmar transações no banco de dados
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "Rota criada com sucesso.",
            "route_id": route_id,
            "slug": slug,
            "query_path": query_path
        }), 201

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@route_bp.route('/list', methods=['GET'])
@token_required

@permission_required(route_prefix='/routes')
def list_routes(user_data):
    """
    Lista todas as rotas com suas associações e suporta paginação.
    """
    try:
        # Obter parâmetros de paginação
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
        offset = (page - 1) * limit

        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Buscar rotas com paginação
        query_routes = f"""
            SELECT r.id, r.name, r.slug, r.query, r.created_at, r.updated_at,
                   GROUP_CONCAT(rs.system_id) AS system_ids,
                   GROUP_CONCAT(rc.connection_id) AS connection_ids
            FROM routes r
            LEFT JOIN route_systems rs ON r.id = rs.route_id
            LEFT JOIN route_connections rc ON r.id = rc.route_id
            GROUP BY r.id
            ORDER BY r.name
            LIMIT {limit} OFFSET {offset}
        """
        cursor.execute(query_routes)
        routes = cursor.fetchall()

        # Obter parâmetros associados às rotas
        query_parameters = """
            SELECT rp.route_id, rp.name AS parameter_name, rp.type AS parameter_type, rp.value AS parameter_value
            FROM route_parameters rp
        """
        cursor.execute(query_parameters)
        parameters = cursor.fetchall()

        # Organizar parâmetros associados por rota
        route_parameters = {}
        for param in parameters:
            route_id = param["route_id"]
            if route_id not in route_parameters:
                route_parameters[route_id] = []
            route_parameters[route_id].append({
                "name": param["parameter_name"],
                "type": param["parameter_type"],
                "value": param["parameter_value"]
            })

        # Contar o total de rotas
        count_query = "SELECT COUNT(*) AS total FROM routes"
        cursor.execute(count_query)
        total_count = cursor.fetchone()["total"]

        cursor.close()
        conn.close()

        # Organizar a resposta
        response = []
        for route in routes:
            response.append({
                "id": route["id"],
                "name": route["name"],
                "slug": route["slug"],
                "query": route["query"],
                "created_at": route["created_at"],
                "updated_at": route["updated_at"],
                "system_ids": route["system_ids"].split(",") if route["system_ids"] else [],
                "connection_ids": route["connection_ids"].split(",") if route["connection_ids"] else [],
                "parameters": route_parameters.get(route["id"], [])
            })

        return jsonify({
            "status": "success",
            "page": page,
            "limit": limit,
            "total": total_count,
            "routes": response
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@route_bp.route('/connections', methods=['POST'])
@token_required
@permission_required(route_prefix='/routes')
def update_route_connections(user_data):
    """
    Atualiza as conexões associadas a uma rota.
    """
    try:
        data = request.json
        route_id = data.get("route_id")
        connection_ids = data.get("connection_ids")

        if not route_id or not connection_ids:
            return jsonify({"status": "error", "message": "Os campos 'route_id' e 'connection_ids' são obrigatórios."}), 400

        conn = create_db_connection_mysql()
        cursor = conn.cursor()

        # Verificar se a rota existe
        query_check_route = "SELECT id FROM routes WHERE id = %s"
        cursor.execute(query_check_route, (route_id,))
        if not cursor.fetchone():
            return jsonify({"status": "error", "message": "Rota não encontrada."}), 404

        # Remover conexões antigas
        query_delete = "DELETE FROM route_connections WHERE route_id = %s"
        cursor.execute(query_delete, (route_id,))

        # Adicionar novas conexões
        query_insert = "INSERT INTO route_connections (route_id, connection_id) VALUES (%s, %s)"
        for connection_id in connection_ids:
            cursor.execute(query_insert, (route_id, connection_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": "Conexões da rota atualizadas com sucesso."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@route_bp.route('/<int:route_id>/connections', methods=['GET'])
@token_required
@permission_required(route_prefix='/routes')
def list_route_connections(user_data, route_id):
    """
    Lista as conexões associadas a uma rota específica.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT c.id, c.name, c.db_type, c.host, c.port 
            FROM connections c
            JOIN route_connections rc ON c.id = rc.connection_id
            WHERE rc.route_id = %s
        """
        cursor.execute(query, (route_id,))
        connections = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({"status": "success", "connections": connections}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
      
@route_bp.route('/edit/<int:route_id>', methods=['PUT'])
@token_required
@permission_required(route_prefix='/routes')
def edit_route(user_data, route_id):
    """
    Edita uma rota existente com base no ID fornecido.
    """
    try:
        # Obter os dados da requisição
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "Nenhum dado enviado para atualização."}), 400

        # Conectar ao banco de dados
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Validar se a rota existe
        query_check_route = "SELECT * FROM routes WHERE id = %s"
        cursor.execute(query_check_route, (route_id,))
        existing_route = cursor.fetchone()

        if not existing_route:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Rota não encontrada."}), 404

        # Atualizar os campos da rota
        update_fields = []
        update_values = []
        editable_fields = ["name", "query"]
        for field in editable_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                update_values.append(data[field])

        if update_fields:
            # Atualizar slug se o nome for alterado
            if "name" in data:
                slug = generate_slug(data["name"])
                update_fields.append("slug = %s")
                update_values.append(slug)

            # Atualizar `query_path` se necessário
            save_query_to_file = data.get("save_query_to_file", False)
            if save_query_to_file and "query" in data:
                slug = generate_slug(data["name"]) if "name" in data else existing_route["slug"]
                system_folder = os.path.join("app", "queries", slug)
                if not os.path.exists(system_folder):
                    os.makedirs(system_folder)
                query_path = os.path.join(system_folder, f"{slug}.sql")
                with open(query_path, "w", encoding="utf-8") as file:
                    file.write(data["query"])
                update_fields.append("query_path = %s")
                update_values.append(query_path)

            update_values.append(route_id)
            query_update_route = f"UPDATE routes SET {', '.join(update_fields)} WHERE id = %s"
            cursor.execute(query_update_route, tuple(update_values))

        # Atualizar sistemas relacionados
        if "system_id" in data:
            cursor.execute("DELETE FROM route_systems WHERE route_id = %s", (route_id,))
            system_ids = data["system_id"]
            if not isinstance(system_ids, list):
                system_ids = [system_ids]
            for system_id in system_ids:
                cursor.execute("INSERT INTO route_systems (route_id, system_id) VALUES (%s, %s)", (route_id, system_id))

        # Atualizar conexões relacionadas
        if "connection_ids" in data:
            cursor.execute("DELETE FROM route_connections WHERE route_id = %s", (route_id,))
            connection_ids = data["connection_ids"]
            for connection_id in connection_ids:
                cursor.execute("INSERT INTO route_connections (route_id, connection_id) VALUES (%s, %s)", (route_id, connection_id))

        # Atualizar parâmetros
        if "parameters" in data:
            cursor.execute("DELETE FROM route_parameters WHERE route_id = %s", (route_id,))
            parameters = data["parameters"]
            for param in parameters:
                cursor.execute(
                    "INSERT INTO route_parameters (route_id, name, type, value) VALUES (%s, %s, %s, %s)",
                    (route_id, param["name"], param["type"], param["value"])
                )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": "Rota atualizada com sucesso."}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@route_bp.route('/profile/<int:route_id>', methods=['GET'])
@token_required
@permission_required(route_prefix='/routes')
def get_route_details(user_data, route_id):
    """
    Retorna os detalhes de uma rota específica com base no ID fornecido, incluindo parâmetros, conexões e sistemas vinculados.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Buscar os detalhes da rota
        query_route = """
            SELECT id, name, slug, query, description
            FROM routes
            WHERE id = %s
        """
        cursor.execute(query_route, (route_id,))
        route = cursor.fetchone()

        if not route:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Rota não encontrada."}), 404

        # Buscar os parâmetros da rota
        query_parameters = """
            SELECT name, type, value
            FROM route_parameters
            WHERE route_id = %s
        """
        cursor.execute(query_parameters, (route_id,))
        parameters = cursor.fetchall()

        # Buscar as conexões associadas à rota
        query_connections = """
            SELECT c.id, c.name, c.db_type, c.host, c.port, c.username, c.database_name, c.slug
            FROM connections c
            JOIN route_connections rc ON c.id = rc.connection_id
            WHERE rc.route_id = %s
        """
        cursor.execute(query_connections, (route_id,))
        connections = cursor.fetchall()

        # Buscar os sistemas associados à rota
        query_systems = """
            SELECT s.id, s.name, s.slug
            FROM systems s
            JOIN route_systems rs ON s.id = rs.system_id
            WHERE rs.route_id = %s
        """
        cursor.execute(query_systems, (route_id,))
        systems = cursor.fetchall()

        cursor.close()
        conn.close()

        # Adicionar parâmetros, conexões e sistemas ao objeto da rota
        route["parameters"] = parameters
        route["connections"] = connections
        route["systems"] = systems

        return jsonify({
            "status": "success",
            "route": route
        }), 200

    except Exception as e:
        logging.error(f"Erro ao buscar detalhes da rota: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@route_bp.route('/execute/<slug>', methods=['POST'])
@token_required
@permission_required(route_prefix='/routes/execute')
def execute_route_query(user_data, slug):
    """
    Executa a query associada a uma rota com base no slug fornecido.
    """
    try:
        # Obter parâmetros enviados pelo usuário
        request_data = request.json or {}
        provided_parameters = {
            param['name']: param['value'] for param in request_data.get("parameters", [])
        }
        provided_connections = request_data.get("connections", [])

        # Conectar ao banco principal
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Buscar informações da rota
        query_route = """
            SELECT r.id, r.query
            FROM routes r
            WHERE r.slug = %s
        """
        cursor.execute(query_route, (slug,))
        route = cursor.fetchone()

        if not route:
            return jsonify({"status": "error", "message": "Rota não encontrada."}), 404

        # Buscar parâmetros da rota, caso não sejam fornecidos
        query_parameters = """
            SELECT name, type, value
            FROM route_parameters
            WHERE route_id = %s
        """
        cursor.execute(query_parameters, (route['id'],))
        route_parameters = cursor.fetchall()

        # Preencher parâmetros com valores padrão, caso não sejam fornecidos
        for param in route_parameters:
            if param['name'] not in provided_parameters:
                provided_parameters[param['name']] = param['value']

        # Substituir parâmetros diretamente na query
        query = route['query']
        for param in route_parameters:
            param_name = param['name']
            param_value = provided_parameters.get(param_name, param['value'])
            query = query.replace(f":{param_name}", f"'{param_value}'")

        # Buscar conexões associadas, caso não sejam fornecidas
        if not provided_connections:
            query_connections = """
                SELECT c.id, c.name, c.db_type, c.host, c.port, c.username, c.password, c.database_name, c.service_name, c.sid
                FROM connections c
                JOIN route_connections rc ON c.id = rc.connection_id
                WHERE rc.route_id = %s
            """
            cursor.execute(query_connections, (route['id'],))
            connections = cursor.fetchall()
        else:
            query_connections = """
                SELECT id, name, db_type, host, port, username, password, database_name, service_name, sid
                FROM connections
                WHERE slug IN (%s)
            """ % ', '.join(['%s'] * len(provided_connections))
            cursor.execute(query_connections, tuple(provided_connections))
            connections = cursor.fetchall()

        if not connections:
            return jsonify({"status": "error", "message": "Nenhuma conexão válida encontrada."}), 404

        results = {}
        for connection in connections:
            try:
                # Conectar ao banco específico
                password = decrypt_password(connection['password'])

                if connection['db_type'] == 'mysql':
                    db_conn = create_mysql_connection(
                        host=connection['host'],
                        port=connection['port'],
                        user=connection['username'],
                        password=password,
                        database_name=connection['database_name']
                    )
                    db_cursor = db_conn.cursor(dictionary=True)
                elif connection['db_type'] == 'oracle':
                    db_conn = create_oracle_connection(
                        host=connection['host'],
                        port=connection['port'],
                        user=connection['username'],
                        password=password,
                        service_name=connection.get('service_name'),
                        sid=connection.get('sid')
                    )
                    db_cursor = db_conn.cursor()
                else:
                    results[connection['name']] = "Tipo de banco desconhecido."
                    continue

                # Executar a query
                db_cursor.execute(query)
                rows = db_cursor.fetchall()
                columns = [col[0] for col in db_cursor.description]
                results[connection['name']] = [dict(zip(columns, row)) for row in rows]
                db_cursor.close()

            except Exception as e:
                results[connection['name']] = str(e)

        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "data": results
        }), 200

    except Exception as e:
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
        
        
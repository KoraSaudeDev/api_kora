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
import sys
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

# @route_bp.route('/create', methods=['POST'])
# @token_required
# @permission_required(route_prefix='/routes')
# def create_route(user_data):
#     """
#     Cria uma nova rota, salva no banco e opcionalmente em arquivos, e relaciona com sistemas e conexões.
#     """
#     try:
#         # Obter os dados da requisição
#         data = request.json
#         name = data.get("name")
#         query = data.get("query")
#         parameters = data.get("parameters", [])
#         system_ids = data.get("system_id", [])  # Pode ser uma lista ou único ID
#         connection_ids = data.get("connection_ids", [])

#         # Validar campos obrigatórios
#         if not name or not query:
#             return jsonify({"status": "error", "message": "Os campos 'name' e 'query' são obrigatórios."}), 400

#         # Gerar slug para a rota
#         slug = generate_slug(name)

#         # Substituir placeholders de parâmetros na query
#         for param in parameters:
#             placeholder = f"@{param['name']}"
#             new_placeholder = f":{param['name']}"
#             query = query.replace(placeholder, new_placeholder)

#         # Inicializar `query_path` como None (opcional)
#         query_path = None

#         # Salvar a query em um arquivo, se necessário
#         save_query_to_file = data.get("save_query_to_file", False)  # Flag opcional
#         if save_query_to_file:
#             system_folder = os.path.join("app", "queries", slug)
#             if not os.path.exists(system_folder):
#                 os.makedirs(system_folder)
#             query_path = os.path.join(system_folder, f"{slug}.sql")
#             with open(query_path, "w", encoding="utf-8") as file:
#                 file.write(query)

#         # Conectar ao banco de dados
#         conn = create_db_connection_mysql()
#         cursor = conn.cursor(dictionary=True)

#         # Inserir a rota na tabela 'routes'
#         query_insert_route = """
#             INSERT INTO routes (name, slug, query, query_path, created_at)
#             VALUES (%s, %s, %s, %s, NOW())
#         """
#         cursor.execute(query_insert_route, (name, slug, query, query_path))
#         route_id = cursor.lastrowid

#         # Relacionar com sistemas na tabela 'route_systems'
#         if system_ids:
#             if not isinstance(system_ids, list):
#                 system_ids = [system_ids]
#             query_insert_systems = """
#                 INSERT INTO route_systems (route_id, system_id)
#                 VALUES (%s, %s)
#             """
#             for system_id in system_ids:
#                 cursor.execute(query_insert_systems, (route_id, system_id))

#         # Relacionar com conexões na tabela 'route_connections'
#         if connection_ids:
#             query_insert_connections = """
#                 INSERT INTO route_connections (route_id, connection_id)
#                 VALUES (%s, %s)
#             """
#             for connection_id in connection_ids:
#                 cursor.execute(query_insert_connections, (route_id, connection_id))

#         # Inserir parâmetros na tabela 'route_parameters'
#         if parameters:
#             query_insert_parameters = """
#                 INSERT INTO route_parameters (route_id, name, type, value)
#                 VALUES (%s, %s, %s, %s)
#             """
#             for param in parameters:
#                 cursor.execute(query_insert_parameters, (route_id, param['name'], param['type'], param['value']))

#         # Confirmar transações no banco de dados
#         conn.commit()
#         cursor.close()
#         conn.close()

#         return jsonify({
#             "status": "success",
#             "message": "Rota criada com sucesso.",
#             "route_id": route_id,
#             "slug": slug,
#             "query_path": query_path
#         }), 201

#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500

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
        
        # 🚀 Log da requisição completa para depuração
        logging.error(f"📩 Requisição recebida: {json.dumps(data, indent=4)}")

        name = data.get("name")
        query = data.get("query")  # Agora não alteramos os placeholders aqui!
        parameters = data.get("parameters", [])
        system_ids = data.get("system_id", [])  # Pode ser uma lista ou único ID
        connection_ids = data.get("connection_ids", [])

        # Validar campos obrigatórios
        if not name or not query:
            return jsonify({"status": "error", "message": "Os campos 'name' e 'query' são obrigatórios."}), 400

        # Gerar slug para a rota
        slug = generate_slug(name)

        # 🚀 Log dos parâmetros recebidos antes de processamento
        logging.error(f"📌 Parâmetros recebidos: {parameters}")

        # Inicializar `query_path` como None (opcional)
        query_path = None

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
                param_name = param["name"]
                param_type = param["type"].lower()
                param_value = param["value"]

                # 🚀 Log do parâmetro antes da conversão
                logging.error(f"🕵️ Processando parâmetro: {param_name} | Tipo: {param_type} | Valor recebido: {param_value}")

                # **🚀 Correção do tipo `datetime-local`**
                if param_type in ["date", "datetime", "datetime-local"]:
                    try:
                        if param_type == "date":
                            param_value = datetime.strptime(param_value, "%Y-%m-%d").strftime("%Y-%m-%d")
                        elif param_type == "datetime":
                            param_value = datetime.strptime(param_value, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S")
                        elif param_type == "datetime-local":  
                            param_value = datetime.strptime(param_value, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S")
                            param_type = "datetime"  # Convertendo para `datetime` que é aceito pelo MySQL

                        logging.error(f"✅ Parâmetro {param_name} formatado corretamente: {param_value}")
                    except ValueError as e:
                        logging.error(f"❌ Erro ao converter {param_name}: {param_value} | {str(e)}")
                        return jsonify({"status": "error", "message": f"Formato inválido para {param_type}: {param_value}"}), 400

                cursor.execute(query_insert_parameters, (route_id, param_name, param_type, param_value))

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
        logging.error(f"❌ Erro ao criar rota: {e}")
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
                param_name = param["name"]
                param_type = param["type"].lower()
                param_value = param["value"]

                # **🚀 Novo Tratamento para `DATE` e `DATETIME`**
                if param_type == "date":
                    param_value = f"STR_TO_DATE('{param_value}', '%Y-%m-%d')"  # MySQL
                elif param_type == "datetime":
                    param_value = f"STR_TO_DATE('{param_value}', '%Y-%m-%d %H:%i:%s')"  # MySQL

                cursor.execute(
                    "INSERT INTO route_parameters (route_id, name, type, value) VALUES (%s, %s, %s, %s)",
                    (route_id, param_name, param_type, param_value)
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

# @route_bp.route('/execute/<slug>', methods=['POST'])
# @token_required
# @permission_required(route_prefix='/routes/execute')
# def execute_route_query(user_data, slug):
#     """
#     Executa a query associada a uma rota com base no slug fornecido.
#     """
#     try:
#         # Obter parâmetros enviados pelo usuário
#         request_data = request.json or {}
#         provided_parameters = {
#             param['name']: param['value'] for param in request_data.get("parameters", [])
#         }
#         provided_connections = request_data.get("connections", [])

#         # Conectar ao banco principal
#         conn = create_db_connection_mysql()
#         cursor = conn.cursor(dictionary=True)

#         # Buscar informações da rota
#         query_route = """
#             SELECT r.id, r.query
#             FROM routes r
#             WHERE r.slug = %s
#         """
#         cursor.execute(query_route, (slug,))
#         route = cursor.fetchone()

#         if not route:
#             return jsonify({"status": "error", "message": "Rota não encontrada."}), 404

#         # Buscar parâmetros da rota, caso não sejam fornecidos
#         query_parameters = """
#             SELECT name, type, value
#             FROM route_parameters
#             WHERE route_id = %s
#         """
#         cursor.execute(query_parameters, (route['id'],))
#         route_parameters = cursor.fetchall()

#         # Preencher parâmetros com valores padrão, caso não sejam fornecidos
#         for param in route_parameters:
#             if param['name'] not in provided_parameters:
#                 provided_parameters[param['name']] = param['value']

#         # Substituir parâmetros diretamente na query
#         query = route['query']
#         for param in route_parameters:
#             param_name = param['name']
#             param_value = provided_parameters.get(param_name, param['value'])
#             query = query.replace(f":{param_name}", f"'{param_value}'")

#         # Buscar conexões associadas, caso não sejam fornecidas
#         if not provided_connections:
#             query_connections = """
#                 SELECT c.id, c.name, c.db_type, c.host, c.port, c.username, c.password, c.database_name, c.service_name, c.sid
#                 FROM connections c
#                 JOIN route_connections rc ON c.id = rc.connection_id
#                 WHERE rc.route_id = %s
#             """
#             cursor.execute(query_connections, (route['id'],))
#             connections = cursor.fetchall()
#         else:
#             query_connections = """
#                 SELECT id, name, db_type, host, port, username, password, database_name, service_name, sid
#                 FROM connections
#                 WHERE slug IN (%s)
#             """ % ', '.join(['%s'] * len(provided_connections))
#             cursor.execute(query_connections, tuple(provided_connections))
#             connections = cursor.fetchall()

#         if not connections:
#             return jsonify({"status": "error", "message": "Nenhuma conexão válida encontrada."}), 404

#         results = {}
#         for connection in connections:
#             try:
#                 # Conectar ao banco específico
#                 password = decrypt_password(connection['password'])

#                 if connection['db_type'] == 'mysql':
#                     db_conn = create_mysql_connection(
#                         host=connection['host'],
#                         port=connection['port'],
#                         user=connection['username'],
#                         password=password,
#                         database_name=connection['database_name']
#                     )
#                     db_cursor = db_conn.cursor(dictionary=True)
#                 elif connection['db_type'] == 'oracle':
#                     db_conn = create_oracle_connection(
#                         host=connection['host'],
#                         port=connection['port'],
#                         user=connection['username'],
#                         password=password,
#                         service_name=connection.get('service_name'),
#                         sid=connection.get('sid')
#                     )
#                     db_cursor = db_conn.cursor()
#                 else:
#                     results[connection['name']] = "Tipo de banco desconhecido."
#                     continue

#                 # Executar a query
#                 db_cursor.execute(query)
#                 rows = db_cursor.fetchall()
#                 columns = [col[0] for col in db_cursor.description]
#                 results[connection['name']] = [dict(zip(columns, row)) for row in rows]
#                 db_cursor.close()

#             except Exception as e:
#                 results[connection['name']] = str(e)

#         cursor.close()
#         conn.close()

#         return jsonify({
#             "status": "success",
#             "data": results
#         }), 200

#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500

# @route_bp.route('/execute/<slug>', methods=['POST'])
# @token_required
# @permission_required(route_prefix='/routes/execute')
# def execute_route_query(user_data, slug):
#     try:
#         logging.debug(f"🔹 [INICIANDO EXECUÇÃO] - Slug recebido: {slug}")

#         request_data = request.json or {}
#         logging.debug(f"📥 Dados recebidos na requisição: {json.dumps(request_data, indent=4)}")

#         provided_parameters = {
#             param['name']: param['value'] for param in request_data.get("parameters", [])
#         }
#         provided_connections = request_data.get("connections", [])

#         conn = create_db_connection_mysql()
#         cursor = conn.cursor(dictionary=True)

#         query_route = """
#             SELECT r.id, r.query FROM routes r WHERE r.slug = %s
#         """
#         cursor.execute(query_route, (slug,))
#         route = cursor.fetchone()

#         if not route:
#             logging.error(f"❌ Rota não encontrada para o slug: {slug}")
#             return jsonify({"status": "error", "message": "Rota não encontrada."}), 404

#         query_parameters = """
#             SELECT name, type, value FROM route_parameters WHERE route_id = %s
#         """
#         cursor.execute(query_parameters, (route['id'],))
#         route_parameters = cursor.fetchall()

#         for param in route_parameters:
#             if param['name'] not in provided_parameters:
#                 provided_parameters[param['name']] = param['value']

#         logging.debug(f"✅ Parâmetros finais após preenchimento: {json.dumps(provided_parameters, indent=4)}")

#         query_connections = """
#             SELECT c.id, c.name, c.db_type, c.host, c.port, c.username, c.password, 
#                    c.database_name, c.service_name, c.sid
#             FROM connections c
#             JOIN route_connections rc ON c.id = rc.connection_id
#             WHERE rc.route_id = %s
#         """
#         cursor.execute(query_connections, (route['id'],))
#         connections = cursor.fetchall()

#         if not connections:
#             logging.error("❌ Nenhuma conexão válida encontrada.")
#             return jsonify({"status": "error", "message": "Nenhuma conexão válida encontrada."}), 404

#         results = {}
#         query = ""  # ✅ Garantir que query seja inicializada

#         for connection in connections:
#             try:
#                 password = decrypt_password(connection['password'])
#                 db_type = connection['db_type']

#                 if db_type == 'oracle':
#                     db_conn = create_oracle_connection(
#                         host=connection['host'],
#                         port=connection['port'],
#                         user=connection['username'],
#                         password=password,
#                         service_name=connection.get('service_name'),
#                         sid=connection.get('sid')
#                     )
#                     db_cursor = db_conn.cursor()
#                 else:
#                     logging.error(f"⚠️ Banco de dados {db_type} não suportado para execução.")
#                     results[connection['name']] = f"Banco de dados {db_type} não suportado."
#                     continue

#                 param_values = {}

#                 for param in route_parameters:
#                     param_name = param['name']
#                     param_value = provided_parameters.get(param_name, param['value'])

#                     if param_name.upper().startswith("DT_") or "DATA" in param_name.upper():
#                         try:
#                             if isinstance(param_value, str):
#                                 # Tentamos múltiplos formatos de data
#                                 for fmt in ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
#                                     try:
#                                         parsed_date = datetime.strptime(param_value, fmt)
#                                         param_value = parsed_date.strftime("%Y-%m-%d %H:%M:%S")  # Formato padrão para Oracle
#                                         break
#                                     except ValueError:
#                                         continue
#                                 else:
#                                     raise ValueError(f"Formato de data inválido para {param_name}: {param_value}")
#                             param_values[param_name] = param_value
#                         except ValueError as e:
#                             logging.error(f"❌ {e}")
#                             return jsonify({"status": "error", "message": str(e)}), 400
#                     else:
#                         if isinstance(param_value, str):
#                             param_value = param_value.replace("'", "''")
#                         param_values[param_name] = param_value

#                 logging.debug(f"🔍 [DEBUG] Parâmetros finais formatados:\n{json.dumps(param_values, indent=4)}")

#                 if db_type == "oracle":
#                     query = f"""
#                         INSERT INTO TASY.CONVERSAO_MATERIAL_CONVENIO 
#                         ({", ".join(param_values.keys())}) 
#                         VALUES ({", ".join([f"TO_DATE(:{k}, 'YYYY-MM-DD HH24:MI:SS')" if "DATA" in k.upper() or "DT_" in k.upper() else f":{k}" for k in param_values.keys()])})
#                     """

#                 logging.debug(f"🔥 [ORACLE] Query final a ser executada:\n{query}")
#                 logging.debug(f"🔥 [ORACLE] Parâmetros passados:\n{json.dumps(param_values, indent=4)}")

#                 db_cursor.execute(query, param_values)
#                 db_conn.commit()

#                 db_cursor.close()
#                 results[connection['name']] = "Query executada com sucesso"
#                 logging.debug(f"✅ Inserção concluída com sucesso na conexão {connection['name']}.")

#             except Exception as e:
#                 logging.error(f"❌ Erro ao executar query na conexão {connection['name']}: {str(e)}")
#                 logging.error(f"🚨 Query que falhou: {query}")
#                 logging.error(f"🚨 Parâmetros enviados: {json.dumps(param_values, indent=4)}")
#                 results[connection['name']] = str(e)

#         cursor.close()
#         conn.close()

#         return jsonify({
#             "status": "success",
#             "data": results
#         }), 200
#     except Exception as e:
#         logging.error(f"❌ Erro inesperado: {str(e)}")
#         return jsonify({"status": "error", "message": str(e)}), 500

# @route_bp.route('/execute/<slug>', methods=['POST'])
# @token_required
# @permission_required(route_prefix='/routes/execute')
# def execute_route_query(user_data, slug):
#     try:
#         logging.error(f"🔹 [INICIANDO EXECUÇÃO] - Slug recebido: {slug}")
#         sys.stdout.flush()

#         request_data = request.json or {}
#         logging.error(f"📥 Dados recebidos na requisição:\n{json.dumps(request_data, indent=4)}")
#         sys.stdout.flush()

#         provided_parameters = request_data.get("parameters", {})
#         provided_connections = request_data.get("connections", [])

#         conn = create_db_connection_mysql()
#         cursor = conn.cursor(dictionary=True)

#         query_route = "SELECT r.id, r.query FROM routes r WHERE r.slug = %s"
#         cursor.execute(query_route, (slug,))
#         route = cursor.fetchone()

#         if not route:
#             error_message = f"❌ Rota não encontrada para o slug: {slug}"
#             logging.error(error_message)
#             sys.stdout.flush()
#             return jsonify({"status": "error", "message": error_message}), 404

#         query = route['query']
#         logging.error(f"📝 Query original armazenada no banco:\n{query}")
#         sys.stdout.flush()

#         query_connections = """
#             SELECT c.id, c.name, c.slug, c.db_type, c.host, c.port, c.username, c.password, 
#                    c.database_name, c.service_name, c.sid
#             FROM connections c
#             JOIN route_connections rc ON c.id = rc.connection_id
#             WHERE rc.route_id = %s
#         """
#         cursor.execute(query_connections, (route['id'],))
#         connections = cursor.fetchall()

#         if not connections:
#             error_message = "❌ Nenhuma conexão válida encontrada no banco de dados."
#             logging.error(error_message)
#             sys.stdout.flush()
#             return jsonify({"status": "error", "message": error_message}), 404

#         logging.error(f"🔍 Conexões encontradas no banco:\n{json.dumps([c['slug'] for c in connections], indent=4)}")
#         logging.error(f"📌 Conexões enviadas na requisição:\n{json.dumps(provided_connections, indent=4)}")
#         sys.stdout.flush()

#         results = {}
#         executed_any_query = False
#         last_error = None  

#         for connection in connections:
#             db_slug = connection['slug'].strip().lower()
#             provided_connections_cleaned = [c.strip().lower() for c in provided_connections]

#             if db_slug not in provided_connections_cleaned:
#                 logging.error(f"🚫 Conexão {db_slug} encontrada no banco, mas não está na lista enviada pelo usuário.")
#                 sys.stdout.flush()
#                 continue

#             logging.error(f"✅ Conexão {db_slug} será utilizada para execução.")
#             sys.stdout.flush()

#             try:
#                 password = decrypt_password(connection['password'])
#                 db_type = connection['db_type']

#                 db_conn = create_oracle_connection(
#                     host=connection['host'],
#                     port=connection['port'],
#                     user=connection['username'],
#                     password=password,
#                     service_name=connection.get('service_name'),
#                     sid=connection.get('sid')
#                 ) if db_type == 'oracle' else None

#                 if not db_conn:
#                     error_message = f"⚠️ Banco de dados {db_type} não suportado para execução."
#                     logging.error(error_message)
#                     sys.stdout.flush()
#                     results[db_slug] = error_message
#                     continue

#                 db_cursor = db_conn.cursor()

#                 if db_slug not in provided_parameters:
#                     error_message = f"⚠️ Nenhum parâmetro foi enviado para a conexão {db_slug}."
#                     logging.error(error_message)
#                     sys.stdout.flush()
#                     results[db_slug] = error_message
#                     continue

#                 logging.error(f"🔍 [{db_slug}] Parâmetros recebidos:\n{json.dumps(provided_parameters[db_slug], indent=4)}")
#                 sys.stdout.flush()

#                 def replace_placeholder(match):
#                     param_name = match.group(1).lower()
#                     return f":{param_name}"

#                 query_filtered = re.sub(r"@(\w+)", replace_placeholder, query)

#                 expected_parameters = re.findall(r":(\w+)", query_filtered)

#                 user_parameters = {
#                     k.lower(): v if v != "" else None for k, v in provided_parameters[db_slug].items()
#                 }

#                 for param in expected_parameters:
#                     if param not in user_parameters:
#                         logging.error(f"⚠️ [{db_slug}] Parâmetro {param} ausente, definindo como NULL.")
#                         sys.stdout.flush()
#                         user_parameters[param] = None

#                 logging.error(f"🔥 [ORACLE] Query final para {db_slug}:\n{query_filtered}")
#                 logging.error(f"🔍 [DEBUG] Parâmetros finais:\n{json.dumps(user_parameters, indent=4)}")
#                 sys.stdout.flush()

#                 db_cursor.execute(query_filtered, user_parameters)
#                 db_conn.commit()
#                 db_cursor.close()

#                 results[db_slug] = "Query executada com sucesso"
#                 executed_any_query = True
#                 logging.error(f"✅ Inserção concluída com sucesso em {db_slug}.")
#                 sys.stdout.flush()

#             except Exception as e:
#                 error_message = str(e)
#                 last_error = error_message  
#                 logging.error(f"❌ Erro ao executar query em {db_slug}: {error_message}")
#                 logging.error(f"🚨 Query que falhou em {db_slug}: {query_filtered}")
#                 logging.error(f"🚨 Parâmetros enviados: {json.dumps(user_parameters, indent=4)}")
#                 sys.stdout.flush()
#                 results[db_slug] = error_message  

#         cursor.close()
#         conn.close()

#         if not executed_any_query:
#             error_message = "Nenhuma query foi executada. Verifique as conexões e parâmetros enviados."
#             logging.error(f"❌ {error_message}")
#             sys.stdout.flush()
#             return jsonify({
#                 "status": "error",
#                 "message": error_message,
#                 "last_error": last_error  
#             }), 400

#         return jsonify({
#             "status": "success",
#             "data": results
#         }), 200

#     except Exception as e:
#         error_message = str(e)
#         logging.error(f"❌ Erro inesperado: {error_message}")
#         sys.stdout.flush()
#         return jsonify({"status": "error", "message": error_message}), 500

@route_bp.route('/execute/<slug>', methods=['POST'])
@token_required
@permission_required(route_prefix='/routes/execute')
def execute_route_query(user_data, slug):
    try:
        logging.error(f"🔹 [INICIANDO EXECUÇÃO] - Slug recebido: {slug}")
        sys.stdout.flush()

        request_data = request.json or {}
        logging.error(f"📥 Dados recebidos na requisição:\n{json.dumps(request_data, indent=4)}")
        sys.stdout.flush()

        provided_connections = request_data.get("connections", [])
        provided_parameters_list = request_data.get("parameters", [])

        # ✅ Adaptar para o novo formato de parâmetros
        provided_parameters = {}
        for param_entry in provided_parameters_list:
            for connection_name, params in param_entry.items():
                provided_parameters[connection_name] = params

        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        query_route = "SELECT r.id, r.query FROM routes r WHERE r.slug = %s"
        cursor.execute(query_route, (slug,))
        route = cursor.fetchone()

        if not route:
            error_message = f"❌ Rota não encontrada para o slug: {slug}"
            logging.error(error_message)
            sys.stdout.flush()
            return jsonify({"status": "error", "message": error_message}), 404

        query = route['query']
        logging.error(f"📝 Query original armazenada no banco:\n{query}")
        sys.stdout.flush()

        query_connections = """
            SELECT c.id, c.name, c.slug, c.db_type, c.host, c.port, c.username, c.password, 
                   c.database_name, c.service_name, c.sid
            FROM connections c
            JOIN route_connections rc ON c.id = rc.connection_id
            WHERE rc.route_id = %s
        """
        cursor.execute(query_connections, (route['id'],))
        connections = cursor.fetchall()

        if not connections:
            error_message = "❌ Nenhuma conexão válida encontrada no banco de dados."
            logging.error(error_message)
            sys.stdout.flush()
            return jsonify({"status": "error", "message": error_message}), 404

        logging.error(f"🔍 Conexões encontradas no banco:\n{json.dumps([c['slug'] for c in connections], indent=4)}")
        logging.error(f"📌 Conexões enviadas na requisição:\n{json.dumps(provided_connections, indent=4)}")
        sys.stdout.flush()

        results = {}
        executed_any_query = False
        last_error = None  

        for connection in connections:
            db_slug = connection['slug'].strip().lower()
            provided_connections_cleaned = [c.strip().lower() for c in provided_connections]

            if db_slug not in provided_connections_cleaned:
                logging.error(f"🚫 Conexão {db_slug} encontrada no banco, mas não está na lista enviada pelo usuário.")
                sys.stdout.flush()
                continue

            logging.error(f"✅ Conexão {db_slug} será utilizada para execução.")
            sys.stdout.flush()

            try:
                password = decrypt_password(connection['password'])
                db_type = connection['db_type']

                db_conn = create_oracle_connection(
                    host=connection['host'],
                    port=connection['port'],
                    user=connection['username'],
                    password=password,
                    service_name=connection.get('service_name'),
                    sid=connection.get('sid')
                ) if db_type == 'oracle' else None

                if not db_conn:
                    error_message = f"⚠️ Banco de dados {db_type} não suportado para execução."
                    logging.error(error_message)
                    sys.stdout.flush()
                    results[db_slug] = error_message
                    continue

                db_cursor = db_conn.cursor()

                if db_slug not in provided_parameters:
                    error_message = f"⚠️ Nenhum parâmetro foi enviado para a conexão {db_slug}."
                    logging.error(error_message)
                    sys.stdout.flush()
                    results[db_slug] = error_message
                    continue

                logging.error(f"🔍 [{db_slug}] Parâmetros recebidos:\n{json.dumps(provided_parameters[db_slug], indent=4)}")
                sys.stdout.flush()

                def replace_placeholder(match):
                    param_name = match.group(1).lower()
                    return f":{param_name}"

                query_filtered = re.sub(r"@(\w+)", replace_placeholder, query)

                expected_parameters = re.findall(r":(\w+)", query_filtered)

                user_parameters = {
                    k.lower(): v if v != "" else None for k, v in provided_parameters[db_slug].items()
                }

                for param in expected_parameters:
                    if param not in user_parameters:
                        logging.error(f"⚠️ [{db_slug}] Parâmetro {param} ausente, definindo como NULL.")
                        sys.stdout.flush()
                        user_parameters[param] = None

                logging.error(f"🔥 [ORACLE] Query final para {db_slug}:\n{query_filtered}")
                logging.error(f"🔍 [DEBUG] Parâmetros finais:\n{json.dumps(user_parameters, indent=4)}")
                sys.stdout.flush()

                db_cursor.execute(query_filtered, user_parameters)
                db_conn.commit()
                db_cursor.close()

                results[db_slug] = "Query executada com sucesso"
                executed_any_query = True
                logging.error(f"✅ Inserção concluída com sucesso em {db_slug}.")
                sys.stdout.flush()

            except Exception as e:
                error_message = str(e)
                last_error = error_message  
                logging.error(f"❌ Erro ao executar query em {db_slug}: {error_message}")
                logging.error(f"🚨 Query que falhou em {db_slug}: {query_filtered}")
                logging.error(f"🚨 Parâmetros enviados: {json.dumps(user_parameters, indent=4)}")
                sys.stdout.flush()
                results[db_slug] = error_message  

        cursor.close()
        conn.close()

        if not executed_any_query:
            error_message = "Nenhuma query foi executada. Verifique as conexões e parâmetros enviados."
            logging.error(f"❌ {error_message}")
            sys.stdout.flush()
            return jsonify({
                "status": "error",
                "message": error_message,
                "last_error": last_error  
            }), 400

        return jsonify({
            "status": "success",
            "data": results
        }), 200

    except Exception as e:
        error_message = str(e)
        logging.error(f"❌ Erro inesperado: {error_message}")
        sys.stdout.flush()
        return jsonify({"status": "error", "message": error_message}), 500


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
        
        
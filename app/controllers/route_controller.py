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
import traceback
import cx_Oracle
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
    Cria uma nova rota, salvando no banco os dados de query normal, pré-processada e/ou pós-processada,
    relacionando também com sistemas e conexões.
    """
    try:
        # Obter os dados da requisição
        data = request.json
        logging.info(f"Requisição recebida: {json.dumps(data, indent=4)}")

        # Extração dos campos
        name = data.get("name")
        system_id = data.get("system_id")
        connection_ids = data.get("connection_ids", [])
        pre_query = data.get("pre_query")
        query_true = data.get("query_true")
        query_false = data.get("query_false")
        query = data.get("query")  # Query principal (modo normal/)
        post_query = data.get("post_query")
        dml_personalizado = data.get("dml_personalizado")
        is_pre_processed = data.get("is_pre_processed", False)
        is_post_processed = data.get("is_post_processed", False)
        parameters = data.get("parameters", [])

        # Validações: Pelo menos uma query deve existir
        if not any([query, pre_query, query_true, query_false, post_query, dml_personalizado]):
            return jsonify({
                "status": "error",
                "message": ("Pelo menos uma das queries (query, pre_query, query_true, query_false, " +
                            "post_query ou dml_personalizado) deve estar preenchida.")
            }), 400

        # Validação para pré-processamento
        if is_pre_processed and not any([pre_query, query_true, query_false]):
            return jsonify({
                "status": "error",
                "message": ("Pré-processamento ativado, mas nenhuma query foi fornecida " +
                            "(pre_query, query_true, query_false).")
            }), 400

        # Validação para pós-processamento
        if is_post_processed and not post_query:
            return jsonify({
                "status": "error",
                "message": "Pós-processamento ativado, mas post_query está vazia."
            }), 400

        # Determinação do tipo de rota (query_type)
        if is_pre_processed and is_post_processed:
            query_type = "pré e pós-processada"
        elif is_pre_processed:
            query_type = "pré-processada"
        elif is_post_processed:
            query_type = "pós-processada"
        elif query or dml_personalizado:
            query_type = "normal"
        else:
            query_type = "indefinida"

        # Gerar slug para a rota
        slug = generate_slug(name)
        logging.info(f"Gerado slug: {slug} | Tipo de query: {query_type}")

        # Conectar ao banco de dados MySQL
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Inserir a rota na tabela 'routes'
        query_insert_route = """
            INSERT INTO routes 
                (name, slug, system_id, query, pre_query, query_true, query_false, post_query, 
                 dml_personalizado, is_pre_processed, is_post_processed, query_path, created_at)
            VALUES 
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """
        # Aqui, query_path é definido como NULL (pode ser usado futuramente)
        cursor.execute(query_insert_route, (
            name, slug, system_id, query, pre_query, query_true, query_false, post_query,
            dml_personalizado, is_pre_processed, is_post_processed, None
        ))
        route_id = cursor.lastrowid

        # Inserir os parâmetros na tabela 'route_parameters', se houver
        if parameters:
            query_insert_parameters = """
                INSERT INTO route_parameters (route_id, name, type)
                VALUES (%s, %s, %s)
            """
            for param in parameters:
                param_name = param.get("name")
                param_type = param.get("type", "").lower()
                logging.info(f"Processando parâmetro: {param_name} | Tipo: {param_type}")
                cursor.execute(query_insert_parameters, (route_id, param_name, param_type))

        # Relacionar a rota com as conexões na tabela 'route_connections'
        if connection_ids:
            query_insert_connections = """
                INSERT INTO route_connections (route_id, connection_id)
                VALUES (%s, %s)
            """
            for connection_id in connection_ids:
                cursor.execute(query_insert_connections, (route_id, connection_id))

        # Efetuar o commit e fechar a conexão
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "Rota criada com sucesso.",
            "route_id": route_id,
            "query_type": query_type
        }), 201

    except Exception as e:
        logging.error(f"❌ Erro ao processar query: {e}")
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
        limit = int(request.args.get("limit", 1000))
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

def remove_quoted_strings(sql: str) -> str:
    """
    Remove tudo que está entre aspas simples em uma instrução SQL,
    para que 'HH24:MI:SS' não gere :MI, :SS como falsas bind vars.
    """
    return re.sub(r"'[^']*'", '', sql)

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
        provided_parameters = {}
        for param_entry in provided_parameters_list:
            for connection_name, params in param_entry.items():
                provided_parameters[connection_name] = params

        # 1) Carrega rota do MySQL
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)
        query_route = """
            SELECT 
                r.id,
                r.pre_query,
                r.query_true,
                r.query_false,
                r.post_query,
                r.is_pre_processed,
                r.is_post_processed,
                r.query
            FROM routes r
            WHERE r.slug = %s
        """
        cursor.execute(query_route, (slug,))
        route = cursor.fetchone()
        cursor.close()
        conn.close()

        if not route:
            return jsonify({"status": "error", "message": f"❌ Rota não encontrada para o slug: {slug}"}), 404

        pre_query = route['pre_query']
        query_true = route['query_true']
        query_false = route['query_false']
        post_query = route['post_query']
        is_pre_processed = route['is_pre_processed']
        is_post_processed = route['is_post_processed']
        query_legacy = route['query']

        logging.error(f"📝 Queries carregadas: pre={pre_query}, true={query_true}, false={query_false}, post={post_query}, legacy={query_legacy}")
        sys.stdout.flush()

        # 2) Carrega conexões associadas
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)
        query_connections = """
            SELECT DISTINCT c.id, c.name, c.slug, c.db_type, c.host, c.port, c.username,
                   c.password, c.database_name, c.service_name, c.sid
            FROM connections c
            JOIN route_connections rc ON c.id = rc.connection_id
            WHERE rc.route_id = %s
        """
        cursor.execute(query_connections, (route['id'],))
        connections = cursor.fetchall()
        cursor.close()
        conn.close()

        # Filtrar duplicatas (caso haja)
        unique_connections = {}
        for conn_entry in connections:
            slug_lower = conn_entry['slug'].strip().lower()
            if slug_lower not in unique_connections:
                unique_connections[slug_lower] = conn_entry
        connections = list(unique_connections.values())

        if not connections:
            return jsonify({"status": "error", "message": "❌ Nenhuma conexão válida encontrada no banco de dados."}), 404

        results = {}
        executed_any_query = False
        last_error = None

        logging.error("🔎 Modo de execução: LEGACY")
        sys.stdout.flush()

        # Variáveis para armazenar os textos executados (após conversão)
        executed_query_str = ""
        executed_post_query_str = ""
        query_parameters = {}      # Parâmetros usados na query principal
        post_query_parameters = {} # Parâmetros da post_query

        # 3) Percorre conexões e executa queries
        for connection in connections:
            db_slug = connection['slug'].strip().lower()
            if db_slug not in [c.strip().lower() for c in provided_connections]:
                continue

            logging.error(f"✅ Conexão {db_slug} será utilizada para execução.")
            sys.stdout.flush()

            try:
                password = decrypt_password(connection['password'])
                db_conn = create_oracle_connection(
                    host=connection['host'],
                    port=connection['port'],
                    user=connection['username'],
                    password=password,
                    service_name=connection.get('service_name'),
                    sid=connection.get('sid')
                ) if connection['db_type'] == 'oracle' else None

                if not db_conn:
                    results[db_slug] = f"⚠️ Não foi possível criar conexão p/ {db_slug}."
                    continue

                db_cursor = db_conn.cursor()

                if db_slug not in provided_parameters:
                    error_msg = f"⚠️ Nenhum parâmetro enviado para {db_slug}."
                    logging.error(error_msg)
                    sys.stdout.flush()
                    results[db_slug] = error_msg
                    db_cursor.close()
                    continue

                user_param_dict = provided_parameters[db_slug]
                logging.error(f"🔍 [{db_slug}] Parâmetros recebidos:\n{json.dumps(user_param_dict, indent=4)}")
                sys.stdout.flush()

                final_params = {k.lower(): v for k, v in user_param_dict.items()}
                logging.error(f"Chaves em final_params: {list(final_params.keys())}")

                # Executa a query principal (coluna 'query')
                main_query = query_legacy
                if main_query:
                    main_query_filtered = re.sub(r"@(\w+)", r":\1", main_query)
                    found_vars = re.findall(r':(\w+)', main_query_filtered)
                    # Constrói o dicionário de parâmetros com chaves minúsculas
                    query_parameters = {var.lower(): final_params.get(var.lower(), None) for var in found_vars}

                    # Validação para queries UPDATE
                    if main_query_filtered.lower().strip().startswith("update"):
                        # Verifica se existe a cláusula WHERE
                        if "where" not in main_query_filtered.lower():
                            error_msg = "ERRO: query update deve conter cláusula WHERE."
                            logging.error(error_msg)
                            results[db_slug] = error_msg
                            db_cursor.close()
                            continue
                        else:
                            # Extrai a parte do WHERE para verificar os parâmetros
                            where_clause = main_query_filtered.lower().split("where", 1)[1]
                            where_params = re.findall(r':(\w+)', where_clause)
                            valid_param_found = False
                            for param in where_params:
                                value = query_parameters.get(param)
                                if value is not None and (not isinstance(value, str) or value.strip() != ""):
                                    valid_param_found = True
                                    break
                            if not valid_param_found:
                                error_msg = "ERRO: query update com WHERE deve ter ao menos 1 parâmetro válido (não nulo ou vazio)."
                                logging.error(error_msg)
                                results[db_slug] = error_msg
                                db_cursor.close()
                                continue

                    logging.error(f"🔥 [ORACLE] Query principal para {db_slug}:\n{main_query_filtered}")
                    logging.error(f"🔍 [DEBUG] Parâmetros da query principal:\n{json.dumps(query_parameters, indent=4)}")
                    db_cursor.execute(main_query_filtered, query_parameters)
                    db_conn.commit()

                    executed_any_query = True
                    executed_query_str = main_query_filtered
                    msg = "Query executada com sucesso (legacy)."
                    logging.error(f"✅ Query legacy executada para {db_slug}.")
                else:
                    msg = "Query legacy não definida."
                    results[db_slug] = msg
                    db_cursor.close()
                    continue

                # Executa a post_query se o flag is_post_processed estiver ativo e se post_query estiver definida
                if is_post_processed and post_query and post_query.strip():
                    try:
                        logging.error(f"🔥 [ORACLE] Iniciando execução da post_query para {db_slug}:\n{post_query}")
                        post_query_filtered = re.sub(r"@(\w+)", r":\1", post_query)
                        found_post_vars = re.findall(r':(\w+)', post_query_filtered)
                        post_query_parameters = {var.lower(): final_params.get(var.lower(), None) for var in found_post_vars}
                        logging.error(f"🔍 [DEBUG] Parâmetros da post_query:\n{json.dumps(post_query_parameters, indent=4)}")
                        db_cursor.execute(post_query_filtered, post_query_parameters)
                        db_conn.commit()
                        executed_post_query_str = post_query_filtered
                        logging.error(f"✅ Post_query executada com sucesso para {db_slug}. Rowcount: {db_cursor.rowcount}")
                        msg += " Post-query executada com sucesso."
                    except Exception as post_e:
                        logging.exception(f"❌ Erro na post-query em {db_slug}: {post_e}")
                        msg += f" Erro na post-query: {str(post_e)}"
                else:
                    logging.error(f"Não há post_query para executar em {db_slug} ou flag is_post_processed é falso.")

                db_cursor.close()
                results[db_slug] = {
                    "message": msg,
                    "executed_query": executed_query_str,
                    "query_parameters": query_parameters,
                    "executed_post_query": executed_post_query_str,
                    "post_query_parameters": post_query_parameters if post_query and post_query.strip() else {}
                }

            except Exception as e:
                error_message = str(e)
                last_error = error_message
                logging.error(f"❌ Erro ao executar query em {db_slug}: {error_message}")
                logging.error(traceback.format_exc())
                sys.stdout.flush()
                results[db_slug] = error_message

        logging.error(f"🔎 Resultados finais: {results}")
        if not executed_any_query:
            return jsonify({
                "status": "error",
                "message": "Nenhuma query foi executada.",
                "last_error": last_error,
                "data": results
            }), 400

        return jsonify({"status": "success", "data": results}), 200

    except Exception as e:
        logging.error(f"❌ Erro inesperado durante a execução: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500

@route_bp.route('/bluemind/sequence/', methods=['POST'])
@token_required
@permission_required(route_prefix='/routes')
def get_sequence_nextval(user_data):
    try:
        logging.error("🔹 [INICIANDO EXECUÇÃO] - Obtendo NEXTVAL da sequência")
        sys.stdout.flush()

        request_data = request.json or {}
        logging.error(f"📥 Dados recebidos na requisição:\n{json.dumps(request_data, indent=4)}")
        sys.stdout.flush()

        provided_connections = request_data.get("connections", [])
        provided_parameters_list = request_data.get("parameters", [])

        provided_parameters = {}
        for param_entry in provided_parameters_list:
            for connection_name, params in param_entry.items():
                provided_parameters[connection_name] = params

        # Criar conexão com MySQL para buscar credenciais das conexões Oracle
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        query_connections = """
            SELECT c.slug, c.db_type, c.host, c.port, c.username, c.password, c.service_name, c.sid
            FROM connections c
            WHERE c.slug IN (%s)
        """ % (",".join(["%s"] * len(provided_connections)))

        cursor.execute(query_connections, tuple(provided_connections))
        connections = {conn["slug"]: conn for conn in cursor.fetchall()}
        cursor.close()
        conn.close()

        if not connections:
            return jsonify({"status": "error", "message": "❌ Nenhuma conexão válida encontrada no banco de dados."}), 404

        results = {}
        executed_any_query = False
        last_error = None

        # Percorre conexões e executa queries
        for db_slug, user_param_dict in provided_parameters.items():
            db_slug_lower = db_slug.strip().lower()
            if db_slug_lower not in connections:
                continue

            logging.error(f"✅ Conexão {db_slug} será utilizada para execução.")
            sys.stdout.flush()

            try:
                # Obter detalhes da conexão
                conn_details = connections[db_slug_lower]
                if conn_details["db_type"].lower() != "oracle":
                    results[db_slug] = f"⚠️ Conexão {db_slug} não é um banco Oracle."
                    continue

                password = decrypt_password(conn_details["password"])
                db_conn = create_oracle_connection(
                    host=conn_details["host"],
                    port=conn_details["port"],
                    user=conn_details["username"],
                    password=password,
                    service_name=conn_details.get("service_name"),
                    sid=conn_details.get("sid")
                )

                if not db_conn:
                    results[db_slug] = f"⚠️ Não foi possível criar conexão para {db_slug}."
                    continue

                db_cursor = db_conn.cursor()

                # Obtendo o nome da sequência
                sequence_name = user_param_dict.get("sequence")
                if not sequence_name:
                    results[db_slug] = "⚠️ Nenhuma sequência informada."
                    db_cursor.close()
                    continue

                logging.error(f"🔍 [{db_slug}] Obtendo NEXTVAL de {sequence_name}")

                # Montando a query dinâmica
                query = f"SELECT {sequence_name}.NEXTVAL AS id_sequence_utilizada FROM DUAL"
                logging.error(f"🔥 [ORACLE] Query final:\n{query}")
                sys.stdout.flush()

                # Executando a query
                db_cursor.execute(query)
                result = db_cursor.fetchone()

                # Fechando conexão
                db_cursor.close()
                db_conn.close()

                if result:
                    results[db_slug] = {
                        "message": "NEXTVAL obtido com sucesso",
                        "id_sequence_utilizada": result[0]
                    }
                    executed_any_query = True
                else:
                    results[db_slug] = "⚠️ Nenhum valor retornado."

            except Exception as e:
                last_error = str(e)
                logging.error(f"❌ Erro ao obter NEXTVAL em {db_slug}: {last_error}")
                results[db_slug] = last_error

        return jsonify({
            "status": "success" if executed_any_query else "error",
            "message": "Nenhuma query foi executada." if not executed_any_query else "NEXTVAL obtido com sucesso",
            "last_error": last_error,
            "data": results
        }), 400 if not executed_any_query else 200

    except Exception as e:
        logging.error(f"❌ Erro inesperado: {str(e)}")
        logging.error(traceback.format_exc())
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
        

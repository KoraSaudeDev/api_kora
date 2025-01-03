import os
from flask import Blueprint, request, jsonify
from app.config.db_config import create_db_connection_mysql
import logging

# Blueprint para acessos
access_bp = Blueprint('access', __name__, url_prefix='/access')

@access_bp.route('/create', methods=['POST'])
def create_access():
    try:
        logging.info("Recebendo requisição para criar access.")
        data = request.json
        logging.info(f"Dados recebidos: {data}")
        
        name = data.get("name")
        route_slugs = data.get("route_slugs", [])
        route_prefixes = data.get("route_prefixes", [])

        if not name or (not route_slugs and not route_prefixes):
            logging.error("Nome ou rotas ausentes.")
            return jsonify({
                "status": "error",
                "message": "O campo 'name' e pelo menos uma rota (slug ou prefix) são obrigatórios."
            }), 400

        conn = create_db_connection_mysql()
        cursor = conn.cursor()
        
        # Inserir o novo access
        query_insert_access = "INSERT INTO access (name) VALUES (%s)"
        cursor.execute(query_insert_access, (name,))
        access_id = cursor.lastrowid
        logging.info(f"Access criado com ID: {access_id}")

        # Associar rotas dinâmicas (slugs)
        query_insert_slug_access = "INSERT INTO access_routes (access_id, route_slug) VALUES (%s, %s)"
        for slug in route_slugs:
            cursor.execute(query_insert_slug_access, (access_id, slug))
            logging.info(f"Associado slug '{slug}' ao access {access_id}")

        # Associar rotas fixas (prefixos)
        query_insert_prefix_access = "INSERT INTO access_routes (access_id, route_prefix) VALUES (%s, %s)"
        for prefix in route_prefixes:
            cursor.execute(query_insert_prefix_access, (access_id, prefix))
            logging.info(f"Associado prefix '{prefix}' ao access {access_id}")

        conn.commit()
        cursor.close()
        conn.close()

        logging.info("Access criado com sucesso.")
        return jsonify({
            "status": "success",
            "message": "Access criado com sucesso.",
            "access_id": access_id
        }), 201

    except Exception as e:
        logging.error(f"Erro ao criar access: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@access_bp.route('/list', methods=['GET'])
def list_access():
    """
    Lista todos os `access` e suas rotas dinâmicas (`slugs`) e fixas (`prefixos`).
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        query_access = "SELECT id, name FROM access"
        cursor.execute(query_access)
        accesses = cursor.fetchall()

        # Buscar associações de slugs e prefixos
        query_routes = """
            SELECT access_id, route_slug, route_prefix
            FROM access_routes
        """
        cursor.execute(query_routes)
        routes = cursor.fetchall()

        cursor.close()
        conn.close()

        # Organizar os dados
        access_data = {}
        for access in accesses:
            access_id = access['id']
            access_data[access_id] = {
                "id": access_id,
                "name": access['name'],
                "route_slugs": [],
                "route_prefixes": []
            }

        for route in routes:
            if route['route_slug']:
                access_data[route['access_id']]["route_slugs"].append(route['route_slug'])
            if route['route_prefix']:
                access_data[route['access_id']]["route_prefixes"].append(route['route_prefix'])

        return jsonify({
            "status": "success",
            "accesses": list(access_data.values())
        }), 200

    except Exception as e:
        logging.error(f"Erro ao listar access: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@access_bp.route('/user/create', methods=['POST'])
def assign_access_to_user():
    """
    Associa um usuário a um ou mais `access`.
    """
    try:
        data = request.json
        user_id = data.get("user_id")
        access_ids = data.get("access_ids")

        if not user_id or not access_ids:
            return jsonify({
                "status": "error",
                "message": "Os campos 'user_id' e 'access_ids' são obrigatórios."
            }), 400

        conn = create_db_connection_mysql()
        cursor = conn.cursor()

        # Associar o usuário aos acessos
        query_insert_user_access = "INSERT INTO user_access (user_id, access_id) VALUES (%s, %s)"
        for access_id in access_ids:
            cursor.execute(query_insert_user_access, (user_id, access_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": "Usuário associado ao access com sucesso."}), 201

    except Exception as e:
        logging.error(f"Erro ao associar access ao usuário: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@access_bp.route('/user/<int:user_id>', methods=['GET'])
def list_user_access(user_id):
    """
    Lista todos os acessos (`access`) e rotas (slugs e prefixos) associados a um usuário.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        query_user_access = """
            SELECT a.id, a.name, 
                   GROUP_CONCAT(ar.route_slug) AS route_slugs,
                   GROUP_CONCAT(ar.route_prefix) AS route_prefixes
            FROM user_access ua
            JOIN access a ON ua.access_id = a.id
            LEFT JOIN access_routes ar ON a.id = ar.access_id
            WHERE ua.user_id = %s
            GROUP BY a.id
        """
        cursor.execute(query_user_access, (user_id,))
        accesses = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "user_id": user_id,
            "accesses": accesses
        }), 200

    except Exception as e:
        logging.error(f"Erro ao listar acessos do usuário: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

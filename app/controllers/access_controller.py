import os
from flask import Blueprint, request, jsonify
from app.config.db_config import create_db_connection_mysql
from app.utils.decorators import token_required, admin_required, permission_required
import logging
from slugify import slugify 
import unidecode
import re

# Blueprint para acessos
access_bp = Blueprint('access', __name__, url_prefix='/access')

def generate_slug(name):
    """
    Gera um slug a partir de um nome.
    """
    if not name:
        raise ValueError("O campo 'name' não pode estar vazio para gerar um slug.")
    name = unidecode.unidecode(name)  # Remove acentos
    name = re.sub(r'[^a-zA-Z0-9\s]', '', name)  # Remove caracteres especiais
    return name.strip().replace(' ', '_').lower()

@access_bp.route('/create', methods=['POST'])
@token_required
@permission_required(route_prefix='/access')
def create_access(user_data=None):
    """
    Cria um novo `access` e associa rotas dinâmicas (`slugs`) e/ou fixas (`prefixos`).
    """
    try:
        # Validar se o payload foi enviado e se está no formato JSON
        if not request.is_json:
            return jsonify({
                "status": "error",
                "message": "O corpo da requisição deve estar no formato JSON e o cabeçalho Content-Type deve ser 'application/json'."
            }), 400

        # Capturar o JSON enviado na requisição
        data = request.get_json()
        if data is None:
            return jsonify({
                "status": "error",
                "message": "Nenhum dado foi enviado na requisição ou o formato está incorreto."
            }), 400

        # Obter os dados do payload
        name = data.get("name")
        route_slugs = data.get("route_slugs", [])  # Rotas dinâmicas
        route_prefixes = data.get("route_prefixes", [])  # Rotas fixas

        if not name or (not route_slugs and not route_prefixes):
            return jsonify({
                "status": "error",
                "message": "O campo 'name' e pelo menos uma rota (slug ou prefix) são obrigatórios."
            }), 400

        # Gerar o slug com base no nome
        slug = generate_slug(name)

        conn = create_db_connection_mysql()
        cursor = conn.cursor()

        # Inserir o novo access com o slug
        query_insert_access = "INSERT INTO access (name, slug) VALUES (%s, %s)"
        cursor.execute(query_insert_access, (name, slug))
        access_id = cursor.lastrowid

        # Associar rotas dinâmicas (slugs)
        query_insert_slug_access = "INSERT INTO access_routes (access_id, route_slug) VALUES (%s, %s)"
        for route_slug in route_slugs:
            cursor.execute(query_insert_slug_access, (access_id, route_slug))

        # Associar rotas fixas (prefixos)
        query_insert_prefix_access = "INSERT INTO access_routes (access_id, route_prefix) VALUES (%s, %s)"
        for prefix in route_prefixes:
            cursor.execute(query_insert_prefix_access, (access_id, prefix))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "Access criado com sucesso.",
            "access_id": access_id
        }), 201

    except Exception as e:
        logging.error(f"Erro ao criar access: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@access_bp.route('/list', methods=['GET'])
@token_required
@permission_required(route_prefix='/access')
def list_access(user_data):
    """
    Lista todos os `access` e suas rotas dinâmicas (`slugs`) e fixas (`prefixos`).
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        query_access = "SELECT id, name, slug, created_at FROM access"
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
                "slug": access['slug'],
                "created_at": access['created_at'],
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
@token_required
@permission_required(route_prefix='/access')
def assign_access_to_user(user_data):
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
@token_required
@permission_required(route_prefix='/access')
def list_user_access(user_data, user_id):
    """
    Lista todos os acessos (`access`) e rotas (slugs e prefixos) associados a um usuário.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        query_user_access = """
            SELECT a.id, a.name, a.slug, 
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
@access_bp.route('/<int:access_id>', methods=['GET'])
@token_required

@permission_required(route_prefix='/access')
def get_access_details(user_data, access_id):
    """
    Retorna os detalhes de um access específico com base no ID fornecido.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Obter o access pelo ID
        query_access = """
            SELECT id, name, slug, created_at
            FROM access
            WHERE id = %s
        """
        cursor.execute(query_access, (access_id,))
        access = cursor.fetchone()

        if not access:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Access não encontrado."}), 404

        # Obter slugs e prefixos associados
        query_routes = """
            SELECT route_slug, route_prefix
            FROM access_routes
            WHERE access_id = %s
        """
        cursor.execute(query_routes, (access_id,))
        routes = cursor.fetchall()

        cursor.close()
        conn.close()

        # Organizar os dados dos slugs e prefixos
        slugs = [route['route_slug'] for route in routes if route['route_slug']]
        prefixes = [route['route_prefix'] for route in routes if route['route_prefix']]

        # Montar a resposta
        response = {
            "id": access["id"],
            "name": access["name"],
            "slug": access["slug"],
            "created_at": access["created_at"],
            "route_slugs": slugs,
            "route_prefixes": prefixes
        }

        return jsonify({
            "status": "success",
            "access": response
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
@access_bp.route('/edit/<int:access_id>', methods=['PUT'])
@token_required
@permission_required(route_prefix='/access')
def edit_access(user_data, access_id):
    """
    Edita um `access` específico com base no ID fornecido.
    """
    try:
        data = request.json
        name = data.get("name")
        route_slugs = data.get("route_slugs", [])
        route_prefixes = data.get("route_prefixes", [])

        if not name and not route_slugs and not route_prefixes:
            return jsonify({
                "status": "error",
                "message": "Pelo menos um campo ('name', 'route_slugs' ou 'route_prefixes') deve ser informado para edição."
            }), 400

        conn = create_db_connection_mysql()
        cursor = conn.cursor()

        # Atualizar o nome do access, se fornecido
        if name:
            query_update_access = "UPDATE access SET name = %s WHERE id = %s"
            cursor.execute(query_update_access, (name, access_id))

        # Remover as associações antigas, se slugs ou prefixes forem fornecidos
        if route_slugs or route_prefixes:
            query_delete_routes = "DELETE FROM access_routes WHERE access_id = %s"
            cursor.execute(query_delete_routes, (access_id,))

        # Inserir as novas associações de slugs
        if route_slugs:
            query_insert_slugs = "INSERT INTO access_routes (access_id, route_slug) VALUES (%s, %s)"
            for slug in route_slugs:
                cursor.execute(query_insert_slugs, (access_id, slug))

        # Inserir as novas associações de prefixes
        if route_prefixes:
            query_insert_prefixes = "INSERT INTO access_routes (access_id, route_prefix) VALUES (%s, %s)"
            for prefix in route_prefixes:
                cursor.execute(query_insert_prefixes, (access_id, prefix))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "Access editado com sucesso."
        }), 200

    except Exception as e:
        logging.error(f"Erro ao editar access: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@access_bp.route('/user/remove', methods=['POST'])
@token_required
@permission_required(route_prefix='/access')
def remove_user_access(user_data):
    """
    Remove um ou mais `access` associados a um usuário.
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

        # Remover as associações
        query_delete_user_access = "DELETE FROM user_access WHERE user_id = %s AND access_id = %s"
        for access_id in access_ids:
            cursor.execute(query_delete_user_access, (user_id, access_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "Associações removidas com sucesso."
        }), 200

    except Exception as e:
        logging.error(f"Erro ao remover access do usuário: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@access_bp.route('/user/edit', methods=['PUT'])
@token_required
@permission_required(route_prefix='/access')
def edit_user_access(user_data):
    """
    Edita as associações de um usuário com seus acessos.
    """
    try:
        data = request.json
        user_id = data.get("user_id")
        new_access_ids = data.get("access_ids", [])

        if not user_id:
            return jsonify({
                "status": "error",
                "message": "O campo 'user_id' é obrigatório."
            }), 400

        conn = create_db_connection_mysql()
        cursor = conn.cursor()

        # Remover todas as associações atuais do usuário
        query_delete_user_access = "DELETE FROM user_access WHERE user_id = %s"
        cursor.execute(query_delete_user_access, (user_id,))

        # Adicionar as novas associações
        if new_access_ids:
            query_insert_user_access = "INSERT INTO user_access (user_id, access_id) VALUES (%s, %s)"
            for access_id in new_access_ids:
                cursor.execute(query_insert_user_access, (user_id, access_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "Associações atualizadas com sucesso."
        }), 200

    except Exception as e:
        logging.error(f"Erro ao editar acessos do usuário: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

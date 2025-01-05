import os
from flask import Blueprint, request, jsonify
import re
from app.utils.decorators import token_required, admin_required, permission_required
from app.config.db_config import create_db_connection_mysql
import cx_Oracle
import logging

system_bp = Blueprint('systems', __name__, url_prefix='/systems')

# Caminho base para as pastas de queries
BASE_QUERIES_PATH = os.path.join("app", "queries")

@system_bp.route('/create', methods=['POST'])
@token_required
@permission_required(route_prefix='/systems')
def create_system(user_data):
    """
    Cria um novo sistema com name, description e slug.
    """
    try:
        data = request.json
        name = data.get("name")
        description = data.get("description")

        # Validação dos campos obrigatórios
        if not name or not description:
            return jsonify({"status": "error", "message": "Os campos 'name' e 'description' são obrigatórios."}), 400

        # Gerar o slug a partir do name
        slug = re.sub(r'[^a-zA-Z0-9 ]', '', name).lower().replace(' ', '_')

        # Conexão com o banco
        conn = create_db_connection_mysql()
        cursor = conn.cursor()

        # Verificar se o slug já existe
        cursor.execute("SELECT id FROM systems WHERE slug = %s", (slug,))
        existing_system = cursor.fetchone()
        if existing_system:
            return jsonify({"status": "error", "message": f"Slug '{slug}' já existe."}), 400

        # Inserir o sistema no banco
        query = "INSERT INTO systems (name, description, slug) VALUES (%s, %s, %s)"
        cursor.execute(query, (name, description, slug))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": "Sistema criado com sucesso.", "slug": slug}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@system_bp.route('/list', methods=['GET'])
@token_required
@permission_required(route_prefix='/systems')
def list_systems(user_data):
    """
    Lista todos os systems com suporte à paginação.
    ---
    tags:
      - Systems
    parameters:
      - name: page
        in: query
        required: false
        type: integer
        description: Número da página para paginação. Default: 1
        example: 1
      - name: limit
        in: query
        required: false
        type: integer
        description: Número de registros por página. Default: 10
        example: 10
    responses:
      200:
        description: Lista de systems paginada.
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
            systems:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  name:
                    type: string
                    example: "System A"
                  description:
                    type: string
                    example: "Descrição do sistema"
    """
    try:
        # Obter os parâmetros de paginação
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
        offset = (page - 1) * limit

        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Query para buscar systems com paginação
        query = """
            SELECT id, name, description
            FROM systems
            ORDER BY id
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, (limit, offset))
        systems = cursor.fetchall()

        # Query para obter o número total de systems
        count_query = "SELECT COUNT(*) AS total FROM systems"
        cursor.execute(count_query)
        total_count = cursor.fetchone()["total"]

        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "page": page,
            "limit": limit,
            "total": total_count,
            "systems": systems
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
      
@system_bp.route('/profile/<int:id>', methods=['GET'])
@token_required
@permission_required(route_prefix='/systems')
def get_system_profile(user_data, id):
    """
    Retorna os detalhes de um sistema específico pelo seu ID.
    ---
    tags:
      - Systems
    parameters:
      - name: id
        in: path
        required: true
        type: integer
        description: ID do sistema a ser buscado.
        example: 1
    responses:
      200:
        description: Detalhes do sistema encontrado.
        schema:
          type: object
          properties:
            status:
              type: string
              example: "success"
            system:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                name:
                  type: string
                  example: "Sistema A"
                description:
                  type: string
                  example: "Descrição do sistema"
      404:
        description: Sistema não encontrado.
      500:
        description: Erro interno no servidor.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Buscar informações do sistema
        query_system = "SELECT id, name, description FROM systems WHERE id = %s"
        cursor.execute(query_system, (id,))
        system = cursor.fetchone()

        if not system:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Sistema não encontrado."}), 404

        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "system": system
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@system_bp.route('/edit/<int:system_id>', methods=['PUT'])
@token_required

@permission_required(route_prefix='/systems')
def edit_system(user_data, system_id):
    """
    Edita as informações de um sistema específico.
    """
    try:
        data = request.json
        fields_to_update = []
        values = []

        # Campos permitidos para edição
        editable_fields = ["name", "description", "is_active"]

        # Construir a query dinamicamente com base nos campos enviados
        for field in editable_fields:
            if field in data:
                fields_to_update.append(f"{field} = %s")
                values.append(data[field])

        if not fields_to_update:
            return jsonify({
                "status": "error",
                "message": "Nenhum campo válido para atualizar."
            }), 400

        values.append(system_id)

        conn = create_db_connection_mysql()
        cursor = conn.cursor()

        query = f"""
            UPDATE systems
            SET {', '.join(fields_to_update)}
            WHERE id = %s
        """
        cursor.execute(query, tuple(values))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "Sistema atualizado com sucesso."
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@system_bp.route('/<int:system_id>/routes', methods=['GET'])
@token_required
@permission_required(route_prefix='/systems')
def list_system_routes(user_data, system_id):
    """
    Lista todas as rotas associadas a um sistema pelo ID do sistema.
    ---
    tags:
      - Systems
    parameters:
      - name: system_id
        in: path
        required: true
        type: integer
        description: ID do sistema para buscar as rotas associadas.
        example: 1
    responses:
      200:
        description: Lista de rotas associadas ao sistema.
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            routes:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  name:
                    type: string
                    example: "Route Name"
                  slug:
                    type: string
                    example: "route-slug"
                  query:
                    type: string
                    example: "SELECT * FROM table"
                  created_at:
                    type: string
                    example: "2024-01-01 12:00:00"
      404:
        description: Sistema não encontrado ou sem rotas associadas.
      500:
        description: Erro interno no servidor.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Verificar se o sistema existe
        query_system = "SELECT id, name FROM systems WHERE id = %s"
        cursor.execute(query_system, (system_id,))
        system = cursor.fetchone()

        if not system:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Sistema não encontrado."}), 404

        # Obter as rotas associadas ao sistema
        query_routes = """
            SELECT r.id, r.name, r.slug, r.query, r.created_at
            FROM routes r
            JOIN route_systems rs ON r.id = rs.route_id
            WHERE rs.system_id = %s
        """
        cursor.execute(query_routes, (system_id,))
        routes = cursor.fetchall()

        cursor.close()
        conn.close()

        if not routes:
            return jsonify({"status": "error", "message": "Nenhuma rota associada ao sistema."}), 404

        return jsonify({
            "status": "success",
            "routes": routes
        }), 200

    except Exception as e:
        logging.error(f"Erro ao listar rotas do sistema {system_id}: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

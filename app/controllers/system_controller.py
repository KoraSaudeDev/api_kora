import os
from flask import Blueprint, request, jsonify
from app.utils.decorators import token_required, admin_required, permission_required
from app.config.db_config import create_db_connection_mysql
import cx_Oracle

system_bp = Blueprint('systems', __name__, url_prefix='/systems')

# Caminho base para as pastas de queries
BASE_QUERIES_PATH = os.path.join("app", "queries")

@system_bp.route('/create', methods=['POST'])
@token_required
@admin_required
@permission_required(route_prefix='/systems')
def create_system(user_data):
    """
    Cria um novo system associado a uma ou mais conexões.
    ---
    tags:
      - Systems
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - name
            - connection_ids
          properties:
            name:
              type: string
              example: "MV"
            connection_ids:
              type: array
              items:
                type: integer
              example: [1, 2]
    responses:
      201:
        description: System criado com sucesso e pasta gerada.
      400:
        description: Campos obrigatórios ausentes ou inválidos.
      500:
        description: Erro interno no servidor.
    """
    try:
        data = request.json
        name = data.get("name")
        connection_ids = data.get("connection_ids")

        # Validação dos campos
        if not name or not connection_ids:
            return jsonify({"status": "error", "message": "Os campos 'name' e 'connection_ids' são obrigatórios."}), 400

        if not isinstance(connection_ids, list) or not all(isinstance(i, int) for i in connection_ids):
            return jsonify({"status": "error", "message": "'connection_ids' deve ser uma lista de inteiros."}), 400

        # Conexão com o banco
        conn = create_db_connection_mysql()
        cursor = conn.cursor()

        # Inserir o novo System
        query_system = "INSERT INTO systems (name) VALUES (%s)"
        cursor.execute(query_system, (name,))
        system_id = cursor.lastrowid

        # Associar as conexões no system_connections
        for connection_id in connection_ids:
            query_association = "INSERT INTO system_connections (system_id, connection_id) VALUES (%s, %s)"
            cursor.execute(query_association, (system_id, connection_id))

        conn.commit()
        cursor.close()
        conn.close()

        # Criação da pasta para o novo sistema
        system_folder = os.path.join(BASE_QUERIES_PATH, name)
        if not os.path.exists(system_folder):
            os.makedirs(system_folder)
        
        return jsonify({
            "status": "success",
            "message": "System criado com sucesso e pasta gerada.",
            "system_id": system_id,
            "folder": system_folder
        }), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@system_bp.route('/list', methods=['GET'])
@token_required
@admin_required
@permission_required(route_prefix='/systems')
def list_systems(user_data):
    """
    Lista todos os systems e suas conexões associadas com suporte à paginação.
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
        description: Lista de systems e conexões, paginada.
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
                  connections:
                    type: array
                    items:
                      type: object
                      properties:
                        id:
                          type: integer
                          example: 1
                        name:
                          type: string
                          example: "Conexão de Produção"
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
            SELECT s.id AS system_id, s.name AS system_name, c.id AS connection_id, c.name AS connection_name
            FROM systems s
            LEFT JOIN system_connections sc ON s.id = sc.system_id
            LEFT JOIN connections c ON sc.connection_id = c.id
            ORDER BY s.id
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, (limit, offset))
        results = cursor.fetchall()

        # Query para obter o número total de systems
        count_query = "SELECT COUNT(DISTINCT s.id) AS total FROM systems s"
        cursor.execute(count_query)
        total_count = cursor.fetchone()["total"]

        systems = {}
        for row in results:
            system_id = row['system_id']
            if system_id not in systems:
                systems[system_id] = {
                    "id": system_id,
                    "name": row['system_name'],
                    "connections": []
                }
            if row['connection_id']:
                systems[system_id]["connections"].append({
                    "id": row['connection_id'],
                    "name": row['connection_name']
                })

        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "page": page,
            "limit": limit,
            "total": total_count,
            "systems": list(systems.values())
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@system_bp.route('/update-connections', methods=['POST'])
@token_required
@admin_required
@permission_required(route_prefix='/systems')
def update_system_connections(user_data):
    """
    Atualiza as conexões associadas a um sistema, removendo todas as existentes e adicionando as novas.
    ---
    tags:
      - Systems
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - system_id
            - connection_ids
          properties:
            system_id:
              type: integer
              example: 1
            connection_ids:
              type: array
              items:
                type: integer
              example: [2, 3]
              description: Lista de IDs de conexões para atualizar os vínculos.
    responses:
      200:
        description: Conexões atualizadas com sucesso.
      400:
        description: Campos obrigatórios ausentes ou inválidos.
      404:
        description: Sistema não encontrado.
      500:
        description: Erro interno no servidor.
    """
    try:
        data = request.json
        system_id = data.get("system_id")
        connection_ids = data.get("connection_ids")

        # Validação dos campos
        if not system_id or not connection_ids:
            return jsonify({"status": "error", "message": "Os campos 'system_id' e 'connection_ids' são obrigatórios."}), 400

        if not isinstance(connection_ids, list) or not all(isinstance(i, int) for i in connection_ids):
            return jsonify({"status": "error", "message": "'connection_ids' deve ser uma lista de inteiros."}), 400

        # Conexão com o banco
        conn = create_db_connection_mysql()
        cursor = conn.cursor()

        # Verificar se o sistema existe
        query_check_system = "SELECT id FROM systems WHERE id = %s"
        cursor.execute(query_check_system, (system_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Sistema não encontrado."}), 404

        # Remover todas as associações existentes para o sistema
        query_delete_all = "DELETE FROM system_connections WHERE system_id = %s"
        cursor.execute(query_delete_all, (system_id,))

        # Adicionar os novos relacionamentos
        query_insert = "INSERT INTO system_connections (system_id, connection_id) VALUES (%s, %s)"
        for connection_id in connection_ids:
            cursor.execute(query_insert, (system_id, connection_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "Conexões atualizadas com sucesso.",
            "system_id": system_id,
            "connection_ids": connection_ids
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@system_bp.route('/profile/<int:id>', methods=['GET'])
@token_required
@admin_required
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
                connections:
                  type: array
                  items:
                    type: object
                    properties:
                      id:
                        type: integer
                        example: 1
                      name:
                        type: string
                        example: "Conexão de Produção"
      404:
        description: Sistema não encontrado.
      500:
        description: Erro interno no servidor.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Buscar informações do sistema
        query_system = "SELECT id, name FROM systems WHERE id = %s"
        cursor.execute(query_system, (id,))
        system = cursor.fetchone()

        if not system:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Sistema não encontrado."}), 404

        # Buscar conexões associadas ao sistema
        query_connections = """
            SELECT c.id, c.name
            FROM connections c
            JOIN system_connections sc ON c.id = sc.connection_id
            WHERE sc.system_id = %s
        """
        cursor.execute(query_connections, (id,))
        connections = cursor.fetchall()

        cursor.close()
        conn.close()

        # Montar resposta
        return jsonify({
            "status": "success",
            "system": {
                "id": system["id"],
                "name": system["name"],
                "connections": connections
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

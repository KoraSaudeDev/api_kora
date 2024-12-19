import os
from flask import Blueprint, request, jsonify
from app.utils.decorators import token_required, admin_required
from app.config.db_config import create_db_connection_mysql
import cx_Oracle

system_bp = Blueprint('systems', __name__, url_prefix='/systems')

# Caminho base para as pastas de queries
BASE_QUERIES_PATH = os.path.join("app", "queries")

@system_bp.route('/create', methods=['POST'])
@token_required
@admin_required
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
def list_systems(user_data):
    """
    Lista todos os systems e suas conexões associadas.
    ---
    tags:
      - Systems
    responses:
      200:
        description: Lista de systems e conexões.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT s.id AS system_id, s.name AS system_name, c.id AS connection_id, c.name AS connection_name
            FROM systems s
            LEFT JOIN system_connections sc ON s.id = sc.system_id
            LEFT JOIN connections c ON sc.connection_id = c.id
            ORDER BY s.id
        """
        cursor.execute(query)
        results = cursor.fetchall()

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

        return jsonify({"status": "success", "systems": list(systems.values())}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@system_bp.route('/remove-connection', methods=['DELETE'])
@token_required
@admin_required
def remove_connection_from_system(user_data):
    """
    Remove uma conexão associada a um system.
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
            - connection_id
          properties:
            system_id:
              type: integer
              example: 1
            connection_id:
              type: integer
              example: 2
    responses:
      200:
        description: Conexão removida do system com sucesso.
      400:
        description: Campos obrigatórios ausentes ou inválidos.
      404:
        description: Associação não encontrada.
      500:
        description: Erro interno no servidor.
    """
    try:
        data = request.json
        system_id = data.get("system_id")
        connection_id = data.get("connection_id")

        # Validação dos campos
        if not system_id or not connection_id:
            return jsonify({"status": "error", "message": "Os campos 'system_id' e 'connection_id' são obrigatórios."}), 400

        # Conexão com o banco
        conn = create_db_connection_mysql()
        cursor = conn.cursor()

        # Verificar se a associação existe
        query_check = """
            SELECT id FROM system_connections
            WHERE system_id = %s AND connection_id = %s
        """
        cursor.execute(query_check, (system_id, connection_id))
        association = cursor.fetchone()

        if not association:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Associação não encontrada."}), 404

        # Remover a associação
        query_delete = """
            DELETE FROM system_connections
            WHERE system_id = %s AND connection_id = %s
        """
        cursor.execute(query_delete, (system_id, connection_id))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": "Conexão removida do system com sucesso."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@system_bp.route('/add-connections', methods=['POST'])
@token_required
@admin_required
def add_connections_to_system(user_data):
    """
    Adiciona novas conexões a um system existente.
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
    responses:
      200:
        description: Conexões adicionadas com sucesso.
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

        # Verificar se o system existe
        query_check_system = "SELECT id FROM systems WHERE id = %s"
        cursor.execute(query_check_system, (system_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "System não encontrado."}), 404

        # Inserir as novas associações
        added_connections = []
        for connection_id in connection_ids:
            try:
                query_insert = """
                    INSERT INTO system_connections (system_id, connection_id)
                    VALUES (%s, %s)
                """
                cursor.execute(query_insert, (system_id, connection_id))
                added_connections.append(connection_id)
            except Exception as e:
                # Ignorar erros de duplicação (conexões já existentes)
                if "Duplicate entry" not in str(e):
                    raise

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "Conexões adicionadas com sucesso.",
            "added_connections": added_connections
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

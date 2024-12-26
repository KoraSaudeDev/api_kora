from flask import Blueprint, request, jsonify
from app.utils.decorators import token_required, admin_required, permission_required
from app.utils.helpers import encrypt_password, decrypt_password
from app.config.db_config import create_db_connection_mysql

# Definição do Blueprint
connection_bp = Blueprint('connections', __name__, url_prefix='/connections')

@connection_bp.route('/create', methods=['POST'])
@token_required
@admin_required
@permission_required(route_prefix='/connections')
def create_connection(user_data):
    """
    Cria uma nova conexão de banco de dados.
    ---
    tags:
      - Conexões
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - name
            - db_type
            - host
            - port
            - username
            - password
            - database_name
          properties:
            name:
              type: string
              example: "cariacica"
            db_type:
              type: string
              enum: ["mysql", "oracle"]
              example: "oracle"
            host:
              type: string
              example: "ODASC1-REDEMERI"
            port:
              type: integer
              example: 1521
            username:
              type: string
              example: "admin"
            password:
              type: string
              example: "senha_segura"
            database_name:
              type: string
              example: "meu_banco"
            service_name:
              type: string
              example: "orcl"
              description: "Apenas para conexões Oracle."
    responses:
      201:
        description: Conexão criada com sucesso.
      400:
        description: Campos obrigatórios ausentes.
      500:
        description: Erro interno no servidor.
    """
    try:
        data = request.json
        name = data.get("name")
        db_type = data.get("db_type")
        host = data.get("host")
        port = data.get("port")
        username = data.get("username")
        password = data.get("password")
        database_name = data.get("database_name") or None
        service_name = data.get("service_name") or None

        # Validação de campos obrigatórios
        if not all([name, db_type, host, port, username, password]):
            return jsonify({"status": "error", "message": "Todos os campos obrigatórios devem ser preenchidos."}), 400

        if db_type == "oracle" and not service_name:
            return jsonify({"status": "error", "message": "O campo 'service_name' é obrigatório para conexões Oracle."}), 400

        # Criptografar a senha
        encrypted_password = encrypt_password(password)

        # Inserir no banco de dados
        conn = create_db_connection_mysql()
        cursor = conn.cursor()

        query = """
            INSERT INTO connections (name, db_type, host, port, username, password, database_name, service_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (name, db_type, host, port, username, encrypted_password, database_name, service_name))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": "Conexão criada com sucesso."}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@connection_bp.route('/list', methods=['GET'])
@token_required
@admin_required
@permission_required(route_prefix='/connections')
def list_connections(user_data):
    """
    Lista todas as conexões de banco de dados.
    ---
    tags:
      - Conexões
    responses:
      200:
        description: Lista de conexões armazenadas no sistema.
      500:
        description: Erro interno no servidor.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT id, name, db_type, host, port, username, database_name, service_name, created_at 
            FROM connections
        """
        cursor.execute(query)
        connections = cursor.fetchall()

        cursor.close()
        conn.close()

        # Retorna a lista de conexões (sem descriptografar a senha)
        return jsonify({"status": "success", "connections": connections}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@connection_bp.route('/delete/<int:connection_id>', methods=['DELETE'])
@token_required
@admin_required
@permission_required(route_prefix='/connections')
def delete_connection(user_data, connection_id):
    """
    Deleta uma conexão de banco de dados.
    ---
    tags:
      - Conexões
    parameters:
      - name: connection_id
        in: path
        required: true
        type: integer
        description: ID da conexão a ser deletada.
    responses:
      200:
        description: Conexão deletada com sucesso.
      404:
        description: Conexão não encontrada.
      500:
        description: Erro interno no servidor.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor()

        # Deleta a conexão pelo ID
        query = "DELETE FROM connections WHERE id = %s"
        cursor.execute(query, (connection_id,))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"status": "error", "message": "Conexão não encontrada."}), 404

        cursor.close()
        conn.close()
        return jsonify({"status": "success", "message": "Conexão deletada com sucesso."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

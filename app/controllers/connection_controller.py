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
    Cria uma nova conexão de banco de dados com suporte a SID e Service Name para Oracle.
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
              description: "Apenas para conexões Oracle usando Service Name."
            sid:
              type: string
              example: "orclsid"
              description: "Apenas para conexões Oracle usando SID."
    responses:
      201:
        description: Conexão criada com sucesso.
      400:
        description: Campos obrigatórios ausentes ou inválidos.
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
        sid = data.get("sid") or None

        # Validação de campos obrigatórios
        if not all([name, db_type, host, port, username, password]):
            return jsonify({"status": "error", "message": "Todos os campos obrigatórios devem ser preenchidos."}), 400

        if db_type == "oracle":
            if not service_name and not sid:
                return jsonify({"status": "error", "message": "Para conexões Oracle, 'service_name' ou 'sid' deve ser preenchido."}), 400
            if service_name and sid:
                return jsonify({"status": "error", "message": "Para conexões Oracle, preencha apenas 'service_name' ou 'sid', não ambos."}), 400

        # Criptografar a senha
        encrypted_password = encrypt_password(password)

        # Inserir no banco de dados
        conn = create_db_connection_mysql()
        cursor = conn.cursor()

        query = """
            INSERT INTO connections (name, db_type, host, port, username, password, database_name, service_name, sid)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (name, db_type, host, port, username, encrypted_password, database_name, service_name, sid))
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
    Lista todas as conexões de banco de dados com suporte à paginação.
    ---
    tags:
      - Conexões
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
        description: Lista de conexões armazenadas no sistema, paginada.
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
                  db_type:
                    type: string
                    example: "MySQL"
                  host:
                    type: string
                    example: "localhost"
                  port:
                    type: integer
                    example: 3306
                  username:
                    type: string
                    example: "admin"
                  database_name:
                    type: string
                    example: "my_database"
                  service_name:
                    type: string
                    example: "my_service"
                  created_at:
                    type: string
                    format: date-time
                    example: "2023-01-01T00:00:00Z"
      500:
        description: Erro interno no servidor.
    """
    try:
        # Obter os parâmetros de paginação
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
        offset = (page - 1) * limit

        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Query para buscar conexões com paginação
        query = """
            SELECT id, name, db_type, host, port, username, database_name, service_name, created_at 
            FROM connections
            ORDER BY id
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, (limit, offset))
        connections = cursor.fetchall()

        # Query para obter o número total de conexões
        count_query = "SELECT COUNT(*) AS total FROM connections"
        cursor.execute(count_query)
        total_count = cursor.fetchone()["total"]

        cursor.close()
        conn.close()

        # Retorna a lista de conexões com paginação
        return jsonify({
            "status": "success",
            "page": page,
            "limit": limit,
            "total": total_count,
            "connections": connections
        }), 200
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

@connection_bp.route('/list-simple', methods=['GET'])
@token_required
@admin_required
@permission_required(route_prefix='/connections')
def list_connections_simple(user_data):
    """
    Lista todas as conexões de banco de dados com os campos simplificados.
    ---
    tags:
      - Conexões
    responses:
      200:
        description: Lista simplificada de conexões armazenadas no sistema.
        schema:
          type: object
          properties:
            status:
              type: string
              example: "success"
            connections:
              type: array
              items:
                type: object
                properties:
                  value:
                    type: integer
                    example: 1
                  label:
                    type: string
                    example: "Conexão de Produção"
      500:
        description: Erro interno no servidor.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Query para buscar conexões simplificadas
        query = """
            SELECT id AS value, name AS label 
            FROM connections
            ORDER BY id
        """
        cursor.execute(query)
        connections = cursor.fetchall()

        cursor.close()
        conn.close()

        # Retorna a lista de conexões simplificadas
        return jsonify({
            "status": "success",
            "connections": connections
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
      
@connection_bp.route('/connections/<int:system_id>', methods=['GET'])
@token_required
@admin_required
@permission_required(route_prefix='/routes')
def list_connections_by_system(user_data, system_id):
    """
    Lista todas as conexões associadas a um sistema específico.
    ---
    tags:
      - Systems
    parameters:
      - name: system_id
        in: path
        required: true
        type: integer
        description: ID do sistema para buscar as conexões associadas.
        example: 1
    responses:
      200:
        description: Lista de conexões associadas ao sistema.
        schema:
          type: object
          properties:
            status:
              type: string
              example: "success"
            system_id:
              type: integer
              example: 1
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
                    example: "Conexão X"
                  host:
                    type: string
                    example: "localhost"
                  port:
                    type: integer
                    example: 3306
                  db_type:
                    type: string
                    example: "mysql"
      404:
        description: Sistema não encontrado ou sem conexões associadas.
      500:
        description: Erro interno no servidor.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Buscar os IDs das conexões associadas ao sistema
        query_connections = """
            SELECT connection_id
            FROM system_connections
            WHERE system_id = %s
        """
        cursor.execute(query_connections, (system_id,))
        connection_ids = [row['connection_id'] for row in cursor.fetchall()]

        if not connection_ids:
            return jsonify({"status": "error", "message": "Sistema não encontrado ou sem conexões associadas."}), 404

        # Buscar detalhes das conexões usando os IDs obtidos
        query_details = """
            SELECT id, name, host, port, db_type
            FROM connections
            WHERE id IN (%s)
        """ % ",".join(["%s"] * len(connection_ids))
        cursor.execute(query_details, connection_ids)
        connections = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "system_id": system_id,
            "connections": connections
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

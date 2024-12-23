import bcrypt
from flask import Blueprint, request, jsonify
from app.utils.decorators import token_required, admin_required, permission_required
from app.config.db_config import create_db_connection_mysql

user_bp = Blueprint('users', __name__, url_prefix='/users')

def validate_json_fields(data, required_fields):
    """
    Valida se os campos obrigatórios estão presentes no JSON.
    """
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return False, f"Campos ausentes: {', '.join(missing_fields)}"
    return True, None

@user_bp.route('/create', methods=['POST'])
@token_required
@admin_required
@permission_required(route_prefix='/users')
def create_user(user_data):
    """
    Cria um novo usuário no sistema.
    ---
    tags:
      - Users
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
            - is_admin
          properties:
            username:
              type: string
              example: "username"
            password:
              type: string
              example: "senha"
            is_admin:
              type: boolean
              example: true
    responses:
      201:
        description: Usuário criado com sucesso.
        schema:
          type: object
          properties:
            status:
              type: string
              example: "success"
            user_id:
              type: integer
              example: 1
      400:
        description: Campos obrigatórios ausentes ou inválidos.
      500:
        description: Erro interno no servidor.
    """
    try:
        data = request.json
        is_valid, message = validate_json_fields(data, ["username", "password", "is_admin"])
        if not is_valid:
            return jsonify({"status": "error", "message": message}), 400

        username = data["username"]
        password = data["password"]
        is_admin = data["is_admin"]

        # Hash da senha
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        with create_db_connection_mysql() as conn:
            with conn.cursor() as cursor:
                # Inserir o novo usuário
                cursor.execute(
                    "INSERT INTO users (username, password_hash, is_admin, is_active) VALUES (%s, %s, %s, %s)",
                    (username, password_hash, is_admin, True)
                )
                # Obter o ID do usuário recém-criado
                user_id = cursor.lastrowid
            conn.commit()

        return jsonify({"status": "success", "message": "Usuário criado com sucesso", "user_id": user_id}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@user_bp.route('/edit/<int:user_id>', methods=['PUT'])
@token_required
@admin_required
@permission_required(route_prefix='/users')
def edit_user(user_data, user_id):
    try:
        data = request.json
        updates = []
        params = []

        if "username" in data:
            updates.append("username = %s")
            params.append(data["username"])
        if "password" in data:
            password_hash = bcrypt.hashpw(data["password"].encode('utf-8'), bcrypt.gensalt())
            updates.append("password_hash = %s")
            params.append(password_hash)
        if "is_admin" in data:
            updates.append("is_admin = %s")
            params.append(data["is_admin"])

        if not updates:
            return jsonify({"status": "error", "message": "Nenhum dado para atualizar"}), 400

        params.append(user_id)
        with create_db_connection_mysql() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = %s", tuple(params))
            conn.commit()

        return jsonify({"status": "success", "message": "Usuário atualizado com sucesso"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@user_bp.route('/delete/<int:user_id>', methods=['DELETE'])
@token_required
@admin_required
@permission_required(route_prefix='/users')
def delete_user(user_data, user_id):
    """
    Realiza o soft delete de um usuário e remove os vínculos com as rotas.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor()

        # Verificar se o usuário existe
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"status": "error", "message": "Usuário não encontrado."}), 404

        # Realizar o soft delete
        query_soft_delete = "UPDATE users SET is_active = FALSE WHERE id = %s"
        cursor.execute(query_soft_delete, (user_id,))

        # Remover vínculos com as rotas
        query_remove_routes = "DELETE FROM user_routes WHERE user_id = %s"
        cursor.execute(query_remove_routes, (user_id,))

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": "Usuário desativado e vínculos removidos com sucesso."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@user_bp.route('/restore/<int:user_id>', methods=['PUT'])
@token_required
@admin_required
@permission_required(route_prefix='/users')
def restore_user(user_data, user_id):
    """
    Restaura um usuário desativado (soft delete).
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor()

        # Verificar se o usuário existe
        cursor.execute("SELECT * FROM users WHERE id = %s AND is_active = FALSE", (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"status": "error", "message": "Usuário não encontrado ou já ativo."}), 404

        # Restaurar o usuário
        query_restore = "UPDATE users SET is_active = TRUE WHERE id = %s"
        cursor.execute(query_restore, (user_id,))

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": "Usuário restaurado com sucesso."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@user_bp.route('/change-password/<int:user_id>', methods=['PUT'])
@token_required
@admin_required
@permission_required(route_prefix='/users')
def change_user_password(user_data, user_id):
    try:
        data = request.json
        new_password = data.get('new_password')

        if not new_password:
            return jsonify({"status": "error", "message": "Nova senha é obrigatória"}), 400

        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        target_user = cursor.fetchone()

        if not target_user:
            return jsonify({"status": "error", "message": "Usuário alvo não encontrado"}), 404

        if user_data['id'] != user_id and target_user['is_admin']:
            return jsonify({"status": "error", "message": "Não é permitido alterar a senha de outro administrador"}), 403

        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (password_hash, user_id))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": "Senha alterada com sucesso"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@user_bp.route('/routes/assign', methods=['POST'])
@token_required
@admin_required
def assign_routes(user_data):
    """
    Associa rotas a um usuário.
    ---
    tags:
      - Users
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - user_id
            - route_ids
          properties:
            user_id:
              type: integer
              example: 1
            route_ids:
              type: array
              items:
                type: integer
              example: [1, 2, 3]
    responses:
      201:
        description: Rotas associadas com sucesso.
      400:
        description: Campos obrigatórios ausentes ou inválidos.
      500:
        description: Erro interno no servidor.
    """
    try:
        data = request.json
        user_id = data.get("user_id")
        route_ids = data.get("route_ids")

        if not user_id or not route_ids:
            return jsonify({"status": "error", "message": "Campos 'user_id' e 'route_ids' são obrigatórios."}), 400

        conn = create_db_connection_mysql()
        cursor = conn.cursor()

        for route_id in route_ids:
            try:
                query = """
                    INSERT INTO user_routes (user_id, route_id)
                    VALUES (%s, %s)
                """
                cursor.execute(query, (user_id, route_id))
            except Exception as e:
                if "Duplicate entry" in str(e):
                    continue  # Ignora duplicatas

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": "Rotas associadas com sucesso."}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@user_bp.route('/routes/remove', methods=['DELETE'])
@token_required
@admin_required
def remove_routes(user_data):
    """
    Remove rotas de um usuário.
    ---
    tags:
      - Users
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - user_id
            - route_ids
          properties:
            user_id:
              type: integer
              example: 1
            route_ids:
              type: array
              items:
                type: integer
              example: [1, 2]
    responses:
      200:
        description: Rotas removidas com sucesso.
      400:
        description: Campos obrigatórios ausentes ou inválidos.
      500:
        description: Erro interno no servidor.
    """
    try:
        data = request.json
        user_id = data.get("user_id")
        route_ids = data.get("route_ids")

        if not user_id or not route_ids:
            return jsonify({"status": "error", "message": "Campos 'user_id' e 'route_ids' são obrigatórios."}), 400

        conn = create_db_connection_mysql()
        cursor = conn.cursor()

        for route_id in route_ids:
            query = """
                DELETE FROM user_routes
                WHERE user_id = %s AND route_id = %s
            """
            cursor.execute(query, (user_id, route_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": "Rotas removidas com sucesso."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@user_bp.route('/routes/update', methods=['PUT'])
@token_required
@admin_required
def update_routes(user_data):
    """
    Atualiza as rotas de um usuário.
    ---
    tags:
      - Users
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - user_id
            - new_route_ids
          properties:
            user_id:
              type: integer
              example: 1
            new_route_ids:
              type: array
              items:
                type: integer
              example: [2, 3]
    responses:
      200:
        description: Rotas atualizadas com sucesso.
      400:
        description: Campos obrigatórios ausentes ou inválidos.
      500:
        description: Erro interno no servidor.
    """
    try:
        data = request.json
        user_id = data.get("user_id")
        new_route_ids = data.get("new_route_ids")

        if not user_id or not new_route_ids:
            return jsonify({"status": "error", "message": "Campos 'user_id' e 'new_route_ids' são obrigatórios."}), 400

        conn = create_db_connection_mysql()
        cursor = conn.cursor()

        # Remover todas as rotas existentes
        query_delete = "DELETE FROM user_routes WHERE user_id = %s"
        cursor.execute(query_delete, (user_id,))

        # Inserir as novas rotas
        for route_id in new_route_ids:
            query_insert = """
                INSERT INTO user_routes (user_id, route_id)
                VALUES (%s, %s)
            """
            cursor.execute(query_insert, (user_id, route_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": "Rotas atualizadas com sucesso."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@user_bp.route('/list', methods=['GET'])
@token_required
@admin_required
def list_users_with_routes(user_data):
    """
    Lista todos os usuários, suas rotas associadas e se são administradores.
    ---
    tags:
      - Users
    responses:
      200:
        description: Lista de usuários com suas rotas e status de administrador.
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 1
              username:
                type: string
                example: "john_doe"
              is_admin:
                type: boolean
                example: true
              routes:
                type: array
                items:
                  type: string
                example: ["/home", "/settings", "/dashboard"]
      500:
        description: Erro interno no servidor.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Query para buscar todos os usuários, suas rotas e status de administrador
        query = """
            SELECT 
                u.id AS user_id, 
                u.username, 
                u.is_admin,
                GROUP_CONCAT(r.route_prefix) AS routes
            FROM users u
            LEFT JOIN user_routes ur ON u.id = ur.user_id
            LEFT JOIN routes r ON ur.route_id = r.id
            GROUP BY u.id
            ORDER BY u.username
        """
        cursor.execute(query)
        users = cursor.fetchall()

        # Formatando a resposta
        response = []
        for user in users:
            response.append({
                "id": user["user_id"],
                "username": user["username"],
                "is_admin": bool(user["is_admin"]),
                "routes": user["routes"].split(",") if user["routes"] else []
            })

        cursor.close()
        conn.close()

        return jsonify({"status": "success", "users": response}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@user_bp.route('/me', methods=['GET'])
@token_required
def get_user_profile(user_data):
    """
    Retorna os dados do usuário ativo e suas rotas associadas.
    ---
    tags:
      - Users
    responses:
      200:
        description: Dados do usuário ativo.
        schema:
          type: object
          properties:
            id:
              type: integer
              example: 1
            username:
              type: string
              example: "john_doe"
            is_admin:
              type: boolean
              example: true
            routes:
              type: array
              items:
                type: string
              example: ["/home", "/settings", "/dashboard"]
      404:
        description: Usuário não encontrado.
        schema:
          type: object
          properties:
            status:
              type: string
              example: "error"
            message:
              type: string
              example: "Usuário não encontrado."
      500:
        description: Erro interno no servidor.
    """
    try:
        user_id = user_data['id']  # Obtém o ID do usuário ativo a partir do token

        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Obter informações do usuário ativo
        user_query = """
            SELECT id, username, is_admin
            FROM users
            WHERE id = %s AND is_active = 1
        """
        cursor.execute(user_query, (user_id,))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Usuário não encontrado."}), 404

        # Obter as rotas associadas ao usuário
        routes_query = """
            SELECT r.route_prefix
            FROM routes r
            JOIN user_routes ur ON r.id = ur.route_id
            WHERE ur.user_id = %s
        """
        cursor.execute(routes_query, (user_id,))
        routes = [row['route_prefix'] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        # Retornar os dados do usuário com as rotas associadas
        return jsonify({
            "status": "success",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "is_admin": bool(user["is_admin"]),
                "routes": routes
            }
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
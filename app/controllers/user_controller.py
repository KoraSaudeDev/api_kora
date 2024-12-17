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
    try:
        data = request.json
        is_valid, message = validate_json_fields(data, ["username", "password"])
        if not is_valid:
            return jsonify({"status": "error", "message": message}), 400

        username = data["username"]
        password_hash = bcrypt.hashpw(data["password"].encode('utf-8'), bcrypt.gensalt())

        with create_db_connection_mysql() as conn:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", 
                               (username, password_hash))
            conn.commit()

        return jsonify({"status": "success", "message": "Usuário criado com sucesso"}), 201
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

    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": "Usuário excluído com sucesso"}), 200
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

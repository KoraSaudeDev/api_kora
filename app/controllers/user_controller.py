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
        promote_to_admin = False

        # Verifica se o username será atualizado
        if "username" in data:
            updates.append("username = %s")
            params.append(data["username"])

        # Verifica se a senha será atualizada
        if "password" in data:
            password_hash = bcrypt.hashpw(data["password"].encode('utf-8'), bcrypt.gensalt())
            updates.append("password_hash = %s")
            params.append(password_hash)

        # Verifica se a permissão de administrador será alterada
        if "is_admin" in data:
            updates.append("is_admin = %s")
            params.append(data["is_admin"])

            # Checar se o usuário está sendo promovido a admin
            conn = create_db_connection_mysql()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT is_admin FROM users WHERE id = %s", (user_id,))
            current_user = cursor.fetchone()
            if not current_user:
                cursor.close()
                conn.close()
                return jsonify({"status": "error", "message": "Usuário não encontrado"}), 404

            if not current_user["is_admin"] and data["is_admin"]:
                promote_to_admin = True  # Marca que está promovendo para admin
            
            cursor.close()
            conn.close()

        if not updates:
            return jsonify({"status": "error", "message": "Nenhum dado para atualizar"}), 400

        # Atualizar os dados do usuário
        params.append(user_id)
        with create_db_connection_mysql() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = %s", tuple(params))
                conn.commit()

                # Se o usuário foi promovido a admin, remover suas rotas
                if promote_to_admin:
                    cursor.execute("DELETE FROM user_routes WHERE user_id = %s", (user_id,))
                    conn.commit()

        # Retornar o ID do usuário atualizado
        return jsonify({"status": "success", "message": "Usuário atualizado com sucesso", "user_id": user_id}), 200

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
    Remove todas as rotas de um usuário.
    ---
    tags:
      - Users
    parameters:
      - name: user_id
        in: query
        required: true
        type: integer
        description: ID do usuário cujas rotas serão removidas.
        example: 1
    responses:
      200:
        description: Todas as rotas removidas com sucesso.
      400:
        description: Campo 'user_id' ausente.
      500:
        description: Erro interno no servidor.
    """
    try:
        # Obter o ID do usuário da query string
        user_id = request.args.get("user_id", type=int)

        if not user_id:
            return jsonify({"status": "error", "message": "Campo 'user_id' é obrigatório."}), 400

        conn = create_db_connection_mysql()
        cursor = conn.cursor()

        # Remover todos os vínculos de rotas para o usuário
        query = "DELETE FROM user_routes WHERE user_id = %s"
        cursor.execute(query, (user_id,))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": f"Todas as rotas foram removidas para o usuário com ID {user_id}."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@user_bp.route('/routes/update', methods=['PUT'])
@token_required
@admin_required
def update_routes(user_data):
    """
    Atualiza as rotas de um usuário, removendo as rotas existentes e associando as novas fornecidas.
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
              example: [3, 4]
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
        route_ids = data.get("route_ids")

        if not user_id or not isinstance(route_ids, list):
            return jsonify({"status": "error", "message": "Campos 'user_id' e 'route_ids' são obrigatórios."}), 400

        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Verificar se as rotas fornecidas existem na tabela `routes`
        query_existing_routes = "SELECT id FROM routes WHERE id IN (%s)" % ",".join(["%s"] * len(route_ids))
        cursor.execute(query_existing_routes, tuple(route_ids))
        valid_route_ids = {row["id"] for row in cursor.fetchall()}

        # Identificar rotas inválidas
        invalid_route_ids = set(route_ids) - valid_route_ids
        if invalid_route_ids:
            return jsonify({
                "status": "error",
                "message": f"As seguintes rotas não existem: {list(invalid_route_ids)}"
            }), 400

        # Remover todas as rotas existentes associadas ao usuário
        query_delete_existing_routes = "DELETE FROM user_routes WHERE user_id = %s"
        cursor.execute(query_delete_existing_routes, (user_id,))

        # Inserir as novas rotas associadas ao usuário
        for route_id in valid_route_ids:
            query_insert_route = "INSERT INTO user_routes (user_id, route_id) VALUES (%s, %s)"
            cursor.execute(query_insert_route, (user_id, route_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "Rotas atualizadas com sucesso.",
            "added_routes": list(valid_route_ids),
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@user_bp.route('/list', methods=['GET'])
@token_required
@admin_required
def list_users_with_routes(user_data):
    """
    Lista todos os usuários, suas rotas associadas, status de administrador e ativo/inativo, com suporte à paginação.
    ---
    tags:
      - Users
    parameters:
      - name: page
        in: query
        required: false
        type: integer
        description: Número da página para a paginação. Default: 1
        example: 1
      - name: limit
        in: query
        required: false
        type: integer
        description: Número de registros por página. Default: 10
        example: 10
    responses:
      200:
        description: Lista de usuários com suas rotas, status de administrador e ativo/inativo.
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
              is_active:
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
        # Obter os parâmetros de paginação
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
        offset = (page - 1) * limit

        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Query para buscar os usuários com paginação
        query = f"""
            SELECT 
                u.id AS user_id, 
                u.username, 
                u.is_admin,
                u.is_active,
                GROUP_CONCAT(r.route_prefix) AS routes
            FROM users u
            LEFT JOIN user_routes ur ON u.id = ur.user_id
            LEFT JOIN routes r ON ur.route_id = r.id
            GROUP BY u.id
            ORDER BY u.username
            LIMIT {limit} OFFSET {offset}
        """
        cursor.execute(query)
        users = cursor.fetchall()

        # Query para obter a contagem total de usuários
        count_query = "SELECT COUNT(*) AS total FROM users"
        cursor.execute(count_query)
        total_count = cursor.fetchone()["total"]

        # Formatando a resposta
        response = []
        for user in users:
            response.append({
                "id": user["user_id"],
                "username": user["username"],
                "is_admin": bool(user["is_admin"]),
                "is_active": bool(user["is_active"]),
                "routes": user["routes"].split(",") if user["routes"] else []
            })

        cursor.close()
        conn.close()

        # Retornar a resposta com paginação
        return jsonify({
            "status": "success",
            "page": page,
            "limit": limit,
            "total": total_count,
            "users": response
        }), 200

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
      
      
@user_bp.route('/profile/<int:user_id>', methods=['GET'])
@token_required
@admin_required
def get_user_profile_by_id(user_data, user_id):
    """
    Retorna o perfil de um usuário específico com base no ID fornecido, incluindo as rotas associadas.
    ---
    tags:
      - Users
    parameters:
      - name: user_id
        in: path
        required: true
        type: integer
        description: ID do usuário a ser buscado.
        example: 1
    responses:
      200:
        description: Perfil do usuário encontrado.
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
            is_active:
              type: boolean
              example: true
            routes:
              type: array
              items:
                type: integer
              example: [1, 2, 3]
      404:
        description: Usuário não encontrado.
      500:
        description: Erro interno no servidor.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Buscar dados do usuário
        query_user = "SELECT id, username, is_admin, is_active FROM users WHERE id = %s"
        cursor.execute(query_user, (user_id,))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Usuário não encontrado."}), 404

        # Buscar IDs das rotas associadas ao usuário
        query_routes = """
            SELECT ur.route_id
            FROM user_routes ur
            WHERE ur.user_id = %s
        """
        cursor.execute(query_routes, (user_id,))
        routes = [row["route_id"] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        # Montar a resposta
        return jsonify({
            "status": "success",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "is_admin": bool(user["is_admin"]),
                "is_active": bool(user["is_active"]),
                "routes": routes
            }
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

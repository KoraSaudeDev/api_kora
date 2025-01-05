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

@permission_required(route_prefix='/users')
def edit_user(user_data, user_id):
    """
    Edita as informações de um usuário, incluindo rotas associadas caso seja promovido a admin.
    """
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

                # Se o usuário foi promovido a admin, remover associações de access
                if promote_to_admin:
                    cursor.execute("DELETE FROM user_access WHERE user_id = %s", (user_id,))
                    conn.commit()

        # Retornar o ID do usuário atualizado
        return jsonify({"status": "success", "message": "Usuário atualizado com sucesso", "user_id": user_id}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@user_bp.route('/delete/<int:user_id>', methods=['DELETE'])
@token_required

@permission_required(route_prefix='/users')
def delete_user(user_data, user_id):
    """
    Realiza o soft delete de um usuário e remove os vínculos com os acessos.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Verificar se o usuário existe
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"status": "error", "message": "Usuário não encontrado."}), 404

        # Realizar o soft delete
        query_soft_delete = "UPDATE users SET is_active = FALSE WHERE id = %s"
        cursor.execute(query_soft_delete, (user_id,))

        # Remover vínculos com os acessos
        query_remove_access = "DELETE FROM user_access WHERE user_id = %s"
        cursor.execute(query_remove_access, (user_id,))

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": "Usuário desativado e vínculos removidos com sucesso."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@user_bp.route('/restore/<int:user_id>', methods=['PUT'])
@token_required

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

@user_bp.route('/list', methods=['GET'])
@token_required

@permission_required(route_prefix='/users')
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
                GROUP_CONCAT(DISTINCT ar.route_slug) AS route_slugs,
                GROUP_CONCAT(DISTINCT ar.route_prefix) AS route_prefixes
            FROM users u
            LEFT JOIN user_access ua ON u.id = ua.user_id
            LEFT JOIN access a ON ua.access_id = a.id
            LEFT JOIN access_routes ar ON a.id = ar.access_id
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
                "routes": {
                    "slugs": user["route_slugs"].split(",") if user["route_slugs"] else [],
                    "prefixes": user["route_prefixes"].split(",") if user["route_prefixes"] else []
                }
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
@permission_required(route_prefix='/users')
def get_user_profile(user_data):
    """
    Retorna os dados do usuário ativo e suas permissões (rotas e acessos).
    """
    try:
        user_id = user_data['id']  # Obtém o ID do usuário ativo a partir do token

        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Obter informações do usuário ativo
        user_query = """
            SELECT id, username, is_admin, is_active
            FROM users
            WHERE id = %s
        """
        cursor.execute(user_query, (user_id,))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Usuário não encontrado."}), 404

        # Obter acessos associados ao usuário
        access_query = """
            SELECT a.id AS access_id, a.name AS access_name,
                   GROUP_CONCAT(DISTINCT ar.route_slug) AS route_slugs,
                   GROUP_CONCAT(DISTINCT ar.route_prefix) AS route_prefixes
            FROM user_access ua
            JOIN access a ON ua.access_id = a.id
            LEFT JOIN access_routes ar ON ar.access_id = a.id
            WHERE ua.user_id = %s
            GROUP BY a.id
        """
        cursor.execute(access_query, (user_id,))
        accesses = cursor.fetchall()

        # Organizar rotas em uma única lista, removendo duplicações
        routes = {
            "slugs": list(set([slug for access in accesses if access["route_slugs"] for slug in access["route_slugs"].split(",")])),
            "prefixes": list(set([prefix for access in accesses if access["route_prefixes"] for prefix in access["route_prefixes"].split(",")]))
        }

        cursor.close()
        conn.close()

        # Retornar os dados do usuário com os acessos e permissões
        return jsonify({
            "status": "success",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "is_admin": bool(user["is_admin"]),
                "is_active": bool(user["is_active"]),
                "accesses": accesses,
                "routes": routes
            }
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@user_bp.route('/profile/<int:user_id>', methods=['GET'])
@token_required

@permission_required(route_prefix='/users')
def get_user_profile_by_id(user_data, user_id):
    """
    Retorna o perfil de um usuário específico, incluindo seus acessos e permissões.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Buscar dados do usuário
        query_user = """
            SELECT id, username, is_admin, is_active
            FROM users
            WHERE id = %s
        """
        cursor.execute(query_user, (user_id,))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Usuário não encontrado."}), 404

        # Obter acessos associados ao usuário
        access_query = """
            SELECT a.id AS access_id, a.name AS access_name,
                   GROUP_CONCAT(DISTINCT ar.route_slug) AS route_slugs,
                   GROUP_CONCAT(DISTINCT ar.route_prefix) AS route_prefixes
            FROM user_access ua
            JOIN access a ON ua.access_id = a.id
            LEFT JOIN access_routes ar ON ar.access_id = a.id
            WHERE ua.user_id = %s
            GROUP BY a.id
        """
        cursor.execute(access_query, (user_id,))
        accesses = cursor.fetchall()

        # Organizar rotas em uma única lista
        routes = {
            "slugs": [],
            "prefixes": []
        }
        for access in accesses:
            if access["route_slugs"]:
                routes["slugs"].extend(access["route_slugs"].split(","))
            if access["route_prefixes"]:
                routes["prefixes"].extend(access["route_prefixes"].split(","))

        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "is_admin": bool(user["is_admin"]),
                "is_active": bool(user["is_active"]),
                "accesses": accesses,
                "routes": routes
            }
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

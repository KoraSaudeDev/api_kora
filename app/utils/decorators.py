from functools import wraps
from flask import request, jsonify
import jwt
from app.config.env import SECRET_KEY
from app.utils.helpers import check_user_permission
from app.config.db_config import create_db_connection_mysql 

def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = None

        # Verifica se o token está no cabeçalho Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith("Bearer "):
                token = auth_header.split("Bearer ")[1]

        if not token:
            return jsonify({"status": "error", "message": "Token é necessário"}), 401

        try:
            # Decodifica o token JWT
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"status": "error", "message": "Token expirado"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"status": "error", "message": "Token inválido"}), 401

        return f(user_data=data, *args, **kwargs)
    return decorator

def admin_required(f):
    @wraps(f)
    def decorator(user_data=None, *args, **kwargs):
        if not user_data or not user_data.get('is_admin'):
            return jsonify({"status": "error", "message": "Acesso negado: apenas administradores podem realizar esta ação"}), 403

        return f(user_data=user_data, *args, **kwargs)
    return decorator

def permission_required(route_prefix):
    """
    Decorator para verificar permissões do usuário com base no prefixo da rota e, se necessário, no slug.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_data = kwargs.get("user_data")

            # Caso o usuário seja administrador, pula a verificação
            if user_data.get("is_admin"):
                return f(*args, **kwargs)

            user_id = user_data.get("id")
            if not user_id:
                return jsonify({"status": "error", "message": "Usuário não autenticado"}), 403

            try:
                conn = create_db_connection_mysql()
                cursor = conn.cursor(dictionary=True)

                # Verifica se o usuário tem acesso ao prefixo da rota
                query_prefix_access = """
                    SELECT 1
                    FROM user_access ua
                    JOIN access_routes ar ON ua.access_id = ar.access_id
                    WHERE ua.user_id = %s AND ar.route_prefix = %s
                """
                cursor.execute(query_prefix_access, (user_id, route_prefix))
                has_prefix_access = cursor.fetchone()

                # Verificação para slug específico
                if route_prefix.startswith("/routes/execute") and "slug" in kwargs:
                    slug = kwargs["slug"]
                    query_slug_access = """
                        SELECT 1
                        FROM user_access ua
                        JOIN access_routes ar ON ua.access_id = ar.access_id
                        WHERE ua.user_id = %s AND ar.route_slug = %s
                    """
                    cursor.execute(query_slug_access, (user_id, slug))
                    has_slug_access = cursor.fetchone()

                    if has_slug_access:
                        cursor.close()
                        conn.close()
                        return f(*args, **kwargs)

                # Se o usuário não tem permissão nem pelo prefixo nem pelo slug, negar acesso
                if not has_prefix_access:
                    cursor.close()
                    conn.close()
                    return jsonify({"status": "error", "message": "Permissão negada"}), 403

                cursor.close()
                conn.close()
                return f(*args, **kwargs)

            except Exception as e:
                return jsonify({"status": "error", "message": f"Erro ao verificar permissões: {str(e)}"}), 500

        return decorated_function
    return decorator

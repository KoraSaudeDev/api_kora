from functools import wraps
from flask import request, jsonify
import jwt
from app.config.env import SECRET_KEY
from app.utils.helpers import check_user_permission
from app.config.db_config import create_db_connection_mysql 
from flask import request, jsonify, g
import logging

def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith("Bearer "):
            token = auth_header.split("Bearer ")[1]

        if not token:
            return jsonify({"status": "error", "message": "Token é necessário"}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"status": "error", "message": "Token expirado"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"status": "error", "message": "Token inválido"}), 401

        # guarda em g, para o after_request também usar
        g.user_data = data
        # injeta no kwargs para as views continuarem recebendo user_data
        kwargs['user_data'] = data

        return f(*args, **kwargs)
    return decorator

def admin_required(f):
    @wraps(f)
    def decorator(user_data=None, *args, **kwargs):
        if not user_data or not user_data.get('is_admin'):
            return jsonify({"status": "error", "message": "Acesso negado: apenas administradores podem realizar esta ação"}), 403

        return f(user_data=user_data, *args, **kwargs)
    return decorator

def permission_required(route_prefix=None):
    """
    Decorator para verificar permissões do usuário com base no prefixo da rota.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(user_data=None, *args, **kwargs):
            user_id = user_data.get("id")
            is_admin = user_data.get("is_admin")

            # Permitir acesso completo para administradores
            if is_admin:
                return f(user_data=user_data, *args, **kwargs)

            try:
                conn = create_db_connection_mysql()
                cursor = conn.cursor(dictionary=True)

                # Verificar permissões do usuário
                query = """
                    SELECT DISTINCT ar.route_prefix, ar.route_slug
                    FROM user_access ua
                    JOIN access_routes ar ON ua.access_id = ar.access_id
                    WHERE ua.user_id = %s
                """
                cursor.execute(query, (user_id,))
                permissions = cursor.fetchall()

                # Verificar se o usuário possui acesso ao route_prefix ou route_slug
                allowed_prefixes = [perm['route_prefix'] for perm in permissions if perm['route_prefix']]
                allowed_slugs = [perm['route_slug'] for perm in permissions if perm['route_slug']]

                cursor.close()
                conn.close()

                # Validação do route_prefix ou route_slug
                if route_prefix and route_prefix not in allowed_prefixes:
                    if kwargs.get('slug') not in allowed_slugs:
                        return jsonify({"status": "error", "message": "Permissão negada"}), 403

                return f(user_data=user_data, *args, **kwargs)

            except Exception as e:
                logging.error(f"Erro ao verificar permissões: {e}")
                return jsonify({"status": "error", "message": f"Erro ao verificar permissões: {e}"}), 500

        return decorated_function
    return decorator

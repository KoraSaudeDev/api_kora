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
    Decorator para verificar permissões do usuário com base no prefixo da rota.
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
                cursor = conn.cursor()

                # Verifica se o usuário tem permissão para acessar a rota
                query = """
                    SELECT r.route_prefix
                    FROM routes r
                    INNER JOIN user_routes ur ON r.id = ur.route_id
                    WHERE ur.user_id = %s AND r.route_prefix = %s
                """
                cursor.execute(query, (user_id, route_prefix))
                result = cursor.fetchone()

                cursor.close()
                conn.close()

                if not result:
                    return jsonify({"status": "error", "message": "Permissão negada"}), 403

                return f(*args, **kwargs)

            except Exception as e:
                return jsonify({"status": "error", "message": f"Erro ao verificar permissões: {str(e)}"}), 500

        return decorated_function
    return decorator
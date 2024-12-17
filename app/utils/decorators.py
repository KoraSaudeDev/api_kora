from functools import wraps
from flask import request, jsonify
import jwt
from app.config.env import SECRET_KEY
from app.utils.helpers import check_user_permission


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
    Middleware para verificar permissões de rota para um usuário autenticado.
    Usuários administradores (is_admin = 1) têm acesso a todas as rotas.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(user_data, *args, **kwargs):
            # Verifica se o usuário é administrador
            if user_data.get("is_admin"):
                return f(user_data, *args, **kwargs)

            user_id = user_data.get("id")

            # Verificar se o usuário possui permissão para acessar a rota
            if not check_user_permission(user_id, route_prefix):
                return jsonify({
                    "status": "error",
                    "message": "Acesso negado. Você não tem permissão para acessar esta rota."
                }), 403

            return f(user_data, *args, **kwargs)
        return wrapper
    return decorator
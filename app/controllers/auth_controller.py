from flask import Blueprint, request, jsonify
from app.services.auth_service import AuthService
from app.utils.decorators import token_required

# Definição do Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Realiza login e gera um token JWT.
    ---
    tags:
      - Autenticação
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              example: "admin"
            password:
              type: string
              example: "senha123"
    responses:
      200:
        description: Login bem-sucedido, retorna o token JWT.
        schema:
          type: object
          properties:
            status:
              type: string
              example: "success"
            token:
              type: string
              example: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
      401:
        description: Credenciais inválidas.
        schema:
          type: object
          properties:
            status:
              type: string
              example: "error"
            message:
              type: string
              example: "Usuário ou senha inválidos"
      403:
        description: Conta inativa.
        schema:
          type: object
          properties:
            status:
              type: string
              example: "error"
            message:
              type: string
              example: "Conta inativa. Entre em contato com o administrador."
      500:
        description: Erro interno no servidor.
    """
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        # Verificar se o username e a senha foram fornecidos
        if not username or not password:
            return jsonify({"status": "error", "message": "Usuário e senha são obrigatórios"}), 400

        # Chamar o serviço de autenticação
        user_data = AuthService.get_user_data(username)
        if not user_data:
            return jsonify({"status": "error", "message": "Usuário ou senha inválidos"}), 401

        # Verificar a senha
        if not AuthService.verify_password(password, user_data['password_hash']):
            return jsonify({"status": "error", "message": "Usuário ou senha inválidos"}), 401

        # Verificar se o usuário está ativo
        if user_data.get("is_active") == 0:
            return jsonify({
                "status": "error",
                "message": "Conta inativa. Entre em contato com o administrador."
            }), 403

        # Gerar o token JWT
        token = AuthService.generate_token(user_data)

        # Retornar a resposta
        return jsonify({
            "status": "success",
            "token": token,
            "routes": user_data.get("routes", [])
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
      
@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(user_data):
    """
    Realiza o logout do usuário.
    ---
    tags:
      - Autenticação
    responses:
      200:
        description: Logout bem-sucedido.
        schema:
          type: object
          properties:
            status:
              type: string
              example: "success"
            message:
              type: string
              example: "Logout realizado com sucesso."
      500:
        description: Erro interno no servidor.
    """
    try:
        return jsonify({
            "status": "success",
            "message": "Logout realizado com sucesso."
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

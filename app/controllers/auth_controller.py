from flask import Blueprint, request, jsonify
from app.services.auth_service import AuthService

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
      500:
        description: Erro interno no servidor.
    """
    data = request.json
    username = data.get('username')
    password = data.get('password')
    response = AuthService.login(username, password)
    return jsonify(response), response.get("status_code", 200)
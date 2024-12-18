from flask import Blueprint, request, jsonify, make_response
from app.services.auth_service import AuthService

# Definição do Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Realiza login e gera um token JWT como cookie seguro.
    """
    data = request.json
    username = data.get('username')
    password = data.get('password')
    response_data = AuthService.login(username, password)

    # Se o login falhar, retorne a mensagem
    if response_data.get("status") != "success":
        return jsonify(response_data), response_data.get("status_code", 401)

    # Caso de sucesso, enviar o token como HttpOnly cookie
    token = response_data.get("token")

    # Criar a resposta e definir o cookie seguro
    response = make_response(jsonify({
        "status": "success",
        "routes": response_data.get("routes")
    }))
    response.set_cookie(
        key="jwt_token",
        value=token,
        httponly=True,  
        secure=True,   
        samesite="Strict",  
        max_age=3600  
    )
    return response
from flask import Flask, request
from flasgger import Swagger
from flask_cors import CORS
from app.controllers.auth_controller import auth_bp
from app.controllers.verzo_controller import verzo_bp
from app.controllers.route_controller import route_bp
from app.controllers.connection_controller import connection_bp
from app.controllers.system_controller import system_bp
from app.controllers.user_controller import user_bp
from app.controllers.executor_controller import executor_bp

app = Flask(__name__)

# Configurando CORS para aceitar requisições do localhost:3000
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)

# Middleware para tratar requisições OPTIONS manualmente
@app.before_request
def handle_options():
    if request.method == 'OPTIONS':
        response = app.make_response("")
        response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

# Configuração do Swagger
template = {
    "swagger": "2.0",
    "info": {
        "title": "API Verzo Documentation",
        "description": "Documentação da API Verzo utilizando Swagger.",
        "version": "1.0.0"
    },
    "host": "127.0.0.1:5000",
    "basePath": "/api",
    "schemes": ["http"],
    "securityDefinitions": {
        "BearerAuth": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Adicione o token JWT no formato: Bearer <token>"
        }
    }
}

swagger = Swagger(app, template=template)

# Registro dos Blueprints com prefixo `/api`
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(verzo_bp, url_prefix="/api/verzo")
app.register_blueprint(route_bp, url_prefix="/api/route")
app.register_blueprint(connection_bp, url_prefix="/api/connection")
app.register_blueprint(system_bp, url_prefix="/api/system")
app.register_blueprint(user_bp, url_prefix="/api/user")
app.register_blueprint(executor_bp, url_prefix="/api/executor")

@app.route('/api', methods=['GET'])
def home():
    """
    Página inicial da API.
    ---
    tags:
      - Base
    responses:
      200:
        description: Mensagem de boas-vindas.
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Bem-vindo à API Verzo!"
    """
    return {"message": "Bem-vindo à API Verzo!"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

from flask import Flask, request
from flasgger import Swagger
from flask_cors import CORS
from app.controllers.auth_controller import auth_bp
from app.controllers.verzo_controller import verzo_bp
from app.controllers.route_controller import route_bp
from app.controllers.connection_controller import connection_bp
from app.controllers.system_controller import system_bp
from app.controllers.user_controller import user_bp
# from app.controllers.executor_controller import executor_bp
from app.controllers.access_controller import access_bp
from app.controllers.depara_controller import depara_bp
import logging
import sys
from app import create_app

app = create_app()

logging.basicConfig(
    level=logging.DEBUG,  # Garantir que DEBUG será exibido
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)  # Redireciona logs para stdout
    ],
)

# Configurando logs específicos para Flask
flask_logger = logging.getLogger('flask.app')
flask_logger.setLevel(logging.DEBUG)

# Configurando CORS para aceitar requisições do frontend no IP e porta corretos
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3200", "http://10.27.254.153:3200","http://localhost:3100", "http://10.27.254.153:3100""http://localhost:3000", "http://10.27.254.153:3000"]}}, supports_credentials=True)

# Middleware para adicionar cabeçalhos de CORS em todas as respostas
@app.after_request
def add_cors_headers(response):
    allowed_origins = ["http://localhost:3200", "http://10.27.254.153:3200","http://localhost:3100", "http://10.27.254.153:3100""http://localhost:3000", "http://10.27.254.153:3000"]
    origin = request.headers.get("Origin")
    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
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
    "host": "172.17.91.170:3793",
    "basePath": "/",
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

config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/verzo/docs/apispec.json",
            "rule_filter": lambda rule: rule.rule.startswith("/api/verzo") or rule.rule.startswith("/api/auth"),
            "model_filter": lambda tag: True
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/verzo/docs"
}

swagger = Swagger(app, template=template, config=config)

# Registro dos Blueprints com prefixo `/api`
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(verzo_bp, url_prefix="/api/verzo")
app.register_blueprint(depara_bp, url_prefix="/api/depara")
app.register_blueprint(route_bp, url_prefix="/api/routes")
app.register_blueprint(connection_bp, url_prefix="/api/connections")
app.register_blueprint(system_bp, url_prefix="/api/systems")
app.register_blueprint(user_bp, url_prefix="/api/users")
# app.register_blueprint(executor_bp, url_prefix="/api/executors")
app.register_blueprint(access_bp, url_prefix="/api/access")

@app.route('/api', methods=['GET'])
def home():
    """
    Página inicial da API.
    ---
    tags:
      - Base
    responses:
      200:
        description: Retorna uma mensagem de boas-vindas.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "Bem-vindo à API Verzo!"
    """
    return {"message": "Bem-vindo à API Verzo!"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3793, debug=True)

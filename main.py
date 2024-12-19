from flask import Flask
from flasgger import Swagger
from flask_cors import CORS
from app.controllers.auth_controller import auth_bp
from app.controllers.verzo_controller import verzo_bp
from app.controllers.route_controller import route_bp
from app.controllers.connection_controller import connection_bp
from app.controllers.system_controller import system_bp
from app.controllers.user_controller import user_bp
from app.controllers.executor_controller import executor_bp
import os

app = Flask(__name__)

# Detecta o ambiente atual (pode ser configurado via variáveis de ambiente)
ENV = os.getenv("FLASK_ENV", "production")

# Configurando CORS baseado no ambiente
if ENV == "development":
    CORS(app, resources={r"/*": {"origins": ["http://localhost:3000"]}}, supports_credentials=True)
else:  # Ambiente de produção
    CORS(app, resources={r"/*": {"origins": ["http://10.27.254.153"]}}, supports_credentials=True)
    
# Configuração do Swagger
template = {
    "swagger": "2.0",
    "info": {
        "title": "API Verzo Documentation",
        "description": "Documentação da API Verzo utilizando Swagger.",
        "version": "1.0.0"
    },
    "host": "127.0.0.1:3793",
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

swagger = Swagger(app, template=template)

# Registro dos Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(verzo_bp)
app.register_blueprint(route_bp)
app.register_blueprint(connection_bp)
app.register_blueprint(system_bp)
app.register_blueprint(user_bp)
app.register_blueprint(executor_bp)

@app.route('/', methods=['GET'])
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
    app.run(host="0.0.0.0", port=3792, debug=(ENV == "development"))

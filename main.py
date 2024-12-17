from flask import Flask
from flasgger import Swagger
from flask_cors import CORS  # Importação do CORS
from app.controllers.auth_controller import auth_bp
from app.controllers.verzo_controller import verzo_bp
from app.controllers.route_controller import route_bp
from app.controllers.connection_controller import connection_bp
from app.controllers.system_controller import system_bp
from app.controllers.user_controller import user_bp

app = Flask(__name__)

# Configurando CORS para aceitar qualquer origem temporariamente
CORS(app, resources={r"/*": {"origins": "*"}})

# Configuração do Swagger
template = {
    "swagger": "2.0",
    "info": {
        "title": "API Verzo Documentation",
        "description": "Documentação da API Verzo utilizando Swagger.",
        "version": "1.0.0"
    },
    "host": "127.0.0.1:3792",
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
    app.run(host="0.0.0.0", port=3792, debug=True)

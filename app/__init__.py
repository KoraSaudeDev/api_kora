# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

# Configuração do SQLAlchemy
db = SQLAlchemy()

def create_app():
    load_dotenv()  # Carregar variáveis de ambiente
    
    app = Flask(__name__)

    # Configuração do banco de dados
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('ITSM_DB_USER')}:{os.getenv('ITSM_DB_PASSWORD')}@{os.getenv('ITSM_DB_HOST')}:{os.getenv('ITSM_DB_PORT')}/{os.getenv('ITSM_DB_DATABASE')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicializar SQLAlchemy com a aplicação
    db.init_app(app)

    return app

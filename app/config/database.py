from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os
from urllib.parse import quote_plus

# Carregar variáveis do arquivo .env
load_dotenv()

# Configuração do banco de dados
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "test")

# Codificar a senha para evitar caracteres especiais na URL
encoded_password = quote_plus(DB_PASSWORD)

# Construir a URL do banco de dados
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Criar o engine do SQLAlchemy
engine = create_engine(DATABASE_URL, echo=True)

# Criar uma fábrica de sessões
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarativa para os modelos
Base = declarative_base()

# Função para inicializar o banco de dados
def init_db():
    import app.models.route_group  # Certifique-se de importar todos os modelos
    Base.metadata.create_all(bind=engine)

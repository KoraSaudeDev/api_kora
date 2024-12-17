import json
import bcrypt
from flask import Blueprint, request, jsonify
from app.utils.decorators import token_required, admin_required, permission_required
from app.config.db_config import create_db_connection_mysql, create_verzo_connection   
from flask import current_app
from flask import Flask, Blueprint, request, jsonify, send_from_directory
import os

# Definindo o Blueprint antes de ser usado
verzo_bp = Blueprint('verzo', __name__, url_prefix='/verzo')

# Glossário para mapear siglas para nomes de bancos de dados
DATABASE_GLOSSARY = {
    "HMS": "mv_serra",
    "HA": "mv_anchieta",
    "HMC": "mv_cariacica",
    "ING_OTO": "mv_neurologia_goiania",
    "HPC": "mv_praia_da_costa",
    "HSL": "mv_sao_luiz",
    "HSF": "mv_sao_francisco",
    "HSM": "mv_sao_matheus",
    "IRT": "tasy_IRT",
    "ENCORE": "tasy_encore",
    "HSFB": "tasy_sao_francisco",
    "HPM": "tasy_palmas",
    "HSMC": "tasy_sao_matheus"
}

MV_DATABASES = [
    "mv_serra",
    "mv_anchieta",
    "mv_cariacica",
    "mv_neurologia_goiania",
    "mv_sao_luiz",
    "mv_praia_da_costa"
]

TASY_DATABASES = [
    "tasy_serra",
    "tasy_irt",
    "tasy_encore",
    "tasy_palmas",
    "tasy_sao_francisco"
]

@verzo_bp.route('/', methods=['GET'])
@token_required
@permission_required(route_prefix='/verzo')
def home():
    """
    Página inicial da API.
    ---
    responses:
      200:
        description: Página inicial da API.
        content:
          text/html:
            schema:
              type: string
    """
    # Caminho absoluto até a pasta static/html
    static_path = os.path.abspath(os.path.join(os.getcwd(), 'static', 'html'))
    return send_from_directory(static_path, 'index.html')

@verzo_bp.route('/docs', methods=['GET'])
@token_required
@permission_required(route_prefix='/verzo')
def verzo_page():
    """
    Rota para exibir a página Verzo.
    ---
    tags:
      - Páginas HTML
    responses:
      200:
        description: Retorna o HTML da página Verzo.
        content:
          text/html:
            schema:
              type: string
    """
    # Caminho absoluto até a pasta static/html
    static_path = os.path.join(os.getcwd(), 'static', 'html')
    return send_from_directory(static_path, 'verzo.html')

@verzo_bp.route('/<route_type>/<database>/<query_name>', methods=['POST'])
@token_required
@permission_required(route_prefix='/verzo')
def query_by_type(user_data, route_type, database, query_name):
    """
    Consulta por tipo e banco de dados.
    ---
    tags:
      - Consultas por Tipo
    parameters:
      - name: route_type
        in: path
        type: string
        required: true
        enum: ["MV", "TASY"]
        description: Tipo da consulta.
      - name: database
        in: path
        type: string
        required: true
        description: Sigla do banco de dados.
        example: "HA"
      - name: query_name
        in: path
        type: string
        required: true
        description: Nome da query no banco.
        example: "CONFIG_UNIDADE"
      - name: limit
        in: query
        type: integer
        default: 100
        description: Número máximo de resultados a retornar.
      - name: offset
        in: query
        type: integer
        default: 0
        description: Offset para paginação.
    responses:
      200:
        description: Dados retornados com sucesso.
        schema:
          type: array
          items:
            type: object
            example:
              id: 1
              name: "Example"
              description: "Exemplo de dados retornados"
      400:
        description: Parâmetros inválidos.
      404:
        description: Tabela ou banco não encontrado.
      500:
        description: Erro interno no servidor.
    """
    try:
        # Traduz a sigla para o nome correto do banco usando o glossário
        actual_database = DATABASE_GLOSSARY.get(database.upper())
        if not actual_database:
            return jsonify({"status": "error", "message": f"Nenhum banco encontrado para a sigla '{database}'"}), 404

        # Determina o tipo de rota e valida o banco
        if route_type.upper() == "MV":
            if actual_database not in MV_DATABASES:
                return jsonify({"status": "error", "message": f"O banco '{actual_database}' não pertence ao tipo MV."}), 400
        elif route_type.upper() == "TASY":
            if actual_database not in TASY_DATABASES:
                return jsonify({"status": "error", "message": f"O banco '{actual_database}' não pertence ao tipo TASY."}), 400
        else:
            return jsonify({"status": "error", "message": "Tipo de rota inválido. Use 'MV' ou 'TASY'."}), 400

        limit = request.args.get("limit", default=100, type=int)
        offset = request.args.get("offset", default=0, type=int)

        table_name = f"{actual_database}"
        conn = create_verzo_connection()
        cursor = conn.cursor(dictionary=True)

        # Verifica se a tabela existe
        cursor.execute(f"SHOW TABLES LIKE '{table_name}';")
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": f"Tabela '{table_name}' não encontrada."}), 404

        route_prefix = f"/{route_type.lower()}/"
        query = f"SELECT data FROM `{table_name}` WHERE route = %s LIMIT %s OFFSET %s;"
        cursor.execute(query, (f"{route_prefix}{query_name}", limit, offset))
        rows = cursor.fetchall()

        processed_rows = []
        for row in rows:
            try:
                record = json.loads(row["data"])
                record.pop("ROWNUM", None)  # Remove o campo ROWNUM
                processed_rows.append(record)
            except (KeyError, json.JSONDecodeError):
                continue  # Ignora entradas inválidas

        cursor.close()
        conn.close()

        # Retorna diretamente a lista de objetos JSON
        return jsonify(processed_rows), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
      
@verzo_bp.route('/routes', methods=['GET'])
def list_verzo_routes():
    """
    Lista todas as rotas registradas no blueprint 'verzo_bp'.
    """
    try:
        # Acessa as rotas da aplicação Flask e filtra as que pertencem ao blueprint 'verzo'
        routes = [rule.rule for rule in current_app.url_map.iter_rules() if rule.endpoint.startswith('verzo')]
        return jsonify({"routes": routes}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
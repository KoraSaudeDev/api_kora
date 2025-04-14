import json
import re
from flask import Blueprint, request, jsonify, redirect
from app.utils.decorators import token_required, permission_required
from app.config.db_config import create_verzo_connection

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
    "tasy_IRT",
    "tasy_encore",
    "tasy_palmas",
    "tasy_sao_francisco"
]

@verzo_bp.route('/', methods=['GET'])
def home():
    """
    Página inicial da API Verzo.
    ---
    tags:
      - Páginas HTML
    responses:
      302:
        description: Redireciona para a página de login.
    """
    return redirect("http://10.27.254.153:3000/login", code=302)

@verzo_bp.route('/docs', methods=['GET'])
def verzo_page():
    """
    Tela de documentação da verzo.
    ---
    tags:
      - Páginas HTML
    responses:
      302:
        description: Redireciona para a página Verzo.
    """
    return redirect("http://10.27.254.153:3000/verzo", code=302)
     
@verzo_bp.route('/<route_type>/<database>/<query_name>', methods=['POST'])
@token_required
@permission_required(route_prefix='/verzo')
def query_by_type(user_data, route_type, database, query_name):
    try:
        # Obtém o nome do banco real a partir do glossário
        actual_database = DATABASE_GLOSSARY.get(database.upper())
        if not actual_database:
            return jsonify({"status": "error", 
                            "message": f"Nenhum banco encontrado para a sigla '{database}'"}), 404

        # Verifica se o banco pertence ao tipo informado
        if route_type.upper() == "MV" and actual_database not in MV_DATABASES:
            return jsonify({"status": "error", 
                            "message": f"O banco '{actual_database}' não pertence ao tipo MV."}), 400
        elif route_type.upper() == "TASY" and actual_database not in TASY_DATABASES:
            return jsonify({"status": "error", 
                            "message": f"O banco '{actual_database}' não pertence ao tipo TASY."}), 400

        # Parâmetros de paginação
        limit = request.args.get("limit", default=100, type=int)
        # Interpreta o parâmetro "offset" como número da página e calcula o offset real:
        page_number = request.args.get("offset", default=0, type=int)
        offset = page_number * limit

        # Extraindo os filtros da query string (excluindo 'limit' e 'offset')
        filters = {}
        for key in request.args:
            if key.lower() not in ['limit', 'offset']:
                filters[key] = request.args.get(key)

        filter_clause = ""
        params = [f"/{route_type.lower()}/{query_name}"]  # Parâmetro para o campo 'route'

        # Construção da cláusula de filtro para cada parâmetro informado
        for key, value in filters.items():
            # Validação para garantir que o nome do campo seja seguro
            if not re.match(r'^[A-Za-z0-9_]+$', key):
                return jsonify({"status": "error", 
                                "message": f"Campo de filtro inválido: {key}."}), 400

            # Define o JSON path com o nome do campo entre aspas duplas
            json_path = f'$."{key}"'

            # Verifica se o valor é numérico (para comparação sem JSON_UNQUOTE)
            try:
                int_value = int(value)
                filter_clause += f" AND JSON_EXTRACT(data, '{json_path}') = %s"
                params.append(int_value)
            except ValueError:
                # Se o valor não for numérico, trata-o como string ou data
                if len(value) == 10:
                    value = value + " 00:00:00"
                filter_clause += f" AND JSON_UNQUOTE(JSON_EXTRACT(data, '{json_path}')) = %s"
                params.append(value)

        # Acrescenta os parâmetros de paginação
        params.extend([limit, offset])

        # Monta a query adicionando ORDER BY baseado no campo "ROWNUM"
        query = (
            f"SELECT data FROM `{actual_database}` "
            f"WHERE route = %s {filter_clause} "
            f"ORDER BY CAST(JSON_UNQUOTE(JSON_EXTRACT(data, '$.ROWNUM')) AS UNSIGNED) "
            f"LIMIT %s OFFSET %s;"
        )

        conn = create_verzo_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        # Carrega o JSON completo (incluindo o campo "ROWNUM")
        # processed_rows = [
        #     json.loads(row["data"]) for row in rows if "data" in row
        # ]
        # return jsonify(processed_rows), 200

        processed_rows = [
            {k: v for k, v in json.loads(row["data"]).items() if k.upper() != "ROWNUM"}
            for row in rows if "data" in row
        ]
        return jsonify(processed_rows), 200
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
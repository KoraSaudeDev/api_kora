import json
import re
from flask import Blueprint, request, jsonify, redirect
from app.utils.decorators import token_required, permission_required
from app.config.db_config import create_verzo_connection
from datetime import datetime

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
    "mv_praia_da_costa",
    "mv_sao_francisco"
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
        # Banco real
        actual_database = DATABASE_GLOSSARY.get(database.upper())
        if not actual_database:
            return jsonify({"status": "error", "message": f"Nenhum banco encontrado para '{database}'"}), 404

        if route_type.upper() == "MV" and actual_database not in MV_DATABASES:
            return jsonify({"status": "error", "message": f"O banco '{actual_database}' não pertence ao tipo MV."}), 400
        elif route_type.upper() == "TASY" and actual_database not in TASY_DATABASES:
            return jsonify({"status": "error", "message": f"O banco '{actual_database}' não pertence ao tipo TASY."}), 400

        # Paginação
        limit = request.args.get("limit", default=100, type=int)
        page_number = request.args.get("offset", default=0, type=int)
        offset = page_number * limit

        # Filtros da query string
        filters = {}
        for key in request.args:
            if key.lower() not in ['limit', 'offset']:
                filters[key] = request.args.get(key)

        filter_clause = ""
        params = [f"/{route_type.lower()}/{query_name}"]

        for key, value in filters.items():
            if not re.match(r'^[A-Za-z0-9_]+$', key):
                return jsonify({"status": "error", "message": f"Campo de filtro inválido: {key}."}), 400

            json_path = f'$."{key}"'

            try:
                # NÚMERO
                int_value = int(value)
                filter_clause += f" AND JSON_EXTRACT(data, '{json_path}') = %s"
                params.append(int_value)
            except ValueError:
                # TRATAMENTO DE INTERVALO DE DATAS: ex: 2024-09-10 AND 2024-09-12
                if " AND " in value:
                    try:
                        start_raw, end_raw = [v.strip() for v in value.split("AND")]
                        start_dt = datetime.strptime(start_raw, "%Y-%m-%d").strftime("%Y-%m-%d 00:00:00")
                        end_dt = datetime.strptime(end_raw, "%Y-%m-%d").strftime("%Y-%m-%d 23:59:59")
                        filter_clause += (
                            f" AND JSON_UNQUOTE(JSON_EXTRACT(data, '{json_path}')) BETWEEN %s AND %s"
                        )
                        params.extend([start_dt, end_dt])
                    except ValueError:
                        return jsonify({"status": "error", "message": f"Formato de intervalo inválido para {key}: {value}"}), 400

                # DATA ÚNICA: ex: 2024-09-10
                elif re.match(r"^\d{4}-\d{2}-\d{2}$", value):
                    start_dt = value + " 00:00:00"
                    end_dt = value + " 23:59:59"
                    filter_clause += (
                        f" AND JSON_UNQUOTE(JSON_EXTRACT(data, '{json_path}')) BETWEEN %s AND %s"
                    )
                    params.extend([start_dt, end_dt])

                # STRING ou DATETIME COMPLETO
                else:
                    filter_clause += (
                        f" AND JSON_UNQUOTE(JSON_EXTRACT(data, '{json_path}')) = %s"
                    )
                    params.append(value)

        # Paginação
        params.extend([limit, offset])

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

        processed_rows = [
            {k: v for k, v in json.loads(row["data"]).items() if k.upper() != "ROWNUM"}
            for row in rows if "data" in row
        ]
        return jsonify(processed_rows), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

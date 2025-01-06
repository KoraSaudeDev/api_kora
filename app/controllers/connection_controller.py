from flask import Blueprint, request, jsonify
from app.services.db_service import DatabaseService
from app.utils.decorators import token_required, admin_required, permission_required
from app.utils.helpers import encrypt_password
from app.config.db_config import create_db_connection_mysql
from app.services.db_service import DatabaseService
import logging
from app.models.connection import Connection
from app.utils.helpers import generate_slug

# Definição do Blueprint
connection_bp = Blueprint('connections', __name__, url_prefix='/connections')

def get_expected_params(db_type):
    """
    Retorna os parâmetros esperados para o tipo de banco de dados especificado.
    """
    PARAMS = {
        "mysql": [
            {"name": "host", "type": "string", "required": True},
            {"name": "port", "type": "integer", "required": True},
            {"name": "username", "type": "string", "required": True},
            {"name": "password", "type": "string", "required": True},
            {"name": "database_name", "type": "string", "required": False}
        ],
        "mariadb": [
            {"name": "host", "type": "string", "required": True},
            {"name": "port", "type": "integer", "required": True},
            {"name": "username", "type": "string", "required": True},
            {"name": "password", "type": "string", "required": True},
            {"name": "database_name", "type": "string", "required": True}
        ],
        "oracle": [
            {"name": "host", "type": "string", "required": True},
            {"name": "port", "type": "integer", "required": True},
            {"name": "username", "type": "string", "required": True},
            {"name": "password", "type": "string", "required": True},
            {"name": "service_name", "type": "string", "required": False},
            {"name": "sid", "type": "string", "required": False}
        ],
        "postgres": [
            {"name": "host", "type": "string", "required": True},
            {"name": "port", "type": "integer", "required": True},
            {"name": "username", "type": "string", "required": True},
            {"name": "password", "type": "string", "required": True},
            {"name": "database_name", "type": "string", "required": True}
        ],
        "sqlite": [
            {"name": "database_name", "type": "string", "required": True}
        ],
        "sap": [
            {"name": "extra_params", "type": "json", "required": True},
            {"name": "username", "type": "string", "required": True},
            {"name": "password", "type": "string", "required": True}
        ],
        "sap_hana": [
            {"name": "host", "type": "string", "required": True},
            {"name": "port", "type": "integer", "required": True},
            {"name": "username", "type": "string", "required": True},
            {"name": "password", "type": "string", "required": True},
            {"name": "database_name", "type": "string", "required": True}
        ],
        "redis": [
            {"name": "host", "type": "string", "required": True},
            {"name": "port", "type": "integer", "required": True},
            {"name": "password", "type": "string", "required": False}
        ],
        "mongodb": [
            {"name": "host", "type": "string", "required": True},
            {"name": "port", "type": "integer", "required": True},
            {"name": "username", "type": "string", "required": True},
            {"name": "password", "type": "string", "required": True}
        ],
        "cassandra": [
            {"name": "host", "type": "string", "required": True},
            {"name": "port", "type": "integer", "required": True},
            {"name": "username", "type": "string", "required": True},
            {"name": "password", "type": "string", "required": True},
            {"name": "database_name", "type": "string", "required": False}
        ],
        "firebase": [
            {"name": "service_account_key", "type": "json", "required": True}
        ],
        "snowflake": [
            {"name": "account", "type": "string", "required": True},
            {"name": "username", "type": "string", "required": True},
            {"name": "password", "type": "string", "required": True},
            {"name": "database_name", "type": "string", "required": True},
            {"name": "warehouse", "type": "string", "required": True}
        ],
        "elasticsearch": [
            {"name": "host", "type": "string", "required": True},
            {"name": "port", "type": "integer", "required": True},
            {"name": "username", "type": "string", "required": False},
            {"name": "password", "type": "string", "required": False}
        ],
        "dynamodb": [
            {"name": "region_name", "type": "string", "required": True},
            {"name": "access_key", "type": "string", "required": True},
            {"name": "secret_key", "type": "string", "required": True}
        ],
        "mssql": [
            {"name": "host", "type": "string", "required": True},
            {"name": "port", "type": "integer", "required": True},
            {"name": "username", "type": "string", "required": True},
            {"name": "password", "type": "string", "required": True},
            {"name": "database_name", "type": "string", "required": True}
        ],
        "ibm_db2": [
            {"name": "host", "type": "string", "required": True},
            {"name": "port", "type": "integer", "required": True},
            {"name": "username", "type": "string", "required": True},
            {"name": "password", "type": "string", "required": True},
            {"name": "database_name", "type": "string", "required": True}
        ]
    }

    return PARAMS.get(db_type.lower(), [])

@connection_bp.route("/expected_params/<db_type>", methods=["GET"])
@token_required
def get_expected_params_endpoint(user_data, db_type):
    """
    Retorna os parâmetros esperados para o tipo de banco de dados especificado.
    """
    params = get_expected_params(db_type)
    if not params:
        return jsonify({"status": "error", "message": f"Tipo de banco de dados '{db_type}' não suportado."}), 400

    return jsonify({"status": "success", "params": params}), 200

# Campos obrigatórios por tipo de banco
REQUIRED_FIELDS = {
    "default": ["name", "db_type", "host", "port", "username", "password"],

    # MySQL
    "mysql": ["name", "db_type", "host", "port", "username", "password", "database_name"],

    # MariaDB
    "mariadb": ["name", "db_type", "host", "port", "username", "password", "database_name"],

    # Oracle
    "oracle": ["name", "db_type", "host", "port", "username", "password"],  # service_name ou sid é opcional

    # PostgreSQL
    "postgres": ["name", "db_type", "host", "port", "username", "password", "database_name"],

    # SQLite
    "sqlite": ["name", "db_type", "database_name"],

    # SAP (via ODBC)
    "sap": ["name", "db_type", "extra_params", "username", "password"],

    # SAP HANA
    "sap_hana": ["name", "db_type", "host", "port", "username", "password", "database_name"],

    # Redis
    "redis": ["name", "db_type", "host", "port"],  # password é opcional

    # MongoDB
    "mongodb": ["name", "db_type", "host", "port", "username", "password"],

    # Cassandra
    "cassandra": ["name", "db_type", "host", "port", "username", "password"],

    # Firebase
    "firebase": ["name", "db_type", "service_account_key"],

    # Snowflake
    "snowflake": ["name", "db_type", "account", "username", "password", "database_name", "warehouse"],

    # Elasticsearch
    "elasticsearch": ["name", "db_type", "host", "port"],  # username e password são opcionais

    # DynamoDB
    "dynamodb": ["name", "db_type", "region_name", "access_key", "secret_key"],
}

def validate_payload(db_type, data):
    """
    Valida o payload com base no tipo de banco de dados.
    """
    expected_params = get_expected_params(db_type)
    if not expected_params:
        return []

    missing_fields = [
        param["name"] for param in expected_params 
        if param["required"] and not data.get(param["name"])
    ]
    return missing_fields

@connection_bp.route("/create", methods=["POST"])
@token_required
def create_connection(user_data):
    """
    Cria uma nova conexão de banco de dados.
    """
    try:
        data = request.json
        name = data.get("name")
        db_type = data.get("db_type")

        if not name or not db_type:
            return jsonify({"status": "error", "message": "Os campos 'name' e 'db_type' são obrigatórios."}), 400

        # Gerar slug
        slug = generate_slug(name)

        # Validar os campos obrigatórios com base no tipo de banco
        missing_fields = validate_payload(db_type.lower(), data)
        if missing_fields:
            return jsonify({
                "status": "error",
                "message": f"Campos obrigatórios ausentes: {', '.join(missing_fields)}"
            }), 400

        # Testar a conexão usando o DatabaseService
        if not DatabaseService.test_connection(
            db_type=db_type,
            host=data.get("host"),
            port=data.get("port"),
            username=data.get("username"),
            password=data.get("password"),
            database=data.get("database_name"),
            service_name=data.get("service_name"),
            sid=data.get("sid"),
            extra_params=data.get("extra_params")
        ):
            return jsonify({"status": "error", "message": "Erro ao testar a conexão."}), 400

        # Criptografar a senha
        encrypted_password = encrypt_password(data["password"])

        # Salvar a conexão no banco
        conn = create_db_connection_mysql()
        cursor = conn.cursor()

        query = """
            INSERT INTO connections (name, slug, db_type, host, port, username, password, database_name, service_name, sid, extra_params)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            query,
            (
                name,
                slug,
                db_type,
                data.get("host"),
                data.get("port"),
                data.get("username"),
                encrypted_password,
                data.get("database_name"),
                data.get("service_name"),
                data.get("sid"),
                data.get("extra_params")
            ),
        )
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": "Conexão criada com sucesso."}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@connection_bp.route('/list', methods=['GET'])
@token_required
def list_connections(user_data):
    """
    Lista todas as conexões com paginação.
    """
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
        offset = (page - 1) * limit

        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT id, name, db_type, host, port, username, database_name, service_name, created_at 
            FROM connections
            ORDER BY id
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, (limit, offset))
        connections = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) AS total FROM connections")
        total_count = cursor.fetchone()["total"]

        cursor.close()
        conn.close()

        return jsonify({"status": "success", "page": page, "limit": limit, "total": total_count, "connections": connections}), 200
    except Exception as e:
        logging.error(f"Erro ao listar conexões: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@connection_bp.route('/delete/<int:connection_id>', methods=['DELETE'])
@token_required
@permission_required(route_prefix='/connections')
def delete_connection(user_data, connection_id):
    """
    Deleta uma conexão de banco de dados.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor()

        query = "DELETE FROM connections WHERE id = %s"
        cursor.execute(query, (connection_id,))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"status": "error", "message": "Conexão não encontrada."}), 404

        cursor.close()
        conn.close()
        return jsonify({"status": "success", "message": "Conexão deletada com sucesso."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@connection_bp.route('/list-simple', methods=['GET'])
@token_required
@permission_required(route_prefix='/connections')
def list_connections_simple(user_data):
    """
    Lista todas as conexões de banco de dados com todos os campos de cada conexão.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Consulta para buscar todas as conexões com todos os detalhes
        query = """
            SELECT 
                id AS value, 
                name AS label, 
                db_type, 
                host, 
                port, 
                username, 
                database_name, 
                service_name, 
                sid, 
                slug, 
                created_at
            FROM connections
            ORDER BY id
        """
        cursor.execute(query)
        connections = cursor.fetchall()

        cursor.close()
        conn.close()

        # Retornar todos os detalhes das conexões
        return jsonify({
            "status": "success",
            "connections": connections
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
@connection_bp.route("/test/<int:connection_id>", methods=["GET"])
@token_required

def test_connection(connection_id, **kwargs):
    """
    Testa uma conexão existente com base no ID.
    """
    try:
        # Conectar ao banco para buscar os dados da conexão
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Buscar conexão pelo ID
        query = "SELECT * FROM connections WHERE id = %s"
        cursor.execute(query, (connection_id,))
        connection_data = cursor.fetchone()

        cursor.close()
        conn.close()

        if not connection_data:
            return jsonify({"status": "error", "message": "Conexão não encontrada."}), 404

        # Testar a conexão
        result = DatabaseService.test_existing_connection(connection_data)
        return jsonify(result), 200 if result["status"] == "success" else 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
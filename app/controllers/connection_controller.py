from flask import Blueprint, request, jsonify
from app.services.db_service import DatabaseService
from app.utils.decorators import token_required, admin_required, permission_required
from app.utils.helpers import encrypt_password
from app.config.db_config import create_db_connection_mysql
from app.services.db_service import DatabaseService
import logging
from app.models.connection import Connection
from app.utils.helpers import generate_slug
import time

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
@permission_required(route_prefix='/connections')
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

        slug = generate_slug(name)
        missing_fields = validate_payload(db_type.lower(), data)

        if missing_fields:
            return jsonify({"status": "error", "message": f"Campos obrigatórios ausentes: {', '.join(missing_fields)}"}), 400

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

        encrypted_password = encrypt_password(data["password"])

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
        logging.error(f"Erro ao criar conexão: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Editar uma conexão existente
@connection_bp.route('/edit/<int:connection_id>', methods=['PUT'])
@token_required
@permission_required(route_prefix='/connections')
def edit_connection(user_data, connection_id):
    """
    Edita uma conexão existente com base no ID fornecido.
    """
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "Nenhum dado enviado para atualização."}), 400

        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        query_check = "SELECT id FROM connections WHERE id = %s"
        cursor.execute(query_check, (connection_id,))
        connection = cursor.fetchone()

        if not connection:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Conexão não encontrada."}), 404

        update_fields = []
        update_values = []

        editable_fields = [
            "name", "db_type", "host", "port", "username", "password", "database_name", "service_name", "sid", "extra_params"
        ]

        for field in editable_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                if field == "password":
                    update_values.append(encrypt_password(data[field]))
                else:
                    update_values.append(data[field])

        if not update_fields:
            return jsonify({"status": "error", "message": "Nenhum campo válido para atualizar."}), 400

        update_values.append(connection_id)

        query_update = f"""
            UPDATE connections
            SET {', '.join(update_fields)}
            WHERE id = %s
        """
        cursor.execute(query_update, tuple(update_values))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": "Conexão atualizada com sucesso."}), 200

    except Exception as e:
        logging.error(f"Erro ao editar conexão: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# # Testar uma conexão existente
# @connection_bp.route("/test/<int:connection_id>", methods=["GET"])
# @token_required
# @permission_required(route_prefix="/connections")
# def test_database_connection(user_data, connection_id):
#     """
#     Testa uma conexão existente com base no ID.
#     """
#     try:
#         conn = create_db_connection_mysql()
#         cursor = conn.cursor(dictionary=True)

#         query = "SELECT * FROM connections WHERE id = %s"
#         cursor.execute(query, (connection_id,))
#         connection_data = cursor.fetchone()

#         cursor.close()
#         conn.close()

#         if not connection_data:
#             return jsonify({"status": "error", "message": "Conexão não encontrada."}), 404

#         result = DatabaseService.test_existing_connection(connection_data)
#         return jsonify(result), 200 if result["status"] == "success" else 400
#     except Exception as e:
#         logging.error(f"Erro ao testar conexão: {e}")
#         return jsonify({"status": "error", "message": str(e)}), 500

@connection_bp.route("/test/<int:connection_id>", methods=["GET"])
@token_required
@permission_required(route_prefix="/connections")
def test_database_connection(user_data, connection_id):
    """
    Testa uma conexão existente com base no ID e retorna logs detalhados.
    """
    start_time = time.time()  # Marca o tempo inicial

    try:
        logging.info(f"Testando conexão para connection_id: {connection_id}")

        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        query = "SELECT * FROM connections WHERE id = %s"
        cursor.execute(query, (connection_id,))
        connection_data = cursor.fetchone()

        cursor.close()
        conn.close()

        if not connection_data:
            logging.warning(f"Conexão ID {connection_id} não encontrada.")
            return jsonify({"status": "error", "message": "Conexão não encontrada."}), 404

        logging.info(f"Conexão ID {connection_id} encontrada: {connection_data}")

        # Testa a conexão
        result = DatabaseService.test_existing_connection(connection_data)

        elapsed_time = round(time.time() - start_time, 3)  # Tempo decorrido
        logging.info(f"Tempo de teste de conexão: {elapsed_time} segundos")

        if result["status"] == "success":
            logging.info(f"Conexão ID {connection_id} bem-sucedida: {result}")
            return jsonify({"status": "success", "message": "Conexão realizada com sucesso.", "details": result, "elapsed_time": elapsed_time}), 200
        else:
            logging.error(f"Erro na conexão ID {connection_id}: {result}")
            return jsonify({"status": "error", "message": "Falha ao conectar.", "details": result, "elapsed_time": elapsed_time}), 400

    except Exception as e:
        elapsed_time = round(time.time() - start_time, 3)
        logging.error(f"Erro ao testar conexão ID {connection_id}: {e} - Tempo: {elapsed_time} segundos")
        return jsonify({"status": "error", "message": str(e), "elapsed_time": elapsed_time}), 500

# Listar conexões
@connection_bp.route('/list', methods=['GET'])
@token_required
@permission_required(route_prefix='/connections')
def list_connections(user_data):
    """
    Lista todas as conexões com paginação.
    """
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 100))
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

# Obter uma única conexão pelo ID
@connection_bp.route('/<int:connection_id>', methods=['GET'])
@token_required
@permission_required(route_prefix='/connections')
def get_connection_by_id(user_data, connection_id):
    """
    Retorna os detalhes de uma conexão específica com base no ID fornecido.
    """
    try:
        # Conectar ao banco de dados
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Consultar a conexão pelo ID
        query = """
            SELECT id, name, db_type, host, port, username, database_name, service_name, sid, extra_params, created_at
            FROM connections
            WHERE id = %s
        """
        cursor.execute(query, (connection_id,))
        connection = cursor.fetchone()

        # Fechar conexão com o banco de dados
        cursor.close()
        conn.close()

        # Verificar se a conexão foi encontrada
        if not connection:
            return jsonify({"status": "error", "message": "Conexão não encontrada."}), 404

        # Retornar os detalhes da conexão
        return jsonify({"status": "success", "connection": connection}), 200

    except Exception as e:
        logging.error(f"Erro ao buscar conexão pelo ID: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Deletar uma conexão
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
        logging.error(f"Erro ao deletar conexão: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@connection_bp.route('/list-simple', methods=['GET'])
@token_required
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
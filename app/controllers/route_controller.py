from flask import Blueprint, request, jsonify
from app.utils.decorators import token_required, admin_required
from app.config.db_config import create_db_connection_mysql

# Blueprint para rotas
route_bp = Blueprint('routes', __name__, url_prefix='/routes')

@route_bp.route('/create', methods=['POST'])
@token_required
@admin_required
def create_route(user_data):
    """
    Insere uma nova rota no banco de dados.
    ---
    tags:
      - Routes
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - route_prefix
            - description
          properties:
            route_prefix:
              type: string
              example: "/nova/rota"
            description:
              type: string
              example: "Rota para acessar dados de usuários."
    responses:
      201:
        description: Rota criada com sucesso.
      400:
        description: Campos obrigatórios ausentes.
      500:
        description: Erro interno no servidor.
    """
    try:
        data = request.json
        route_prefix = data.get("route_prefix")
        description = data.get("description")

        if not route_prefix or not description:
            return jsonify({"status": "error", "message": "Campos 'route_prefix' e 'description' são obrigatórios."}), 400

        conn = create_db_connection_mysql()
        cursor = conn.cursor()

        query = "INSERT INTO routes (route_prefix, description) VALUES (%s, %s)"
        cursor.execute(query, (route_prefix, description))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": "Rota criada com sucesso."}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@route_bp.route('/list', methods=['GET'])
@token_required
@admin_required
def list_routes(user_data):
    """
    Lista todas as rotas existentes com suporte à paginação.
    ---
    tags:
      - Routes
    parameters:
      - name: page
        in: query
        required: false
        type: integer
        description: Número da página para a paginação. Default: 1
        example: 1
      - name: limit
        in: query
        required: false
        type: integer
        description: Número de registros por página. Default: 10
        example: 10
    responses:
      200:
        description: Lista de rotas paginada.
        schema:
          type: object
          properties:
            status:
              type: string
              example: "success"
            page:
              type: integer
              example: 1
            limit:
              type: integer
              example: 10
            total:
              type: integer
              example: 50
            routes:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  route_prefix:
                    type: string
                    example: "/minha/rota"
                  description:
                    type: string
                    example: "Descrição da rota"
      500:
        description: Erro interno no servidor.
    """
    try:
        # Obter os parâmetros de paginação
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
        offset = (page - 1) * limit

        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Query para buscar as rotas com paginação
        query = f"""
            SELECT id, route_prefix, description 
            FROM routes
            ORDER BY id
            LIMIT {limit} OFFSET {offset}
        """
        cursor.execute(query)
        routes = cursor.fetchall()

        # Query para obter a contagem total de rotas
        count_query = "SELECT COUNT(*) AS total FROM routes"
        cursor.execute(count_query)
        total_count = cursor.fetchone()["total"]

        cursor.close()
        conn.close()

        # Retornar os dados paginados
        return jsonify({
            "status": "success",
            "page": page,
            "limit": limit,
            "total": total_count,
            "routes": routes
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@route_bp.route('/edit/<int:route_id>', methods=['PUT'])
@token_required
@admin_required
def edit_route(user_data, route_id):
    """
    Edita o nome de uma rota existente.
    ---
    tags:
      - Routes
    parameters:
      - name: route_id
        in: path
        required: true
        type: integer
        description: ID da rota a ser editada.
        example: 1
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - name
          properties:
            name:
              type: string
              example: "/rota/atualizada"
    responses:
      200:
        description: Nome da rota atualizado com sucesso.
      400:
        description: Campo obrigatório ausente.
      404:
        description: Rota não encontrada.
      500:
        description: Erro interno no servidor.
    """
    try:
        data = request.json
        new_name = data.get("name")

        if not new_name:
            return jsonify({"status": "error", "message": "Campo 'name' é obrigatório."}), 400

        conn = create_db_connection_mysql()
        cursor = conn.cursor()

        # Verificar se a rota existe
        cursor.execute("SELECT * FROM routes WHERE id = %s", (route_id,))
        route = cursor.fetchone()

        if not route:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Rota não encontrada."}), 404

        # Atualizar o nome da rota
        query = "UPDATE routes SET name = %s WHERE id = %s"
        cursor.execute(query, (new_name, route_id))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": "Nome da rota atualizado com sucesso."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@route_bp.route('/me', methods=['GET'])
@token_required
def get_user_routes(user_data):
    """
    Retorna todas as rotas associadas ao usuário logado.
    ---
    tags:
      - Routes
    security:
      - BearerAuth: []
    responses:
      200:
        description: Lista de rotas associadas ao usuário.
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  route_prefix:
                    type: string
                    example: "/verzo"
                  description:
                    type: string
                    example: "Rota principal da API Verzo"
      500:
        description: Erro interno no servidor.
    """
    try:
        user_id = user_data['id']

        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT r.id, r.route_prefix, r.description
            FROM routes r
            INNER JOIN user_routes ur ON r.id = ur.route_id
            WHERE ur.user_id = %s
        """
        cursor.execute(query, (user_id,))
        user_routes = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({"status": "success", "routes": user_routes}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
      
@route_bp.route('/profile/<int:user_id>', methods=['GET'])
@token_required
@admin_required
def get_routes_by_user_id(user_data, user_id):
    """
    Retorna os IDs, route_prefix e descrição das rotas associadas a um usuário específico com base no ID fornecido.
    ---
    tags:
      - Routes
    parameters:
      - name: user_id
        in: path
        required: true
        type: integer
        description: ID do usuário para buscar as rotas associadas.
        example: 1
    responses:
      200:
        description: Rotas associadas ao usuário.
        schema:
          type: object
          properties:
            status:
              type: string
              example: "success"
            routes:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  route_prefix:
                    type: string
                    example: "/dashboard"
                  description:
                    type: string
                    example: "Acesso ao dashboard principal"
      404:
        description: Usuário não encontrado ou sem rotas associadas.
      500:
        description: Erro interno no servidor.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Buscar informações das rotas associadas ao usuário
        query_routes = """
            SELECT r.id, r.route_prefix, r.description
            FROM routes r
            JOIN user_routes ur ON r.id = ur.route_id
            WHERE ur.user_id = %s
        """
        cursor.execute(query_routes, (user_id,))
        routes = cursor.fetchall()

        if not routes:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Usuário não encontrado ou sem rotas associadas."}), 404

        cursor.close()
        conn.close()

        # Retornar as informações das rotas associadas
        return jsonify({
            "status": "success",
            "routes": routes
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

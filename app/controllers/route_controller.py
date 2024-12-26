from flask import Blueprint, request, jsonify
from app.utils.decorators import token_required, admin_required, permission_required
from app.config.db_config import create_db_connection_mysql

# Blueprint para rotas
route_bp = Blueprint('routes', __name__, url_prefix='/routes')

@route_bp.route('/create', methods=['POST'])
@token_required
@admin_required
@permission_required(route_prefix='/routes')
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
@permission_required(route_prefix='/routes')
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
@permission_required(route_prefix='/routes')
def edit_route(user_data, route_id):
    """
    Edita uma rota existente com base no ID fornecido.
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
          properties:
            route_prefix:
              type: string
              example: "/nova/rota"
            description:
              type: string
              example: "Descrição da nova rota"
    responses:
      200:
        description: Rota atualizada com sucesso.
      400:
        description: Nenhum dado para atualizar ou valor duplicado.
      404:
        description: Rota não encontrada.
      500:
        description: Erro interno no servidor.
    """
    try:
        data = request.json

        # Conectar ao banco e buscar os dados existentes da rota
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Obter os valores existentes da rota
        query_get_route = "SELECT route_prefix, description FROM routes WHERE id = %s"
        cursor.execute(query_get_route, (route_id,))
        route = cursor.fetchone()

        if not route:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Rota não encontrada."}), 404

        # Use os valores existentes se os novos não forem fornecidos
        route_prefix = data.get("route_prefix", route["route_prefix"])
        description = data.get("description", route["description"])

        # Verificar se o novo route_prefix já existe para outra rota
        if route_prefix != route["route_prefix"]:
            query_check_duplicate = "SELECT id FROM routes WHERE route_prefix = %s AND id != %s"
            cursor.execute(query_check_duplicate, (route_prefix, route_id))
            duplicate = cursor.fetchone()
            if duplicate:
                cursor.close()
                conn.close()
                return jsonify({
                    "status": "error",
                    "message": f"O route_prefix '{route_prefix}' já está em uso por outra rota."
                }), 400

        # Atualizar os valores da rota no banco
        query_update = """
            UPDATE routes
            SET route_prefix = %s, description = %s
            WHERE id = %s
        """
        cursor.execute(query_update, (route_prefix, description, route_id))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": "Rota atualizada com sucesso."}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@route_bp.route('/me', methods=['GET'])
@token_required
@permission_required(route_prefix='/routes')
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
      
@route_bp.route('/profile/<int:route_id>', methods=['GET'])
@token_required
@admin_required
@permission_required(route_prefix='/routes')
def get_route_details(user_data, route_id):
    """
    Retorna os detalhes de uma rota específica com base no ID fornecido.
    ---
    tags:
      - Routes
    parameters:
      - name: route_id
        in: path
        required: true
        type: integer
        description: ID da rota para buscar os detalhes.
        example: 1
    responses:
      200:
        description: Detalhes da rota.
        schema:
          type: object
          properties:
            status:
              type: string
              example: "success"
            route:
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
        description: Rota não encontrada.
      500:
        description: Erro interno no servidor.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Buscar os detalhes da rota
        query_route = """
            SELECT id, route_prefix, description
            FROM routes
            WHERE id = %s
        """
        cursor.execute(query_route, (route_id,))
        route = cursor.fetchone()

        if not route:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Rota não encontrada."}), 404

        cursor.close()
        conn.close()

        # Retornar os detalhes da rota
        return jsonify({
            "status": "success",
            "route": route
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

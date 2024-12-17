import bcrypt
from app.config.db_config import create_mysql_connection
import jwt
from app.utils.helpers import create_token
import logging

class AuthService:
    @staticmethod
    def login(username, password):
        try:
            # Conexão com o banco
            connection = create_mysql_connection()
            cursor = connection.cursor(dictionary=True)

            # Buscar o usuário no banco
            query = "SELECT * FROM users WHERE username = %s"
            cursor.execute(query, (username,))
            user = cursor.fetchone()

            if not user:
                cursor.close()
                connection.close()
                return {"status": "error", "message": "Usuário não encontrado", "status_code": 404}

            # Verificar a senha com bcrypt
            if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                cursor.close()
                connection.close()
                return {"status": "error", "message": "Senha incorreta", "status_code": 401}

            # Buscar as rotas do usuário
            query_routes_all = "SELECT route_prefix FROM routes"
            query_user_routes = """
                SELECT r.route_prefix 
                FROM user_routes ur
                JOIN routes r ON ur.route_id = r.id
                WHERE ur.user_id = %s
            """

            if user.get('is_admin', 0) == 1:
                # Se for administrador, busca todas as rotas
                cursor.execute(query_routes_all)
                routes = [row['route_prefix'] for row in cursor.fetchall()]
            else:
                # Caso contrário, busca somente as rotas permitidas
                cursor.execute(query_user_routes, (user['id'],))
                routes = [row['route_prefix'] for row in cursor.fetchall()]

            cursor.close()
            connection.close()

            # Gerar o token JWT
            token = create_token({
                "id": user['id'],
                "username": user['username'],
                "is_admin": user.get('is_admin', False)
            })

            # Retorno com rotas
            return {
                "status": "success",
                "token": token,
                "routes": routes
            }

        except Exception as e:
            logging.error(f"Erro no AuthService: {e}")
            return {"status": "error", "message": str(e), "status_code": 500}

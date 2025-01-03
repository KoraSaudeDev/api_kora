import bcrypt
from app.config.db_config import create_mysql_connection
import logging
from app.utils.helpers import create_token

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

            # Buscar todas as rotas de acesso para o usuário
            access_slugs = []
            access_prefixes = []

            if user.get('is_admin', 0) == 1:
                # Se for administrador, busca todas as rotas
                query_access_all_slugs = "SELECT route_slug FROM access_routes WHERE route_slug IS NOT NULL"
                query_access_all_prefixes = "SELECT route_prefix FROM access_routes WHERE route_prefix IS NOT NULL"

                cursor.execute(query_access_all_slugs)
                access_slugs = [row['route_slug'] for row in cursor.fetchall()]

                cursor.execute(query_access_all_prefixes)
                access_prefixes = [row['route_prefix'] for row in cursor.fetchall()]
            else:
                # Caso contrário, busca somente as rotas permitidas no `access` (com associação ao usuário)
                query_user_access_slugs = """
                    SELECT ar.route_slug
                    FROM user_access ua
                    JOIN access_routes ar ON ua.access_id = ar.access_id
                    WHERE ua.user_id = %s AND ar.route_slug IS NOT NULL
                """
                query_user_access_prefixes = """
                    SELECT ar.route_prefix
                    FROM user_access ua
                    JOIN access_routes ar ON ua.access_id = ar.access_id
                    WHERE ua.user_id = %s AND ar.route_prefix IS NOT NULL
                """

                cursor.execute(query_user_access_slugs, (user['id'],))
                access_slugs = [row['route_slug'] for row in cursor.fetchall()]

                cursor.execute(query_user_access_prefixes, (user['id'],))
                access_prefixes = [row['route_prefix'] for row in cursor.fetchall()]

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
                "access": {
                    "slugs": access_slugs,
                    "prefixes": access_prefixes
                }
            }

        except Exception as e:
            logging.error(f"Erro no AuthService: {e}")
            return {"status": "error", "message": str(e), "status_code": 500}

    @staticmethod
    def get_user_data(username):
        try:
            connection = create_mysql_connection()
            cursor = connection.cursor(dictionary=True)

            # Buscar informações do usuário
            query_user = "SELECT * FROM users WHERE username = %s"
            cursor.execute(query_user, (username,))
            user_data = cursor.fetchone()

            if not user_data:
                return None

            # Buscar as rotas do usuário
            access_slugs = []
            access_prefixes = []

            if user_data.get('is_admin', 0) == 1:
                # Se for administrador, busca todas as rotas
                cursor.execute("SELECT route_slug FROM access_routes WHERE route_slug IS NOT NULL")
                access_slugs = [row['route_slug'] for row in cursor.fetchall()]

                cursor.execute("SELECT route_prefix FROM access_routes WHERE route_prefix IS NOT NULL")
                access_prefixes = [row['route_prefix'] for row in cursor.fetchall()]
            else:
                # Caso contrário, busca somente as rotas permitidas
                cursor.execute("""
                    SELECT route_slug
                    FROM user_access ua
                    JOIN access_routes ar ON ua.access_id = ar.access_id
                    WHERE ua.user_id = %s AND ar.route_slug IS NOT NULL
                """, (user_data['id'],))
                access_slugs = [row['route_slug'] for row in cursor.fetchall()]

                cursor.execute("""
                    SELECT route_prefix
                    FROM user_access ua
                    JOIN access_routes ar ON ua.access_id = ar.access_id
                    WHERE ua.user_id = %s AND ar.route_prefix IS NOT NULL
                """, (user_data['id'],))
                access_prefixes = [row['route_prefix'] for row in cursor.fetchall()]

            cursor.close()
            connection.close()

            user_data['access'] = {
                "slugs": access_slugs,
                "prefixes": access_prefixes
            }

            return user_data

        except Exception as e:
            logging.error(f"Erro ao buscar dados do usuário: {e}")
            return None

    @staticmethod
    def verify_password(password, hashed_password):
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    @staticmethod
    def generate_token(user_data):
        payload = {
            "id": user_data['id'],
            "username": user_data['username'],
            "is_admin": user_data.get('is_admin', False)
        }
        return create_token(payload)

from app.config.db_config import create_mysql_connection

class User:
    @staticmethod
    def get_user_by_username(username):
        connection = create_mysql_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            query = "SELECT * FROM users WHERE username = %s"
            cursor.execute(query, (username,))
            user = cursor.fetchone()
        finally:
            cursor.close()
            connection.close()
        return user

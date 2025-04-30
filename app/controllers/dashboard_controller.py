from flask import Blueprint, request, jsonify
from sqlalchemy import func, and_
from datetime import datetime
from app import db  
from app.config.db_config import create_db_connection_mysql
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/relatorio', methods=['GET'])
def dashboard_relatorio():
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor()

        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        username = request.args.get('username')
        endpoint = request.args.get('endpoint')

        filtros = []
        valores = []

        # Filtro de datas
        if data_inicio and data_fim:
            filtros.append("DATE(requested_at) BETWEEN %s AND %s")
            valores.extend([data_inicio, data_fim])
        elif data_inicio:
            filtros.append("DATE(requested_at) = %s")
            valores.append(data_inicio)
        elif data_fim:
            filtros.append("DATE(requested_at) = %s")
            valores.append(data_fim)

        if username:
            filtros.append("username = %s")
            valores.append(username)
        if endpoint:
            filtros.append("endpoint = %s")
            valores.append(endpoint)

        where_clause = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        # Gráfico 1: Top 10 rotas mais acessadas
        cursor.execute(f"""
            SELECT endpoint, COUNT(*) AS quantidade
            FROM request_logs
            {where_clause}
            GROUP BY endpoint
            ORDER BY quantidade DESC
            LIMIT 10
        """, valores)
        rotas_data = [{"endpoint": row[0], "quantidade": row[1]} for row in cursor.fetchall()]
        total_rotas = sum(r["quantidade"] for r in rotas_data)

        # Gráfico 2: Top 10 usuários que mais acessaram
        cursor.execute(f"""
            SELECT username, COUNT(*) AS quantidade
            FROM request_logs
            {where_clause}
            GROUP BY username
            ORDER BY quantidade DESC
            LIMIT 10
        """, valores)
        usuarios_data = [{"username": row[0], "quantidade": row[1]} for row in cursor.fetchall()]

        # Novo total_usuarios: total de usuários cadastrados na tabela `users`
        cursor.execute("SELECT COUNT(*) FROM users")
        total_usuarios = cursor.fetchone()[0]

        # Gráfico 3: Requisições por dia
        if not data_inicio and not data_fim:
            # últimos 7 dias por padrão
            filtros_dias = ["requested_at >= %s"]
            valores_dias = [(datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d')]
            if username:
                filtros_dias.append("username = %s")
                valores_dias.append(username)
            if endpoint:
                filtros_dias.append("endpoint = %s")
                valores_dias.append(endpoint)
            where_clause_dias = f"WHERE {' AND '.join(filtros_dias)}"
        else:
            where_clause_dias = where_clause
            valores_dias = valores

        cursor.execute(f"""
            SELECT DATE(requested_at) AS dia, COUNT(*) AS quantidade
            FROM request_logs
            {where_clause_dias}
            GROUP BY dia
            ORDER BY dia ASC
        """, valores_dias)
        dias_data = [
            {"dia": row[0].strftime('%Y-%m-%d'), "quantidade": row[1]}
            for row in cursor.fetchall()
        ]
        total_dias = sum(d["quantidade"] for d in dias_data)

        cursor.close()
        conn.close()

        return jsonify({
            "rotas": {
                "total": total_rotas,
                "dados": rotas_data
            },
            "usuarios": {
                "total": total_usuarios,
                "dados": usuarios_data
            },
            "dias": {
                "total": total_dias,
                "dados": dias_data
            }
        }), 200

    except Exception as e:
        return jsonify({"error": f"Erro ao gerar relatório: {str(e)}"}), 500

@dashboard_bp.route('/usuarios', methods=['GET'])
def listar_usuarios_unicos():
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT username
            FROM request_logs
            WHERE username IS NOT NULL
            ORDER BY username
        """)
        usuarios = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return jsonify({"usuarios": usuarios}), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar usuários: {str(e)}"}), 500

@dashboard_bp.route('/rotas', methods=['GET'])
def listar_rotas_unicas():
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT endpoint
            FROM request_logs
            WHERE endpoint IS NOT NULL
            ORDER BY endpoint
        """)
        rotas = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return jsonify({"rotas": rotas}), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar rotas: {str(e)}"}), 500

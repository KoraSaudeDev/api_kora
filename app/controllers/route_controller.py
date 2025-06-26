import os
from flask import Blueprint, request, jsonify
from app.utils.decorators import token_required, admin_required, permission_required
from app.config.db_config import create_db_connection_mysql
from datetime import datetime
from app.utils.db_connection_util import connect_to_database
import json
import logging
import unidecode
import re
import sys
import traceback
import cx_Oracle
from sqlalchemy.sql import text
from app.utils.db_connections import create_oracle_connection, create_mysql_connection
from app.utils.security import decrypt_password
from typing import Tuple

# Blueprint para rotas
route_bp = Blueprint('routes', __name__, url_prefix='/routes')

# Caminho base para as pastas de queries
BASE_QUERIES_PATH = os.path.join("app", "queries")

def generate_slug(name):
    """
    Gera um slug a partir de um nome.
    """
    if not name:
        raise ValueError("O campo 'name' não pode estar vazio para gerar um slug.")
    name = unidecode.unidecode(name)  # Remove acentos
    name = re.sub(r'[^a-zA-Z0-9\s]', '', name)  # Remove caracteres especiais
    return name.strip().replace(' ', '_').lower()

@route_bp.route('/create', methods=['POST'])
@token_required
@permission_required(route_prefix='/routes')
def create_route(user_data):
    """
    Cria uma nova rota, salvando no banco os dados de query normal, pré-processada e/ou pós-processada,
    relacionando também com sistemas e conexões, e parâmetros com stage opcional ('default' ou 'post').
    """
    try:
        # 1) Obter os dados da requisição
        data = request.json or {}
        logging.info(f"Requisição recebida: {json.dumps(data, indent=4)}")

        # 2) Extrair campos principais
        name               = data.get("name")
        system_id          = data.get("system_id")
        connection_ids     = data.get("connection_ids", [])
        pre_query          = data.get("pre_query")
        query_true         = data.get("query_true")
        query_false        = data.get("query_false")
        query              = data.get("query")           # query principal
        post_query         = data.get("post_query")
        dml_personalizado  = data.get("dml_personalizado")
        is_pre_processed   = data.get("is_pre_processed", False)
        is_post_processed  = data.get("is_post_processed", False)
        parameters         = data.get("parameters", [])

        # 3) Validações de existência de query
        if not any([query, pre_query, query_true, query_false, post_query, dml_personalizado]):
            return jsonify({
                "status": "error",
                "message": ("Pelo menos uma das queries (query, pre_query, query_true, query_false, "
                            "post_query ou dml_personalizado) deve estar preenchida.")
            }), 400

        if is_pre_processed and not any([pre_query, query_true, query_false]):
            return jsonify({
                "status": "error",
                "message": ("Pré-processamento ativado, mas nenhuma query foi fornecida "
                            "(pre_query, query_true, query_false).")
            }), 400

        if is_post_processed and not post_query:
            return jsonify({
                "status": "error",
                "message": "Pós-processamento ativado, mas post_query está vazia."
            }), 400

        # 4) Determinar tipo de rota
        if is_pre_processed and is_post_processed:
            query_type = "pré e pós-processada"
        elif is_pre_processed:
            query_type = "pré-processada"
        elif is_post_processed:
            query_type = "pós-processada"
        else:
            query_type = "normal"

        # 5) Gerar slug
        slug = generate_slug(name)
        logging.info(f"Gerado slug: {slug} | Tipo de query: {query_type}")

        # 6) Conectar ao MySQL e inserir na tabela routes
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)
        query_insert_route = """
            INSERT INTO routes
                (name, slug, system_id, query, pre_query, query_true, query_false, post_query,
                 dml_personalizado, is_pre_processed, is_post_processed, query_path, created_at)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """
        cursor.execute(query_insert_route, (
            name, slug, system_id, query, pre_query, query_true, query_false, post_query,
            dml_personalizado, is_pre_processed, is_post_processed, None
        ))
        route_id = cursor.lastrowid

        # 7) Inserir parâmetros com stage opcional (NULL = default)
        if parameters:
            query_insert_parameters = """
                INSERT INTO route_parameters
                  (route_id, name, type, value, stage)
                VALUES (%s, %s, %s, %s, %s)
            """
            for param in parameters:
                param_name  = param.get("name")
                param_type  = param.get("type", "").lower()
                param_value = param.get("value", "")
                stage       = param.get("stage")  # 'default', 'post' ou None

                # validar stage
                if stage not in (None, "default", "post"):
                    return jsonify({
                        "status": "error",
                        "message": f"Stage inválido no parâmetro '{param_name}': {stage}"
                    }), 400

                # **tratamento de boolean**
                if param_type == "boolean":
                    if isinstance(param_value, bool):
                        param_value = 1 if param_value else 0
                    else:
                        sval = str(param_value).strip().lower()
                        param_value = 1 if sval in ("1", "true", "t", "s", "y", "yes") else 0

                logging.info(f"Parâmetro => name: {param_name}, type: {param_type}, "
                             f"value: {param_value}, stage: {stage or 'default'}")
                cursor.execute(
                    query_insert_parameters,
                    (route_id, param_name, param_type, param_value, stage)
                )

        # 8) Relacionar a rota com conexões
        if connection_ids:
            query_insert_connections = """
                INSERT INTO route_connections (route_id, connection_id)
                VALUES (%s, %s)
            """
            for conn_id in connection_ids:
                cursor.execute(query_insert_connections, (route_id, conn_id))

        # 9) Commit e cleanup
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "Rota criada com sucesso.",
            "route_id": route_id,
            "query_type": query_type
        }), 201

    except Exception as e:
        logging.error(f"❌ Erro ao criar rota: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@route_bp.route('/list', methods=['GET'])
@token_required
@permission_required(route_prefix='/routes')
def list_routes(user_data):
    """
    Lista todas as rotas com suas associações e suporta paginação.
    Inclui agora em cada parâmetro o seu 'stage' (ou 'default' quando NULL).
    """
    try:
        # Obter parâmetros de paginação
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 1000))
        offset = (page - 1) * limit

        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # 1) Buscar rotas com paginação
        query_routes = f"""
            SELECT r.id,
                   r.name,
                   r.slug,
                   r.query,
                   r.created_at,
                   r.updated_at,
                   GROUP_CONCAT(DISTINCT rs.system_id)     AS system_ids,
                   GROUP_CONCAT(DISTINCT rc.connection_id) AS connection_ids
              FROM routes r
              LEFT JOIN route_systems rs       ON r.id = rs.route_id
              LEFT JOIN route_connections rc   ON r.id = rc.route_id
             GROUP BY r.id
             ORDER BY r.name
             LIMIT {limit} OFFSET {offset}
        """
        cursor.execute(query_routes)
        routes = cursor.fetchall()

        # 2) Buscar parâmetros (agora incluindo o campo stage)
        query_parameters = """
            SELECT
                rp.route_id,
                rp.name            AS parameter_name,
                rp.type            AS parameter_type,
                rp.value           AS parameter_value,
                rp.stage           AS parameter_stage
              FROM route_parameters rp
        """
        cursor.execute(query_parameters)
        parameters = cursor.fetchall()

        cursor.close()
        conn.close()

        # 3) Agrupar parâmetros por rota
        route_parameters = {}
        for p in parameters:
            rid   = p["route_id"]
            stage = p["parameter_stage"] or "default"
            entry = {
                "name":  p["parameter_name"],
                "type":  p["parameter_type"],
                "value": p["parameter_value"],
                "stage": stage
            }
            route_parameters.setdefault(rid, []).append(entry)

        # 4) Contar total de rotas
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS total FROM routes")
        total_count = cursor.fetchone()["total"]
        cursor.close()
        conn.close()

        # 5) Montar payload
        response = []
        for r in routes:
            response.append({
                "id":             r["id"],
                "name":           r["name"],
                "slug":           r["slug"],
                "query":          r["query"],
                "created_at":     r["created_at"],
                "updated_at":     r["updated_at"],
                "system_ids":     (r["system_ids"]     or "").split(","),
                "connection_ids": (r["connection_ids"] or "").split(","),
                "parameters":     route_parameters.get(r["id"], [])
            })

        return jsonify({
            "status": "success",
            "page":    page,
            "limit":   limit,
            "total":   total_count,
            "routes":  response
        }), 200

    except Exception as e:
        logging.exception("Erro ao listar rotas")
        return jsonify({
            "status":  "error",
            "message": str(e)
        }), 500

@route_bp.route('/connections', methods=['POST'])
@token_required
@permission_required(route_prefix='/routes')
def update_route_connections(user_data):
    """
    Atualiza as conexões associadas a uma rota.
    """
    try:
        data = request.json
        route_id = data.get("route_id")
        connection_ids = data.get("connection_ids")

        if not route_id or not connection_ids:
            return jsonify({"status": "error", "message": "Os campos 'route_id' e 'connection_ids' são obrigatórios."}), 400

        conn = create_db_connection_mysql()
        cursor = conn.cursor()

        # Verificar se a rota existe
        query_check_route = "SELECT id FROM routes WHERE id = %s"
        cursor.execute(query_check_route, (route_id,))
        if not cursor.fetchone():
            return jsonify({"status": "error", "message": "Rota não encontrada."}), 404

        # Remover conexões antigas
        query_delete = "DELETE FROM route_connections WHERE route_id = %s"
        cursor.execute(query_delete, (route_id,))

        # Adicionar novas conexões
        query_insert = "INSERT INTO route_connections (route_id, connection_id) VALUES (%s, %s)"
        for connection_id in connection_ids:
            cursor.execute(query_insert, (route_id, connection_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": "Conexões da rota atualizadas com sucesso."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@route_bp.route('/<int:route_id>/connections', methods=['GET'])
@token_required
@permission_required(route_prefix='/routes')
def list_route_connections(user_data, route_id):
    """
    Lista as conexões associadas a uma rota específica.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT c.id, c.name, c.db_type, c.host, c.port
            FROM connections c
            JOIN route_connections rc ON c.id = rc.connection_id
            WHERE rc.route_id = %s
        """
        cursor.execute(query, (route_id,))
        connections = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({"status": "success", "connections": connections}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@route_bp.route('/edit/<int:route_id>', methods=['PUT'])
@token_required
@permission_required(route_prefix='/routes')
def edit_route(user_data, route_id):
    """
    Edita uma rota existente com base no ID fornecido, now incluindo:
      - post_query, pre_query, query_true, query_false, dml_personalizado
      - flags is_pre_processed, is_post_processed
      - tratamento de parâmetros com stage e tipos especiais
    """
    try:
        data = request.json or {}
        if not data:
            return jsonify({"status": "error", "message": "Nenhum dado enviado para atualização."}), 400

        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # 1) Verifica se a rota existe
        cursor.execute("SELECT * FROM routes WHERE id = %s", (route_id,))
        existing = cursor.fetchone()
        if not existing:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Rota não encontrada."}), 404

        # 2) Campos que podem ser atualizados diretamente
        editable = [
            "name", "query", "pre_query", "query_true", "query_false",
            "post_query", "dml_personalizado", "is_pre_processed", "is_post_processed"
        ]
        update_fields = []
        update_values = []
        for field in editable:
            if field in data:
                update_fields.append(f"{field} = %s")
                update_values.append(data[field])

        # se mudou name, atualiza slug também
        if "name" in data:
            new_slug = generate_slug(data["name"])
            update_fields.append("slug = %s")
            update_values.append(new_slug)

        # salvar query em arquivo, se solicitado
        if data.get("save_query_to_file") and "query" in data:
            slug = new_slug if "name" in data else existing["slug"]
            folder = os.path.join("app", "queries", slug)
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, f"{slug}.sql")
            with open(path, "w", encoding="utf-8") as f:
                f.write(data["query"])
            update_fields.append("query_path = %s")
            update_values.append(path)

        if update_fields:
            update_values.append(route_id)
            sql = f"UPDATE routes SET {', '.join(update_fields)} WHERE id = %s"
            cursor.execute(sql, tuple(update_values))

        # 3) Sistemas
        if "system_id" in data:
            cursor.execute("DELETE FROM route_systems WHERE route_id = %s", (route_id,))
            sids = data["system_id"]
            if not isinstance(sids, list):
                sids = [sids]
            for sid in sids:
                cursor.execute(
                    "INSERT INTO route_systems (route_id, system_id) VALUES (%s, %s)",
                    (route_id, sid)
                )

        # 4) Conexões
        if "connection_ids" in data:
            cursor.execute("DELETE FROM route_connections WHERE route_id = %s", (route_id,))
            for cid in data["connection_ids"]:
                cursor.execute(
                    "INSERT INTO route_connections (route_id, connection_id) VALUES (%s, %s)",
                    (route_id, cid)
                )

        # 5) Parâmetros (com stage e tipos especiais)
        if "parameters" in data:
            cursor.execute("DELETE FROM route_parameters WHERE route_id = %s", (route_id,))
            for param in data["parameters"]:
                name   = param.get("name")
                ptype  = (param.get("type") or "").lower()
                pvalue = param.get("value")
                stage  = param.get("stage")

                # data / datetime
                if ptype == "date" and pvalue:
                    pvalue = f"STR_TO_DATE('{pvalue}', '%Y-%m-%d')"
                elif ptype == "datetime" and pvalue:
                    pvalue = f"STR_TO_DATE('{pvalue}', '%Y-%m-%d %H:%i:%s')"
                # boolean
                elif ptype == "boolean":
                    if isinstance(pvalue, bool):
                        pvalue = 1 if pvalue else 0
                    else:
                        sval = str(pvalue).strip().lower()
                        pvalue = 1 if sval in ("1","true","t","s","y","yes") else 0

                cursor.execute(
                    """
                    INSERT INTO route_parameters
                      (route_id, name, type, value, stage)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (route_id, name, ptype, pvalue, stage)
                )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": "Rota atualizada com sucesso."}), 200

    except Exception as e:
        logging.exception("Erro ao editar rota")
        return jsonify({"status": "error", "message": str(e)}), 500

@route_bp.route('/profile/<int:route_id>', methods=['GET'])
@token_required
@permission_required(route_prefix='/routes')
def get_route_details(user_data, route_id):
    """
    Retorna os detalhes de uma rota específica com base no ID fornecido,
    incluindo parâmetros (com stage), conexões e sistemas vinculados.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # 1) Buscar os detalhes da rota
        query_route = """
            SELECT id, name, slug, query, description, post_query, system_id
            FROM routes
            WHERE id = %s
        """
        cursor.execute(query_route, (route_id,))
        route = cursor.fetchone()
        if not route:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Rota não encontrada."}), 404

        # 2) Buscar os parâmetros da rota, agora com o campo 'stage'
        query_parameters = """
            SELECT name, type, value, stage
            FROM route_parameters
            WHERE route_id = %s
        """
        cursor.execute(query_parameters, (route_id,))
        parameters = cursor.fetchall()
        # Se algum value vier nulo, transformamos em string vazia
        for param in parameters:
            if param["value"] is None:
                param["value"] = ""
            # stage pode ser None → no JSON ficará null

        # 3) Buscar as conexões associadas
        query_connections = """
            SELECT c.id, c.name, c.db_type, c.host, c.port,
                   c.username, c.database_name, c.slug
            FROM connections c
            JOIN route_connections rc ON c.id = rc.connection_id
            WHERE rc.route_id = %s
        """
        cursor.execute(query_connections, (route_id,))
        connections = cursor.fetchall()

        # 4) Buscar sistemas associados
        query_systems = """
            SELECT s.id, s.name, s.slug
            FROM systems s
            JOIN route_systems rs ON s.id = rs.system_id
            WHERE rs.route_id = %s
        """
        cursor.execute(query_systems, (route_id,))
        systems = cursor.fetchall()
        # fallback para campo system_id em routes
        if not systems and route.get("system_id"):
            cursor.execute("SELECT id, name, slug FROM systems WHERE id = %s", (route["system_id"],))
            system = cursor.fetchone()
            if system:
                systems = [system]

        cursor.close()
        conn.close()

        # 5) Montar o objeto de resposta
        route["parameters"]  = parameters
        route["connections"] = connections
        route["systems"]     = systems

        return jsonify({"status": "success", "route": route}), 200

    except Exception as e:
        logging.exception("Erro ao buscar detalhes da rota")
        return jsonify({"status": "error", "message": str(e)}), 500

def remove_quoted_strings(sql: str) -> str:
    """
    Remove tudo que está entre aspas simples em uma instrução SQL,
    para que 'HH24:MI:SS' não gere :MI, :SS como falsas bind vars.
    """
    return re.sub(r"'[^']*'", '', sql)

@route_bp.route('/execute/<slug>', methods=['POST'])
@token_required
@permission_required(route_prefix='/routes/execute')
def execute_route_query(user_data, slug):
    try:
        logging.error(f"🔹 [INICIANDO EXECUÇÃO] - Slug recebido: {slug}")
        request_data = request.json or {}
        logging.error(f"📅 Dados recebidos na requisição:\n{json.dumps(request_data, indent=4)}")

        provided_connections = request_data.get("connections", [])
        provided_parameters_list = request_data.get("parameters", [])
        provided_parameters = {
            conn_name.lower(): params
            for param_entry in provided_parameters_list
            for conn_name, params in param_entry.items()
        }

        # Obter rota
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT r.id, r.query FROM routes r WHERE r.slug = %s", (slug,))
        route = cursor.fetchone()
        cursor.close()
        conn.close()

        if not route:
            return jsonify({"status": "error", "message": f"❌ Rota não encontrada para o slug: {slug}"}), 404

        query_legacy = route['query']

        # Obter conexões
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT DISTINCT c.* FROM connections c
            JOIN route_connections rc ON c.id = rc.connection_id
            WHERE rc.route_id = %s
        """, (route['id'],))
        connections = cursor.fetchall()
        cursor.close()
        conn.close()

        slugs_requisitados = [c.strip().lower() for c in provided_connections]
        results = {}
        executed_any_query = False
        last_error = None

        def remove_invalid_column_from_query(query: str, param_name: str) -> str:
            logging.warning(f"🛠️ Removendo coluna inválida: {param_name}")

            # ✅ Lógica específica para os slugs especiais
            if slug in ['bluemind_mv_tab115', 'bluemind_mv_tab116']:
                logging.warning(f"🔁 Substituindo query para slug '{slug}' devido a erro de coluna inválida")
                if slug == 'bluemind_mv_tab115':
                    return """
                    INSERT INTO DBAMV.PROIBICAO (
                        CD_PRO_FAT, CD_CON_PLA, CD_CONVENIO, DS_PROIBICAO, TP_PROIBICAO,
                        TP_ATENDIMENTO, DT_INICIAL_PROIBICAO, CD_MULTI_EMPRESA,
                        CD_SETOR, CD_REGRA_PROIBICAO_VALOR
                    )
                    SELECT DISTINCT
                        pf.cd_pro_fat, cp.CD_CON_PLA, ecp.CD_CONVENIO, :DS_PROIBICAO,
                        :TP_PROIBICAO, :TP_ATENDIMENTO, TO_DATE(:DT_INICIAL_PROIBICAO, 'DD/MM/YYYY'),
                        ecp.CD_MULTI_EMPRESA, :CD_SETOR, :CD_REGRA_PROIBICAO_VALOR
                    FROM dbamv.CON_PLA cp, dbamv.EMPRESA_CON_PLA ecp, dbamv.pro_fat pf
                    WHERE cp.CD_CONVENIO = ecp.CD_CONVENIO
                        AND cp.CD_CON_PLA = ecp.CD_CON_PLA
                        AND cp.SN_ATIVO = 'S'
                        AND ecp.SN_ATIVO = 'S'
                        AND ecp.CD_CONVENIO = :CD_CONVENIO
                        AND ecp.CD_MULTI_EMPRESA = :CD_MULTI_EMPRESA
                        AND ecp.CD_CON_PLA = NVL(:CD_CON_PLA, ecp.CD_CON_PLA)
                        AND pf.sn_ativo = 'S'
                        AND pf.CD_PRO_FAT = :CD_PRO_FAT
                        AND NOT EXISTS (
                            SELECT 'K'
                            FROM DBAMV.PROIBICAO p
                            WHERE p.CD_PRO_FAT = pf.cd_pro_fat
                                AND p.CD_CONVENIO = cp.CD_CONVENIO
                                AND NVL(p.CD_CON_PLA, 0) = NVL(cp.CD_CON_PLA, 0)
                                AND p.TP_PROIBICAO = :TP_PROIBICAO
                                AND p.TP_ATENDIMENTO = NVL(:TP_ATENDIMENTO, p.TP_ATENDIMENTO)
                                AND TRUNC(p.DT_INICIAL_PROIBICAO) = TRUNC(TO_DATE(:DT_INICIAL_PROIBICAO, 'DD/MM/YYYY'))
                                AND p.CD_MULTI_EMPRESA = ecp.CD_MULTI_EMPRESA
                                AND NVL(p.cd_setor, 0) = NVL(:CD_SETOR, 0)
                        )
                    """
                elif slug == 'bluemind_mv_tab116':
                    return """
        INSERT INTO DBAMV.PROIBICAO (
             CD_PRO_FAT, CD_CON_PLA, CD_CONVENIO, DS_PROIBICAO, TP_PROIBICAO,
             TP_ATENDIMENTO, DT_INICIAL_PROIBICAO, CD_MULTI_EMPRESA,
             CD_SETOR, CD_REGRA_PROIBICAO_VALOR
                    )
                    SELECT DISTINCT
             pf.cd_pro_fat, cp.CD_CON_PLA, ecp.CD_CONVENIO, :DS_PROIBICAO,
             :TP_PROIBICAO, :TP_ATENDIMENTO, TO_DATE(:DT_INICIAL_PROIBICAO, 'DD/MM/YYYY'),
             ecp.CD_MULTI_EMPRESA, :CD_SETOR, :CD_REGRA_PROIBICAO_VALOR
         FROM dbamv.CON_PLA cp, dbamv.EMPRESA_CON_PLA ecp, dbamv.pro_fat pf
         WHERE cp.CD_CONVENIO = ecp.CD_CONVENIO
             AND cp.CD_CON_PLA = ecp.CD_CON_PLA
                        AND cp.SN_ATIVO = 'S'
                        AND ecp.SN_ATIVO = 'S'
             AND ecp.CD_CONVENIO = :CD_CONVENIO
             AND ecp.CD_MULTI_EMPRESA = :CD_MULTI_EMPRESA
             AND ecp.CD_CON_PLA = NVL(:CD_CON_PLA, ecp.CD_CON_PLA)
                        AND pf.sn_ativo = 'S'
           AND pf.CD_GRU_PRO = :CD_PRO_FAT
                        AND NOT EXISTS (
                            SELECT 'K'
                 FROM DBAMV.PROIBICAO p
                 WHERE p.CD_PRO_FAT = pf.cd_pro_fat
                   AND p.CD_CONVENIO = cp.CD_CONVENIO
                     AND NVL(p.CD_CON_PLA, 0) = NVL(cp.CD_CON_PLA, 0)
                   AND p.TP_PROIBICAO = :TP_PROIBICAO
                     AND p.TP_ATENDIMENTO = NVL(:TP_ATENDIMENTO, p.TP_ATENDIMENTO)
                     AND TRUNC(p.DT_INICIAL_PROIBICAO) = TRUNC(TO_DATE(:DT_INICIAL_PROIBICAO, 'DD/MM/YYYY'))
                     AND p.CD_MULTI_EMPRESA = ecp.CD_MULTI_EMPRESA
                     AND NVL(p.cd_setor, 0) = NVL(:CD_SETOR, 0)
                        )
                    """

            # 🔧 Caso comum continua aqui
            original_query = query
            query = re.sub(rf"TO_DATE\s*\(\s*:\s*{param_name}\s*,\s*'[^']*'\s*\)", '', query, flags=re.IGNORECASE)
            query = re.sub(rf"TRUNC\s*\(\s*:\s*{param_name}\s*\)", '', query, flags=re.IGNORECASE)
            query = re.sub(rf"NVL\s*\(\s*:\s*{param_name}\s*,\s*[^)]+\)", '', query, flags=re.IGNORECASE)
            query = re.sub(rf":{param_name}\b", '', query, flags=re.IGNORECASE)
            query = re.sub(rf'\b{param_name}\b\s*,?', '', query, flags=re.IGNORECASE)
            query = re.sub(r',\s*\)', ')', query)
            query = re.sub(
                rf'AND\s+[^()]*{param_name}[^()]*?(=|<>|<|>|IS|LIKE|IN)[^()]*',
                '', query, flags=re.IGNORECASE
            )
            query = re.sub(r'TO_DATE\s*\(\s*:\s*,\s*\'[^\']*\'\s*\)', '', query, flags=re.IGNORECASE)
            query = re.sub(r',\s*,', ',', query)
            query = re.sub(r'\(\s*,', '(', query)
            query = re.sub(r',\s*\)', ')', query)
            query = re.sub(r',\s*FROM', ' FROM', query, flags=re.IGNORECASE)
            query = re.sub(r'\s+', ' ', query).strip()

            logging.error(f"🧼 Query original:\n{original_query}")
            logging.error(f"🧹 Query após remover '{param_name}':\n{query}")
            return query


        def build_update_query_with_non_nulls(query: str, params: dict) -> Tuple[str, dict]:
            # 🔒 Validação obrigatória do campo primary_key
            primary_key = params.get("primary_key")
            if primary_key in [None, "", "null", "none"]:
                raise ValueError("❌ Parâmetro obrigatório 'primary_key' não foi informado ou está vazio.")

            set_clause_match = re.search(r'SET\s+(.*?)\s+WHERE', query, re.IGNORECASE | re.DOTALL)
            if not set_clause_match:
                return query, params

            set_clause = set_clause_match.group(1)
            assignments = re.findall(r'(\w+)\s*=\s*(TO_DATE\s*\(:\w+[^)]*\)|:\w+)', set_clause)

            kept_assignments = []
            kept_params = {}

            for column, expression in assignments:
                param_match = re.search(r':(\w+)', expression)
                if not param_match:
                    continue
                param_name = param_match.group(1).lower()
                value = params.get(param_name)
                if value not in [None, "", "null"]:
                    kept_assignments.append(f"{column} = {expression}")
                    kept_params[param_name] = value

            set_clause_clean = ', '.join(kept_assignments)
            new_query = re.sub(r'SET\s+.*?\s+WHERE', f"SET {set_clause_clean} WHERE", query, flags=re.IGNORECASE | re.DOTALL)

            # Mantém parâmetros do WHERE mesmo se não estiverem no SET
            where_params = re.findall(r':(\w+)', new_query)
            for param in where_params:
                param_lower = param.lower()
                if param_lower not in kept_params:
                    kept_params[param_lower] = params.get(param_lower)

            return new_query, kept_params

        for connection in connections:
            db_slug = connection['slug'].strip().lower()
            if db_slug not in slugs_requisitados:
                continue

            logging.error(f"✅ Conexão {db_slug} será utilizada para execução.")
            password = decrypt_password(connection['password'])

            # 1) Levantar a conexão certa
            if connection['db_type'] == 'oracle':
                db_conn = create_oracle_connection(
                    host=connection['host'],
                    port=connection['port'],
                    user=connection['username'],
                    password=password,
                    service_name=connection.get('service_name'),
                    sid=connection.get('sid')
                )
                placeholder_style = "oracle"
            elif connection['db_type'] in ('mysql', 'mariadb'):
                db_conn = create_db_connection_mysql(
                    host=connection['host'],
                    port=connection['port'],
                    user=connection['username'],
                    password=password,
                    database=connection['database_name']
                )
                placeholder_style = "mysql"
            else:
                results[db_slug] = f"⚠️ Tipo de DB não suportado: {connection['db_type']}"
                continue

            if not db_conn:
                results[db_slug] = f"⚠️ Falha ao conectar com {db_slug}."
                continue

            db_cursor = db_conn.cursor()
            if db_slug not in provided_parameters:
                results[db_slug] = f"⚠️ Nenhum parâmetro enviado para {db_slug}."
                db_cursor.close()
                continue

            user_param_dict = provided_parameters[db_slug]
            final_params = {k.lower(): v for k, v in user_param_dict.items()}
            current_query = re.sub(r"@(\w+)", r":\1", query_legacy)

            attempt_count = 0
            removed_columns = []

            while True:
                attempt_count += 1
                query_type = current_query.strip().split()[0].upper()

                if query_type == "UPDATE":
                    current_query, query_parameters = build_update_query_with_non_nulls(current_query, final_params)
                else:
                    found_vars = re.findall(r':(\w+)', current_query)
                    query_parameters = {var.lower(): final_params.get(var.lower()) for var in found_vars}

                logging.error(f"🪢 [Tentativa {attempt_count}] Executando query para {db_slug}")
                logging.error(f"📝 Query atual:\n{current_query}")
                logging.error(f"📌 Parâmetros:\n{json.dumps(query_parameters, indent=4)}")

                try:
                    db_cursor.execute(current_query, query_parameters)
                    db_conn.commit()
                    executed_any_query = True
                    rows_affected = db_cursor.rowcount
                    logging.info(f"📊 Linhas afetadas: {rows_affected}")

                    results[db_slug] = {
                        "message": "✅ Query executada com sucesso.",
                        "executed_query": current_query,
                        "query_parameters": query_parameters,
                        "rows_affected": rows_affected
                    }
                    break

                except Exception as e:
                    last_error = str(e)
                    logging.error(f"❌ Erro tentativa {attempt_count}: {last_error}")
                    logging.error(traceback.format_exc())

                    # ✅ Trata erros de coluna inválida ou sinônimo inválido
                    if "invalid identifier" in last_error.lower() or "synonym translation is no longer valid" in last_error.lower():
                        match = re.search(r'ORA-00904:\s+"?(?:\w+"\.)?"?(?P<coluna>\w+)"?', last_error)
                        
                        if match:
                            invalid_column = match.group("coluna")
                            removed_columns.append(invalid_column)
                            current_query = remove_invalid_column_from_query(current_query, invalid_column)
                            continue  # tenta novamente com a coluna removida
                        elif "synonym translation is no longer valid" in last_error.lower():
                            if slug in ['bluemind_mv_tab115', 'bluemind_mv_tab116']:
                                logging.warning("🔁 Substituindo query para slug especial após ORA-00980 (synonym inválido).")
                                current_query = remove_invalid_column_from_query(current_query, "")  # força uso da query alternativa
                                continue
                            else:
                                logging.warning("⚠️ ORA-00980 em slug sem tratamento especial.")
                                break
                        else:
                            logging.warning("⚠️ 'invalid identifier' ou erro relacionado sem coluna capturada.")
                            break


                    # ❌ Qualquer outro erro deve encerrar a execução
                    results[db_slug] = {
                        "error": f"❌ Falha na execução",
                        "message": last_error,
                        "executed_query": current_query,
                        "query_parameters": query_parameters
                    }
                    break

            db_cursor.close()

        if not executed_any_query:
            return jsonify({
                "status": "error",
                "message": "Nenhuma query foi executada.",
                "last_error": last_error,
                "data": results
            }), 400

        return jsonify({"status": "success", "data": results}), 200

    except Exception as e:
        logging.error(f"❌ Erro inesperado: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500


@route_bp.route('/bluemind/sequence/', methods=['POST'])
@token_required
@permission_required(route_prefix='/routes')
def get_sequence_nextval(user_data):
    try:
        logging.error("🔹 [INICIANDO EXECUÇÃO] - Obtendo NEXTVAL da sequência")
        sys.stdout.flush()

        request_data = request.json or {}
        logging.error(f"📥 Dados recebidos na requisição:\n{json.dumps(request_data, indent=4)}")
        sys.stdout.flush()

        provided_connections = request_data.get("connections", [])
        provided_parameters_list = request_data.get("parameters", [])

        provided_parameters = {}
        for param_entry in provided_parameters_list:
            for connection_name, params in param_entry.items():
                provided_parameters[connection_name] = params

        # Criar conexão com MySQL para buscar credenciais das conexões Oracle
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        query_connections = """
            SELECT c.slug, c.db_type, c.host, c.port, c.username, c.password, c.service_name, c.sid
            FROM connections c
            WHERE c.slug IN (%s)
        """ % (",".join(["%s"] * len(provided_connections)))

        cursor.execute(query_connections, tuple(provided_connections))
        connections = {conn["slug"]: conn for conn in cursor.fetchall()}
        cursor.close()
        conn.close()

        if not connections:
            return jsonify({"status": "error", "message": "❌ Nenhuma conexão válida encontrada no banco de dados."}), 404

        results = {}
        executed_any_query = False
        last_error = None

        # Percorre conexões e executa queries
        for db_slug, user_param_dict in provided_parameters.items():
            db_slug_lower = db_slug.strip().lower()
            if db_slug_lower not in connections:
                continue

            logging.error(f"✅ Conexão {db_slug} será utilizada para execução.")
            sys.stdout.flush()

            try:
                # Obter detalhes da conexão
                conn_details = connections[db_slug_lower]
                if conn_details["db_type"].lower() != "oracle":
                    results[db_slug] = f"⚠️ Conexão {db_slug} não é um banco Oracle."
                    continue

                password = decrypt_password(conn_details["password"])
                db_conn = create_oracle_connection(
                    host=conn_details["host"],
                    port=conn_details["port"],
                    user=conn_details["username"],
                    password=password,
                    service_name=conn_details.get("service_name"),
                    sid=conn_details.get("sid")
                )

                if not db_conn:
                    results[db_slug] = f"⚠️ Não foi possível criar conexão para {db_slug}."
                    continue

                db_cursor = db_conn.cursor()

                # Obtendo o nome da sequência
                sequence_name = user_param_dict.get("sequence")
                if not sequence_name:
                    results[db_slug] = "⚠️ Nenhuma sequência informada."
                    db_cursor.close()
                    continue

                logging.error(f"🔍 [{db_slug}] Obtendo NEXTVAL de {sequence_name}")

                # Montando a query dinâmica
                query = f"SELECT {sequence_name}.NEXTVAL AS id_sequence_utilizada FROM DUAL"
                logging.error(f"🔥 [ORACLE] Query final:\n{query}")
                sys.stdout.flush()

                # Executando a query
                db_cursor.execute(query)
                result = db_cursor.fetchone()

                # Fechando conexão
                db_cursor.close()
                db_conn.close()

                if result:
                    results[db_slug] = {
                        "message": "NEXTVAL obtido com sucesso",
                        "id_sequence_utilizada": result[0]
                    }
                    executed_any_query = True
                else:
                    results[db_slug] = "⚠️ Nenhum valor retornado."

            except Exception as e:
                last_error = str(e)
                logging.error(f"❌ Erro ao obter NEXTVAL em {db_slug}: {last_error}")
                results[db_slug] = last_error

        return jsonify({
            "status": "success" if executed_any_query else "error",
            "message": "Nenhuma query foi executada." if not executed_any_query else "NEXTVAL obtido com sucesso",
            "last_error": last_error,
            "data": results
        }), 400 if not executed_any_query else 200

    except Exception as e:
        logging.error(f"❌ Erro inesperado: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500


@route_bp.route('/bluemind/table_structure/', methods=['POST'])
@token_required
@permission_required(route_prefix='/routes')
def get_table_structure(user_data):
    try:
        logging.info("🔹 Iniciando obtenção da estrutura da tabela")
        request_data = request.json or {}
        logging.info(f"📥 Dados recebidos: {json.dumps(request_data, indent=4)}")

        provided_connections = request_data.get("connections", [])
        provided_parameters_list = request_data.get("parameters", [])

        provided_parameters = {}
        for param_entry in provided_parameters_list:
            for connection_name, params in param_entry.items():
                provided_parameters[connection_name] = params

        # Obter credenciais Oracle
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT c.slug, c.db_type, c.host, c.port, c.username, c.password, c.service_name, c.sid
            FROM connections c
            WHERE c.slug IN (%s)
        """ % (",".join(["%s"] * len(provided_connections)))
        cursor.execute(query, tuple(provided_connections))
        connections = {conn["slug"]: conn for conn in cursor.fetchall()}
        cursor.close()
        conn.close()

        if not connections:
            return jsonify({"status": "error", "message": "❌ Nenhuma conexão encontrada."}), 404

        results = {}
        for db_slug, params in provided_parameters.items():
            if db_slug not in connections:
                continue

            conn_details = connections[db_slug]
            if conn_details["db_type"].lower() != "oracle":
                results[db_slug] = "⚠️ Não é Oracle."
                continue

            schema = params.get("schema")
            table_name = params.get("table_name")

            if not schema or not table_name:
                results[db_slug] = "⚠️ Schema ou tabela não informados."
                continue

            try:
                password = decrypt_password(conn_details["password"])
                db_conn = create_oracle_connection(
                    host=conn_details["host"],
                    port=conn_details["port"],
                    user=conn_details["username"],
                    password=password,
                    service_name=conn_details.get("service_name"),
                    sid=conn_details.get("sid")
                )

                db_cursor = db_conn.cursor()

                query = f"""
                    SELECT column_name, data_type, data_length, data_precision, data_scale, nullable
                    FROM all_tab_columns
                    WHERE owner = :schema
                      AND table_name = :table_name
                    ORDER BY column_id
                """
                db_cursor.execute(query, {"schema": schema.upper(), "table_name": table_name.upper()})
                columns = db_cursor.fetchall()

                structure = []
                for col in columns:
                    structure.append({
                        "column_name": col[0],
                        "data_type": col[1],
                        "data_length": col[2],
                        "data_precision": col[3],
                        "data_scale": col[4],
                        "nullable": col[5]
                    })

                results[db_slug] = structure

                db_cursor.close()
                db_conn.close()

            except Exception as e:
                results[db_slug] = f"❌ Erro: {str(e)}"
                logging.error(f"[{db_slug}] Erro: {str(e)}")
                continue

        return jsonify({"status": "success", "data": results}), 200

    except Exception as e:
        logging.error(f"Erro inesperado: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500




def validate_executor_parameters_with_user_input(executor_id, user_parameters):
    """
    Valida os parâmetros de um executor considerando valores fornecidos pelo usuário.
    """
    try:
        conn = create_db_connection_mysql()
        cursor = conn.cursor(dictionary=True)

        # Buscar parâmetros do executor
        query = "SELECT name, type, value FROM executor_parameters WHERE executor_id = %s"
        cursor.execute(query, (executor_id,))
        parameters = cursor.fetchall()

        cursor.close()
        conn.close()

        validation_results = []
        for param in parameters:
            param_name = param["name"]
            param_value = user_parameters.get(param_name, param["value"])  # Priorizar valor enviado pelo usuário

            param_result = {
                "name": param_name,
                "type": param["type"],
                "value": param_value,
                "is_valid": True,
                "error": None
            }

            # Validar se o valor está vazio somente se o parâmetro foi declarado
            if param["value"] in (None, "") and param_value in (None, ""):
                param_result["is_valid"] = False
                param_result["error"] = f"O parâmetro '{param_name}' está vazio e é obrigatório."

            # Validar tipos
            elif param["type"].lower() == "integer":
                if not str(param_value).isdigit():
                    param_result["is_valid"] = False
                    param_result["error"] = f"O parâmetro '{param_name}' deve ser um número inteiro."

            elif param["type"].lower() == "string":
                if not isinstance(param_value, str):
                    param_result["is_valid"] = False
                    param_result["error"] = f"O parâmetro '{param_name}' deve ser uma string."

            elif param["type"].lower() == "date":
                try:
                    # Validar formato de data
                    datetime.strptime(param_value, "%Y-%m-%d")
                except ValueError:
                    param_result["is_valid"] = False
                    param_result["error"] = f"O parâmetro '{param_name}' deve estar no formato 'YYYY-MM-DD'."

            validation_results.append(param_result)

        return validation_results
    except Exception as e:
        return [{
            "name": "unknown",
            "type": "unknown",
            "value": None,
            "is_valid": False,
            "error": f"Erro ao validar parâmetros: {e}"
        }]

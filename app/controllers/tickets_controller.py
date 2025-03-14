import uuid
import json
from os import getenv
from dotenv import load_dotenv
import requests
from flask import Blueprint, jsonify, make_response, request
from app.models.tb_tickets import TbTickets
from app.models.tb_tickets_tasks import TbTicketsTasks
from app.models.tb_itsm_tickets_status import TbItsmTicketsStatus
from app.models.tb_users_new import TbUsersNew
from app.models.tb_hub import TbHub
from app.models.tb_unidade import TbUnidade
from app.models.tb_categoria import TbCategoria
from app.models.tb_subcategoria import TbSubcategoria
from app.models.tb_assunto import TbAssunto
from app.models.tb_sla_niveis import TbSlaNiveis
from app import db
from datetime import datetime, timedelta
from app.utils.decorators import token_required, permission_required

def adiciona_minutos_uteis(data_inicio, minutos, horario_inicio="08:00:00", horario_fim="18:00:00"):
    data_atual = datetime.strptime(data_inicio, "%Y-%m-%d %H:%M:%S")
    inicio_hora = datetime.strptime(horario_inicio, "%H:%M:%S").time()
    fim_hora = datetime.strptime(horario_fim, "%H:%M:%S").time()

    def eh_dia_util(data):
        return data.weekday() < 5  # Segunda (0) a Sexta (4) são dias úteis

    # Ajustar o horário inicial se estiver fora do expediente
    if data_atual.time() < inicio_hora:
        data_atual = data_atual.replace(hour=inicio_hora.hour, minute=inicio_hora.minute, second=0)
    elif data_atual.time() > fim_hora:
        data_atual += timedelta(days=1)
        while not eh_dia_util(data_atual):
            data_atual += timedelta(days=1)
        data_atual = data_atual.replace(hour=inicio_hora.hour, minute=inicio_hora.minute, second=0)

    minutos_restantes = minutos

    while minutos_restantes > 0:
        if eh_dia_util(data_atual):
            hora_atual_minutos = data_atual.hour * 60 + data_atual.minute
            inicio_minutos = inicio_hora.hour * 60 + inicio_hora.minute
            fim_minutos = fim_hora.hour * 60 + fim_hora.minute
            minutos_ate_fim_expediente = fim_minutos - hora_atual_minutos

            if minutos_restantes <= minutos_ate_fim_expediente:
                data_atual += timedelta(minutes=minutos_restantes)
                minutos_restantes = 0
            else:
                minutos_restantes -= minutos_ate_fim_expediente
                data_atual += timedelta(days=1)
                while not eh_dia_util(data_atual):
                    data_atual += timedelta(days=1)
                data_atual = data_atual.replace(hour=inicio_hora.hour, minute=inicio_hora.minute, second=0)
        else:
            data_atual += timedelta(days=1)

    return data_atual.strftime("%Y-%m-%d %H:%M:%S")

def adiciona_minutos_corridos(data_inicio, minutos):
    data_atual = datetime.strptime(data_inicio, "%Y-%m-%d %H:%M:%S")
    data_atual += timedelta(minutes=minutos)
    return data_atual.strftime("%Y-%m-%d %H:%M:%S")

def formatStatus(status: str) -> str:
    if not isinstance(status, str):
        return ""
    
    status_mapping = {
        "Em Andamento": "EM ATENDIMENTO",
        "Cancelado": "CANCELADA"
    }
    
    status_upper = status_mapping.get(status, status.upper())
    return status_upper

load_dotenv()

ticket_bp = Blueprint('ticket', __name__, url_prefix='/ticket')

@ticket_bp.route('/', methods=['GET'])
@token_required
@permission_required(route_prefix='/ticket')
def get_tickets(user_data):
    fila = request.args.get('fila', None)
    analista = request.args.get('analista', None)

    if fila and analista:
        return jsonify({"error": "Não é permitido filtrar por fila e analista ao mesmo tempo."}), 400
    
    if fila:
        filas_validas = TbUsersNew.query.filter_by(bl_fila=1).order_by(TbUsersNew.ds_nome.asc()).all()
        if not filas_validas:
            return jsonify({"error": "Nenhuma fila disponível"}), 400
        
        filas_dict = {fila.ds_nome.lower(): fila.id for fila in filas_validas}

        fila_lower = fila.lower()
        if fila_lower in filas_dict:
            fila = filas_dict[fila_lower]
        else:
            return jsonify({
                "error": "Fila inválida",
                "filas_disponiveis": [fila.ds_nome for fila in filas_validas]
            }), 400

    if analista:
        analistas_validos = TbUsersNew.query.filter(
            TbUsersNew.bl_analista == 1,
            TbUsersNew.bl_fila == None
        ).order_by(TbUsersNew.ds_nome.asc()).all()

        if not analistas_validos:
            return jsonify({"error": "Nenhum analista disponível"}), 400

        analistas_dict = {analista.ds_nome.lower(): analista.id for analista in analistas_validos}

        analista_lower = analista.lower()
        if analista_lower in analistas_dict:
            analista = analistas_dict[analista_lower]
        else:
            return jsonify({
                "error": "Analista inválido",
                "analistas_disponiveis": [analista.ds_nome for analista in analistas_validos]
            }), 400

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    try:
        query = TbTickets.query
        
        if fila is not None:
            query = query.filter_by(executor=fila)
        elif analista is not None:
            query = query.filter_by(executor=analista)

        paginated_tickets = query.paginate(page=page, per_page=per_page, error_out=False)

        results = [
            {
                "id": ticket.id,
                "cod_fluxo": ticket.cod_fluxo,
                "abertura": ticket.abertura,
                "nome": ticket.nome,
                "email_solicitante": ticket.email_solicitante,
                "status": ticket.status,
                "sla": ticket.st_sla,
                "data_limite": ticket.data_limite,
                "grupo": ticket.grupo,
                "hub": ticket.hub,
                "unidade": ticket.unidade,
                "categoria": ticket.categoria,
                "subcategoria": ticket.subcategoria,
                "assunto": ticket.assunto,
                "ds_nivel": ticket.ds_nivel,
            }
            for ticket in paginated_tickets.items
        ]

        return jsonify({
            "page": paginated_tickets.page,
            "pages": paginated_tickets.pages,
            "total_items": paginated_tickets.total,
            "items_per_page": paginated_tickets.per_page,
            "tickets": results
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ticket_bp.route('/<int:id>', methods=['GET'])
@token_required
@permission_required(route_prefix='/ticket')
def get_ticket(user_data, id):    
    if not id:
        return jsonify({"error": "Parâmetro 'id' é obrigatório"}), 400

    try:
        ticket = TbTickets.query.filter_by(cod_fluxo=id).first()

        if ticket:
            result = {
                "id": ticket.id,
                "cod_fluxo": ticket.cod_fluxo,
                "abertura": ticket.abertura,
                "nome": ticket.nome,
                "email_solicitante": ticket.email_solicitante,
                "status": ticket.status,
                "sla": ticket.st_sla,
                "data_limite": ticket.data_limite,
                "executor": ticket.executor,
                "grupo": ticket.grupo,
                "hub": ticket.hub,
                "unidade": ticket.unidade,
                "categoria": ticket.categoria,
                "subcategoria": ticket.subcategoria,
                "assunto": ticket.assunto,
                "reincidencia_assunto": ticket.reincidencia_assunto,
                "ds_nivel": ticket.ds_nivel,
                "descricao": ticket.descricao,
                "ds_obs": ticket.ds_obs
            }
            return jsonify(result)
        
        else:
            return jsonify({"error": f"Ticket {id} não encontrado"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ticket_bp.route('/', methods=['POST'])
@token_required
@permission_required(route_prefix='/ticket')
def create_ticket(user_data):
    data = request.json

    if not data:
        return jsonify({"error": "Nenhum dado fornecido na requisição"}), 400

    required_fields = ['nome', 'email_solicitante', 'hub', 'unidade', 'categoria', 'subcategoria', 'assunto', 'descricao']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"Campo obrigatório ausente ou vazio: {field}"}), 400

    try:
        errors = {}

        hub_exists = db.session.query(TbHub).filter_by(ds_hub=data['hub']).first()
        if not hub_exists:
            hubs_validos = [hub.ds_hub for hub in db.session.query(TbHub).all()]
            errors['hub'] = {
                "mensagem": "Hub inválido",
                "opcoes_validas": hubs_validos
            }
        else:
            unidade_exists = db.session.query(TbUnidade).filter_by(
                st_razao_social=data['unidade'],
                nu_hub=data['hub']
            ).first()
            if not unidade_exists:
                unidades_validas = [unidade.st_razao_social for unidade in db.session.query(TbUnidade).filter_by(nu_hub=data['hub']).all()]
                errors['unidade'] = {
                    "mensagem": "Unidade inválida",
                    "opcoes_validas": unidades_validas
                }

        categoria_exists = db.session.query(TbCategoria).filter_by(descricao=data['categoria']).first()
        if not categoria_exists:
            categorias_validas = [categoria.descricao for categoria in db.session.query(TbCategoria).all()]
            errors['categoria'] = {
                "mensagem": "Categoria inválida",
                "opcoes_validas": categorias_validas
            }
        else:
            subcategoria_exists = db.session.query(TbSubcategoria).filter_by(
                sub_descricao=data['subcategoria'],
                categoria_id=categoria_exists.id
            ).first()

            if not subcategoria_exists:
                subcategorias_validas = [
                    subcategoria.sub_descricao for subcategoria in db.session.query(TbSubcategoria)
                    .filter_by(categoria_id=categoria_exists.id).all()
                ]
                errors['subcategoria'] = {
                    "mensagem": "Subcategoria inválida",
                    "opcoes_validas": subcategorias_validas
                }
            else:
                assunto_exists = db.session.query(TbAssunto).filter_by(
                    ass_descricao=data['assunto'],
                    categoria_id=categoria_exists.id,
                    subcategoria_id=subcategoria_exists.id
                ).first()

                if not assunto_exists:
                    assuntos_validos = [
                        assunto.ass_descricao for assunto in db.session.query(TbAssunto)
                        .filter_by(categoria_id=categoria_exists.id, subcategoria_id=subcategoria_exists.id).all()
                    ]
                    errors['assunto'] = {
                        "mensagem": "Assunto inválido",
                        "opcoes_validas": assuntos_validos
                    }
        
        if errors:
            return jsonify({"erros": errors}), 400

        abertura = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data['id'] = str(uuid.uuid4())
        data['status'] = 'Em Aberto'
        data['abertura'] = abertura

        if assunto_exists.sla_id_padrao:
            sla_nivel = db.session.query(TbSlaNiveis).filter_by(id=assunto_exists.sla_id_padrao).first()
            if sla_nivel:
                data['ds_nivel'] = sla_nivel.prioridade
                data['sla'] = sla_nivel.tempo
                data_limite = adiciona_minutos_uteis(abertura, int(sla_nivel.tempo)) if sla_nivel.tipo_tempo == "Útil" else adiciona_minutos_corridos(abertura, int(sla_nivel.tempo))
                data['data_limite'] = data_limite
                data['reincidencia_assunto'] = 'RM-' if assunto_exists.sla_tipo == 'Requisição' else 'IM-'

        if assunto_exists.ds_grupo_atendimento:
            executor = db.session.query(TbUsersNew).filter_by(id=assunto_exists.ds_grupo_atendimento).first()
            if executor:
                data['executor'] = assunto_exists.ds_grupo_atendimento
                data['grupo'] = executor.ds_nome

        new_ticket = TbTickets(
            id=data.get('id'),
            abertura=data.get('abertura'),
            status=data.get('status'),
            nome=data.get('nome'),
            email_solicitante=data.get('email_solicitante'),
            hub=data.get('hub'),
            unidade=f"{data.get('hub')}: {data.get('unidade')}",
            categoria=data.get('categoria'),
            subcategoria=data.get('subcategoria'),
            assunto=data.get('assunto'),
            descricao=data.get('descricao'),
            ds_obs=data.get('ds_obs'),
            ds_nivel=data.get('ds_nivel'),
            executor=data.get('executor'),
            grupo=data.get('grupo'),
            data_att_grupo=abertura,
            sla=data.get('sla'),
            st_sla='No Prazo',
            st_sla_corrido='No Prazo',
            reincidencia_assunto=data.get('reincidencia_assunto'),
            data_limite=data.get('data_limite')
        )

        db.session.add(new_ticket)
        db.session.commit()

        return jsonify({
            "message": "Ticket criado com sucesso",
            "id": new_ticket.cod_fluxo,
            "ticket": data
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Internal server error: {e}"}), 500

@ticket_bp.route('/<int:id>', methods=['PATCH'])
@token_required
@permission_required(route_prefix='/ticket')
def update_ticket(user_data, id):
    data = request.json

    if not data:
        return jsonify({"error": "Nenhum dado fornecido na requisição"}), 400

    required_fields = ['status', 'executor', 'descricao']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"Campo obrigatório ausente ou vazio: {field}"}), 400
    
    categoria_present = any(field in data for field in ['categoria', 'subcategoria', 'assunto'])
    hub_present = any(field in data for field in ['hub', 'unidade'])
    prioridade_present = any(field in data for field in ['ds_nivel'])

    if categoria_present and not all(field in data for field in ['categoria', 'subcategoria', 'assunto']):
        return jsonify({"error": "Se enviar 'categoria', 'subcategoria' ou 'assunto', os três devem estar presentes."}), 400

    if hub_present and not all(field in data for field in ['hub', 'unidade']):
        return jsonify({"error": "Se enviar 'hub' ou 'unidade', ambos devem estar presentes."}), 400

    try:
        ticket_exists = db.session.query(TbTickets).filter_by(cod_fluxo=id).first()
        if not ticket_exists:
            return jsonify({"error": f"Ticket {id} não encontrado."}), 400
        
        errors = {}

        executor_exists = db.session.query(TbUsersNew).filter_by(bl_analista=1, ds_nome=data['executor']).first()
        if not executor_exists:
            executor_validos = db.session.query(TbUsersNew).filter_by(bl_analista=1).order_by(TbUsersNew.ds_nome.asc()).all()
            errors['executor'] = {
                "mensagem": "Executor inválido",
                "opcoes_validas": [executor.ds_nome for executor in executor_validos]
            }
        else:
            data['executor'] = executor_exists.id
            data['grupo'] = executor_exists.ds_nome

        status_exists = db.session.query(TbItsmTicketsStatus).filter_by(nome=data['status']).first()
        if not status_exists:
            status_validos = db.session.query(TbItsmTicketsStatus).order_by(TbItsmTicketsStatus.nome.asc()).all()
            errors['status'] = {
                "mensagem": "Status inválido",
                "opcoes_validas": [status.nome for status in status_validos]
            }

        if hub_present:
            hub_exists = db.session.query(TbHub).filter_by(ds_hub=data['hub']).first()
            if not hub_exists:
                hubs_validos = [hub.ds_hub for hub in db.session.query(TbHub).all()]
                errors['hub'] = {
                    "mensagem": "Hub inválido",
                    "opcoes_validas": hubs_validos
                }
            else:
                unidade_exists = db.session.query(TbUnidade).filter_by(
                    st_razao_social=data['unidade'],
                    nu_hub=data['hub']
                ).first()
                if not unidade_exists:
                    unidades_validas = [unidade.st_razao_social for unidade in db.session.query(TbUnidade).filter_by(nu_hub=data['hub']).all()]
                    errors['unidade'] = {
                        "mensagem": "Unidade inválida",
                        "opcoes_validas": unidades_validas
                    }
        
        if categoria_present:
            categoria_exists = db.session.query(TbCategoria).filter_by(descricao=data['categoria']).first()
            if not categoria_exists:
                categorias_validas = [categoria.descricao for categoria in db.session.query(TbCategoria).all()]
                errors['categoria'] = {
                    "mensagem": "Categoria inválida",
                    "opcoes_validas": categorias_validas
                }
            else:
                subcategoria_exists = db.session.query(TbSubcategoria).filter_by(
                    sub_descricao=data['subcategoria'],
                    categoria_id=categoria_exists.id
                ).first()
                if not subcategoria_exists:
                    subcategorias_validas = [
                        subcategoria.sub_descricao for subcategoria in db.session.query(TbSubcategoria)
                        .filter_by(categoria_id=categoria_exists.id).all()
                    ]
                    errors['subcategoria'] = {
                        "mensagem": "Subcategoria inválida",
                        "opcoes_validas": subcategorias_validas
                    }
                else:
                    assunto_exists = db.session.query(TbAssunto).filter_by(
                        ass_descricao=data['assunto'],
                        categoria_id=categoria_exists.id,
                        subcategoria_id=subcategoria_exists.id
                    ).first()
                    if not assunto_exists:
                        assuntos_validos = [
                            assunto.ass_descricao for assunto in db.session.query(TbAssunto)
                            .filter_by(categoria_id=categoria_exists.id, subcategoria_id=subcategoria_exists.id).all()
                        ]
                        errors['assunto'] = {
                            "mensagem": "Assunto inválido",
                            "opcoes_validas": assuntos_validos
                        }

        if prioridade_present:
            prioridade_exists = db.session.query(TbSlaNiveis).filter_by(prioridade=data['ds_nivel']).first()
            if not prioridade_exists:
                prioridade_validos = db.session.query(TbSlaNiveis).order_by(TbSlaNiveis.prioridade.asc()).all()
                errors['ds_nivel'] = {
                    "mensagem": "Prioridade inválida",
                    "opcoes_validas": [prioridade.prioridade for prioridade in prioridade_validos]
                }
            else:
                data['ds_nivel'] = prioridade_exists.prioridade
                data['sla'] = prioridade_exists.tempo
                data_limite = adiciona_minutos_uteis(str(ticket_exists.abertura), int(prioridade_exists.tempo)) if prioridade_exists.tipo_tempo == "Útil" else adiciona_minutos_corridos(str(ticket_exists.abertura), int(prioridade_exists.tempo))
                data['data_limite'] = data_limite

        if errors:
            return jsonify({"erros": errors}), 400

        agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if data.get('status') in ["Encerrado", "Finalizado"]:
            data['finalizado_por'] = user_data.get("username", "Usuário Desconhecido")
            data['data_fim'] = agora
            ticket_exists.finalizado_por = data.get('finalizado_por', ticket_exists.finalizado_por)
            ticket_exists.data_fim = data.get('data_fim', ticket_exists.data_fim)
        elif data.get('status') == "Cancelado":
            data['cancelado_por'] = user_data.get("username", "Usuário Desconhecido")
            data['data_fim'] = agora
            ticket_exists.cancelado_por = data.get('cancelado_por', ticket_exists.cancelado_por)
            ticket_exists.data_fim = data.get('data_fim', ticket_exists.data_fim)
        
        ticket_exists.status = data.get('status', ticket_exists.status)
        ticket_exists.executor = data.get('executor', ticket_exists.executor)
        ticket_exists.grupo = data.get('grupo', ticket_exists.grupo)
        ticket_exists.hub = data.get('hub', ticket_exists.hub)
        ticket_exists.unidade = f"{data.get('hub')}: {data.get('unidade')}" if 'hub' in data and 'unidade' in data else ticket_exists.unidade
        ticket_exists.categoria = data.get('categoria', ticket_exists.categoria)
        ticket_exists.subcategoria = data.get('subcategoria', ticket_exists.subcategoria)
        ticket_exists.assunto = data.get('assunto', ticket_exists.assunto)
        ticket_exists.ds_nivel = data.get('ds_nivel', ticket_exists.ds_nivel)
        ticket_exists.data_att_grupo = agora
        ticket_exists.sla = data.get('sla', ticket_exists.sla)
        ticket_exists.data_limite = data.get('data_limite', ticket_exists.data_limite)

        last_task = (
            db.session.query(TbTicketsTasks)
            .filter_by(cod_fluxo=ticket_exists.id)
            .order_by(TbTicketsTasks.cod_task.desc())
            .first()
        )

        if last_task:
            last_task.dt_fim = agora
            last_task.ds_concluido_por = user_data.get("username", "Usuário Desconhecido")
        
        new_task = TbTicketsTasks(
            id=str(uuid.uuid4()),
            cod_fluxo=ticket_exists.id,
            status=formatStatus(data.get('status', ticket_exists.status)),
            descricao=data.get('descricao'),
            executor=data.get('grupo', ticket_exists.grupo),
            aberto_por=user_data.get("username", "Usuário Desconhecido"),
            aberto_em=agora,
        )

        if data.get('status') in ["Encerrado", "Finalizado", "Cancelado"]:
            new_task.ds_concluido_por = user_data.get("username", "Usuário Desconhecido")
            new_task.dt_fim = agora
        
        db.session.add(new_task)
        db.session.commit()

        url = f"{getenv('URL_GCP_KORA_API')}/sla"

        payload = json.dumps({
            "cod_fluxo": ticket_exists.cod_fluxo,
            "N° Ticket": ticket_exists.cod_fluxo
        })
        headers = {
            'Content-Type': 'application/json'
        }

        requests.post(url, headers=headers, data=payload).json()

        return jsonify({
            "message": "Ticket atualizado com sucesso",
            "id": ticket_exists.cod_fluxo,
            "ticket": data
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Internal server error: {e}"}), 500

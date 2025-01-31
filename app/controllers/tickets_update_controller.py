import uuid
from datetime import datetime
from flask import Blueprint, jsonify, request
import requests
import json
from os import getenv
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError
from app.models.tb_tickets import TbTickets
from app.models.tb_tickets_tasks import TbTicketsTasks
from app.models.tb_tickets_files import TbTicketsFiles
from app.models.tb_itsm_log import TbItsmLog
from app.models.tb_hub import TbHub
from app.models.tb_unidade import TbUnidade
from app.models.tb_categoria import TbCategoria
from app.models.tb_subcategoria import TbSubcategoria
from app.models.tb_assunto import TbAssunto
from app.models.tb_sla_niveis import TbSlaNiveis
from app.models.tb_users_new import TbUsersNew
from app import db
from datetime import datetime
from uuid import uuid4
from app.utils.decorators import token_required, permission_required
import logging
import sys

logging.basicConfig(
    level=logging.DEBUG,  # Garantir que DEBUG será exibido
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)  # Redireciona logs para stdout
    ],
)

# Configurando logs específicos para Flask
flask_logger = logging.getLogger('flask.app')
flask_logger.setLevel(logging.DEBUG)

load_dotenv()

tickets_update_bp = Blueprint('tickets-update', __name__, url_prefix='/api/tickets-update')

@tickets_update_bp.route('/', methods=['POST'])
@token_required
@permission_required(route_prefix='/tickets-update')
def create_ticket(user_data):
    logging.info("Iniciando criação de ticket.")
    data = request.json

    if not data:
        logging.error("Nenhum dado fornecido na requisição.")
        return jsonify({"error": "No data provided"}), 400

    # Campos obrigatórios
    required_fields = ['email_solicitante', 'descricao', 'hub', 'unidade', 'categoria', 'subcategoria', 'assunto']
    for field in required_fields:
        if field not in data or not data[field]:
            logging.error(f"Campo obrigatório ausente ou vazio: {field}")
            return jsonify({"error": f"Missing required field: {field}"}), 400

    try:
        # Verificar se o hub informado existe na tabela tb_hub
        logging.info(f"Verificando se o hub '{data['hub']}' existe.")
        hub_exists = db.session.query(TbHub).filter_by(ds_hub=data['hub']).first()
        if not hub_exists:
            logging.error("Hub inválido informado.")
            return jsonify({"error": "Invalid hub"}), 400

        # Verificar se a unidade informada existe na tabela tb_unidade
        logging.info(f"Verificando se a unidade '{data['unidade']}' existe.")
        unidade_exists = db.session.query(TbUnidade).filter_by(st_razao_social=data['unidade']).first()
        if not unidade_exists:
            logging.error("Unidade inválida informada.")
            return jsonify({"error": "Invalid unidade"}), 400

        # Verificar se a categoria informada existe na tabela tb_categoria
        logging.info(f"Verificando se a categoria '{data['categoria']}' existe.")
        categoria_exists = db.session.query(TbCategoria).filter_by(descricao=data['categoria']).first()
        if not categoria_exists:
            logging.error("Categoria inválida informada.")
            return jsonify({"error": "Invalid categoria"}), 400

        # Verificar se a subcategoria informada existe na tabela tb_subcategoria
        logging.info(f"Verificando se a subcategoria '{data['subcategoria']}' existe.")
        subcategoria_exists = db.session.query(TbSubcategoria).filter_by(sub_descricao=data['subcategoria']).first()
        if not subcategoria_exists:
            logging.error("Subcategoria inválida informada.")
            return jsonify({"error": "Invalid subcategoria"}), 400

        # Verificar se o assunto informado existe na tabela tb_assunto
        logging.info(f"Verificando se o assunto '{data['assunto']}' existe.")
        assunto_exists = db.session.query(TbAssunto).filter_by(ass_descricao=data['assunto']).first()
        if not assunto_exists:
            logging.error("Assunto inválido informado.")
            return jsonify({"error": "Invalid assunto"}), 400

        # Preencher campos automáticos
        logging.info("Preenchendo campos automáticos.")
        ticket_uuid = str(uuid.uuid4())  # Gerar UUID para o ticket
        data['id'] = ticket_uuid
        data['status'] = 'Em Aberto'  # Status padrão
        data['abertura'] = datetime.now()  # Data e hora atual

        # Obter ds_nivel da tabela sla_niveis via sla_id_padrao
        if assunto_exists.sla_id_padrao:
            logging.info(f"Obtendo nível e SLA padrão para o assunto.")
            sla_nivel = db.session.query(TbSlaNiveis).filter_by(id=assunto_exists.sla_id_padrao).first()
            if sla_nivel:
                data['ds_nivel'] = sla_nivel.prioridade  # Preencher prioridade em ds_nivel
                data['sla'] = sla_nivel.tempo  # Preencher tempo em sla

        # Obter executor da tabela tb_users_new via ds_grupo_atendimento
        executor_nome = None
        if assunto_exists.ds_grupo_atendimento:
            logging.info("Obtendo executor associado ao grupo de atendimento.")
            executor = db.session.query(TbUsersNew).filter_by(id=assunto_exists.ds_grupo_atendimento).first()
            if executor:
                executor_nome = executor.ds_nome  # Nome do executor

        # Criar o novo ticket
        logging.info("Criando o novo ticket.")
        new_ticket = TbTickets(
            id=ticket_uuid,
            nome=data.get('nome'),
            email_solicitante=data.get('email_solicitante'),
            cargo_solic=data.get('cargo_solic', ''),
            hub=data.get('hub'),
            unidade=data.get('unidade'),
            categoria=data.get('categoria'),
            subcategoria=data.get('subcategoria'),
            assunto=data.get('assunto'),
            descricao=data.get('descricao'),
            ds_nivel=data.get('ds_nivel'),
            sla=data.get('sla'),
            status=data.get('status'),
            abertura=data.get('abertura')
        )

        # Adicionar e salvar no banco de dados
        logging.info("Adicionando o ticket ao banco de dados.")
        db.session.add(new_ticket)
        db.session.commit()

        # Adicionar entrada na tabela tb_tickets_tasks
        logging.info("Adicionando task associada ao ticket.")
        new_task = TbTicketsTasks(
            id=str(uuid.uuid4()),
            cod_fluxo=new_ticket.cod_fluxo,
            status=new_ticket.status,
            descricao="Criação do ticket",
            executor=executor_nome,  # Nome do executor
            aberto_por=user_data.get('username', 'Sistema'),
            aberto_em=datetime.now()
        )
        db.session.add(new_task)
        db.session.commit()

        # Retornar a resposta com sucesso
        logging.info("Ticket criado com sucesso.")
        return jsonify({
            "message": "Ticket created successfully",
            "cod_fluxo": new_ticket.cod_fluxo,
            "id": new_ticket.id
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Erro ao salvar no banco de dados: {str(e)}")
        return jsonify({"error": str(e)}), 500

    except Exception as e:
        logging.error(f"Erro inesperado: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
 
@tickets_update_bp.route('/task', methods=['POST'])
@token_required
@permission_required(route_prefix='/tickets-update')
def create_task(user_data):
    data = request.json

    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        user_id = user_data.get("id")
        if 'id' not in data or not data['id']:
            data['id'] = str(uuid.uuid4())

        new_task = TbTicketsTasks(**data)

        db.session.add(new_task)
        db.session.commit()

        return jsonify({"message": "Task created successfully", "task_id": new_task.cod_task}), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@tickets_update_bp.route('/file', methods=['POST'])
@token_required
def create_file(user_data):
    data = request.json

    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        user_id = user_data.get("id")
        if 'id' not in data or not data['id']:
            data['id'] = str(uuid.uuid4())

        new_file = TbTicketsFiles(**data)

        db.session.add(new_file)
        db.session.commit()

        return jsonify({"message": "File created successfully", "anexo_id": new_file.cod_anexo}), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@tickets_update_bp.route('/log', methods=['POST'])
@token_required
def create_log(user_data):
    data = request.json

    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        user_id = user_data.get("id")
        new_log = TbItsmLog(**data)

        db.session.add(new_log)
        db.session.commit()

        return jsonify({"message": "Log created successfully"}), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@tickets_update_bp.route('/<int:cod_fluxo>', methods=['PATCH'])
@token_required
@permission_required(route_prefix='/tickets-update')
def update_ticket(user_data, cod_fluxo):
    logging.debug(f"Conteúdo de user_data extraído do JWT: {user_data}")

    data = request.json

    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        user_id = user_data.get("id")
        user_name = user_data.get("username", "Usuário Desconhecido")  # Nome do usuário logado via JWT

        # Buscando o ticket a ser atualizado
        ticket = TbTickets.query.get(cod_fluxo)
        if not ticket:
            return jsonify({"error": "Ticket not found"}), 404

        # Atualizando os campos do ticket
        for key, value in data.items():
            if hasattr(ticket, key):
                setattr(ticket, key, value)
            else:
                return jsonify({"error": f"Invalid field: {key}"}), 400

        # Garantindo que a descrição foi atualizada
        descricao_atualizada = ticket.descricao  # Pegando o valor atualizado para usar na tarefa

        # Commit da atualização do ticket antes de criar a nova task
        db.session.commit()

        # Criando uma nova task vinculada ao ticket
        if 'executor' in data or 'status' in data:
            new_task = TbTicketsTasks(
                id=str(uuid4()),  # Gerando UUID para o id
                cod_fluxo=ticket.id,  # Usando o id do ticket existente
                status=data.get('status', ticket.status),  # Se não for passado, mantém o status atual
                descricao=descricao_atualizada,  # Usando a descrição do ticket atualizado
                executor=f"{user_name} - Via API",  # Nome do usuário logado com o sufixo
                aberto_por=f"{user_name} - Via API",  # Nome do usuário logado com o sufixo
                aberto_em=datetime.now(),  # Hora atual
            )

            # Usando logger para exibir os valores
            logging.info("Debug - Valores da nova task:")
            logging.info(f"id: {new_task.id}")
            logging.info(f"cod_fluxo: {new_task.cod_fluxo}")
            logging.info(f"status: {new_task.status}")
            logging.info(f"descricao: {new_task.descricao}")
            logging.info(f"executor: {new_task.executor}")
            logging.info(f"aberto_por: {new_task.aberto_por}")
            logging.info(f"aberto_em: {new_task.aberto_em}")

            # Inserindo a nova task no banco de dados
            db.session.add(new_task)
            db.session.commit()

        # Consultar o ticket novamente, incluindo as tasks associadas
        ticket_with_tasks = TbTickets.query.filter_by(id=ticket.id).first()
        tasks = TbTicketsTasks.query.filter_by(cod_fluxo=ticket.id).all()

        # Serializar os dados do ticket e das tasks
        ticket_data = {
            "id": ticket_with_tasks.id,
            "descricao": ticket_with_tasks.descricao,
            "status": ticket_with_tasks.status,
            "executor": ticket_with_tasks.executor,
            "finalizado_por": ticket_with_tasks.finalizado_por,
            "data_fim": ticket_with_tasks.data_fim,
        }
        tasks_data = [
            {
                "id": task.id,
                "cod_fluxo": task.cod_fluxo,
                "status": task.status,
                "descricao": task.descricao,
                "executor": task.executor,
                "aberto_por": task.aberto_por,
                "aberto_em": task.aberto_em,
                "dt_fim": task.dt_fim,
                "ds_concluido_por": task.ds_concluido_por,
            }
            for task in tasks
        ]

        # Retornar o JSON com o ticket e suas tasks
        return jsonify({
            "ticket": ticket_data,
            "tasks": tasks_data
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@tickets_update_bp.route('/task/<int:cod_task>', methods=['PATCH'])
@token_required
@permission_required(route_prefix='/tickets-update')
def update_task(user_data, cod_task):
    data = request.json

    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        user_id = user_data.get("id")
        task = TbTicketsTasks.query.get(cod_task)

        if not task:
            return jsonify({"error": "Task not found"}), 404

        # Verifica se a alteração é apenas do 'executor' ou 'status'
        if 'executor' in data or 'status' in data:
            # Criar nova tarefa apenas com as alterações de status ou executor
            new_task_data = {key: value for key, value in data.items() if key in ['executor', 'status', 'descricao', 'execucao']}
            new_task_data['cod_fluxo'] = task.cod_fluxo
            new_task = TbTicketsTasks(**new_task_data)
            db.session.add(new_task)

            # Atualizar a tabela de tickets se o executor foi alterado
            if 'executor' in data:
                task.executor = data['executor']
                ticket = TbTickets.query.filter_by(cod_fluxo=task.cod_fluxo).first()
                if ticket:
                    # Atualizar a coluna `grupo` na tabela `tb_tickets`
                    ticket.grupo = data['executor']  # Atualiza o nome do executor
                    db.session.commit()

            db.session.commit()

            return jsonify({"message": "New task created with updated executor or status"}), 201
        
        # Atualiza a tarefa normalmente se não for apenas o executor ou status
        for key, value in data.items():
            if hasattr(task, key):
                setattr(task, key, value)
            else:
                return jsonify({"error": f"Invalid field: {key}"}), 400

        db.session.commit()

        return jsonify({"message": "Task updated successfully"}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500



# @tickets_update_blueprint.route('/filtro-ma', methods=['POST'])
# @token_required
# def create_update_filtro_ma():
#     user_id = request.args.get('user_id')
#     if not user_id:
#         return jsonify({"error": "User_id parameter is required"}), 400
    
#     data = request.json
#     if not data:
#         return jsonify({"error": "No data provided"}), 400

#     try:
#         json_data = json.dumps(data)
#         existing_filtro = TbItsmFiltroMa.query.filter_by(id_user=user_id).first()
        
#         if existing_filtro:
#             existing_filtro.filtro = json_data
#             db.session.commit()
#             return jsonify("Filtro updated successfully"), 200
#         else:
#             filtro = TbItsmFiltroMa(id_user=user_id, filtro=json_data)
#             db.session.add(filtro)
#             db.session.commit()
#             return jsonify("Filtro created successfully"), 201

#     except SQLAlchemyError as e:
#         db.session.rollback()
#         return jsonify({"error": str(e)}), 500

# @tickets_update_blueprint.route('/delete-filtro-ma', methods=['POST'])
# @token_required
# def delete_filtro_ma():
#     user_id = request.args.get('user_id')
#     if not user_id:
#         return jsonify({"error": "User_id parameter is required"}), 400
    
#     try:
#         existing_filtro = TbItsmFiltroMa.query.filter_by(id_user=user_id).first()
        
#         if existing_filtro:
#             db.session.delete(existing_filtro)
#             db.session.commit()
#             return jsonify("Filtro deleted successfully")
#         else:
#             return jsonify("User does not have a filter")

#     except SQLAlchemyError as e:
#         db.session.rollback()
#         return jsonify({"error": str(e)}), 500

# @tickets_update_blueprint.route('/filtro-me', methods=['POST'])
# @token_required
# def create_update_filtro_me():
#     user_id = request.args.get('user_id')
#     if not user_id:
#         return jsonify({"error": "User_id parameter is required"}), 400
    
#     data = request.json
#     if not data:
#         return jsonify({"error": "No data provided"}), 400

#     try:
#         json_data = json.dumps(data)
#         existing_filtro = TbItsmFiltroMe.query.filter_by(id_user=user_id).first()
        
#         if existing_filtro:
#             existing_filtro.filtro = json_data
#             db.session.commit()
#             return jsonify("Filtro updated successfully"), 200
#         else:
#             filtro = TbItsmFiltroMe(id_user=user_id, filtro=json_data)
#             db.session.add(filtro)
#             db.session.commit()
#             return jsonify("Filtro created successfully"), 201

#     except SQLAlchemyError as e:
#         db.session.rollback()
#         return jsonify({"error": str(e)}), 500

# @tickets_update_blueprint.route('/delete-filtro-me', methods=['POST'])
# @token_required
# def delete_filtro_me():
#     user_id = request.args.get('user_id')
#     if not user_id:
#         return jsonify({"error": "User_id parameter is required"}), 400
    
#     try:
#         existing_filtro = TbItsmFiltroMe.query.filter_by(id_user=user_id).first()
        
#         if existing_filtro:
#             db.session.delete(existing_filtro)
#             db.session.commit()
#             return jsonify("Filtro deleted successfully")
#         else:
#             return jsonify("User does not have a filter")

#     except SQLAlchemyError as e:
#         db.session.rollback()
#         return jsonify({"error": str(e)}), 500

# @tickets_update_blueprint.route('/create-user-google', methods=['POST'])
# @token_required
# def create_google_user():
    data = request.json

    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        url = f"{getenv('URL_GCP_KORA_API')}/create"
        
        headers = {}

        response = requests.post(url, headers=headers, data=data).json()
        
        return jsonify(response)

    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500

# @tickets_update_blueprint.route('/sla', methods=['POST'])
# @token_required
# def update_sla_status():
    cod_fluxo = request.args.get('cod_fluxo')

    if not cod_fluxo:
        return jsonify({"error": "Cod_fluxo parameter is required"}), 400

    try:
        url = f"{getenv('URL_GCP_KORA_API')}/sla"

        payload = json.dumps({
            "cod_fluxo": cod_fluxo,
            "N° Ticket": cod_fluxo
        })
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(url, headers=headers, data=payload).json()
        
        return jsonify(response)

    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500
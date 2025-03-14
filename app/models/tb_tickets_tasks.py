from app import db

class TbTicketsTasks(db.Model):
    __tablename__ = 'tb_tickets_tasks'
    
    id = db.Column(db.String(255), nullable=True)
    cod_task = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    cod_fluxo = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(255), nullable=True)
    descricao = db.Column(db.Text, nullable=True)
    executor = db.Column(db.String(255), nullable=True)
    aberto_por = db.Column(db.String(150), nullable=True)
    aberto_em = db.Column(db.String(255), nullable=True)
    execucao = db.Column(db.Text, nullable=True)
    dt_fim = db.Column(db.String(100), nullable=True)
    tempo = db.Column(db.Text, nullable=True)
    tempo_corrido = db.Column(db.Text, nullable=True)
    dt_atual = db.Column(db.DateTime, nullable=True)
    ds_concluido_por = db.Column(db.String(100), nullable=True)
    ds_obs = db.Column(db.Text, nullable=True)
    ticket_sap = db.Column(db.String(50), nullable=True)
    ticket_solman = db.Column(db.String(50), nullable=True)
    ds_anexo = db.Column(db.String(600), nullable=True)
    email_criador_atividade = db.Column(db.String(150), nullable=True)
    email_executor = db.Column(db.Text, nullable=True)
    tipo_atividade = db.Column(db.String(30), nullable=True)
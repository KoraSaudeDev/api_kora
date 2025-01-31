from app import db

class TbSlaNiveis(db.Model):
    __tablename__ = 'sla_niveis'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tempo = db.Column(db.String(25), nullable=True)
    prioridade = db.Column(db.String(25), nullable=True)
    tipo_tempo = db.Column(db.String(20), nullable=False)
    bl_ativo = db.Column(db.Integer, nullable=False)
    descricao = db.Column(db.String(50), nullable=False)

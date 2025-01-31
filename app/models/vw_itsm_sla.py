from app import db

class VwItsmSla(db.Model):
    __tablename__ = 'VW_ITSM_SLA'
    
    id = db.Column(db.Integer, primary_key=True)
    tempo = db.Column(db.Integer)
    prioridade = db.Column(db.String(25))
    descricao = db.Column(db.String(50))
    tipo_tempo = db.Column(db.String(20))
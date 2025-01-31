from app import db

class TbItsmLog(db.Model):
    __tablename__ = 'tb_itsm_log'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    cod_fluxo = db.Column(db.Integer)
    nome = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    log = db.Column(db.Text, nullable=True)
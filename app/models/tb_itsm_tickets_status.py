from app import db

class TbItsmTicketsStatus(db.Model):
    __tablename__ = 'tb_itsm_tickets_status'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    nome = db.Column(db.String(50))
    bl_ativo = db.Column(db.Integer)
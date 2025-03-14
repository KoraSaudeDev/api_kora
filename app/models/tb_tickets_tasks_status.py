from app import db

class TbTicketsTasksStatus(db.Model):
    __tablename__ = 'tb_tickets_tasks_status'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    st_decricao = db.Column(db.String(150))
    contabiliza_sla = db.Column(db.Integer)
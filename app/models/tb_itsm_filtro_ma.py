from app import db

class TbItsmFiltroMa(db.Model):
    __tablename__ = 'tb_itsm_filtro_ma'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    id_user = db.Column(db.Integer)
    filtro = db.Column(db.Text, nullable=True)
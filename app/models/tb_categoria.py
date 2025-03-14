from app import db

class TbCategoria(db.Model):
    __tablename__ = 'tb_categoria'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True) 
    descricao = db.Column(db.String(100), nullable=True)
    bl_ativo = db.Column(db.Integer, nullable=False)

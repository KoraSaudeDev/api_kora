from app import db

class TbSubcategoria(db.Model):
    __tablename__ = 'tb_subcategoria'

    id = db.Column(db.Integer, primary_key=True, nullable=True)
    categoria_id = db.Column(db.Integer, nullable=True)
    sub_descricao = db.Column(db.String(100), nullable=True)
    bl_ativo = db.Column(db.Integer, nullable=False)

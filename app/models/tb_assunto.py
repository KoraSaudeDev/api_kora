from app import db

class TbAssunto(db.Model):
    __tablename__ = 'tb_assunto'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    categoria_id = db.Column(db.Integer, nullable=False)
    subcategoria_id = db.Column(db.Integer, nullable=False)
    ass_descricao = db.Column(db.String(250), nullable=True)
    sla_tipo = db.Column(db.String(25), nullable=True)
    sla_id_padrao = db.Column(db.Integer, nullable=False)
    bl_ativo = db.Column(db.Integer, nullable=False)
    ds_grupo_atendimento = db.Column(db.String(100), nullable=True)
    

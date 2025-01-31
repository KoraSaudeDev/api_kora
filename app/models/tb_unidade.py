from app import db

class TbUnidade(db.Model):
    __tablename__ = 'tb_unidade'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bl_ativo = db.Column(db.Integer, nullable=True)
    st_razao_social = db.Column(db.String(128), nullable=True)
    st_cnpj = db.Column(db.String(50), nullable=True)
    nu_codigo_cnpj = db.Column(db.String(50), nullable=True)
    st_endereco = db.Column(db.String(50), nullable=True)
    st_estado = db.Column(db.String(50), nullable=True)
    st_cep = db.Column(db.String(50), nullable=True)
    st_sigla = db.Column(db.String(50), nullable=True)
    st_his = db.Column(db.String(50), nullable=True)
    nu_codigo_sap = db.Column(db.Integer, nullable=True)
    nu_hub = db.Column(db.String(50), nullable=True)
    bl_matriz = db.Column(db.Integer, nullable=True)
    st_descricao = db.Column(db.String(50), nullable=True)
    n_bloco_sap = db.Column(db.String(20), nullable=True)
    cod_empresa = db.Column(db.String(10), nullable=True)
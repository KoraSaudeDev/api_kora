from app import db

class TbTicketsFiles(db.Model):
    __tablename__ = 'tb_tickets_files'
    
    id = db.Column(db.String(255), nullable=True)
    cod_anexo = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    cod_fluxo = db.Column(db.String(255), nullable=True)
    ds_texto = db.Column(db.Text, nullable=True)
    ds_anexo = db.Column(db.String(600), nullable=True)
    ds_adicionado_por = db.Column(db.String(255), nullable=True)
    abertura = db.Column(db.DateTime, nullable=True)
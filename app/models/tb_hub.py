from app import db

from sqlalchemy.orm import relationship

class TbHub(db.Model):
    __tablename__ = 'tb_hub'

    id = db.Column(db.Integer, primary_key=True, nullable=True)
    ds_hub = db.Column(db.String(100), nullable=False)
    bl_ativo = db.Column(db.Integer, nullable=True)
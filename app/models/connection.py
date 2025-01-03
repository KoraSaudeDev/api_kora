from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, func
from app.config.database import Base

class Connection(Base):
    __tablename__ = 'connections'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True)
    db_type = Column(Enum('mysql', 'oracle', 'postgresql', 'sqlite'), nullable=False)
    host = Column(String(255), nullable=True)
    port = Column(Integer, nullable=True)
    username = Column(String(255), nullable=True)
    password = Column(Text, nullable=True)
    database_name = Column(String(255), nullable=True)
    service_name = Column(String(255), nullable=True)
    sid = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    def to_dict(self):
        return {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "database_name": self.database_name,
            "service_name": self.service_name,
            "sid": self.sid,
        }

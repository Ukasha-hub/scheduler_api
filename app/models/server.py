from sqlalchemy import Column, Integer, String
from app.db.base import Base

class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, index=True)
    server = Column(String, nullable=False)
    ip1 = Column(String, nullable=False)
    ip2 = Column(String, nullable=False)
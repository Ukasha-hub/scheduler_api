from sqlalchemy import Column, Integer, String
from app.db.base import Base


class AsRunLog(Base):
    __tablename__ = "asrunlog"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    scheduler_id = Column(Integer, nullable=True)

    program_type = Column(String(255), nullable=True)

    name = Column(String(255), nullable=True)

    duration = Column(String(255), nullable=True)

    played_time = Column(String(255), nullable=True)
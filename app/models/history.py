from sqlalchemy import Column, Integer, String, DateTime, func
from app.db.base import Base

class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True)
    action_time = Column(DateTime(timezone=True), server_default=func.now())
    emp_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
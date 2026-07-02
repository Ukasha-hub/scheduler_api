from sqlalchemy import Column, Integer, DateTime, String
from app.db.base import Base

class XYZ(Base):
    __tablename__ = "xyz"

    id = Column(Integer, primary_key=True, index=True)
    data = Column(String)
    created_at = Column(DateTime(timezone=True), index=True)
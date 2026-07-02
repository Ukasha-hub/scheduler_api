from sqlalchemy import Column, Integer, DateTime, String
from app.db.base import Base

class XYZBackup(Base):
    __tablename__ = "xyz_backup"

    id = Column(Integer, primary_key=True, index=True)
    data = Column(String)
    created_at = Column(DateTime(timezone=True), index=True)
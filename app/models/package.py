# app/models/package.py

from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean
from datetime import datetime
from app.db.base import Base

class Package(Base):
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    items = Column(JSON, nullable=False)  # Store selected rows as JSON
    is_active = Column(Boolean, default=True)  
    created_at = Column(DateTime, default=datetime.utcnow)

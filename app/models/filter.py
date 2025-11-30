# Purpose: Filter model for storing type + color
from sqlalchemy import Column, Integer, String
from app.db.base import Base


class Filter(Base):
    __tablename__ = "filters"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)
    color = Column(String, nullable=False)
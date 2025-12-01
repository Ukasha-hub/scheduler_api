from sqlalchemy import Column, Integer, String
from app.db.base import Base
from sqlalchemy.orm import relationship
from app.models.privilege import Privilege

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)
    name = Column(String)
    department = Column(String)
    role = Column(String)  # admin, editor, viewer, guest

    # Add this relationship
    privileges = relationship("Privilege", back_populates="user")
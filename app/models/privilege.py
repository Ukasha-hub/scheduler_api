from sqlalchemy import Column, Integer, Boolean, String, ForeignKey
from app.db.base import Base
from sqlalchemy.orm import relationship

class Privilege(Base):
    __tablename__ = "privileges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    module_name = Column(String)
    can_read = Column(Boolean, default=False)
    can_write = Column(Boolean, default=False)
    can_update = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)

       # Add this relationship
    user = relationship("User", back_populates="privileges")
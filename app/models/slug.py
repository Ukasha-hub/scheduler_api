from sqlalchemy import Column, Integer, String
from app.db.base import Base

class Slug(Base):
    __tablename__ = "slugs"

    id = Column(Integer, primary_key=True, index=True)
    programe_name = Column(String, nullable=False)     # Programee Code
    slug = Column(String, nullable=False)    # Slug Name
    slug_repeat = Column(String, nullable=False)   # Slug Name Repeat
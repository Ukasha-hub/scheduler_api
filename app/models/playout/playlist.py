# Purpose: Playlist model for storing playout playlist information

from sqlalchemy import Column, Integer, String, DateTime
from app.db.base import Base


class Playlist(Base):
    __tablename__ = "playlist"

    id = Column(Integer, primary_key=True, index=True)

    label = Column(String(255), nullable=True)
    name = Column(String(255), nullable=True)
    timecode = Column(String(255), nullable=True)
    starttime = Column(String(255), nullable=True)

    seek = Column(String(255), nullable=True, default="0")
    length = Column(String(255), nullable=True, default="0")

    state = Column(String(10), nullable=True)

    pushtime = Column(DateTime, nullable=True)

    asset_id = Column(String(255), nullable=True)

    scheduler_id = Column(Integer, nullable=True)

    createdby = Column(String(255), nullable=True)

    created = Column(DateTime, nullable=True)

    updated = Column(DateTime, nullable=True)

    updatedby = Column(String(255), nullable=True)

    slug_name = Column(String(255), nullable=True)
from sqlalchemy import Column, Integer, Time
from app.db.base import Base

class HourlyAdSetting(Base):
    __tablename__ = "hourly_ad_settings"

    id = Column(Integer, primary_key=True, index=True)
    hourly_interval = Column(Time, nullable=False) 
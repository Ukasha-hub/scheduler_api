# app/models/scheduler.py
from sqlalchemy import Column, Integer, String, Date, Time, Float
from app.db.base import Base

class Scheduler(Base):
    __tablename__ = "scheduler_settings"

    id = Column(Integer, primary_key=True, index=True)
    slot = Column(String, nullable=False)
    Type = Column(String, nullable=False)

    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=False)

    from_time = Column(Time, nullable=False)
    to_time = Column(Time, nullable=False)

    ad_limit = Column(Float, nullable=False)

    # New nullable fields
    rate_agreement = Column(String, nullable=True)
    bp_code = Column(String, nullable=True)
    time_band = Column(String, nullable=True)

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Date, BigInteger
from sqlalchemy.sql import func
from app.db.base import Base


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)

    client_id = Column(BigInteger, unique=True, index=True, nullable=False)

    # Core info
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    duration = Column(String, default="00:00:00:00")

    # Timing
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    # Frame / time-period metadata
    prev_time_period = Column(JSON, nullable=True)
    time_period = Column(JSON, nullable=True)

    # Business flags
    is_paid = Column(Boolean, default=False)
    bonus = Column(Boolean, default=False)
    repeat = Column(Boolean, default=False)

    # Optional relations
    rate_agreement_no = Column(String, nullable=True)
    agency = Column(String, nullable=True)
    slug = Column(String, nullable=True)
    select_spot = Column(String, nullable=True)

    schedule_date = Column(Date, index=True, nullable=False)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

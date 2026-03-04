from sqlalchemy import Column, Integer, String, BigInteger, TIMESTAMP, Text, JSON, Boolean
from sqlalchemy.sql import func
from app.db.base import Base


class Scheduler(Base):
    __tablename__ = "scheduler"

    id = Column(Integer, primary_key=True, index=True)

    start_date = Column(TIMESTAMP, nullable=True)
    end_date = Column(TIMESTAMP, nullable=True)

    type = Column(String(255), nullable=True)
    program = Column(String(255), nullable=True)
    format = Column(String(255), nullable=True)
    remark = Column(String(255), nullable=True)
    rec_type = Column(String(100), nullable=True)

    event_length = Column(BigInteger, nullable=True)
    event_pid = Column(Integer, nullable=True)

    order_ref = Column(String(20), nullable=True)
    bp_code = Column(String(20), nullable=True)

    duration = Column(String(20), nullable=True)
    sframe = Column(Integer, nullable=True)
    dframe = Column(Integer, nullable=True)
    eframe = Column(Integer, nullable=True)

    episode = Column(String(100), nullable=True)
    segment = Column(String(100), nullable=True)
    serial_type = Column(String(255), nullable=True)
    asset = Column(String(255), nullable=True)
    input_type = Column(String(255), nullable=True)

    created = Column(TIMESTAMP, nullable=True, server_default=func.now())
    createdby = Column(String(100), nullable=True)

    updated = Column(TIMESTAMP, nullable=True, onupdate=func.now())
    updatedby = Column(String(100), nullable=True)

    invoiced = Column(Boolean, nullable=True)
    rate_agreement = Column(Integer, nullable=True)
    rateAgreement_Line = Column(Integer, nullable=True)

    ordered = Column(Boolean, nullable=True)
    invoice_no = Column(String(20), nullable=True)
    rateValidated = Column(Boolean, nullable=True)

    slug_name = Column(Text, nullable=True)
    prev_time_period = Column(JSON, nullable=True)
    time_period = Column(JSON, nullable=True)
    table_id = Column(BigInteger, unique=True, index=True, nullable=False)

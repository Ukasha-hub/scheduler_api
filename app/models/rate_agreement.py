from sqlalchemy import Column, Integer, String, TIMESTAMP, Float
from sqlalchemy.sql import func
from app.db.base import Base


class RateAgreement(Base):
    __tablename__ = "rate_agreement"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    rate_agreementNo = Column(Integer, nullable=False)
    agent_code = Column(String(100), nullable=False)
    agent_name = Column(String(100), nullable=False)

    startDate = Column(TIMESTAMP, nullable=True)
    endDate = Column(TIMESTAMP, nullable=False)
    approveDate = Column(TIMESTAMP, nullable=False)

    rate_agreementLine_ID = Column(Integer, index=True, nullable=False)

    timeslot = Column(String(100), nullable=False)
    positionName = Column(String(100), nullable=True)
    priority = Column(String(100), nullable=True)
    program = Column(String(150), nullable=True)
    timeBand = Column(String(50), nullable=True)

    rate = Column(Float, nullable=False)
    adType = Column(String(100), nullable=False)
    episode_no = Column(Integer, nullable=False)

    limit1 = Column(Float, nullable=False)
    type = Column(String(20), nullable=False)

    lineStartDate = Column(TIMESTAMP, nullable=False)
    lineEndDate = Column(TIMESTAMP, nullable=False)
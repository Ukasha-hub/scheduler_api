from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RateAgreementBase(BaseModel):
    rate_agreementNo: int
    agent_code: str
    agent_name: str

    startDate: Optional[datetime]
    endDate: datetime
    approveDate: datetime

    rate_agreementLine_ID: int

    timeslot: str
    positionName: Optional[str]
    priority: Optional[str]
    program: Optional[str]
    timeBand: Optional[str]

    rate: float
    adType: str
    episode_no: int

    limit1: float
    type: str

    lineStartDate: datetime
    lineEndDate: datetime


class RateAgreementCreate(RateAgreementBase):
    pass


class RateAgreementResponse(RateAgreementBase):
    id: int

    class Config:
        from_attributes = True  # for SQLAlchemy (Pydantic v2)
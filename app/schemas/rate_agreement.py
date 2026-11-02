from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RateAgreementBase(BaseModel):
    rate_agreementNo: Optional[int] = None
    agent_code: Optional[str] = None
    agent_name: Optional[str] = None

    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    approveDate: Optional[datetime] = None

    rate_agreementLine_ID: Optional[int] = None

    timeslot: Optional[str] = None
    positionName: Optional[str] = None
    priority: Optional[str] = None
    program: Optional[str] = None
    timeBand: Optional[str] = None

    rate: Optional[float] = None
    adType: Optional[str] = None
    episode_no: Optional[int] = None

    limit1: Optional[float] = None
    type: Optional[str] = None

    lineStartDate: Optional[datetime] = None
    lineEndDate: Optional[datetime] = None


class RateAgreementCreate(RateAgreementBase):
    pass


class RateAgreementResponse(RateAgreementBase):
    id: int

    class Config:
        from_attributes = True  # SQLAlchemy support (Pydantic v2)
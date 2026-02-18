from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, Dict, List


class ScheduleBase(BaseModel):
    client_id: int
    name: str
    type: str
    duration: str
    start_time: datetime
    end_time: datetime

    prev_time_period: Optional[Dict] = None
    time_period: Optional[Dict] = None

    is_paid: bool = False
    bonus: bool = False
    repeat: bool = False

    rate_agreement_no: Optional[str] = None
    agency: Optional[str] = None
    slug: Optional[str] = None
    select_spot : Optional[str] = None


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    duration: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    prev_time_period: Optional[Dict] = None
    time_period: Optional[Dict] = None

    is_paid: Optional[bool] = None
    bonus: Optional[bool] = None
    repeat: Optional[bool] = None

    rate_agreement_no: Optional[str] = None
    agency: Optional[str] = None
    slug: Optional[str] = None
    select_spot: Optional[str] = None


class ScheduleRead(ScheduleBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ScheduleBulkDelete(BaseModel):
    client_ids: List[int]


class ScheduleSync(BaseModel):
    id: Optional[int]   # null for new rows
    start_time: datetime
    end_time: datetime
    duration: str


class ScheduleReorderRow(BaseModel):
    client_id: int
    duration: str  # "HH:MM:SS:FF"


class ScheduleReorderRequest(BaseModel):
    date: date
    start_time: datetime   # page/day start time
    rows: List[ScheduleReorderRow]
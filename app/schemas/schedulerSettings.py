
from pydantic import BaseModel
from datetime import date, time
from typing import Optional


class SchedulerBase(BaseModel):
    slot: str
    Type: str
    from_date: date
    to_date: date
    from_time: time
    to_time: time
    ad_limit: float

    rate_agreement: Optional[str] = None
    bp_code: Optional[str] = None
    time_band: Optional[str] = None


class SchedulerCreate(SchedulerBase):
    pass

class SchedulerUpdate(SchedulerBase):
    pass

class SchedulerRead(SchedulerBase):
    id: int

    class Config:
        from_attributes = True

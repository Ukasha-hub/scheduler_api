from pydantic import BaseModel
from datetime import datetime

class HistoryBase(BaseModel):
    emp_id: str
    action: str

class HistoryCreate(HistoryBase):
    pass

class HistoryRead(HistoryBase):
    id: int
    action_time: datetime

    class Config:
        from_attributes = True

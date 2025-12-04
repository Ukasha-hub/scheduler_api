from pydantic import BaseModel
from datetime import time

class HourlyAdBase(BaseModel):
    hourly_interval: time 

class HourlyAdCreate(HourlyAdBase):
    pass

class HourlyAdUpdate(HourlyAdBase):
    pass

class HourlyAdRead(HourlyAdBase):
    id: int

    class Config:
        from_attributes = True

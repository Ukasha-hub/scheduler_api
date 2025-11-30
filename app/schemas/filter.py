# Purpose: Pydantic schemas for Filter model
from pydantic import BaseModel

class FilterBase(BaseModel):
    type: str
    color: str

class FilterCreate(FilterBase):
    pass

class FilterRead(FilterBase):
    id: int

    class Config:
        from_attributes = True
        
class FilterDeleteResponse(BaseModel):
    success: bool
    message: str
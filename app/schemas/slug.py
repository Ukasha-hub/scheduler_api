from pydantic import BaseModel
from typing import Optional

class SlugBase(BaseModel):
    programe_name: str
    slug: str
    slug_repeat: str

class SlugCreate(SlugBase):
    pass

class SlugUpdate(SlugBase):
    pass

class SlugCreateWithUser(SlugCreate):
    programe_name: str
    slug: str
    slug_repeat: str
    emp_id: Optional[str] = None 

class DeleteSlugRequest(BaseModel):
    emp_id: Optional[str] = None

class SlugRead(SlugBase):
    id: int

    class Config:
        from_attributes = True

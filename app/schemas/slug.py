from pydantic import BaseModel

class SlugBase(BaseModel):
    programe_name: str
    slug: str
    slug_repeat: str

class SlugCreate(SlugBase):
    pass

class SlugUpdate(SlugBase):
    pass

class SlugRead(SlugBase):
    id: int

    class Config:
        from_attributes = True

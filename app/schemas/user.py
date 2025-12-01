from pydantic import BaseModel

class UserBase(BaseModel):
    user_id: str
    name: str
    department: str
    role: str

class UserCreate(UserBase):
    pass

class UserRead(UserBase):
    id: int

    class Config:
        from_attributes = True

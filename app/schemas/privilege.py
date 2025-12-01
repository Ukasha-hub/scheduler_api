from pydantic import BaseModel

class PrivilegeBase(BaseModel):
    
    can_read: bool = False
    can_write: bool = False
    can_update: bool = False
    can_delete: bool = False

class PrivilegeCreate(PrivilegeBase):
    user_id: int

class PrivilegeRead(PrivilegeBase):
    id: int
    module_name: str
    user_id: int

    class Config:
        from_attributes = True

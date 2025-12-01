from pydantic import BaseModel
from typing import List
from app.schemas.privilege import PrivilegeRead

class UserWithPrivileges(BaseModel):
    id: int
    user_id: str
    name: str
    department: str
    role: str
    privileges: List[PrivilegeRead] = []

    class Config:
        from_attributes = True

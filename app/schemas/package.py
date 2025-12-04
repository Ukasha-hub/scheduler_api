# app/schemas/package.py

from pydantic import BaseModel
from typing import List, Any

class PackageBase(BaseModel):
    name: str
    items: List[Any]

class PackageCreate(PackageBase):
    pass

class PackageRead(PackageBase):
    id: int

    class Config:
        from_attributes = True

class PackagePatch(BaseModel):
    name: str | None = None
    items: List[Any] | None = None        

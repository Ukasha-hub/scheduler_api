from pydantic import BaseModel

class ServerBase(BaseModel):
    server: str
    ip1: str
    ip2: str


class ServerCreate(ServerBase):
    pass


class ServerUpdate(ServerBase):
    pass


class ServerRead(ServerBase):
    id: int

    class Config:
        from_attributes = True

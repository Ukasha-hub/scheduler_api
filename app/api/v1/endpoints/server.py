from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.server import Server
from app.schemas.server import ServerCreate, ServerRead, ServerUpdate
from app.utils.logger import log_action
from app.services.storage.db_lock import execute_with_table_lock
import time

router = APIRouter(prefix="/servers", tags=["Servers"])

# --------------------
# GET ALL SERVERS
# --------------------
@router.get("/", response_model=list[ServerRead])
def get_servers(db: Session = Depends(get_db)):
    servers = db.query(Server).all()
    return servers

# --------------------
# CREATE SERVER
# --------------------
@router.post("/", response_model=ServerRead)
def create_server(payload: ServerCreate, db: Session = Depends(get_db)):
    def operation():
        new_server = Server(
            server=payload.server,
            ip1=payload.ip1,
            ip2=payload.ip2
        )
        db.add(new_server)
        db.flush()
        log_action(db, emp_id="101", action=f"New server created: serber:{payload.server}, ip1:{payload.ip1}, ip2:{payload.ip2}")
        return new_server
    return execute_with_table_lock(
        db=db,
        table_name="servers",
        operation=operation,
        
    )
# --------------------
# UPDATE SERVER
# --------------------
@router.put("/{id}", response_model=ServerRead)
def update_server(id: int, payload: ServerUpdate, db: Session = Depends(get_db)):
    def operation():
        server_item = db.query(Server).filter(Server.id == id).first()

        if not server_item:
            raise HTTPException(status_code=404, detail="Server not found")

        server_item.server = payload.server
        server_item.ip1 = payload.ip1
        server_item.ip2 = payload.ip2

        db.flush()
        log_action(db, emp_id="101", action=f"Updated server: server:{payload.server}, ip1:{payload.ip1}, ip2:{payload.ip2}")
        return server_item
    return execute_with_table_lock(
        db=db,
        table_name="servers",
        operation=operation,
        
    )

# --------------------
# DELETE SERVER
# --------------------
@router.delete("/{id}", response_model=dict)
def delete_server(id: int, db: Session = Depends(get_db)):
    def operation():
        server_item = db.query(Server).filter(Server.id == id).first()

        if not server_item:
            raise HTTPException(status_code=404, detail="Server not found")

        db.delete(server_item)
        db.flush()
        log_action(db, emp_id="101", action=f"Deleted server: {server_item.server}")
        return {"detail": "Server deleted successfully"}
    return execute_with_table_lock(
        db=db,
        table_name="servers",
        operation=operation,
        
    )
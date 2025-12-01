from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict
from pydantic import BaseModel

from app.db.session import get_db
from app.models.privilege import Privilege
from app.schemas.privilege import PrivilegeCreate

router = APIRouter(prefix="/privileges")

class PrivilegeMatrix(BaseModel):
    user_id: int
    crudMatrix: Dict[str, Dict[str, bool]]  # {"isRead": {"Scheduler": True, ...}, ...}

@router.post("/set")
def set_privilege(payload: PrivilegeMatrix, db: Session = Depends(get_db)):
    user_id = payload.user_id
    matrix = payload.crudMatrix

    # Delete old privileges
    db.query(Privilege).filter(Privilege.user_id == user_id).delete()

    # Store new privileges
    for crud, modules in matrix.items():
        for module, value in modules.items():
            if value:
                # Use schema for creating new privilege
                priv_data = PrivilegeCreate(
                    user_id=user_id,
                    module_name=module,
                    can_read=(crud == "isRead"),
                    can_write=(crud == "isWrite"),
                    can_update=(crud == "isUpdate"),
                    can_delete=(crud == "isDelete"),
                )
                priv = Privilege(**priv_data.dict())
                db.add(priv)

    db.commit()
    return {"message": "Privileges updated"}

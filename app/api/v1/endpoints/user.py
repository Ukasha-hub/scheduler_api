from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from typing import Dict, Optional
from pydantic import BaseModel
from typing import List

from app.db.session import get_db
from app.models.user import User
from app.models.privilege import Privilege
from app.core.default_privileges import DEFAULT_PRIVILEGES
from app.schemas.user import UserCreate, UserRead
from app.schemas.privilege import PrivilegeCreate, PrivilegeBase
from app.schemas.userwithprivilege import UserWithPrivileges
from app.services.storage.db_lock import execute_with_table_lock
import time

router = APIRouter(prefix="/users")

class UserWithPrivilege(BaseModel):
    user_id: str
    name: str
    department: str
    role: str
    privilegeSet: Optional[bool] = False
    crudMatrix: Optional[Dict[str, PrivilegeBase]] = None  # Optional manual privileges

@router.get("/users", response_model=List[UserWithPrivileges])
def get_users_with_privileges(db: Session = Depends(get_db)):
    users = (
        db.query(User)
        .options(joinedload(User.privileges))  # load privileges automatically
        .all()
    )
    return users 

@router.post("/create", response_model=UserRead)
def create_user_with_privileges(payload: UserWithPrivilege, db: Session = Depends(get_db)):
    # 1. Create user
    # Create user
    user = User(
        user_id=payload.user_id,
        name=payload.name,
        department=payload.department,
        role=payload.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # If privilegeSet = true → Use crudMatrix from frontend
    if payload.privilegeSet and payload.crudMatrix:

        for module_name, perms in payload.crudMatrix.items():
            priv = Privilege(
                user_id=user.id,
                module_name=module_name,
                can_read=perms.can_read,
                can_write=perms.can_write,
                can_update=perms.can_update,
                can_delete=perms.can_delete,
            )
            db.add(priv)

    else:
        # Otherwise assign default privileges
        role_privs = DEFAULT_PRIVILEGES.get(payload.role, {})
        for module, perms in role_privs.items():
            db.add(Privilege(
                user_id=user.id,
                module_name=module,
                can_read=perms.get("read", False),
                can_write=perms.get("write", False),
                can_update=perms.get("update", False),
                can_delete=perms.get("delete", False)
            ))

    db.commit()
    return user

@router.delete("/delete/{id}", response_model=dict)
def delete_user(id: int, db: Session = Depends(get_db)):
    # 1. Fetch the user by database id
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Delete all privileges for this user
    db.query(Privilege).filter(Privilege.user_id == id).delete(synchronize_session=False)

    # 3. Delete the user
    db.delete(user)

    # 4. Commit changes
    db.commit()

    return {"detail": f"User with id '{id}' and all associated privileges have been deleted."}

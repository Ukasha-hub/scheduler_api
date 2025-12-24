from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.history import History
from app.schemas.history import HistoryRead

router = APIRouter()

# -------------------------------------------------
# GET all history logs
# -------------------------------------------------
@router.get("/", response_model=list[HistoryRead])
def get_all_history(db: Session = Depends(get_db)):
    history_rows = db.query(History).order_by(History.id.desc()).all()
    return history_rows

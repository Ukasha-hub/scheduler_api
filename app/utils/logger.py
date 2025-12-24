from sqlalchemy.orm import Session
from app.models.history import History

def log_action(db: Session, emp_id: str, action: str):
    """Global logging function shared across all modules"""
    log_entry = History(
        emp_id=emp_id,
        action=action
    )
    db.add(log_entry)
    db.commit()
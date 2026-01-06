# app/api/v1/endpoints/scheduler.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.schedulerSettings import Scheduler
from app.schemas.schedulerSettings import SchedulerCreate, SchedulerUpdate, SchedulerRead
from app.utils.logger import log_action
from app.services.storage.db_lock import execute_with_table_lock
import time

router = APIRouter()

# ▶ GET all schedules
@router.get("/", response_model=list[SchedulerRead])
def get_all_schedules(db: Session = Depends(get_db)):
    return db.query(Scheduler).all()


# ▶ CREATE schedule
@router.post("/", response_model=SchedulerRead)
def create_schedule(data: SchedulerCreate, db: Session = Depends(get_db)):
    def operation():
        schedule = Scheduler(**data.dict())
        db.add(schedule)
        db.flush()
        
        log_action(db, emp_id="101", action=f"New scheduler created {schedule}")
        return schedule
    return execute_with_table_lock(
        db=db,
        table_name="scheduler_settings",
        operation=operation,
        
    )

# ▶ UPDATE schedule
@router.put("/{schedule_id}", response_model=SchedulerRead)
def update_schedule(schedule_id: int, data: SchedulerUpdate, db: Session = Depends(get_db)):
    def operation():
        schedule = db.query(Scheduler).filter(Scheduler.id == schedule_id).first()

        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        for key, value in data.dict().items():
            setattr(schedule, key, value)

        db.flush()
        log_action(db, emp_id="101", action=f"Updated scheduler {schedule}")
        return schedule
    return execute_with_table_lock(
        db=db,
        table_name="scheduler_settings",
        operation=operation,
        
    )

# ▶ DELETE schedule
@router.delete("/{schedule_id}")
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    def operation():
        schedule = db.query(Scheduler).filter(Scheduler.id == schedule_id).first()
        
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        db.delete(schedule)
        db.flush()
        log_action(db, emp_id="101", action=f"Deleted scheduler  {schedule}")
        return {"message": "Schedule deleted successfully"}
    return execute_with_table_lock(
        db=db,
        table_name="scheduler_settings",
        operation=operation,
        
    )
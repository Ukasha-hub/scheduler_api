# app/api/v1/endpoints/scheduler.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.schedulerSettings import Scheduler
from app.schemas.schedulerSettings import SchedulerCreate, SchedulerUpdate, SchedulerRead, SchedulerCreateWithUser, DeleteScheduleRequest
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
def create_schedule(
    data: SchedulerCreateWithUser,  # includes emp_id for history
    db: Session = Depends(get_db),
):
    def operation():
        # 1️⃣ create scheduler row
        schedule = Scheduler(**data.dict(exclude={"emp_id"}))  # exclude emp_id
        db.add(schedule)
        db.flush()

        # 2️⃣ log history
        if data.emp_id:
            log_action(
                db,
                emp_id=data.emp_id,
                action=f"New scheduler settings created {schedule.slot}"
            )

        return schedule

    return execute_with_table_lock(
        db=db,
        table_name="scheduler_settings",
        operation=operation,
    )

# ▶ UPDATE schedule
@router.put("/{schedule_id}", response_model=SchedulerRead)
def update_schedule(
    schedule_id: int,
    data: SchedulerCreateWithUser,  # use same schema with emp_id
    db: Session = Depends(get_db)
):
    def operation():
        schedule = db.query(Scheduler).filter(Scheduler.id == schedule_id).first()
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        for key, value in data.dict(exclude={"emp_id"}).items():
            setattr(schedule, key, value)

        db.flush()

        if data.emp_id:
            log_action(
                db,
                emp_id=data.emp_id,
                action=f"Updated scheduler settings {schedule.slot}"
            )

        return schedule

    return execute_with_table_lock(
        db=db,
        table_name="scheduler_settings",
        operation=operation,
    )

# ▶ DELETE schedule
@router.delete("/{schedule_id}")
def delete_schedule(schedule_id: int, data: DeleteScheduleRequest, db: Session = Depends(get_db)):
    def operation():
        schedule = db.query(Scheduler).filter(Scheduler.id == schedule_id).first()
        
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        db.delete(schedule)
        db.flush()
        log_action(db, emp_id=data.emp_id, action=f"Deleted scheduler settings {schedule}")
        return {"message": "Schedule deleted successfully"}
    return execute_with_table_lock(
        db=db,
        table_name="scheduler_settings",
        operation=operation,
        
    )
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.utils.logger import log_action
from typing import List
from app.services.storage.db_lock import execute_with_table_lock
from sqlalchemy import Date

from app.db.session import get_db
from app.models.scheduler import Scheduler
from app.schemas.scheduler import (
    SchedulerCreate,
    SchedulerRead,
    SchedulerUpdate,
    SchedulerBulkDelete,
    SchedulerSync,
    SchedulerReorderRequest
)

from datetime import date, timedelta

router = APIRouter()

@router.get("/", response_model=List[SchedulerRead])
def list_schedulers(
    date: date,
    db: Session = Depends(get_db)
):
    return (
        db.query(Scheduler)
        .filter(Scheduler.start_date.cast(Date) == date)
        .order_by(Scheduler.start_date)
        .all()
    )

@router.get("/{scheduler_id}", response_model=SchedulerRead)
def get_scheduler(scheduler_id: int, db: Session = Depends(get_db)):
    obj = db.query(Scheduler).filter(Scheduler.id == scheduler_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Scheduler not found")
    return obj


@router.post("/", response_model=SchedulerRead)
def create_scheduler(
    payload: SchedulerCreate,
    emp_id: str = Query(...),
    db: Session = Depends(get_db)
):
    obj = Scheduler(**payload.model_dump())

    db.add(obj)
    db.commit()
    db.refresh(obj)

    log_action(
        db,
        emp_id=emp_id,
        action=f"Created scheduler row {obj.id}"
    )

    return obj


@router.post("/sync", response_model=List[SchedulerRead])
def sync_day_scheduler(
    date: date,
    rows: List[SchedulerCreate],
    emp_id: str = Query(...),
    action: str = Query(None),
    db: Session = Depends(get_db)
):
    def operation():
        existing = {
            s.table_id: s
            for s in db.query(Scheduler)
            .filter(Scheduler.start_date.cast(Date) == date)
            .all()
        }

        incoming_ids = set()

        for row in rows:
            if not hasattr(row, "table_id"):
                continue

            incoming_ids.add(row.table_id)

            if row.table_id in existing:
                obj = existing[row.table_id]
                for field, value in row.model_dump().items():
                    setattr(obj, field, value)
            else:
                obj = Scheduler(**row.model_dump())
                db.add(obj)

        for table_id, obj in existing.items():
            if table_id not in incoming_ids:
                db.delete(obj)

        db.flush()

        log_action(
            db,
            emp_id=emp_id,
            action=action
        )

        return (
            db.query(Scheduler)
            .filter(Scheduler.start_date.cast(Date) == date)
            .order_by(Scheduler.start_date)
            .all()
        )

    return execute_with_table_lock(
        db=db,
        table_name="scheduler",
        operation=operation,
    )


@router.put("/{table_id}", response_model=SchedulerRead)
def update_scheduler_by_table_id(
    table_id: int,
    payload: SchedulerUpdate,
    emp_id: str = Query(...),
    db: Session = Depends(get_db),
):
    def operation():
        obj = db.query(Scheduler).filter(Scheduler.table_id == table_id).first()
        if not obj:
            raise HTTPException(status_code=404, detail="Scheduler not found")

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)

        db.flush()

        log_action(
            db,
            emp_id=emp_id,
            action=f"Updated scheduler {table_id}"
        )

        return obj

    return execute_with_table_lock(
        db=db,
        table_name="scheduler",
        operation=operation,
    )

@router.delete("/{table_id}")
def delete_scheduler_by_table_id(
    table_id: int,
    db: Session = Depends(get_db)
):
    def operation():
        obj = db.query(Scheduler).filter(Scheduler.table_id == table_id).first()
        if not obj:
            raise HTTPException(status_code=404, detail="Scheduler not found")

        db.delete(obj)
        db.flush()

        return {"success": True}

    return execute_with_table_lock(
        db=db,
        table_name="scheduler",
        operation=operation,
    )
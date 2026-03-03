from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.utils.logger import log_action
from typing import List
from app.services.storage.db_lock import execute_with_table_lock

from app.db.session import get_db
from app.models.schedule import Schedule
from app.schemas.schedule import (
    ScheduleCreate,
    ScheduleRead,
    ScheduleUpdate,
    ScheduleBulkDelete,
    ScheduleSync,
    ScheduleReorderRequest
)

from datetime import timedelta, date

router = APIRouter()



def validate_duration(start, end, duration_str):
    h, m, s, f = map(int, duration_str.split(":"))
    expected = timedelta(hours=h, minutes=m, seconds=s)
    if end - start != expected:
        raise HTTPException(
            status_code=400,
            detail="Duration does not match start/end time"
        )


@router.get("/", response_model=List[ScheduleRead])
def list_schedules(
    date: date,
    db: Session = Depends(get_db)
):
    return (
        db.query(Schedule)
        .filter(Schedule.schedule_date == date)
        .order_by(Schedule.start_time)
        .all()
    )


@router.get("/{schedule_id}", response_model=ScheduleRead)
def get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    obj = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return obj


@router.post("/", response_model=ScheduleRead)
def create_schedule(
    payload: ScheduleCreate,
    emp_id: str = Query(...),
    db: Session = Depends(get_db)
):
    obj = Schedule(
        **payload.model_dump(),
        schedule_date=payload.start_time.date()
    )

    db.add(obj)
    db.commit()
    db.refresh(obj)

    log_action(
        db,
        emp_id=emp_id,
        action=f"Created schedule {obj.client_id} - {obj.name}"
    )

    return obj

@router.post("/sync", response_model=List[ScheduleRead])
def sync_day_schedules(
    date: date,
    rows: List[ScheduleCreate],
    emp_id: str = Query(...),
    action: str = Query(...),
    db: Session = Depends(get_db)
):
    def operation():
        existing = {
            s.client_id: s
            for s in db.query(Schedule)
            .filter(Schedule.schedule_date == date)
            .all()
        }

        incoming_ids = set()

        for row in rows:
            incoming_ids.add(row.client_id)

            if row.client_id in existing:
                obj = existing[row.client_id]
                for field, value in row.model_dump().items():
                    setattr(obj, field, value)
            else:
                obj = Schedule(**row.model_dump(), schedule_date=date)
                db.add(obj)

        for client_id, obj in existing.items():
            if client_id not in incoming_ids:
                db.delete(obj)

        db.flush()

        log_action(
            db,
            emp_id=emp_id,
            action=action
        )

        return (
            db.query(Schedule)
            .filter(Schedule.schedule_date == date)
            .order_by(Schedule.start_time)
            .all()
        )

    return execute_with_table_lock(
        db=db,
        table_name="schedules",
        operation=operation,
    )




@router.put("/{client_id}", response_model=ScheduleRead)
def update_schedule_by_client_id(
    client_id: int,
    payload: ScheduleUpdate,
    emp_id: str = Query(...),
    db: Session = Depends(get_db),
):
    def operation():
        obj = db.query(Schedule).filter(Schedule.client_id == client_id).first()
        if not obj:
            raise HTTPException(status_code=404, detail="Schedule not found")

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)

        if payload.start_time and payload.end_time and payload.duration:
            validate_duration(payload.start_time, payload.end_time, payload.duration)

        db.flush()

        log_action(
            db,
            emp_id=emp_id,
            action=f"Updated schedule {client_id}"
        )

        return obj

    return execute_with_table_lock(
        db=db,
        table_name="schedules",
        operation=operation,
    )


@router.delete("/{client_id}")
def delete_schedule_by_client_id(
    client_id: int,
    
    db: Session = Depends(get_db)
):
    def operation():
        obj = db.query(Schedule).filter(Schedule.client_id == client_id).first()
        if not obj:
            raise HTTPException(status_code=404, detail="Schedule not found")

        db.delete(obj)
        db.flush()

       

        return {"success": True}

    return execute_with_table_lock(
        db=db,
        table_name="schedules",
        operation=operation,
    )








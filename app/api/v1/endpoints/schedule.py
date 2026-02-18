from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

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
def create_schedule(payload: ScheduleCreate, db: Session = Depends(get_db)):
    obj = Schedule(
    **payload.model_dump(),
    schedule_date=payload.start_time.date()
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.post("/sync", response_model=List[ScheduleRead])
def sync_day_schedules(
    date: date,
    rows: List[ScheduleCreate],
    db: Session = Depends(get_db)
):
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

    # delete removed rows
    for client_id, obj in existing.items():
        if client_id not in incoming_ids:
            db.delete(obj)

    db.commit()

    return (
        db.query(Schedule)
        .filter(Schedule.schedule_date == date)
        .order_by(Schedule.start_time)
        .all()
    )




@router.put("/{client_id}", response_model=ScheduleRead)
def update_schedule_by_client_id(
    client_id: int,
    payload: ScheduleUpdate,
    db: Session = Depends(get_db),
):
    obj = db.query(Schedule).filter(Schedule.client_id == client_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Schedule not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)

    if payload.start_time and payload.end_time and payload.duration:
        validate_duration(payload.start_time, payload.end_time, payload.duration)

    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{client_id}")
def delete_schedule_by_client_id(
    client_id: int,
    db: Session = Depends(get_db)
):
    obj = db.query(Schedule).filter(Schedule.client_id == client_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Schedule not found")

    db.delete(obj)
    db.commit()
    return {"success": True}


@router.delete("/bulk")
def bulk_delete_by_client_id(
    payload: ScheduleBulkDelete,
    db: Session = Depends(get_db)
):
    rows = (
        db.query(Schedule)
        .filter(Schedule.client_id.in_(payload.client_ids))
        .all()
    )

    for row in rows:
        db.delete(row)

    db.commit()
    return {"deleted": len(rows)}



@router.put("/reorder", response_model=List[ScheduleRead])
def reorder_day_schedules(
    payload: ScheduleReorderRequest,
    db: Session = Depends(get_db)
):
    schedules = {
        s.client_id: s
        for s in db.query(Schedule)
        .filter(Schedule.schedule_date == payload.date.date())
        .all()
    }

    current_time = payload.start_time

    for row in payload.rows:
        if row.client_id not in schedules:
            raise HTTPException(
                status_code=404,
                detail=f"Schedule {row.client_id} not found"
            )

        obj = schedules[row.client_id]

        # parse duration
        h, m, s, _ = map(int, row.duration.split(":"))
        duration_delta = timedelta(hours=h, minutes=m, seconds=s)

        obj.start_time = current_time
        obj.end_time = current_time + duration_delta
        obj.duration = row.duration

        current_time = obj.end_time

    db.commit()

    return (
        db.query(Schedule)
        .filter(Schedule.schedule_date == payload.date.date())
        .order_by(Schedule.start_time)
        .all()
    )

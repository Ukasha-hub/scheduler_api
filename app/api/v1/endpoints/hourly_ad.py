from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.hourly_ad import HourlyAdSetting
from app.schemas.hourly_ad import HourlyAdCreate, HourlyAdRead, HourlyAdUpdate
from app.utils.logger import log_action

router = APIRouter()

# -------------------------------------------------
# GET current hourly ad settings
# -------------------------------------------------
@router.get("/", response_model=HourlyAdRead)
def get_hourly_ad_settings(db: Session = Depends(get_db)):
    settings = db.query(HourlyAdSetting).first()

    if not settings:
        # return default if nothing stored yet
        return HourlyAdSetting(id=0, hourly_interval="01:00:00")

    return settings


# -------------------------------------------------
# CREATE or UPDATE settings
# -------------------------------------------------
@router.post("/", response_model=HourlyAdRead)
def save_hourly_ad_settings(payload: HourlyAdCreate, db: Session = Depends(get_db)):
    settings = db.query(HourlyAdSetting).first()

    if settings:
        # UPDATE
        settings.hourly_interval = payload.hourly_interval
        db.commit()
        db.refresh(settings)
        return settings

    # CREATE
    new_settings = HourlyAdSetting(hourly_interval=payload.hourly_interval)
    db.add(new_settings)
    db.commit()
    db.refresh(new_settings)
    log_action(db, emp_id="101", action=f"Updated hourly interval to {payload.hourly_interval}")

    return new_settings

from fastapi import APIRouter
from datetime import datetime, timezone
from app.models.xyz import XYZ
from app.models.xyz_backup import XYZBackup
from app.schemas.backup import BackupRequest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

router = APIRouter()

def get_db_by_ip(ip: str):
    DB_URL = f"postgresql://postgres:password@{ip}:5432/scheduler"
    engine = create_engine(DB_URL)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return SessionLocal()


def backup_and_clear_logic(db: Session, cutoff_date: datetime):
    records = db.query(XYZ).filter(XYZ.created_at <= cutoff_date).all()

    if not records:
        return 0

    db.bulk_save_objects([
        XYZBackup(data=r.data, created_at=r.created_at)
        for r in records
    ])

    db.query(XYZ).filter(XYZ.created_at <= cutoff_date).delete()

    return len(records)


@router.post("/backup-and-clear")
def backup_and_clear(payload: BackupRequest):
    results = []

    # ✅ FIX: cutoff INSIDE function
    cutoff_date = datetime.fromisoformat(payload.date_upto)

    # make timezone-safe
    if cutoff_date.tzinfo is None:
        cutoff_date = cutoff_date.replace(tzinfo=timezone.utc)

    for ip in payload.ip_list:
        db = None
        try:
            db = get_db_by_ip(ip)

            moved = backup_and_clear_logic(db, cutoff_date)
            db.commit()

            results.append({
                "ip": ip,
                "status": "Success",
                "moved": moved
            })

        except Exception as e:
            if db:
                db.rollback()

            results.append({
                "ip": ip,
                "status": "Error",
                "error": str(e)
            })

        finally:
            if db:
                db.close()

    return {
        "message": "Backup completed",
        "details": results
    }
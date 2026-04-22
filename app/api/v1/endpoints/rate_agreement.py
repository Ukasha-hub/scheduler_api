from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import distinct

from app.db.session import SessionLocal
from app.models.rate_agreement import RateAgreement

router = APIRouter()


# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/rate-agreements")
def get_rate_agreements_by_agent(
    agent_code: str = Query(...),
    db: Session = Depends(get_db)
):
    results = (
        db.query(distinct(RateAgreement.rate_agreementNo))
        .filter(RateAgreement.agent_code == agent_code)
        .all()
    )

    # results comes like [(1,), (2,), (3,)] → flatten it
    rate_agreements = [r[0] for r in results]

    return {
        "agent_code": agent_code,
        "rate_agreementNos": rate_agreements
    }
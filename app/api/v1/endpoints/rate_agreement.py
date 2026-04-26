from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import SessionLocal
from app.models.rate_agreement import RateAgreement
from app.schemas.rate_agreement import RateAgreementResponse

router = APIRouter()


# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# IMPORTANT: All static routes MUST come BEFORE any route with path parameters
# Static route 1: Filter by agency only
@router.get("/by-agency", response_model=List[RateAgreementResponse])
def get_rate_agreements_by_agency(
    agent_code: str = Query(..., description="Agency code"),
    db: Session = Depends(get_db)
):
    """
    Get all rate agreements for a specific agency
    """
    print(f"Searching for agent_code: {agent_code}")
    
    results = (
        db.query(RateAgreement)
        .filter(RateAgreement.agent_code == agent_code)
        .all()
    )
    
    print(f"Found {len(results)} results")
    
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No rate agreements found for agency: {agent_code}"
        )
    
    return results


# Static route 2: Filter by programme and agency
@router.get("/by-program-agency", response_model=List[RateAgreementResponse])
def get_rate_agreements_by_program_agency(
    program: str = Query(..., description="Programme code"),
    agent_code: str = Query(..., description="Agency code"),
    db: Session = Depends(get_db)
):
    """
    Get all rate agreements that match both programme and agency
    """
    print(f"Searching for program: {program}, agent_code: {agent_code}")
    
    results = (
        db.query(RateAgreement)
        .filter(
            RateAgreement.program == program,
            RateAgreement.agent_code == agent_code
        )
        .all()
    )
    
    print(f"Found {len(results)} results")
    
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No rate agreements found for programme: {program} and agency: {agent_code}"
        )
    
    return results


# Dynamic route with path parameter - MUST be LAST
@router.get("/{rate_agreementNo}", response_model=List[RateAgreementResponse])
def get_rate_agreements_by_agreement_no(
    rate_agreementNo: int,
    db: Session = Depends(get_db)
):
    """
    Get all rate agreement lines for a specific rate_agreementNo
    """
    print(f"Searching for rate_agreementNo: {rate_agreementNo}")
    
    results = (
        db.query(RateAgreement)
        .filter(RateAgreement.rate_agreementNo == rate_agreementNo)
        .all()
    )
    
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No rate agreements found for rate_agreementNo: {rate_agreementNo}"
        )
    
    return results
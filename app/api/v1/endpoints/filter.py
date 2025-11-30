# Purpose: Filter CRUD API endpoints
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.filter import FilterCreate, FilterRead, FilterDeleteResponse
from app.models.filter import Filter

router = APIRouter()

# Create filter
@router.post("/", response_model=FilterRead)
def create_filter(payload: FilterCreate, db: Session = Depends(get_db)):
    db_obj = Filter(type=payload.type, color=payload.color)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

# Get all filters
@router.get("/", response_model=list[FilterRead])
def get_filters(db: Session = Depends(get_db)):
    return db.query(Filter).all()

# Delete filter by ID
@router.delete("/{filter_id}", response_model=dict)
def delete_filter(filter_id: int, db: Session = Depends(get_db)):
    db_obj = db.query(Filter).filter(Filter.id == filter_id).first()
    if not db_obj:
        return {"success": False, "message": "Filter not found"}
    
    db.delete(db_obj)
    db.commit()
    return {"success": True, "message": f"Filter with id {filter_id} deleted"}   

# Delete filter by ID using schema
@router.delete("/{filter_id}", response_model=FilterDeleteResponse)
def delete_filter(filter_id: int, db: Session = Depends(get_db)):
    db_obj = db.query(Filter).filter(Filter.id == filter_id).first()
    if not db_obj:
        return FilterDeleteResponse(success=False, message="Filter not found")
    
    db.delete(db_obj)
    db.commit()
    return FilterDeleteResponse(success=True, message=f"Filter with id {filter_id} deleted")     

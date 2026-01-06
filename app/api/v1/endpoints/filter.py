# Purpose: Filter CRUD API endpoints
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.filter import FilterCreate, FilterRead, FilterDeleteResponse, FilterUpdate
from app.models.filter import Filter
from app.utils.logger import log_action
from app.services.storage.db_lock import execute_with_table_lock
import time

router = APIRouter()

# Create filter
@router.post("/", response_model=FilterRead)
def create_filter(payload: FilterCreate, db: Session = Depends(get_db)):
    def operation():
        db_obj = Filter(type=payload.type, color=payload.color)
        db.add(db_obj)
        db.flush()
        log_action(db, emp_id="101", action=f"Created filter: {payload.type}, {payload.color}")
        return db_obj
    return execute_with_table_lock(
        db=db,
        table_name="filters",
        operation=operation,
        success_message="filtersettings saved successfully"
    )
# Get all filters
@router.get("/", response_model=list[FilterRead])
def get_filters(db: Session = Depends(get_db)):
    return db.query(Filter).all()



# Delete filter by ID using schema
@router.delete("/{filter_id}", response_model=FilterDeleteResponse)
def delete_filter( filter_id: int, db: Session = Depends(get_db)):
    def operation():
        db_obj = db.query(Filter).filter(Filter.id == filter_id).first()
        #time.sleep(20) 
        if not db_obj:
            return FilterDeleteResponse(success=False, message="Filter not found")
    
        db.delete(db_obj)
        db.flush()
        log_action(db, emp_id="101", action=f"Deleted a filter: type:{db_obj.type} color:{db_obj.color} ")
        return FilterDeleteResponse(success=True, message=f"Filter with id {filter_id} deleted")     
    return execute_with_table_lock(
        db=db,
        table_name="filters",
        operation=operation,
        success_message="filtersettings saved successfully"
    )
# Update filter
@router.put("/{filter_id}", response_model=FilterRead)
def update_filter(filter_id: int, payload: FilterUpdate, db: Session = Depends(get_db)):
    def operation():
        db_obj = db.query(Filter).filter(Filter.id == filter_id).first()
        if not db_obj:
            return {"error": "Filter not found"}

        db_obj.type = payload.type
        db_obj.color = payload.color

        db.flush()
        log_action(db, emp_id="101", action=f"Updated filter to: type:{payload.type}, color:{payload.color}")
        return db_obj
    return execute_with_table_lock(
        db=db,
        table_name="filters",
        operation=operation,
        
    )
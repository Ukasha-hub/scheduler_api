from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import MetaData, Table, select, text, func
from typing import List, Dict, Any, Optional

from app.db.archive_session import get_archive_db

router = APIRouter(prefix="/archive", tags=["archive"])

# Define the table name
ARCHIVE_TABLE_NAME = "archive"

@router.get("/records")
def get_archive_records(
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    per_page: int = Query(100, ge=1, le=500, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term for filtering"),
    db: Session = Depends(get_archive_db)
):
    """
    Get paginated records from archive database using reflection
    """
    try:
        # Reflect the table from database
        metadata = MetaData()
        archive_table = Table(ARCHIVE_TABLE_NAME, metadata, autoload_with=db.get_bind())
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Build base query
        query = select(archive_table)
        
        # Add search filter if provided
        if search:
            search_term = f"%{search}%"
            query = query.where(
                archive_table.c.program_name.ilike(search_term) |
                archive_table.c.tape_id.ilike(search_term) |
                archive_table.c.archiver_name.ilike(search_term)
            )
        
        # Get total count
        count_query = select(func.count()).select_from(archive_table)
        if search:
            count_query = count_query.where(
                archive_table.c.program_name.ilike(search_term) |
                archive_table.c.tape_id.ilike(search_term) |
                archive_table.c.archiver_name.ilike(search_term)
            )
        total_records = db.execute(count_query).scalar()
        
        # Get paginated records
        query = query.order_by(archive_table.c.id.desc()).offset(offset).limit(per_page)
        result = db.execute(query)
        records = result.mappings().all()
        
        # Convert to list of dicts
        records_list = [dict(record) for record in records]
        
        # Calculate total pages
        total_pages = (total_records + per_page - 1) // per_page
        
        return {
            "data": records_list,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_records": total_records,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }
        }
        
    except Exception as e:
        print(f"Error fetching archive records: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/records/{record_id}")
def get_archive_record(
    record_id: int,
    db: Session = Depends(get_archive_db)
):
    """
    Get specific record from archive database by ID
    """
    try:
        # Reflect the table
        metadata = MetaData()
        archive_table = Table(ARCHIVE_TABLE_NAME, metadata, autoload_with=db.get_bind())
        
        # Query by ID
        query = select(archive_table).where(archive_table.c.id == record_id)
        result = db.execute(query)
        record = result.mappings().first()
        
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")
        
        return dict(record)
    except Exception as e:
        print(f"Error fetching archive record: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
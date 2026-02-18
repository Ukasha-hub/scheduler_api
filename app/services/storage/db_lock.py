from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from fastapi import HTTPException
from sqlalchemy import text
from typing import List

def execute_with_table_lock(
    db: Session,
    table_name: str,
    operation,
    success_message: str = "Execution successful"
):
    try:
        # Set lock timeout (prevents infinite waiting)
        #db.execute(text("SET lock_timeout = '5s'"))

        # Lock table
        db.execute(text(f"LOCK TABLE {table_name}  IN EXCLUSIVE MODE"))

        # Execute the business logic
        result = operation()

        # Commit releases the lock
        db.commit()

        return result

    except OperationalError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Table is busy. Please try again."
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

def execute_with_joined_table_lock(
    db: Session,
    tables: List[str],
    operation,
):
    try:
        table_sql = ", ".join(tables)
        db.execute(text(f"LOCK TABLE {table_sql} IN EXCLUSIVE MODE"))
        result = operation()
        db.commit()
        return result

    except OperationalError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="One of the tables is busy. Please try again."
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
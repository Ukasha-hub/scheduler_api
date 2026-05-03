# Purpose: Endpoint to fetch media data with alias-specific queries

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from fastapi.concurrency import run_in_threadpool

router = APIRouter()


def get_sessionmaker_by_alias(alias: str):
    """
    Return SQLAlchemy sessionmaker for the given DB alias
    """
    db_conf = next(
        (c for c in settings.DB_CONFIGS if c["alias"].lower() == alias.lower()),
        None
    )

    if not db_conf:
        raise KeyError(f"DB alias '{alias}' not found")

    conn_str = (
        f"{db_conf['driver']}://{db_conf['user']}:{db_conf['password']}"
        f"@{db_conf['host']}:{db_conf['port']}/{db_conf['database']}"
    )

    engine = create_engine(conn_str, pool_pre_ping=True)

    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )


def run_query(session, alias: str):
    """Sync function that executes SQL query"""
    if alias.lower() == "razuna":
        query = text("""
            SELECT 
                VID_FILENAME, 
                VID_ID, 
                VID_CREATE_DATE,
                ROUND(VID_SIZE / (1024 * 1024 * 1024), 2) AS VID_SIZE_GB
            FROM raz1_videos
            ORDER BY VID_CREATE_DATE DESC
        """)
    else:
        query = text("SELECT filename, id, created_at FROM media_table")

    result = session.execute(query).fetchall()
    return [dict(row._mapping) for row in result]


def run_asset_query_by_program(session, alias: str, program_name: str):
    """Sync function that executes SQL query to fetch asset IDs by program"""
    if alias.lower() == "razuna":
        # Adjust table/column names based on your Razuna schema
        query = text("""
            SELECT 
                VID_ID as asset_id,
                VID_FILENAME as asset_name,
                VID_CREATE_DATE as created_date
            FROM raz1_videos
            WHERE VID_FILENAME LIKE :program_pattern
            ORDER BY VID_CREATE_DATE DESC
        """)
    else:
        # Generic query - adjust based on your schema
        query = text("""
            SELECT 
                id as asset_id,
                filename as asset_name,
                created_at as created_date
            FROM media_table
            WHERE filename LIKE :program_pattern
        """)
    
    # Add wildcards for partial matching
    program_pattern = f"%{program_name}%"
    result = session.execute(query, {"program_pattern": program_pattern}).fetchall()
    return [dict(row._mapping) for row in result]


@router.get("/")
async def get_media(alias: str = Query(...)):
    """
    Fetch media metadata from the DB using the dynamic server alias (ASYNC).
    Uses threadpool for DB (no aiomysql needed).
    """
    try:
        SessionLocal = get_sessionmaker_by_alias(alias)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    session = SessionLocal()

    try:
        media_list = await run_in_threadpool(run_query, session, alias)
        return {"status": "success", "data": media_list}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        await run_in_threadpool(session.close)


@router.get("/assets/by-program/")
async def get_asset_by_program(
    alias: str = Query(..., description="Database alias (e.g., 'razuna')"),
    program_name: str = Query(..., description="Program name to search for")
):
    """
    Fetch asset IDs based on a given program name.
    
    Args:
        alias: Database configuration alias from settings
        program_name: Program name to search for associated assets
    
    Returns:
        List of assets matching the program name
    """
    try:
        SessionLocal = get_sessionmaker_by_alias(alias)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    session = SessionLocal()

    try:
        assets = await run_in_threadpool(
            run_asset_query_by_program, 
            session, 
            alias, 
            program_name
        )
        
        if not assets:
            return {
                "status": "success", 
                "data": [], 
                "message": f"No assets found for program: {program_name}"
            }
        
        return {"status": "success", "data": assets}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        await run_in_threadpool(session.close)
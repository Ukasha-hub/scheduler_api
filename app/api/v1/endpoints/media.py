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
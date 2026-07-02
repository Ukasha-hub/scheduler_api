# app/api/v1/endpoints/playlist.py
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, and_
from fastapi import Body

from app.schemas.playlist import PlaylistCreate, PlaylistResponse, PlaylistListResponse
from app.models.playout.playlist import Playlist
from app.db.playout_db_session import get_playout_db

router = APIRouter()


@router.post("/", response_model=PlaylistResponse, status_code=status.HTTP_201_CREATED)
async def create_playlist(
    playlist_in: PlaylistCreate,
    db: Session = Depends(get_playout_db)
):
    """
    Create a new playlist.
    
    - **name**: Required, max 255 characters
    - **createdby**: Required, max 255 characters
    - All other fields are optional
    """
    # Create new playlist
    now = datetime.utcnow()
    db_playlist = Playlist(
        label=playlist_in.label,
        name=playlist_in.name,
        timecode=playlist_in.timecode,
        starttime=playlist_in.starttime,
        seek=playlist_in.seek,
        length=playlist_in.length,
        state=playlist_in.state,
        pushtime=playlist_in.pushtime,
        asset_id=playlist_in.asset_id,
        scheduler_id=playlist_in.scheduler_id,
        createdby=playlist_in.createdby,
        slug_name=playlist_in.slug_name,
        created=now,
        updated=now
    )
    
    db.add(db_playlist)
    db.commit()
    db.refresh(db_playlist)
    
    return db_playlist


@router.get("/", response_model=PlaylistListResponse)
async def get_playlists(
    db: Session = Depends(get_playout_db),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name, label, or slug"),
    state: Optional[str] = Query(None, description="Filter by state"),
    scheduler_id: Optional[int] = Query(None, description="Filter by scheduler ID"),
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)")
):
    """
    Get a paginated list of playlists with optional filters.
    """
    skip = (page - 1) * size
    query = db.query(Playlist)

    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Playlist.name.ilike(search_term),
                Playlist.label.ilike(search_term),
                Playlist.slug_name.ilike(search_term)
            )
        )

    if state:
        query = query.filter(Playlist.state == state)

    if scheduler_id is not None:
        query = query.filter(Playlist.scheduler_id == scheduler_id)

    if date:
        # Filter by date (starttime)
        query = query.filter(Playlist.starttime.startswith(date))

    # Get total count
    total = query.count()

    # Apply pagination and order
    items = query.order_by(desc(Playlist.created)).offset(skip).limit(size).all()

    pages = (total + size - 1) // size if total > 0 else 0

    return PlaylistListResponse(
        total=total,
        items=items,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/{playlist_id}", response_model=PlaylistResponse)
async def get_playlist(
    playlist_id: int,
    db: Session = Depends(get_playout_db)
):
    """
    Get a specific playlist by ID.
    """
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    return playlist


@router.get("/by-slug/{slug_name}", response_model=PlaylistResponse)
async def get_playlist_by_slug(
    slug_name: str,
    db: Session = Depends(get_playout_db)
):
    """
    Get a playlist by its slug name.
    """
    playlist = db.query(Playlist).filter(Playlist.slug_name == slug_name).first()
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    return playlist


@router.put("/{playlist_id}", response_model=PlaylistResponse)
async def update_playlist(
    playlist_id: int,
    playlist_in: PlaylistCreate,
    db: Session = Depends(get_playout_db)
):
    """
    Update an existing playlist.
    """
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    
    # Update fields
    now = datetime.utcnow()
    
    playlist.label = playlist_in.label
    playlist.name = playlist_in.name
    playlist.timecode = playlist_in.timecode
    playlist.starttime = playlist_in.starttime
    playlist.seek = playlist_in.seek
    playlist.length = playlist_in.length
    playlist.state = playlist_in.state
    playlist.pushtime = playlist_in.pushtime
    playlist.asset_id = playlist_in.asset_id
    playlist.scheduler_id = playlist_in.scheduler_id
    playlist.createdby = playlist_in.createdby
    playlist.slug_name = playlist_in.slug_name
    playlist.updated = now
    playlist.updatedby = playlist_in.updatedby
    
    db.commit()
    db.refresh(playlist)
    
    return playlist


@router.delete("/{playlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_playlist(
    playlist_id: int,
    db: Session = Depends(get_playout_db)
):
    """
    Delete a specific playlist by ID.
    """
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    
    db.delete(playlist)
    db.commit()
    
    return None


@router.delete("/by-date/{date}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_playlists_by_date(
    date: str,
    db: Session = Depends(get_playout_db)
):
    """
    Delete all playlists for a specific date (YYYY-MM-DD).
    """
    # Find all playlists with starttime starting with the given date
    playlists = db.query(Playlist).filter(Playlist.starttime.startswith(date)).all()
    
    if not playlists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No playlists found for date: {date}"
        )
    
    deleted_count = len(playlists)
    
    for playlist in playlists:
        db.delete(playlist)
    
    db.commit()
    
    return {
        "message": f"Successfully deleted {deleted_count} playlist(s) for date: {date}",
        "deleted_count": deleted_count
    }


@router.delete("/by-date-range/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_playlists_by_date_range(
    from_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    to_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_playout_db)
):
    """
    Delete all playlists within a date range.
    """
    # Find all playlists with starttime within the date range
    playlists = db.query(Playlist).filter(
        Playlist.starttime >= from_date,
        Playlist.starttime <= f"{to_date} 23:59:59"
    ).all()
    
    if not playlists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No playlists found between {from_date} and {to_date}"
        )
    
    deleted_count = len(playlists)
    
    for playlist in playlists:
        db.delete(playlist)
    
    db.commit()
    
    return {
        "message": f"Successfully deleted {deleted_count} playlist(s) between {from_date} and {to_date}",
        "deleted_count": deleted_count
    }


@router.delete("/by-scheduler/{scheduler_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_playlists_by_scheduler_id(
    scheduler_id: int,
    db: Session = Depends(get_playout_db)
):
    """
    Delete all playlists with a specific scheduler ID.
    """
    playlists = db.query(Playlist).filter(Playlist.scheduler_id == scheduler_id).all()
    
    if not playlists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No playlists found with scheduler_id: {scheduler_id}"
        )
    
    deleted_count = len(playlists)
    
    for playlist in playlists:
        db.delete(playlist)
    
    db.commit()
    
    return {
        "message": f"Successfully deleted {deleted_count} playlist(s) with scheduler_id: {scheduler_id}",
        "deleted_count": deleted_count
    }


@router.post("/replace/", response_model=dict)
async def replace_playlists_by_date(
    date: str = Query(..., description="Date (YYYY-MM-DD)"),
    rows: List[dict] = Body(..., description="List of playlist rows to insert"),
    db: Session = Depends(get_playout_db)
):
    """
    Replace ALL playlists for a specific date with new rows.
    This deletes all existing playlists for the date and inserts new ones.
    """
    # 1. Delete all existing playlists for the date
    existing_playlists = db.query(Playlist).filter(Playlist.starttime.startswith(date)).all()
    deleted_count = len(existing_playlists)
    
    for playlist in existing_playlists:
        db.delete(playlist)
    
    # 2. Insert new playlists
    now = datetime.utcnow()
    inserted_count = 0
    
    # rows is already a list directly
    for row in rows:
        db_playlist = Playlist(
            label=row.get('label', ''),
            name=row.get('name', ''),
            timecode=row.get('timecode', '00:00:00:00'),
            starttime=row.get('starttime', date),
            seek=row.get('seek', ''),
            length=row.get('length', ''),
            state=row.get('state', 'active'),
            pushtime=row.get('pushtime', now),
            asset_id=row.get('asset_id'),
            scheduler_id=row.get('scheduler_id'),
            createdby=row.get('createdby', 'system'),
            slug_name=row.get('slug_name', f'playlist_{date}_{datetime.now().timestamp()}'),
            created=row.get('created', now),
            updated=now,
            updatedby=row.get('updatedby', 'system')
        )
        db.add(db_playlist)
        inserted_count += 1
    
    db.commit()
    
    return {
        "message": f"Successfully replaced playlists for {date}",
        "deleted_count": deleted_count,
        "inserted_count": inserted_count,
        "date": date
    }

# app/api/v1/endpoints/playlist.py - Add this new endpoint

@router.post("/create-for-server/", response_model=dict)
async def create_playlist_for_server(
    date: str = Query(..., description="Date (YYYY-MM-DD)"),
    server: str = Query(..., description="Server name (primary, secondary, third, fourth)"),
    rows: List[dict] = Body(..., description="List of playlist rows to insert"),
    db: Session = Depends(get_playout_db)
):
    """
    Create playlist for a specific server.
    """
    # Get the database URL for the specified server
    from app.core.config import settings
    
    server_db_url = settings.SERVER_DB_CONFIGS.get(server)
    if not server_db_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid server name: {server}. Must be one of: primary, secondary, third, fourth"
        )
    
    # Create a new database session for the server
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(server_db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    server_db = SessionLocal()
    
    try:
        # 1. Delete all existing playlists for the date on this server
        existing_playlists = server_db.query(Playlist).filter(Playlist.starttime.startswith(date)).all()
        deleted_count = len(existing_playlists)
        
        for playlist in existing_playlists:
            server_db.delete(playlist)
        
        # 2. Insert new playlists
        now = datetime.utcnow()
        inserted_count = 0
        
        for row in rows:
            db_playlist = Playlist(
                label=row.get('label', ''),
                name=row.get('name', ''),
                timecode=row.get('timecode', '00:00:00:00'),
                starttime=row.get('starttime', date),
                seek=row.get('seek', ''),
                length=row.get('length', ''),
                state=row.get('state', 'active'),
                pushtime=row.get('pushtime', now),
                asset_id=row.get('asset_id'),
                scheduler_id=row.get('scheduler_id'),
                createdby=row.get('createdby', 'system'),
                slug_name=row.get('slug_name', f'playlist_{date}_{server}_{datetime.now().timestamp()}'),
                created=row.get('created', now),
                updated=now,
                updatedby=row.get('updatedby', 'system')
            )
            server_db.add(db_playlist)
            inserted_count += 1
        
        server_db.commit()
        
        return {
            "message": f"Successfully created playlist for {server} server on {date}",
            "server": server,
            "deleted_count": deleted_count,
            "inserted_count": inserted_count,
            "date": date
        }
    
    except Exception as e:
        server_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create playlist for server {server}: {str(e)}"
        )
    finally:
        server_db.close()


# app/api/v1/endpoints/playlist.py - Updated create_for_servers endpoint

# app/api/v1/endpoints/playlist.py - Updated create_for_servers endpoint

@router.post("/create-for-servers/", response_model=dict)
async def create_playlist_for_multiple_servers(
    date: str = Query(..., description="Date (YYYY-MM-DD)"),
    servers: List[str] = Body(..., description="List of server names to create playlists for"),
    rows: List[dict] = Body(..., description="List of playlist rows to insert"),
    db: Session = Depends(get_playout_db)
):
    """
    Create playlists for multiple servers simultaneously.
    If a server fails, it skips and continues with the next server.
    """
    from app.core.config import settings
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.exc import SQLAlchemyError, OperationalError
    import logging
    
    logger = logging.getLogger(__name__)
    
    results = {}
    total_deleted = 0
    total_inserted = 0
    skipped_servers = []
    
    for server in servers:
        server_db_url = settings.SERVER_DB_CONFIGS.get(server)
        
        # Check if server configuration exists
        if not server_db_url:
            results[server] = {
                "status": "skipped",
                "message": f"Server configuration not found for: {server}"
            }
            skipped_servers.append(server)
            continue
        
        try:
            logger.info(f"Connecting to {server} server at {server_db_url}")
            
            # Create engine with SHORT connection timeout (2 seconds)
            engine = create_engine(
                server_db_url,
                connect_args={
                    "connect_timeout": 2,  # Reduced from 10 to 2 seconds
                    "keepalives": 1,
                    "keepalives_idle": 10,  # Reduced from 30
                    "keepalives_interval": 5,  # Reduced from 10
                    "keepalives_count": 3  # Reduced from 5
                },
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            # Create a session
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            server_db = SessionLocal()
            
            # Also set a query timeout
            try:
                # Test connection with timeout
                server_db.execute(text("SET statement_timeout = '3000'"))  # 3 second query timeout
                result = server_db.execute(text("SELECT 1"))
                result.fetchone()
                logger.info(f"Successfully connected to {server} server")
            except Exception as conn_err:
                server_db.close()
                engine.dispose()
                results[server] = {
                    "status": "skipped",
                    "message": f"Server not available: {str(conn_err)}"
                }
                skipped_servers.append(server)
                continue
            
            try:
                # Delete existing playlists
                with engine.connect() as conn:
                    # Set query timeout for this connection
                    conn.execute(text("SET statement_timeout = '5000'"))  # 5 second timeout
                    delete_result = conn.execute(
                        text("DELETE FROM playlist WHERE starttime LIKE :date_pattern"),
                        {"date_pattern": f"{date}%"}
                    )
                    deleted_count = delete_result.rowcount
                    conn.commit()
                
                # Insert new playlists
                inserted_count = 0
                now = datetime.utcnow()
                
                with engine.connect() as conn:
                    # Set query timeout for this connection
                    conn.execute(text("SET statement_timeout = '5000'"))
                    
                    for row in rows:
                        try:
                            insert_sql = text("""
                                INSERT INTO playlist (
                                    label, name, timecode, starttime, seek, length, 
                                    state, pushtime, asset_id, scheduler_id, 
                                    createdby, slug_name, created, updated, updatedby
                                ) VALUES (
                                    :label, :name, :timecode, :starttime, :seek, :length,
                                    :state, :pushtime, :asset_id, :scheduler_id,
                                    :createdby, :slug_name, :created, :updated, :updatedby
                                )
                            """)
                            
                            conn.execute(insert_sql, {
                                'label': row.get('label', ''),
                                'name': row.get('name', ''),
                                'timecode': row.get('timecode', '00:00:00:00'),
                                'starttime': row.get('starttime', date),
                                'seek': row.get('seek', ''),
                                'length': row.get('length', ''),
                                'state': row.get('state', 'active'),
                                'pushtime': row.get('pushtime', now),
                                'asset_id': row.get('asset_id'),
                                'scheduler_id': row.get('scheduler_id'),
                                'createdby': row.get('createdby', 'system'),
                                'slug_name': row.get('slug_name', f'playlist_{date}_{server}_{datetime.now().timestamp()}'),
                                'created': row.get('created', now),
                                'updated': now,
                                'updatedby': row.get('updatedby', 'system')
                            })
                            inserted_count += 1
                        except Exception as row_err:
                            logger.error(f"Error inserting row for {server}: {row_err}")
                            continue
                    
                    conn.commit()
                
                server_db.close()
                engine.dispose()
                
                results[server] = {
                    "status": "success",
                    "deleted_count": deleted_count,
                    "inserted_count": inserted_count
                }
                
                total_deleted += deleted_count
                total_inserted += inserted_count
                
                logger.info(f"Successfully processed {server} server: {inserted_count} rows inserted, {deleted_count} deleted")
                
            except Exception as db_err:
                server_db.close()
                engine.dispose()
                logger.error(f"Database error on {server}: {str(db_err)}")
                results[server] = {
                    "status": "skipped",
                    "message": f"Database operation failed: {str(db_err)}"
                }
                skipped_servers.append(server)
                continue
                
        except OperationalError as e:
            logger.error(f"Connection error for {server}: {str(e)}")
            results[server] = {
                "status": "skipped",
                "message": f"Database connection failed: {str(e)}"
            }
            skipped_servers.append(server)
            continue
            
        except SQLAlchemyError as e:
            logger.error(f"SQL error for {server}: {str(e)}")
            results[server] = {
                "status": "skipped",
                "message": f"Database error: {str(e)}"
            }
            skipped_servers.append(server)
            continue
            
        except Exception as e:
            logger.error(f"Unexpected error for {server}: {str(e)}")
            results[server] = {
                "status": "skipped",
                "message": f"Unexpected error: {str(e)}"
            }
            skipped_servers.append(server)
            continue
    
    # Prepare response message
    success_count = sum(1 for r in results.values() if r.get('status') == 'success')
    skipped_count = sum(1 for r in results.values() if r.get('status') == 'skipped')
    
    if skipped_count > 0:
        message = f"Playlist creation completed. {success_count} server(s) succeeded, {skipped_count} server(s) skipped."
    else:
        message = f"Playlist creation completed successfully on all {success_count} server(s)."
    
    return {
        "message": message,
        "date": date,
        "total_deleted": total_deleted,
        "total_inserted": total_inserted,
        "success_count": success_count,
        "skipped_count": skipped_count,
        "servers": results,
        "skipped_servers": skipped_servers
    }
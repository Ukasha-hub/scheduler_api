from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Archive Database Engine
archive_engine = create_engine(
    settings.ARCHIVE_DB_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600
)

# Archive Database Session Local
ArchiveSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=archive_engine
)

def get_archive_db():
    """
    Dependency to get archive database session.
    Usage: db: Session = Depends(get_archive_db)
    """
    db = ArchiveSessionLocal()
    try:
        yield db
    finally:
        db.close()


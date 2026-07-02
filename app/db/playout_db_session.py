from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

playout_engine = create_engine(
    settings.PLAYOUT_DB_URL,
    pool_pre_ping=True
)

PlayoutSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=playout_engine
)

def get_playout_db():
    db = PlayoutSessionLocal()
    try:
        yield db
    finally:
        db.close()
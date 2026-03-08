from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

razuna_engine = create_engine(settings.RAZUNA_DATABASE_URL)

RazunaSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=razuna_engine
)

def get_razuna_db():
    db = RazunaSessionLocal()
    try:
        yield db
    finally:
        db.close()

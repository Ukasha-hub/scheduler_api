from app.db.base import Base
from app.db.playout_db_session import playout_engine
from app.models.playout.playlist import Playlist
from app.models.playout.asrunlog import AsRunLog


Base.metadata.create_all(bind=playout_engine)
print("Tables in playout created successfully!")
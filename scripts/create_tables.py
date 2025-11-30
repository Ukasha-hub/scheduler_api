# Purpose: Create all tables in the database
from app.db.base import Base
from app.db.session import engine
from app.models.filter import Filter  # Import all models you want to create

# This will create the table(s) in PostgreSQL
Base.metadata.create_all(bind=engine)
print("Tables created successfully!")
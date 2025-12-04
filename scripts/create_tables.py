# Purpose: Create all tables in the database
from app.db.base import Base
from app.db.session import engine
from app.models.filter import Filter 
from app.models.user import User
from app.models.privilege import Privilege 
from app.models.server import Server
from app.models.slug import Slug
from app.models.hourly_ad import HourlyAdSetting 
from app.models.package import Package  # Import all models you want to create

# This will create the table(s) in PostgreSQL
Base.metadata.create_all(bind=engine)
print("Tables created successfully!")
import os
from pydantic_settings import BaseSettings
from typing import List, Dict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:password@172.16.9.132:5432/scheduler"

    PLAYOUT_DB_URL: str = (
        "postgresql+psycopg2://postgres:password@172.16.9.132:5432/playout"
    )

    # Archive Database Configuration
    ARCHIVE_DB_URL: str = (
        "postgresql+psycopg2://archive:archive@172.31.10.52:5432/archive"
    )

    # Server-specific database configurations
    SERVER_DB_CONFIGS: Dict[str, str] = {
        "primary": "postgresql+psycopg2://postgres:password@172.16.9.132:5432/playout",
        "secondary": "",
        "third": "",
        "fourth": "",
    }

    DB_CONFIGS: List[Dict] = [
        {
            "alias": "razuna",
            "driver": "mysql+pymysql",
            "host": "172.31.10.55",
            "port": 3306,
            "user": "root",
            "password": "password",
            "database": "razuna"
        },
        {
            "alias": "archive",
            "driver": "postgresql+psycopg2",
            "host": "172.31.10.53",
            "port": 5432,
            "user": "archive",
            "password": "archive",
            "database": "archive"
        }
    ]

settings = Settings()
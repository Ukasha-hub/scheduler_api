import os
from pydantic_settings import BaseSettings
from typing import List, Dict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/scheduler"

    DB_CONFIGS: List[Dict] = [
        {
            "alias": "razuna",
            "driver": "mysql+pymysql",
            "host": "172.31.10.55",
            "port": 3306,
            "user": "root",
            "password": "password",
            "database": "razuna"
        }
    ]

settings = Settings()
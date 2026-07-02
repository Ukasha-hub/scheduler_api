from pydantic import BaseModel
from typing import List

class BackupRequest(BaseModel):
    ip_list: List[str]
    date_upto: str   # ISO date (YYYY-MM-DD)
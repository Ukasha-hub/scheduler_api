import os
import subprocess
from datetime import datetime
from pathlib import Path
from sqlalchemy.engine.url import make_url

from app.core.config import settings

url = make_url(settings.PLAYOUT_DB_URL)

backup_dir = Path("backups")
backup_dir.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_file = backup_dir / f"playout_{timestamp}.dump"

env = os.environ.copy()
env["PGPASSWORD"] = url.password

subprocess.run(
    [
        "pg_dump",
        "-U", url.username,
        "-h", url.host,
        "-p", str(url.port),
        "-Fc",
        "-d", url.database,
        "-f", str(backup_file),
    ],
    env=env,
    check=True,
)

print(f"Backup created: {backup_file}")
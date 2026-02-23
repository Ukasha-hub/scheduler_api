import os
import glob
import hashlib
import subprocess
import requests

from fastapi import APIRouter

router = APIRouter()

PRIVATE_KEY = "691527108155802fad51a2b4dd8f26e943d4b231ff6747101a2603e6780870f4"
USER = "admin"
BASE_URL = "http://172.16.9.132/resourcespace/api/"
FILESTORE_ROOT = "/var/www/172.16.9.132/resourcespace/filestore/"


# ----------------------------------------
# Helper: Get duration using ffprobe
# ----------------------------------------
def get_video_duration(file_path: str):
    if not os.path.exists(file_path):
        return None

    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        return round(float(result.stdout.strip()), 2)

    return None

def seconds_to_timecode(total_seconds: float, fps: int = 25):
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    frames = int((total_seconds - int(total_seconds)) * fps)

    return f"{hours:02}:{minutes:02}:{seconds:02}:{frames:02}"

# ----------------------------------------
# GET all resources
# ----------------------------------------
@router.get("/")
def get_all_resources():

    # 1️⃣ Fetch all resources
    query = f"user={USER}&function=do_search&search="
    sign = hashlib.sha256((PRIVATE_KEY + query).encode()).hexdigest()

    response = requests.get(f"{BASE_URL}?{query}&sign={sign}")
    resources = response.json()

    if not isinstance(resources, list):
        return []

    for res in resources:
        ref = res["ref"]
        extension = res.get("file_extension")

        # 2️⃣ Find real file
        if extension:
            extension = extension.lower()

            pattern = os.path.join(
                FILESTORE_ROOT,
                str(ref),
                "*",
                f"*.{extension}"
            )

            files = glob.glob(pattern)
        else:
            files = []

        res["real_duration_seconds"] = None

        if files:
            file_path = files[0]
            duration = get_video_duration(file_path)

            if duration is not None:
                res["real_duration_seconds"] = duration
                res["real_duration_timecode"] = seconds_to_timecode(duration)

        # 3️⃣ Fetch metadata
        q2 = f"user={USER}&function=get_resource_field_data&resource={ref}"
        s2 = hashlib.sha256((PRIVATE_KEY + q2).encode()).hexdigest()

        meta_response = requests.get(f"{BASE_URL}?{q2}&sign={s2}")
        fields = meta_response.json()

        # Defaults
        res.update({
            "duration": None,
            "framerate": None,
            "videobitrate": None,
            "aspectratio": None,
            "videosize": None,
            "channelmode": None,
        })

        if isinstance(fields, list):
            for f in fields:
                name = f.get("name")
                if name in res:
                    res[name] = f.get("value")

    return resources

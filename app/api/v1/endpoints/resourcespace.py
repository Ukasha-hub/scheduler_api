import hashlib
import subprocess
import requests
from fastapi import APIRouter

router = APIRouter()

PRIVATE_KEY = "691527108155802fad51a2b4dd8f26e943d4b231ff6747101a2603e6780870f4"
USER = "admin"
BASE_URL = "http://172.16.9.132/resourcespace/api/"

VIDEO_EXTENSIONS = ["mp4", "mov", "avi", "mkv", "webm"]


# ----------------------------------------
# Helper: Get duration from URL using ffprobe
# ----------------------------------------
def get_video_duration_from_http(file_url: str):
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_url
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        output = result.stdout.strip()

        if not output or output == "N/A":
            return None

        return round(float(output), 2)

    except Exception:
        return None


# ----------------------------------------
# Convert seconds → HH:MM:SS:FF
# ----------------------------------------
def seconds_to_timecode(total_seconds: float, fps: int = 25):
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    frames = int((total_seconds - int(total_seconds)) * fps)
    return f"{hours:02}:{minutes:02}:{seconds:02}:{frames:02}"


# ----------------------------------------
# GET all resources with durations
# ----------------------------------------
@router.get("/")
def get_all_resources():

    # 1️⃣ Search all resources
    query = f"user={USER}&function=do_search&search="
    sign = hashlib.sha256((PRIVATE_KEY + query).encode()).hexdigest()

    response = requests.get(f"{BASE_URL}?{query}&sign={sign}")
    resources = response.json()

    if not isinstance(resources, list):
        return []

    for res in resources:
        ref = res.get("ref")

        # -----------------------------------
        # 2️⃣ Get resource metadata FIRST
        # -----------------------------------
        q_type = f"user={USER}&function=get_resource_data&resource={ref}"
        s_type = hashlib.sha256((PRIVATE_KEY + q_type).encode()).hexdigest()

        type_response = requests.get(f"{BASE_URL}?{q_type}&sign={s_type}")
        resource_data = type_response.json()

        file_extension = resource_data.get("file_extension")

        # -----------------------------------
        # 3️⃣ Get correct download URL with extension
        # -----------------------------------
        file_url = None

        if file_extension:
            q_url = (
                f"user={USER}"
                f"&function=get_resource_path"
                f"&ref={ref}"
                f"&extension={file_extension}"
            )

            s_url = hashlib.sha256((PRIVATE_KEY + q_url).encode()).hexdigest()

            path_response = requests.get(f"{BASE_URL}?{q_url}&sign={s_url}")
            file_url = path_response.json()

        res["file_url"] = file_url
        res["real_duration_seconds"] = None
        res["real_duration_timecode"] = None

        # -----------------------------------
        # 4️⃣ Extract duration ONLY if video
        # -----------------------------------
        if (
            file_url
            and file_extension
            and file_extension.lower() in VIDEO_EXTENSIONS
        ):
            duration = get_video_duration_from_http(file_url)

            if duration is not None:
                res["real_duration_seconds"] = duration
                res["real_duration_timecode"] = seconds_to_timecode(duration)

        # -----------------------------------
        # 5️⃣ Fetch metadata fields
        # -----------------------------------
        q2 = f"user={USER}&function=get_resource_field_data&resource={ref}"
        s2 = hashlib.sha256((PRIVATE_KEY + q2).encode()).hexdigest()

        meta_response = requests.get(f"{BASE_URL}?{q2}&sign={s2}")
        fields = meta_response.json()

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
import hashlib
import asyncio
import json
import requests
from fastapi import APIRouter, HTTPException

router = APIRouter()

PRIVATE_KEY = "691527108155802fad51a2b4dd8f26e943d4b231ff6747101a2603e6780870f4"
USER = "admin"
BASE_URL = "http://172.16.9.132/resourcespace/api/"

VIDEO_EXTENSIONS = ["mp4", "mov", "avi", "mkv", "webm", "mxf"]


def generate_signature(query: str):
    return hashlib.sha256((PRIVATE_KEY + query).encode()).hexdigest()


async def run_ffprobe_async(file_url: str):
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        file_url
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        return None

    return json.loads(stdout.decode())


def seconds_to_timecode(seconds: float, fps: float):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    frames = int((seconds - int(seconds)) * fps)

    return f"{hours:02}:{minutes:02}:{secs:02}:{frames:02}"


@router.get("/metadata/{ref}")
async def get_resourcespace_metadata(ref: int):
    """
    Heavy API → fetch metadata per resource (like razuna.py)
    """

    # 1️⃣ Get resource data
    q1 = f"user={USER}&function=get_resource_data&resource={ref}"
    s1 = generate_signature(q1)

    res_data = requests.get(f"{BASE_URL}?{q1}&sign={s1}").json()

    if not res_data:
        raise HTTPException(status_code=404, detail="Resource not found")

    file_extension = res_data.get("file_extension")
   

    # 2️⃣ Get file URL
    file_url = None
    if file_extension:
        q2 = (
            f"user={USER}"
            f"&function=get_resource_path"
            f"&ref={ref}"
            f"&extension={file_extension}"
        )
        s2 = generate_signature(q2)

        file_url = requests.get(f"{BASE_URL}?{q2}&sign={s2}").json()

    if not file_url:
        raise HTTPException(status_code=404, detail="File URL not found")

    # 3️⃣ Run ffprobe
    metadata = None
    duration_seconds = None
    fps = 25

    if file_extension and file_extension.lower() in VIDEO_EXTENSIONS:
        metadata = await run_ffprobe_async(file_url)
    
    if metadata:
        format_info = metadata.get("format", {})
        streams = metadata.get("streams", [])

        video_stream = next(
            (s for s in streams if s.get("codec_type") == "video"),
            {}
        )

        duration_seconds = float(format_info.get("duration", 0))
        r_frame_rate = video_stream.get("r_frame_rate", "25/1")
        fps = eval(r_frame_rate)

        timecode = seconds_to_timecode(duration_seconds, fps)

        response = {
            "ref": ref,
            "file_url": file_url,
            "duration_seconds": duration_seconds,
            "timecode": timecode,
            "fps": fps,
            "codec": video_stream.get("codec_name"),
            "width": video_stream.get("width"),
            "height": video_stream.get("height"),
            "bitrate": format_info.get("bit_rate")
        }

    else:
        response = {
            "ref": ref,
            "file_url": file_url,
            "message": "Not a video or metadata unavailable"
        }

    return {
        "status": "success",
        "data": response
    }
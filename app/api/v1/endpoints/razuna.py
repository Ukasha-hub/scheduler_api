# app/api/v1/endpoints/media_metadata.py
import asyncio
import json
from fastapi import APIRouter, HTTPException
from app.core.config import settings

router = APIRouter()

RAZUNA_URL = "http://172.31.10.55:8080/razuna/raz2/dam/index.cfm?fa=c.serve_file&file_id={}&type=vid"

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

def convert_to_timecode(duration_float: float, fps: float) -> str:
    hours = int(duration_float // 3600)
    minutes = int((duration_float % 3600) // 60)
    seconds = int(duration_float % 60)

    # Calculate frames
    fractional = duration_float - int(duration_float)
    frames = int(fractional * fps)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"

@router.get("/metadata/{asset_id}", summary="Fetch async metadata with timecode")
async def get_media_metadata(asset_id: str):
    url = RAZUNA_URL.format(asset_id)
    metadata = await run_ffprobe_async(url)

    if not metadata:
        raise HTTPException(status_code=404, detail="Unable to read media metadata")

    format_info = metadata.get("format", {})
    streams = metadata.get("streams", [])

    video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})

    duration_seconds = float(format_info.get("duration", 0))
    r_frame_rate = video_stream.get("r_frame_rate", "25/1")
    fps = eval(r_frame_rate)  # string "25/1" -> float 25.0

    timecode = convert_to_timecode(duration_seconds, fps)

    response = {
        "asset_id": asset_id,
        "file_url": url,
        "duration_seconds": duration_seconds,
        "timecode": timecode,          # <-- HH:MM:SS:FF
        "fps": fps,
        "codec": video_stream.get("codec_name"),
        "width": video_stream.get("width"),
        "height": video_stream.get("height"),
        "bitrate": format_info.get("bit_rate")
    }

    return {"status": "success", "data": response}
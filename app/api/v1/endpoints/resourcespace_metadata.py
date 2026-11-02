import hashlib
import asyncio
import json
from fractions import Fraction

import httpx

from fastapi import APIRouter, HTTPException

router = APIRouter()

PRIVATE_KEY = "2baf70b3931b509c9bc5c7333d913d7eb1ed7a0b5b5aff72adaec9e373298211"
USER = "admin"
BASE_URL = "http://172.31.10.1/resourcespace/api/"

VIDEO_EXTENSIONS = ["mp4", "mov", "avi", "mkv", "webm", "mxf"]

HTTP_TIMEOUT = 15
FFPROBE_TIMEOUT = 30


def generate_signature(query: str):
    return hashlib.sha256(
        (PRIVATE_KEY + query).encode()
    ).hexdigest()


async def resourcespace_api(client: httpx.AsyncClient, query: str):
    signature = generate_signature(query)

    response = await client.get(
        BASE_URL,
        params={
            **dict(item.split("=", 1) for item in query.split("&")),
            "sign": signature,
        },
    )

    response.raise_for_status()
    return response.json()


async def run_ffprobe_async(file_url: str):
    cmd = [
        "ffprobe",
        "-v", "error",
        "-print_format", "json",
        "-show_entries",
        "format=duration,bit_rate:"
        "stream=codec_type,codec_name,width,height,r_frame_rate",
        "-show_format",
        "-show_streams",
        "-probesize", "5000000",
        "-analyzeduration", "5000000",
        file_url,
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=FFPROBE_TIMEOUT,
        )

    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        return None

    if process.returncode != 0:
        return None

    try:
        return json.loads(stdout.decode())
    except json.JSONDecodeError:
        return None


def seconds_to_timecode(seconds: float, fps: float):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    frames = int((seconds - int(seconds)) * fps)

    return f"{hours:02}:{minutes:02}:{secs:02}:{frames:02}"


@router.get("/metadata/{ref}")
async def get_resourcespace_metadata(ref: int):

    async with httpx.AsyncClient(
        timeout=HTTP_TIMEOUT
    ) as client:

        # 1. Get resource data
        try:
            res_data = await resourcespace_api(
                client,
                f"user={USER}&function=get_resource_data&resource={ref}",
            )
        except (httpx.HTTPError, ValueError):
            raise HTTPException(
                status_code=502,
                detail="ResourceSpace resource-data request failed",
            )

        if not res_data:
            raise HTTPException(
                status_code=404,
                detail="Resource not found",
            )

        file_extension = res_data.get("file_extension")

        if not file_extension:
            raise HTTPException(
                status_code=404,
                detail="File extension not found",
            )

        # 2. Get file URL
        try:
            file_url = await resourcespace_api(
                client,
                f"user={USER}&function=get_resource_path"
                f"&ref={ref}&extension={file_extension}",
            )
        except (httpx.HTTPError, ValueError):
            raise HTTPException(
                status_code=502,
                detail="ResourceSpace file-path request failed",
            )

        if not file_url or not isinstance(file_url, str):
            raise HTTPException(
                status_code=404,
                detail="File URL not found",
            )

    # 3. Run FFprobe only for video extensions
    if file_extension.lower() not in VIDEO_EXTENSIONS:
        return {
            "status": "success",
            "data": {
                "ref": ref,
                "file_url": file_url,
                "message": "Not a video",
            },
        }

    metadata = await run_ffprobe_async(file_url)

    if not metadata:
        raise HTTPException(
            status_code=504,
            detail="FFprobe failed or timed out while analyzing the media",
        )

    format_info = metadata.get("format", {})
    streams = metadata.get("streams", [])

    video_stream = next(
        (
            stream
            for stream in streams
            if stream.get("codec_type") == "video"
        ),
        {},
    )

    duration_seconds = float(format_info.get("duration", 0) or 0)

    rate = video_stream.get("r_frame_rate", "25/1")

    try:
        fps = float(Fraction(rate))
        if fps <= 0:
            fps = 25
    except (ValueError, ZeroDivisionError):
        fps = 25

    return {
        "status": "success",
        "data": {
            "ref": ref,
            "file_url": file_url,
            "duration_seconds": duration_seconds,
            "timecode": seconds_to_timecode(
                duration_seconds,
                fps,
            ),
            "fps": fps,
            "codec": video_stream.get("codec_name"),
            "width": video_stream.get("width"),
            "height": video_stream.get("height"),
            "bitrate": format_info.get("bit_rate"),
        },
    }
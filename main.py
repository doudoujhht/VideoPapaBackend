import uuid
import subprocess
import os
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_DIR = "videos"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

@app.post("/create-video")
async def create_video(image: UploadFile = File(...), audio: UploadFile = File(...)):
    image_ext = image.filename.split(".")[-1]
    audio_ext = audio.filename.split(".")[-1]

    img_path = f"{OUTPUT_DIR}/{uuid.uuid4()}.{image_ext}"
    audio_path = f"{OUTPUT_DIR}/{uuid.uuid4()}.{audio_ext}"
    output_path = f"{OUTPUT_DIR}/{uuid.uuid4()}.mp4"

    # Save files
    with open(img_path, "wb") as f:
        f.write(await image.read())
    with open(audio_path, "wb") as f:
        f.write(await audio.read())

    # FFmpeg command
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", img_path,
        "-i", audio_path,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
        "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        "-movflags", "+faststart",
        output_path
    ]

    subprocess.run(cmd, check=True)

    return {"video_url": f"/download/{os.path.basename(output_path)}"}


@app.get("/download/{filename}")
def download_video(filename: str):
    file_path = f"{OUTPUT_DIR}/{filename}"
    return FileResponse(file_path, media_type="video/mp4", filename="output.mp4")

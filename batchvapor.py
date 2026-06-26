hostrich@gpu-node:/app/vapor# sys: cat batchvapor.py
import sys, os
os.environ["PYTHONNOUSERSITE"]="1"
import os
import uuid
import subprocess
import shutil
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
import uvicorn

app = FastAPI()
JOBS_DIR = "jobs"
os.makedirs(JOBS_DIR, exist_ok=True)

def run_vapoursynth_pipeline(job_id: str, video_path: str, target_path: str, new_path: str):
    job_folder = os.path.join(JOBS_DIR, job_id)
    output_mp4 = os.path.join(job_folder, f"{job_id}.mp4")
    log_file_path = os.path.join(job_folder, "log.txt")

    env = os.environ.copy()
    env["PYTHONPATH"] = "/app/vapor/.venv/lib/python3.12/site-packages"
    env["VIDEO_INPUT"] = video_path
    env["IMAGE_TARGET"] = target_path
    env["IMAGE_NEW"] = new_path

    # Matches the hardware NVENC encoding parameters from your batch controller
    cmd = (
        f'.venv/bin/python engine.vpy | '
        f'ffmpeg -i pipe: -i "{video_path}" -map 0:v -map 1:a? '
        f'-c:v libx264 -preset ultrafast -tune film -c:a copy "{output_mp4}" -y'
    )

    with open(log_file_path, "a") as log_file:
        log_file.write(f"[SYSTEM] Executing VapourSynth pipeline...\n")
        process = subprocess.Popen(cmd, shell=True, env=env, stdout=log_file, stderr=subprocess.STDOUT)
        process.wait()

        if process.returncode == 0:
            log_file.write(f"\n[SYSTEM] Job {job_id} completed successfully.\n")
        else:
            log_file.write(f"\n[SYSTEM] Job {job_id} exited with fatal code {process.returncode}.\n")

@app.post("/submit")
async def submit_job(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    image_target: UploadFile = File(...),
    image_new: UploadFile = File(...)
):
    job_id = str(uuid.uuid4())
    job_folder = os.path.join(JOBS_DIR, job_id)
    os.makedirs(job_folder, exist_ok=True)

    video_path = os.path.join(job_folder, video.filename)
    target_path = os.path.join(job_folder, image_target.filename)
    new_path = os.path.join(job_folder, image_new.filename)

    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(image_target.file, buffer)
    with open(new_path, "wb") as buffer:
        shutil.copyfileobj(image_new.file, buffer)

    log_file_path = os.path.join(job_folder, "log.txt")
    with open(log_file_path, "w") as f:
        f.write("[SYSTEM] Files secured. Task queued.\n")

    background_tasks.add_task(run_vapoursynth_pipeline, job_id, video_path, target_path, new_path)

    return JSONResponse({"job_task_id": job_id, "status": "processing"})

@app.get("/status/{job_id}")
async def check_status(job_id: str):
    log_file_path = os.path.join(JOBS_DIR, job_id, "log.txt")
    if not os.path.exists(log_file_path):
        return JSONResponse({"error": "Job task ID not found"}, status_code=404)

    with open(log_file_path, "r") as f:
        lines = f.readlines()

    return JSONResponse({"job_task_id": job_id, "log_tail": lines[-15:]})

@app.get("/download/{job_id}")
async def download_job(job_id: str):
    output_mp4 = os.path.join(JOBS_DIR, job_id, f"{job_id}.mp4")
    if not os.path.exists(output_mp4):
        return JSONResponse({"error": "Video processing incomplete or task failed"}, status_code=404)

    return FileResponse(output_mp4, media_type="video/mp4", filename=f"{job_id}.mp4")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7384)

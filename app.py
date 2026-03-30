from flask import Flask, request, jsonify, send_from_directory
import os
import uuid
import mimetypes
import cv2
import pandas as pd
import shutil
import logging
import subprocess
from threading import Thread
from pipeline import download_youtube_video, analyze_animal_behavior

tasks = {}

def _set_task(task_id, data):
    tasks[task_id] = {**tasks.get(task_id, {}), **data}

def check_ffmpeg_installed():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False

def download_and_analyze(url, outdir, task_id):
    try:
        if not check_ffmpeg_installed():
            raise RuntimeError("FFmpeg is not installed. Please install ffmpeg to process YouTube videos.")

        _set_task(task_id, {"status": "downloading"})
        video_path = download_youtube_video(url, output_path=outdir)
        _set_task(task_id, {"status": "analyzing"})
        behavior_log, csvpath = analyze_animal_behavior(video_path, outdir=outdir)

        annotated = os.path.join(outdir, "annotated_video.mp4")
        log = behavior_log or []

        annotated_url = f"/static/{task_id}/annotated_video.mp4" if os.path.exists(annotated) else None
        csv_url = f"/static/{task_id}/animal_behavior_log.csv" if os.path.exists(csvpath) else None

        _set_task(task_id, {
            "status": "done",
            "annotatedVideoUrl": annotated_url,
            "csvUrl": csv_url,
            "log": log,
            "summary": {"count": len(log)}
        })
    except Exception as e:
        _set_task(task_id, {"status": "error", "error": str(e)})

app = Flask(__name__, static_folder="static")
os.makedirs("static", exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', filename='server.log', filemode='a')
logger = logging.getLogger('animal-behaviour')

@app.route("/api/process-youtube", methods=["POST"])
def process_youtube():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return "Missing url", 400
    task_id = str(uuid.uuid4())
    outdir = os.path.join("static", task_id)
    os.makedirs(outdir, exist_ok=True)

    _set_task(task_id, {"status": "queued"})
    t = Thread(target=download_and_analyze, args=(url, outdir, task_id), daemon=True)
    t.start()
    return jsonify({"task_id": task_id, "status": "queued"})

@app.route("/api/process-file", methods=["POST"])
def process_file():
    if 'file' not in request.files:
        return "No file", 400
    f = request.files['file']
    task_id = str(uuid.uuid4())
    outdir = os.path.join("static", task_id)
    os.makedirs(outdir, exist_ok=True)

    _, ext = os.path.splitext(f.filename)
    if not ext:
        ext = '.mp4'
    filepath = os.path.join(outdir, f"input{ext}")
    f.save(filepath)

    mime, _ = mimetypes.guess_type(filepath)
    _set_task(task_id, {"status": "queued"})

    def analyze_file(path, outdir, task_id, is_image=False):
        try:
            if is_image:
                img = cv2.imread(path)
                if img is None:
                    raise RuntimeError("Failed to read image")
                annotated_path = os.path.join(outdir, "annotated_image.jpg")
                cv2.putText(img, "Annotated Image", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
                cv2.imwrite(annotated_path, img)
                log = [{"frame": 1, "label": "unknown", "behavior": "unknown", "speed": 0.0, "confidence": 0.0, "abnormal": ""}]
                pd.DataFrame(log).to_csv(os.path.join(outdir, "animal_behavior_log.csv"), index=False)
                _set_task(task_id, {
                    "status": "done",
                    "annotatedImageUrl": f"/static/{task_id}/annotated_image.jpg",
                    "csvUrl": f"/static/{task_id}/animal_behavior_log.csv",
                    "log": log,
                    "summary": {"count": 1}
                })
                return

            behavior_log, csvpath = analyze_animal_behavior(path, outdir=outdir)
            annotated = os.path.join(outdir, "annotated_video.mp4")
            log = behavior_log or []

            _set_task(task_id, {
                "status": "done",
                "annotatedVideoUrl": f"/static/{task_id}/annotated_video.mp4" if os.path.exists(annotated) else None,
                "csvUrl": f"/static/{task_id}/animal_behavior_log.csv" if os.path.exists(csvpath) else None,
                "log": log,
                "summary": {"count": len(log)}
            })
        except Exception as e:
            _set_task(task_id, {"status": "error", "error": str(e)})

    is_image = mime and mime.startswith("image")
    t = Thread(target=analyze_file, args=(filepath, outdir, task_id, is_image), daemon=True)
    t.start()
    return jsonify({"task_id": task_id, "status": "queued"})

@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory("static", filename)

@app.route("/api/task-status/<task_id>")
def task_status(task_id):
    return jsonify(tasks.get(task_id, {"status": "unknown"}))


@app.route('/api/download-csv/<task_id>')
def download_csv(task_id):
    """Serve the CSV file for a given task as an attachment.

    Looks under static/<task_id>/animal_behavior_log.csv and returns it
    with a Content-Disposition header so browsers download it.
    """
    task = tasks.get(task_id)
    if not task:
        return jsonify({"status": "not_found"}), 404

    csv_path = os.path.abspath(os.path.join('static', task_id, 'animal_behavior_log.csv'))
    if not os.path.exists(csv_path):
        return jsonify({"status": "not_found"}), 404

    directory = os.path.dirname(csv_path)
    filename = os.path.basename(csv_path)
    # Flask >=2.0 supports download_name; as_attachment ensures Content-Disposition
    return send_from_directory(directory, filename, as_attachment=True, download_name=f"animal_behavior_log_{task_id}.csv")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860, debug=True)

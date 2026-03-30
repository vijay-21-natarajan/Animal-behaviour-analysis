import os
import cv2
import csv
import yt_dlp
from ultralytics import YOLO

# Paths
DOWNLOADS_DIR = "downloads"
STATIC_DIR = "static"
OUTPUTS_DIR = "outputs"

os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

# Load YOLO model (you can replace 'yolov8n.pt' with your custom model if needed)
model = YOLO("yolov8n.pt")

print("Available classes:", model.names)  # Shows what classes the model can detect

# Ask for YouTube link
url = input("Enter YouTube video URL: ")

# Download video
ydl_opts = {
    'outtmpl': os.path.join(DOWNLOADS_DIR, '%(id)s.%(ext)s'),
    'format': 'best[ext=mp4]/best'
}
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(url, download=True)
    video_id = info.get("id", None)
    video_path = os.path.join(DOWNLOADS_DIR, f"{video_id}.mp4")

print(f"Video downloaded: {video_path}")

# Open video
cap = cv2.VideoCapture(video_path)

# Video writer for annotated output
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out_path = os.path.join(STATIC_DIR, f"{video_id}_annotated.mp4")
out = None

# CSV output
csv_path = os.path.join(OUTPUTS_DIR, f"{video_id}_detections.csv")
csv_file = open(csv_path, mode='w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["Frame", "Class", "Confidence", "X1", "Y1", "X2", "Y2"])

frame_count = 0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    frame_count += 1

    # Run detection with lower confidence threshold
    results = model(frame, conf=0.15)

    # Initialize video writer once we know frame size
    if out is None:
        height, width = frame.shape[:2]
        out = cv2.VideoWriter(out_path, fourcc, 20.0, (width, height))

    # Process results
    for r in results:
        boxes = r.boxes
        for box in boxes:
            cls_id = int(box.cls[0])
            cls_name = model.names[cls_id]
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # Write to CSV
            csv_writer.writerow([frame_count, cls_name, conf, x1, y1, x2, y2])

            # Draw on frame
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"{cls_name} {conf:.2f}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    out.write(frame)

cap.release()
out.release()
csv_file.close()

print(f"\n✅ Annotated video saved at: {out_path}")
print(f"✅ Detections CSV saved at: {csv_path}")

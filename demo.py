from pytube import YouTube
import os
import cv2
from ultralytics import YOLO
import pandas as pd
from collections import Counter, defaultdict,deque
import yt_dlp
import math

# ========== STEP 1: Download YouTube Video ==========
def download_youtube_video(url, output_path="downloads"):
    os.makedirs(output_path, exist_ok=True)
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]',
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',
        'noplaylist': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_path = ydl.prepare_filename(info)
        print(f"Video downloaded: {video_path}")
        return video_path

# ========== STEP 2: Behavior Analysis ==========

def analyze_animal_behavior(video_path):
    model = YOLO("yolov8n.pt")
    cap = cv2.VideoCapture(video_path)
    behavior_log = []
    frame_count = 0

    last_positions = defaultdict(lambda: None)
    # Queues to hold last 20 speeds and behaviors for smoothing
    speed_window = defaultdict(lambda: deque(maxlen=20))
    behavior_window = defaultdict(lambda: deque(maxlen=20))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1
        results = model(frame)[0]

        for box in results.boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            conf = float(box.conf[0])

            if label in ["dog", "cat", "cow", "horse", "sheep", "elephant", "zebra", "giraffe", "bird"]:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                last_pos = last_positions[label]
                speed = 0
                if last_pos:
                    dx = cx - last_pos[0]
                    dy = cy - last_pos[1]
                    speed = math.sqrt(dx**2 + dy**2)
                last_positions[label] = (cx, cy)

                speed_window[label].append(speed)

                # Calculate average speed over last 20 frames
                avg_speed = sum(speed_window[label]) / len(speed_window[label])

                # Classify behavior based on averaged speed
                if avg_speed < 2:
                    behavior = "resting"
                elif avg_speed < 10:
                    behavior = "walking"
                else:
                    behavior = "running"

                behavior_window[label].append(behavior)

                # Majority vote for behavior in last 20 frames
                behavior_counts = Counter(behavior_window[label])
                smoothed_behavior = behavior_counts.most_common(1)[0][0]

                # Detect abnormalities based on smoothed behavior
                abnormal = ""
                if smoothed_behavior == "resting" and frame_count > 50:
                    abnormal = "possible illness"
                elif smoothed_behavior == "running" and avg_speed > 20:
                    abnormal = "possible stress/fear"

                # Draw detection and smoothed behavior label
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{label} {smoothed_behavior} {conf:.2f}",
                            (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.6, (0, 255, 0), 2)

                behavior_log.append({
                    "frame": frame_count,
                    "label": label,
                    "center": (cx, cy),
                    "confidence": conf,
                    "speed": round(avg_speed, 2),
                    "behavior": smoothed_behavior,
                    "abnormal": abnormal
                })

        cv2.imshow("Animal Behavior Analysis", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

    df = pd.DataFrame(behavior_log)
    df.to_csv("animal_behavior_log.csv", index=False)
    print("Saved log to animal_behavior_log.csv")

    counts = Counter([entry["behavior"] for entry in behavior_log])
    print("\nBehavior Summary:")
    for k, v in counts.items():
        print(f" {k}: {v} frames")

    abnormal_counts = Counter([entry["abnormal"] for entry in behavior_log if entry["abnormal"]])
    if abnormal_counts:
        print("\n⚠️ Abnormal Behaviors Detected:")
        for k, v in abnormal_counts.items():
            print(f" {k}: {v} frames")
    else:
        print("\nNo abnormal behaviors detected.")

# ========== MAIN ==========
if __name__ == "__main__":
    youtube_url = input("Enter YouTube video URL: ")
    path = download_youtube_video(youtube_url)
    analyze_animal_behavior(path)

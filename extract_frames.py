import cv2, os, json
from tqdm import tqdm

# Load generated label mapping
with open("video_labels.json") as f:
    VIDEO_LABELS = json.load(f)

def extract_frames(video_path, label, step=30):
    cap = cv2.VideoCapture(video_path)
    count = 0
    label_dir = os.path.join("dataset", label)
    os.makedirs(label_dir, exist_ok=True)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if count % step == 0:
            name = os.path.splitext(os.path.basename(video_path))[0]
            out_path = os.path.join(label_dir, f"{name}_frame_{count}.jpg")
            cv2.imwrite(out_path, frame)
        count += 1
    cap.release()

for file, label in tqdm(VIDEO_LABELS.items()):
    path = os.path.join("videos", file)
    if os.path.exists(path):
        extract_frames(path, label)
    else:
        print(f"Missing video: {file}")

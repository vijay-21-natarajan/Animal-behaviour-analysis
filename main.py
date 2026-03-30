import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import cv2
# Optional for YouTube downloading:
from pytube import YouTube

# 1. Load Excel data
excel_path = r"C:\Users\Lenovo\Downloads\animal-behaviour\data\AR_metadata.xlsx"
excel = pd.ExcelFile(excel_path)

df_action = excel.parse("Action")
df_animal = excel.parse("Animal")
df_video = excel.parse("video_url")

print("Sheets loaded successfully.")

# 2. Save CSV for action data
os.makedirs("output", exist_ok=True)
df_action.to_csv("output/actions.csv", index=False)
df_video.to_csv("output/video_urls.csv", index=False)
print("Saved CSVs in output/")

# 3. Visualize Action Category Distribution
plt.figure(figsize=(12, 6))
sns.countplot(data=df_action, y='Category', order=df_action['Category'].value_counts().index, palette='viridis')
plt.title("Distribution of Animal Action Categories")
plt.xlabel("Count")
plt.ylabel("Category")
plt.tight_layout()
plt.savefig("output/action_category_distribution.png")
plt.show()

# 4. Download video from YouTube (Optional)
def download_video(youtube_url, output_path="videos/"):
    os.makedirs(output_path, exist_ok=True)
    yt = YouTube(youtube_url)
    stream = yt.streams.filter(file_extension="mp4", progressive=True).order_by('resolution').desc().first()
    stream.download(output_path=output_path)
    print(f"Downloaded: {yt.title}")

# Example usage:
# download_video("https://www.youtube.com/watch?v=_9G1PND0vWA")

# 5. Extract frames from video
def extract_frames(video_path, output_folder, step=30):
    cap = cv2.VideoCapture(video_path)
    count = 0
    saved = 0
    os.makedirs(output_folder, exist_ok=True)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if count % step == 0:
            frame_path = os.path.join(output_folder, f"frame_{saved:04d}.jpg")
            cv2.imwrite(frame_path, frame)
            saved += 1
        count += 1

    cap.release()
    print(f"Extracted {saved} frames to {output_folder}")

# Example usage (once you download or have a local video):
# extract_frames("videos/sample.mp4", "frames/sample")

# 6. Show video list
print("\n--- Sample Video URLs ---")
print(df_video.head())

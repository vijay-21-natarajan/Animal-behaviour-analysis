from pytube import YouTube
import pandas as pd
import os
import requests

# Load Excel
excel = pd.ExcelFile("data/AR_metadata.xlsx")  # Update path if needed
df = excel.parse("video_url")
df.columns = df.columns.str.lower().str.strip()

# Create output folder
os.makedirs("videos", exist_ok=True)

for i, row in df.iterrows():
    video_id = str(row["video_id"]).strip()
    url = str(row["url"]).strip()
    filename = f"{video_id}.mp4"
    filepath = os.path.join("videos", filename)

    if os.path.exists(filepath):
        print(f"✅ Already exists: {filename}")
        continue

    # Reconstruct full YouTube URL if only ID is given
    if len(url) < 15 or "youtube" not in url:
        url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        if "youtube.com" in url or "youtu.be" in url:
            yt = YouTube(url)
            stream = yt.streams.filter(progressive=True, file_extension='mp4').first()
            if stream:
                stream.download(output_path="videos", filename=filename)
                print(f"📥 Downloaded YouTube: {filename}")
            else:
                print(f"⚠️ No suitable stream found for: {filename}")
        elif url.endswith(".mp4"):
            r = requests.get(url, stream=True)
            with open(filepath, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"📥 Downloaded MP4: {filename}")
        else:
            print(f"⚠️ Unsupported URL format: {url}")
    except Exception as e:
        print(f"❌ Failed to download {filename}: {e}")

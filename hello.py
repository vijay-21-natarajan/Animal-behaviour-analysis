from pipeline import download_youtube_video

url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
video_path = download_youtube_video(url, output_path="static/test")
print("Downloaded video at:", video_path)

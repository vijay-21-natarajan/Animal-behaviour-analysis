from pytube import YouTube

url = "https://www.youtube.com/watch?v=2Vv-BfVoq4g"  # Ed Sheeran - Perfect (public test video)
yt = YouTube(url)
yt.streams.get_highest_resolution().download(output_path="videos", filename="test_video.mp4")
print("Downloaded test_video.mp4")

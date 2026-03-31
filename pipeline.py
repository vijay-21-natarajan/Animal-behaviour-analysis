from pytube import YouTube
from collections import deque
import os
import cv2
import shutil
from ultralytics import YOLO
import pandas as pd
from collections import Counter, defaultdict
import yt_dlp
import math

# ========== STEP 1: Download YouTube Video ==========
def download_youtube_video(url, output_path="downloads"):
    os.makedirs(output_path, exist_ok=True)

    # Detect ffmpeg
    ffmpeg_available = shutil.which("ffmpeg") is not None
    is_windows = os.name == "nt"

    # On Windows without ffmpeg, avoid merge formats
    if ffmpeg_available and not is_windows:
        format_attempts = [
            'bestvideo[ext=mp4]+bestaudio/best',
            'bestvideo+bestaudio/best',
            'best'
        ]
    else:
        format_attempts = [
            'best[ext=mp4]/best',  # single-file mp4 if possible
            'best'                 # fallback to any single file
        ]

    info = None
    vid = None
    last_exception = None

    for fmt in format_attempts:
        ydl_opts = {
            'format': fmt,
            'outtmpl': os.path.join(output_path, '%(id)s.%(ext)s'),
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'referer': 'https://www.google.com/',
        }
        if ffmpeg_available and not is_windows:
            ydl_opts['merge_output_format'] = 'mp4'
        try:
            print(f"yt-dlp: attempting download with format '{fmt}' for url={url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
            if info:
                vid = info.get('id') or info.get('url')
                break
        except Exception as e:
            print(f"yt-dlp: format '{fmt}' failed: {e}")
            last_exception = e

    if not info:
        raise RuntimeError(f"Failed to download video after trying formats. Last error: {last_exception}")

    # Build final path
    ext = info.get('ext', 'mp4')
    final_path = os.path.join(output_path, f"{vid}.{ext}")
    print(f"Video downloaded: {final_path}")
    return final_path

'''def download_youtube_video(url, output_path="downloads"):
    os.makedirs(output_path, exist_ok=True)
    # Use video id in filename to avoid issues with titles containing special chars
    # Detect whether ffmpeg is available. If it's not installed, avoid requesting
    # yt-dlp to merge separate video+audio streams (which requires ffmpeg).
    ffmpeg_available = shutil.which("ffmpeg") is not None

    # Try a sequence of format choices. When ffmpeg is available we'll attempt
    # video-only + audio merge formats first. Without ffmpeg we prefer single-file
    # formats ("best") to avoid yt-dlp failing with a merge error.
    if ffmpeg_available:
        format_attempts = [
            'bestvideo[ext=mp4]+bestaudio/best',
            'bestvideo+bestaudio/best',
            'best'
        ]
    else:
        format_attempts = [
            # prefer a single-file best format so no merging is required
            'best',
            # try mp4-only single-file next
            'best[ext=mp4]/best'
        ]

    info = None
    vid = None
    last_exception = None
    for fmt in format_attempts:
        # Build options; only request merge_output_format when ffmpeg is available
        ydl_opts = {
            'format': fmt,
            'outtmpl': os.path.join(output_path, '%(id)s.%(ext)s'),
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
        }
        if ffmpeg_available:
            ydl_opts['merge_output_format'] = 'mp4'
        try:
            print(f"yt-dlp: attempting download with format '{fmt}' for url={url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
            if info:
                vid = info.get('id') or info.get('url')
                break
        except Exception as e:
            print(f"yt-dlp: format '{fmt}' failed: {e}")
            last_exception = e
            # try next format

    if info is None:
        # as a last resort, attempt a no-format download with verbose output
        try:
            print("yt-dlp: falling back to default download (no explicit format)")
            ydl_opts = {
                'outtmpl': os.path.join(output_path, '%(id)s.%(ext)s'),
                'noplaylist': True,
                'merge_output_format': 'mp4',
                'quiet': True,
                'no_warnings': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
            if info:
                vid = info.get('id') or info.get('url')
        except Exception as e:
            print(f"yt-dlp: final fallback failed: {e}")
            raise
        # Prepare expected filename using video id
        vid = info.get('id') or info.get('url')
        candidate = os.path.join(output_path, f"{vid}.mp4")

        # Wait for the final file (not .part) to appear. Downloads can take a while,
        # so wait up to 600 seconds (10 minutes) before giving up.
        import glob, time
        final_path = None
        timeout = 600
        waited = 0
        while waited < timeout:
            # look for matching files that are not .part
            matches = [p for p in glob.glob(os.path.join(output_path, f"{vid}.*")) if not p.endswith('.part')]
            if matches:
                # prefer mp4
                mp4s = [p for p in matches if p.lower().endswith('.mp4')]
                final_path = sorted(mp4s if mp4s else matches, key=os.path.getmtime)[-1]
                break
            time.sleep(1)
            waited += 1

        if final_path and os.path.exists(final_path):
            print(f"Video downloaded (final): {final_path}")
            return final_path

        # fallback: return expected candidate (may not exist yet)
        print(f"Video downloaded (fallback, may be incomplete): {candidate}")
        return candidate'''

# ========== STEP 2: Behavior Analysis ==========

'''def analyze_animal_behavior(video_path, outdir="static"):
    cap = cv2.VideoCapture(video_path)

    # Prepare video writer for annotated video
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_video = os.path.join(outdir, "annotated_video.mp4")
    writer = cv2.VideoWriter(out_video, fourcc, 20.0, 
                             (int(cap.get(3)), int(cap.get(4))))

    log = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # ----- run YOLO detection here -----
        # Suppose you get: label, behavior, speed, confidence, abnormal

        result = {
            "frame": int(cap.get(cv2.CAP_PROP_POS_FRAMES)),
            "label": "dog",
            "behavior": "walking",
            "speed": 2.1,
            "confidence": 0.95,
            "abnormal": ""
        }
        log.append(result)

        # ----- draw on frame -----
        cv2.putText(frame, f"{result['label']} {result['behavior']}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

        writer.write(frame)

    cap.release()
    writer.release()

    # Save CSV log
    df = pd.DataFrame(log)
    df.to_csv(os.path.join(outdir, "animal_behavior_log.csv"), index=False)

    return log
'''
'''def analyze_animal_behavior(video_path):
    model = YOLO("yolov8n.pt")  # Small YOLO model
    cap = cv2.VideoCapture(video_path)
    behavior_log = []
    frame_count = 0

    # Track last positions for movement estimation
    last_positions = defaultdict(lambda: None)

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
            # Consider selected animal classes only
            if label in ["dog", "cat", "cow", "horse", "sheep", "elephant", "zebra", "giraffe", "bird"]:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                # Estimate movement speed
                last_pos = last_positions[label]
                speed = 0
                if last_pos:
                    dx = cx - last_pos[0]
                    dy = cy - last_pos[1]
                    speed = math.sqrt(dx**2 + dy**2)

                last_positions[label] = (cx, cy)

                # Classify behavior based on speed
                if speed < 2:
                    behavior = "resting"
                elif speed < 10:
                    behavior = "walking"
                else:
                    behavior = "running"

                # Detect abnormalities (very low OR very high movement)
                abnormal = ""
                # Prolonged resting might indicate illness
                if behavior == "resting" and frame_count > 50:
                    abnormal = "possible illness"
                # Sudden high-speed running might indicate stress/fear
                elif behavior == "running" and speed > 20:
                    abnormal = "possible stress/fear"

                # Draw detections and annotations on frame
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{label} {behavior} {conf:.2f}",
                            (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.6, (0, 255, 0), 2)

                behavior_log.append({
                    "frame": frame_count,
                    "label": label,
                    "center": (cx, cy),
                    "confidence": conf,
                    "speed": round(speed, 2),
                    "behavior": behavior,
                    "abnormal": abnormal
                })

        cv2.imshow("Animal Behavior Analysis", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

    # Save log to CSV
    df = pd.DataFrame(behavior_log)
    df.to_csv("animal_behavior_log.csv", index=False)
    print("Saved log to animal_behavior_log.csv")

    # Print behavior summary
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
        print("\nNo abnormal behaviors detected.")'''
'''def analyze_animal_behavior(video_path, outdir="static"):
    os.makedirs(outdir, exist_ok=True)

    model = YOLO("yolov8n.pt")  # Small YOLO model
    results = model(frame, conf=0.25)
    print(model.names)
    cap = cv2.VideoCapture(video_path)
    behavior_log = []
    frame_count = 0

    # Save annotated video
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_video = os.path.join(outdir, "annotated_video.mp4")
    writer = cv2.VideoWriter(out_video, fourcc, 20.0,
                             (int(cap.get(3)), int(cap.get(4))))

    last_positions = defaultdict(lambda: None)

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

                if speed < 2:
                    behavior = "resting"
                elif speed < 10:
                    behavior = "walking"
                else:
                    behavior = "running"

                abnormal = ""
                if behavior == "resting" and frame_count > 50:
                    abnormal = "possible illness"
                elif behavior == "running" and speed > 20:
                    abnormal = "possible stress/fear"

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{label} {behavior} {conf:.2f}",
                            (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.6, (0, 255, 0), 2)

                behavior_log.append({
                    "frame": frame_count,
                    "label": label,
                    "center": (cx, cy),
                    "confidence": conf,
                    "speed": round(speed, 2),
                    "behavior": behavior,
                    "abnormal": abnormal
                })

        writer.write(frame)
        cv2.imshow("Animal Behavior Analysis", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    writer.release()
    cv2.destroyAllWindows()

    # Save log to CSV
    csv_path = os.path.join(outdir, "animal_behavior_log.csv")
    df = pd.DataFrame(behavior_log)
    df.to_csv(csv_path, index=False)
    print(f"✅ Saved log to {csv_path}")
    print(f"✅ Saved annotated video to {out_video}")

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
        print("\nNo abnormal behaviors detected.")'''

def analyze_animal_behavior(video_path, outdir="static"):
    os.makedirs(outdir, exist_ok=True)

    # Load action categories from CSV
    try:
        actions_df = pd.read_csv("output/merged_animal_actions.csv")
        # Create a mapping from behavior names to categories
        behavior_to_category = {}
        for _, row in actions_df.iterrows():
            if pd.notna(row['Action']):
                behavior_to_category[row['Action'].lower()] = row['Category']
        print("✅ Loaded behavior categories from CSV")
    except FileNotFoundError:
        print("⚠️ actions.csv not found, using default categories")
        behavior_to_category = {}

    # Initialize YOLO model
    try:
        model = YOLO("yolo11n.pt")  # Updated to YOLOv11
        print("✅ YOLO model loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load YOLO model: {e}")
        return []

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Failed to open video: {video_path}")
        return []

    # Get video properties for writer
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"📹 Video properties: {frame_width}x{frame_height}, {fps:.2f} FPS")

    # Save annotated video
    # Use avc1 (H.264) for better web compatibility
    fourcc = cv2.VideoWriter_fourcc(*"avc1")
    out_video = os.path.join(outdir, "annotated_video.mp4")
    writer = cv2.VideoWriter(out_video, fourcc, fps, (frame_width, frame_height))
    
    if not writer.isOpened():
        print("⚠️ Warning: AVC1 codec failed, falling back to mp4v")
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(out_video, fourcc, fps, (frame_width, frame_height))

    behavior_log = []
    frame_count = 0

    # Track last positions for movement estimation
    last_positions = defaultdict(lambda: None)
    behavior_history = defaultdict(lambda: deque(maxlen=30))

    print("🎬 Starting behavior analysis...")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_count += 1
        
        # Process every 5th frame to speed up analysis (optional)
        if frame_count % 5 != 0:
            continue

        try:
            # Run YOLO detection
            results = model(frame, verbose=False)
            
            if len(results) == 0:
                continue
                
            result = results[0]  # Get first result

            if result.boxes is None or len(result.boxes) == 0:
                continue

            for box in result.boxes:
                cls_id = int(box.cls[0])
                label = model.names[cls_id]
                conf = float(box.conf[0])

                # Only process animal classes with good confidence
                if label in ["dog", "cat", "cow", "horse", "sheep", "elephant", "zebra", "giraffe", "bird"] and conf > 0.5:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                    # Calculate movement speed
                    last_pos = last_positions[label]
                    speed = 0
                    if last_pos:
                        dx = cx - last_pos[0]
                        dy = cy - last_pos[1]
                        speed = math.sqrt(dx**2 + dy**2)
                    last_positions[label] = (cx, cy)

                    # Behavior classification based on speed
                    if speed < 2:
                        behavior = "resting"
                    elif speed < 10:
                        behavior = "walking"
                    elif speed < 25:
                        behavior = "running"
                    else:
                        behavior = "running fast"

                    # Adjust behavior for specific animals
                    if label == "bird" and speed > 15:
                        behavior = "flying"
                    elif label in ["dog", "cat"] and speed > 20:
                        behavior = "chasing"

                    # Get category from CSV mapping
                    category = behavior_to_category.get(behavior.lower(), "Movement")

                    # Abnormality detection
                    abnormal = ""
                    behavior_history[label].append(behavior)
                    
                    # Detect prolonged resting
                    if behavior == "resting" and len(behavior_history[label]) > 20:
                        recent_behaviors = list(behavior_history[label])[-20:]
                        if all(b == "resting" for b in recent_behaviors):
                            abnormal = "prolonged resting"
                    
                    # Detect high-speed stress
                    if speed > 30:
                        abnormal = "high speed stress"

                    # Create log entry
                    log_entry = {
                        "frame": frame_count,
                        "label": label,
                        "center_x": cx,
                        "center_y": cy,
                        "confidence": round(conf, 3),
                        "speed": round(speed, 2),
                        "behavior": behavior,
                        "category": category,
                        "abnormal": abnormal,
                        "timestamp": frame_count / fps  # Add timestamp in seconds
                    }
                    behavior_log.append(log_entry)

                    # Draw bounding box and annotation
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # Create annotation text
                    annotation_text = f"{label} {behavior}"
                    if abnormal:
                        annotation_text += f" ⚠{abnormal}"
                    
                    cv2.putText(frame, annotation_text,
                                (x1, max(y1 - 10, 20)), cv2.FONT_HERSHEY_SIMPLEX,
                                0.6, (0, 255, 0), 2)

            # Write frame to output video
            writer.write(frame)

            # Display progress
            if frame_count % 100 == 0:
                print(f"📊 Processed frame {frame_count}, detected {len(behavior_log)} behaviors")

            # Display frame (optional)
            cv2.imshow("Animal Behavior Analysis", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        except Exception as e:
            print(f"⚠️ Error processing frame {frame_count}: {e}")
            continue

    cap.release()
    writer.release()
    cv2.destroyAllWindows()

    print(f"✅ Finished processing {frame_count} frames")

    # Ensure CSV is always written (even if empty) so callers can download it
    csv_path = os.path.join(outdir, "animal_behavior_log.csv")
    columns = [
        "frame",
        "label",
        "center_x",
        "center_y",
        "confidence",
        "speed",
        "behavior",
        "category",
        "abnormal",
        "timestamp",
    ]

    if behavior_log:
        df = pd.DataFrame(behavior_log)
    else:
        # write empty dataframe with headers so clients can download an empty CSV
        df = pd.DataFrame(columns=columns)

    try:
        df.to_csv(csv_path, index=False)
        print(f"✅ Saved behavior log to {csv_path}")
        print(f"📁 Total entries: {len(behavior_log)}")
    except Exception as e:
        print(f"❌ Failed to save CSV to {csv_path}: {e}")

    # Generate summary stats for charts
    stats = {
        "behavior_distribution": [],
        "animal_distribution": [],
        "confidence_distribution": [] # Simplified for now, or use bins
    }

    if behavior_log:
        df = pd.DataFrame(behavior_log)
        
        # Behavior counts
        b_counts = df['behavior'].value_counts().to_dict()
        stats["behavior_distribution"] = [{"name": k, "value": int(v)} for k, v in b_counts.items()]
        
        # Animal counts
        a_counts = df['label'].value_counts().to_dict()
        stats["animal_distribution"] = [{"name": k, "value": int(v)} for k, v in a_counts.items()]
        
        # Confidence bins (0.5 to 1.0)
        bins = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        conf_counts = pd.cut(df['confidence'], bins=bins).value_counts().sort_index()
        stats["confidence_distribution"] = [{"range": f"{bins[i]}-{bins[i+1]}", "count": int(v)} for i, v in enumerate(conf_counts)]

        generate_analysis_summary(behavior_log, frame_count, fps)
    else:
        print("❌ No animal behaviors detected in the video")

    # Return behavior_log, csv path, and stats
    return behavior_log, csv_path, stats


def generate_analysis_summary(behavior_log, total_frames, fps):
    """Generate a detailed summary of the behavior analysis"""
    if not behavior_log:
        print("❌ No data to analyze")
        return
    
    df = pd.DataFrame(behavior_log)
    
    print("\n" + "="*60)
    print("ANIMAL BEHAVIOR ANALYSIS SUMMARY")
    print("="*60)
    
    # Basic statistics
    print(f"\n📊 BASIC STATISTICS:")
    print(f"   Total frames analyzed: {total_frames}")
    print(f"   Total behavior detections: {len(behavior_log)}")
    print(f"   Video duration: {total_frames/fps:.2f} seconds")
    print(f"   Analysis duration: {max(df['timestamp']) if len(df) > 0 else 0:.2f} seconds")
    
    # Animal distribution
    print(f"\n🐾 ANIMAL DISTRIBUTION:")
    animal_counts = df['label'].value_counts()
    for animal, count in animal_counts.items():
        percentage = (count / len(df)) * 100
        print(f"   {animal}: {count} detections ({percentage:.1f}%)")
    
    # Behavior distribution
    print(f"\n🎭 BEHAVIOR DISTRIBUTION:")
    behavior_counts = df['behavior'].value_counts()
    for behavior, count in behavior_counts.head(10).items():  # Top 10 behaviors
        percentage = (count / len(df)) * 100
        print(f"   {behavior}: {count} times ({percentage:.1f}%)")
    
    # Category distribution
    print(f"\n📂 CATEGORY DISTRIBUTION:")
    category_counts = df['category'].value_counts()
    for category, count in category_counts.items():
        percentage = (count / len(df)) * 100
        print(f"   {category}: {count} times ({percentage:.1f}%)")
    
    # Abnormal behaviors
    abnormal_df = df[df['abnormal'] != '']
    if len(abnormal_df) > 0:
        print(f"\n⚠️  ABNORMAL BEHAVIORS DETECTED:")
        abnormal_counts = abnormal_df['abnormal'].value_counts()
        for abnormal, count in abnormal_counts.items():
            percentage = (count / len(df)) * 100
            print(f"   {abnormal}: {count} times ({percentage:.1f}%)")
        
        # Animals with abnormal behaviors
        print(f"\n🐾 ANIMALS WITH ABNORMAL BEHAVIORS:")
        abnormal_animals = abnormal_df['label'].value_counts()
        for animal, count in abnormal_animals.items():
            print(f"   {animal}: {count} abnormal detections")
    else:
        print(f"\n✅ No abnormal behaviors detected")
    
    # Speed analysis
    print(f"\n📈 SPEED ANALYSIS:")
    print(f"   Average speed: {df['speed'].mean():.2f} pixels/frame")
    print(f"   Maximum speed: {df['speed'].max():.2f} pixels/frame")
    print(f"   Minimum speed: {df['speed'].min():.2f} pixels/frame")
    
    # Confidence analysis
    print(f"\n🎯 CONFIDENCE ANALYSIS:")
    print(f"   Average confidence: {df['confidence'].mean():.3f}")
    print(f"   Minimum confidence: {df['confidence'].min():.3f}")

# Update your main function to handle errors better
if __name__ == "__main__":
    try:
        youtube_url = input("Enter YouTube video URL: ")
        print("📥 Downloading video...")
        path = download_youtube_video(youtube_url)
        
        if path and os.path.exists(path):
            print(f"✅ Video downloaded: {path}")
            print("🔬 Starting behavior analysis...")
            analyze_animal_behavior(path)
        else:
            print("❌ Failed to download video or video file not found")
            
    except Exception as e:
        print(f"❌ Error in main execution: {e}")
        import traceback
        traceback.print_exc()
# ========== MAIN ==========
if __name__ == "__main__":
    youtube_url = input("Enter YouTube video URL: ")
    path = download_youtube_video(youtube_url)
    analyze_animal_behavior(path)

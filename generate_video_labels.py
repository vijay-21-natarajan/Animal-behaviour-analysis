import pandas as pd
import random
import json

# Load Excel file
excel = pd.ExcelFile("data/AR_metadata.xlsx")  # or your updated path
df_video = excel.parse("video_url")
df_action = excel.parse("Action")

# Normalize columns
df_video.columns = df_video.columns.str.lower().str.strip()
df_action.columns = df_action.columns.str.lower().str.strip()

# Use 'video_id' as the filename
df_video = df_video.dropna(subset=["video_id"])
available_categories = df_action["category"].dropna().unique().tolist()

# Assign random category for now
random.seed(42)
df_video["category"] = [random.choice(available_categories) for _ in range(len(df_video))]

# Add .mp4 extension
df_video["video_file"] = df_video["video_id"].astype(str) + ".mp4"

# Generate dictionary
video_labels = dict(zip(df_video["video_file"], df_video["category"]))

# Save to JSON
with open("video_labels.json", "w") as f:
    json.dump(video_labels, f, indent=4)

print("✅ VIDEO_LABELS saved to video_labels.json")

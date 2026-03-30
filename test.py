import pandas as pd

excel = pd.ExcelFile("data/AR_metadata.xlsx")  # or your new file path
df_video = excel.parse("video_url")

# Print the actual column names
print(df_video.columns.tolist()) 

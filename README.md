# Animal Behaviour Analysis

A comprehensive tool designed to analyze animal behaviour in videos using YOLOv8 computer vision and a React-based web interface.

## 🌟 Features
- **Video Analysis**: Upload local videos or provide YouTube links for automated animal detection.
- **Behaviour Tracking**: Detects common animals (dogs, cats, cows, horses, etc.) and classifies behaviours like resting, walking, and running based on movement speed. 
- **Abnormality Detection**: Identifies potential health or stress issues (e.g., prolonged resting or high-speed stress).
- **Interactive Web Interface**: Live progress tracking and video preview.
- **Data Export**: Download analysis results in CSV format for further research.

---

## 🏗️ Project Structure
```text
animal-behaviour/
├── app.py                # Flask Backend - API entry point
├── pipeline.py           # Core logic for video processing & analysis
├── requirements.txt      # Python dependencies
├── package.json          # Node.js dependencies & scripts
├── vite.config.js        # Vite configuration with API proxy
├── src/                  # React Frontend Source
│   ├── App.jsx           # Main UI component
│   └── main.jsx          # React entry point
├── static/               # Processed videos and analysis results
├── templates/            # HTML templates (if used)
└── yolov8n.pt            # Pre-trained YOLO model
```

---

## 🛠️ System Requirements
- **Python 3.8+**
- **Node.js & npm**
- **FFmpeg**: Essential for downloading and processing YouTube videos.

---

## 🚀 Getting Started

### 1. Backend Setup (Python/Flask)
1. **(Optional) Create a virtual environment:**
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```
2. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```
3. **Run the server:**
   ```powershell
   python app.py
   ```
   *The backend will be available at `http://127.0.0.1:7860`.*

### 2. Frontend Setup (React/Vite)
1. **Install Node modules:**
   ```powershell
   npm install
   ```
2. **Start the development server:**
   ```powershell
   npm run dev
   ```
   *The frontend will be available at `http://localhost:5173`.*

---

## 🧪 Technologies Used
- **Backend**: Flask, OpenCV, Pandas, Ultralytics (YOLOv8), yt-dlp.
- **Frontend**: React 19, Vite, Axios.
- **Computer Vision**: YOLOv8 for object detection and tracking.

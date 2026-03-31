import React, { useState, useRef, useEffect } from "react";
import {
  PieChart, Pie, Cell,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from "recharts";
import "./App.css";

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884d8", "#82ca9d"];

const MODEL_COMPARISON_DATA = [
  { name: "YOLOv8n", map: 37.3, speed: 0.99, params: 3.2 },
  { name: "YOLOv10n", map: 38.5, speed: 0.85, params: 2.3 },
  { name: "YOLO11n (Used)", map: 39.4, speed: 1.1, params: 2.6 },
];

function getYouTubeEmbedUrl(url) {
  if (!url) return null;
  const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
  const match = url.match(regExp);
  return (match && match[2].length === 11)
    ? `https://www.youtube.com/embed/${match[2]}`
    : null;
}

export default function App() {
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [file, setFile] = useState(null);
  const [originalPreview, setOriginalPreview] = useState("");
  const [loading, setLoading] = useState(false);
  const [log, setLog] = useState([]);
  const [annotatedUrl, setAnnotatedUrl] = useState("");
  const [csvUrl, setCsvUrl] = useState("");
  const [summary, setSummary] = useState({});
  const [lastTaskId, setLastTaskId] = useState("");

  const fileInputRef = useRef();

  /* -------------------- SUBMIT YOUTUBE -------------------- */
  async function submitYouTube(e) {
    e.preventDefault();
    if (!youtubeUrl) return alert("Paste a YouTube URL");

    setLoading(true);
    resetState();
    setOriginalPreview(youtubeUrl);

    try {
      const resp = await fetch("/api/process-youtube", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: youtubeUrl }),
      });

      const data = await resp.json();
      if (data.task_id) {
        setLastTaskId(data.task_id);
        pollTask(data.task_id);
      }
    } catch (err) {
      alert("Error: " + err.message);
      setLoading(false);
    }
  }

  /* -------------------- SUBMIT FILE -------------------- */
  async function submitFile(e) {
    e.preventDefault();
    if (!file) return alert("Choose a file");

    setLoading(true);
    resetState();

    const form = new FormData();
    form.append("file", file);

    try {
      const resp = await fetch("/api/process-file", {
        method: "POST",
        body: form,
      });

      const data = await resp.json();
      if (data.task_id) {
        setLastTaskId(data.task_id);
        pollTask(data.task_id);
      }
    } catch (err) {
      alert("Error: " + err.message);
      setLoading(false);
    }
  }

  /* -------------------- RESET -------------------- */
  function resetState() {
    setLog([]);
    setAnnotatedUrl("");
    setCsvUrl("");
    setSummary({});
  }

  /* -------------------- POLL TASK -------------------- */
  async function pollTask(taskId) {
    try {
      while (true) {
        const resp = await fetch(`/api/task-status/${taskId}`);
        const d = await resp.json();

        if (d.status === "done") {
          if (d.annotatedVideoUrl) setAnnotatedUrl(d.annotatedVideoUrl);
          if (d.annotatedImageUrl) setAnnotatedUrl(d.annotatedImageUrl);
          if (d.csvUrl) setCsvUrl(d.csvUrl);
          if (Array.isArray(d.log)) setLog(d.log);
          if (d.summary) setSummary(d.summary);
          break;
        }

        if (d.status === "error") {
          alert("Error: " + d.error);
          break;
        }

        await new Promise((r) => setTimeout(r, 1500));
      }
    } finally {
      setLoading(false);
    }
  }

  /* -------------------- LOCAL FILE PREVIEW -------------------- */
  useEffect(() => {
    if (!file) return;
    const url = URL.createObjectURL(file);
    setOriginalPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  /* -------------------- UI COMPONENTS -------------------- */
  const Dashboard = ({ charts }) => {
    if (!charts) return null;
    return (
      <div className="dashboard">
        <div className="chart-item">
          <h4>Behavior Distribution</h4>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={charts.behavior_distribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {charts.behavior_distribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-item">
          <h4>Animal Distribution</h4>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={charts.animal_distribution}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" fill="#82ca9d" name="Detections" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-item">
          <h4>Confidence Range</h4>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={charts.confidence_distribution}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="range" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#8884d8" name="Count" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  };

  const ModelComparison = () => (
    <div className="comparison-section">
      <h3>🚀 Model Performance Comparison (COCO)</h3>
      <table className="comparison-table">
        <thead>
          <tr>
            <th>Model</th>
            <th>mAP (50-95)</th>
            <th>Speed (ms)</th>
            <th>Params (M)</th>
          </tr>
        </thead>
        <tbody>
          {MODEL_COMPARISON_DATA.map((d, i) => (
            <tr key={i} className={d.name.includes("(Used)") ? "active-row" : ""}>
              <td>{d.name}</td>
              <td>{d.map}%</td>
              <td>{d.speed}</td>
              <td>{d.params}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="note">*Data based on standard Ultralytics benchmarks. YOLO11n provides the best balance of speed and accuracy.</p>
    </div>
  );

  return (
    <div className="container">
      <h1 className="title">🐾 Animal Behaviour Analyzer</h1>

      <div className="forms">
        <form onSubmit={submitFile} className="form">
          <div className="form-group">
            <label>Upload Local Video/Image</label>
            <input
              ref={fileInputRef}
              className="input"
              type="file"
              accept="video/*,image/*"
              onChange={(e) => setFile(e.target.files[0])}
            />
          </div>
          <button className="btn">Analyze File</button>
        </form>

        <div className="form-separator">OR</div>

        <form onSubmit={submitYouTube} className="form">
          <div className="form-group">
            <label>Analyze YouTube Link</label>
            <input
              className="input"
              type="text"
              placeholder="Paste YouTube URL here..."
              value={youtubeUrl}
              onChange={(e) => setYoutubeUrl(e.target.value)}
            />
          </div>
          <button className="btn youtube-btn">Analyze Link</button>
        </form>
      </div>

      {loading && <div className="loading-container"><p className="loading">⏳ Processing analysis...</p></div>}

      <div className="main-grid">
        <div className="left-panel">
          {originalPreview && (
            <section className="section">
              <h3>Source Preview</h3>
              <div className="media-container">
                {file?.type?.startsWith("image") ? (
                  <img className="media" src={originalPreview} alt="original" />
                ) : getYouTubeEmbedUrl(originalPreview) ? (
                  <iframe
                    className="media youtube-preview"
                    src={getYouTubeEmbedUrl(originalPreview)}
                    title="YouTube video player"
                    frameBorder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  />
                ) : (
                  <video className="media" controls src={originalPreview} />
                )}
              </div>
            </section>
          )}

          {annotatedUrl && (
            <section className="section">
              <h3>Annotated Result</h3>
              <div className="media-container">
                {annotatedUrl.endsWith(".jpg") ? (
                  <img className="media" src={annotatedUrl} alt="result" />
                ) : (
                  <video className="media" controls src={annotatedUrl} />
                )}
              </div>
            </section>
          )}
        </div>

        <div className="right-panel">
          {summary.charts && <Dashboard charts={summary.charts} />}
          <ModelComparison />
        </div>
      </div>

      {log.length > 0 && (
        <section className="section table-section">
          <div className="table-header">
            <h3>Recent Detections</h3>
            {csvUrl && <a className="csv-btn" href={csvUrl} target="_blank" rel="noreferrer">📥 Download CSV</a>}
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Frame</th>
                  <th>Label</th>
                  <th>Behavior</th>
                  <th>Speed</th>
                  <th>Confidence</th>
                  <th>Abnormal</th>
                </tr>
              </thead>
              <tbody>
                {log.slice(0, 10).map((r, i) => (
                  <tr key={i}>
                    <td>{r.frame}</td>
                    <td>{r.label}</td>
                    <td>{r.behavior}</td>
                    <td>{r.speed}</td>
                    <td>{r.confidence}</td>
                    <td>{r.abnormal || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}

import React, { useState, useRef, useEffect } from "react";
import "./App.css";

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

  /* -------------------- UI -------------------- */
  return (
    <div className="container">
      <h1 className="title">🐾 Animal Behaviour Analyzer</h1>

      <div className="forms">

        <form onSubmit={submitFile} className="form">
          <input
            ref={fileInputRef}
            className="input"
            type="file"
            accept="video/*,image/*"
            onChange={(e) => setFile(e.target.files[0])}
          />
          <button className="btn">Upload & Analyze</button>
        </form>
      </div>

      {loading && <p className="loading">⏳ Processing…</p>}

      {/* -------------------- ORIGINAL PREVIEW -------------------- */}
      {originalPreview && (
        <section className="section">
          <h3>Original</h3>

          {originalPreview.includes("youtube") ? (
            <iframe
              title="yt"
              className="media"
              src={`https://www.youtube.com/embed/${new URL(
                originalPreview
              ).searchParams.get("v")}`}
            />
          ) : file?.type?.startsWith("image") ? (
            <img className="media" src={originalPreview} alt="original" />
          ) : (
            <video className="media" controls src={originalPreview} />
          )}
        </section>
      )}

    

      {/* -------------------- LOG TABLE -------------------- */}
      {log.length > 0 && (
        <section className="section">
          <h3>Detections (first 10)</h3>

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
        </section>
      )}

      {csvUrl && (
        <a className="csv" href={csvUrl} target="_blank" rel="noreferrer">
          📥 Download Full CSV
        </a>
      )}
    </div>
  );
}

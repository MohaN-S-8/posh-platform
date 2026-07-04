import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import apiClient from "../../api/client";

export function VideoListPage() {
  const navigate = useNavigate();
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState("");
  const fileInputRef = useRef(null);
  const [form, setForm] = useState({
    title: "",
    description: "",
    category_id: "",
    duration_minutes: "",
  });

  useEffect(() => {
    fetchVideos();
  }, []);

  const fetchVideos = async () => {
    setLoading(true);
    try {
      // Get all company videos — use compliance endpoint for now
      const res = await apiClient.get("/hr/compliance/dashboard");
      setVideos([]); // Videos list endpoint to be called with admin token
      setLoading(false);
    } catch {
      setLoading(false);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!fileInputRef.current?.files?.[0]) {
      setError("Please select a video file.");
      return;
    }
    setUploading(true);
    setError("");
    setUploadProgress("Uploading...");

    const formData = new FormData();
    formData.append("file", fileInputRef.current.files[0]);
    formData.append("title", form.title);
    if (form.description) formData.append("description", form.description);
    if (form.category_id) formData.append("category_id", form.category_id);
    if (form.duration_minutes)
      formData.append("duration_minutes", form.duration_minutes);

    try {
      await apiClient.post("/videos/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setUploadProgress("✅ Upload successful! Video is in Draft status.");
      setForm({
        title: "",
        description: "",
        category_id: "",
        duration_minutes: "",
      });
      fileInputRef.current.value = "";
    } catch (err) {
      setError(err.response?.data?.detail || "Upload failed.");
      setUploadProgress("");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={{ padding: "32px", background: "#f5f7fa", minHeight: "100vh" }}>
      <div style={{ marginBottom: "24px" }}>
        <button
          onClick={() => navigate("/admin")}
          style={{
            background: "none",
            border: "none",
            color: "#1a3c5e",
            cursor: "pointer",
            marginBottom: "8px",
          }}
        >
          ← Back to Dashboard
        </button>
        <h1 style={{ color: "#1a3c5e", margin: 0 }}>Video Management</h1>
      </div>

      {error && (
        <div
          style={{
            background: "#fdf0f0",
            border: "1px solid #e74c3c",
            borderRadius: "8px",
            padding: "12px 16px",
            color: "#e74c3c",
            marginBottom: "16px",
          }}
        >
          {error}
        </div>
      )}

      {/* Upload Form */}
      <div
        style={{
          background: "white",
          borderRadius: "12px",
          padding: "24px",
          boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
          marginBottom: "24px",
        }}
      >
        <h3 style={{ color: "#1a3c5e", marginTop: 0 }}>Upload New Video</h3>
        <p style={{ color: "#666", fontSize: "13px", marginBottom: "20px" }}>
          Supported formats: MP4, AVI, MOV. Maximum size: 500MB. Videos are
          stored securely — never publicly accessible.
        </p>
        <form onSubmit={handleUpload}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "16px",
              marginBottom: "16px",
            }}
          >
            <div>
              <label
                style={{
                  display: "block",
                  marginBottom: "4px",
                  fontWeight: 500,
                  fontSize: "14px",
                }}
              >
                Video Title *
              </label>
              <input
                required
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  border: "1px solid #ddd",
                  borderRadius: "6px",
                  fontSize: "14px",
                  boxSizing: "border-box",
                }}
              />
            </div>
            <div>
              <label
                style={{
                  display: "block",
                  marginBottom: "4px",
                  fontWeight: 500,
                  fontSize: "14px",
                }}
              >
                Duration (minutes)
              </label>
              <input
                type="number"
                value={form.duration_minutes}
                onChange={(e) =>
                  setForm({ ...form, duration_minutes: e.target.value })
                }
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  border: "1px solid #ddd",
                  borderRadius: "6px",
                  fontSize: "14px",
                  boxSizing: "border-box",
                }}
              />
            </div>
          </div>
          <div style={{ marginBottom: "16px" }}>
            <label
              style={{
                display: "block",
                marginBottom: "4px",
                fontWeight: 500,
                fontSize: "14px",
              }}
            >
              Description
            </label>
            <textarea
              value={form.description}
              onChange={(e) =>
                setForm({ ...form, description: e.target.value })
              }
              rows={3}
              style={{
                width: "100%",
                padding: "8px 12px",
                border: "1px solid #ddd",
                borderRadius: "6px",
                fontSize: "14px",
                boxSizing: "border-box",
                resize: "vertical",
              }}
            />
          </div>
          <div style={{ marginBottom: "16px" }}>
            <label
              style={{
                display: "block",
                marginBottom: "4px",
                fontWeight: 500,
                fontSize: "14px",
              }}
            >
              Video File *
            </label>
            <input
              type="file"
              ref={fileInputRef}
              accept=".mp4,.avi,.mov"
              style={{ fontSize: "14px" }}
            />
          </div>
          {uploadProgress && (
            <div
              style={{
                padding: "10px 14px",
                background: "#e8f5e9",
                borderRadius: "6px",
                color: "#27ae60",
                fontSize: "14px",
                marginBottom: "16px",
              }}
            >
              {uploadProgress}
            </div>
          )}
          <button
            type="submit"
            disabled={uploading}
            style={{
              padding: "10px 24px",
              background: uploading ? "#93b8d4" : "#1a3c5e",
              color: "white",
              border: "none",
              borderRadius: "6px",
              cursor: uploading ? "not-allowed" : "pointer",
              fontWeight: 600,
            }}
          >
            {uploading ? "Uploading..." : "Upload Video"}
          </button>
        </form>
      </div>

      <div
        style={{
          background: "white",
          borderRadius: "12px",
          padding: "24px",
          boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
        }}
      >
        <p style={{ color: "#666", fontSize: "14px" }}>
          After uploading a video, go to{" "}
          <strong>http://localhost:8000/docs</strong> →
          <code> PATCH /api/v1/videos/{"{video_id}"}/publish</code> to publish
          it so employees can watch it. The video management UI will be expanded
          in the next iteration.
        </p>
      </div>
    </div>
  );
}

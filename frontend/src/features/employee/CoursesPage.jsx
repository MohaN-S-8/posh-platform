import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import apiClient from "../../api/client";
import { useAuthStore } from "../../store/authStore";

export function CoursesPage() {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Get assigned courses via compliance dashboard
    apiClient
      .get("/hr/compliance/dashboard")
      .then(() => {
        // Placeholder — real course list would come from a dedicated employee endpoint
        setCourses([]);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div style={{ padding: "32px", background: "#f5f7fa", minHeight: "100vh" }}>
      <button
        onClick={() => navigate("/employee")}
        style={{
          background: "none",
          border: "none",
          color: "#1a3c5e",
          cursor: "pointer",
          marginBottom: "16px",
        }}
      >
        ← Back to Dashboard
      </button>
      <h1 style={{ color: "#1a3c5e", marginBottom: "24px" }}>My Courses</h1>

      {loading ? (
        <p style={{ color: "#666" }}>Loading your courses...</p>
      ) : courses.length === 0 ? (
        <div
          style={{
            background: "white",
            borderRadius: "12px",
            padding: "40px",
            boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: "48px", marginBottom: "16px" }}>📚</div>
          <h3 style={{ color: "#1a3c5e" }}>No courses assigned yet</h3>
          <p style={{ color: "#666" }}>
            Your HR will assign training courses to you. Check back soon.
          </p>
        </div>
      ) : (
        <div style={{ display: "grid", gap: "16px" }}>
          {courses.map((course) => (
            <div
              key={course.id}
              style={{
                background: "white",
                borderRadius: "12px",
                padding: "20px",
                boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <div>
                <h3 style={{ color: "#1a3c5e", margin: "0 0 4px" }}>
                  {course.title}
                </h3>
                <p style={{ color: "#666", margin: 0, fontSize: "13px" }}>
                  {course.completion_percent || 0}% complete
                </p>
              </div>
              <button
                onClick={() => navigate(`/employee/video/${course.video_id}`)}
                style={{
                  padding: "8px 20px",
                  background: "#1a3c5e",
                  color: "white",
                  border: "none",
                  borderRadius: "6px",
                  cursor: "pointer",
                }}
              >
                {course.status === "Completed" ? "Review" : "Watch"}
              </button>
            </div>
          ))}
        </div>
      )}

      <div
        style={{
          background: "white",
          borderRadius: "12px",
          padding: "20px",
          boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
          marginTop: "24px",
        }}
      >
        <p style={{ color: "#666", fontSize: "14px", margin: 0 }}>
          <strong>To test video playback:</strong> Go to{" "}
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">
            http://localhost:8000/docs
          </a>{" "}
          → <code>GET /api/v1/videos/{"{video_id}"}/stream-url</code> with your
          access token. The video must be Published and you must be assigned the
          course.
        </p>
      </div>
    </div>
  );
}

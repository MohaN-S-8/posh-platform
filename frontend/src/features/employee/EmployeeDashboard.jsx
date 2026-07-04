import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import apiClient from "../../api/client";
import { useAuthStore } from "../../store/authStore";

export function EmployeeDashboard() {
  const navigate = useNavigate();
  const { clearAuth } = useAuthStore();
  const [stats, setStats] = useState(null);

  useEffect(() => {
    // Fetch compliance data for this employee's company
    apiClient
      .get("/hr/compliance/dashboard")
      .then((res) => setStats(res.data))
      .catch(() => {});
  }, []);

  const logout = () => {
    clearAuth();
    navigate("/login");
  };

  return (
    <div style={{ padding: "32px", background: "#f5f7fa", minHeight: "100vh" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "32px",
        }}
      >
        <div>
          <h1 style={{ color: "#1a3c5e", margin: 0 }}>My Training Dashboard</h1>
          <p style={{ color: "#666", margin: "4px 0 0" }}>
            POSH Training Platform
          </p>
        </div>
        <button
          onClick={logout}
          style={{
            padding: "8px 20px",
            background: "#e74c3c",
            color: "white",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
          }}
        >
          Logout
        </button>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "20px",
          marginBottom: "32px",
        }}
      >
        {[
          {
            label: "My Courses",
            icon: "📚",
            path: "/employee/courses",
            desc: "View and watch assigned training",
          },
          {
            label: "My Certificates",
            icon: "🎓",
            path: "/employee/certificates",
            desc: "Download your certificates",
          },
          {
            label: "Training History",
            icon: "📊",
            path: "/employee/courses",
            desc: "Track your progress",
          },
        ].map(({ label, icon, path, desc }) => (
          <div
            key={label}
            onClick={() => navigate(path)}
            style={{
              background: "white",
              borderRadius: "12px",
              padding: "24px",
              boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
              cursor: "pointer",
              borderLeft: "4px solid #1a3c5e",
              transition: "transform 0.1s",
            }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.transform = "translateY(-2px)")
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.transform = "translateY(0)")
            }
          >
            <div style={{ fontSize: "32px", marginBottom: "12px" }}>{icon}</div>
            <h3 style={{ color: "#1a3c5e", margin: "0 0 6px" }}>{label}</h3>
            <p style={{ color: "#666", fontSize: "13px", margin: 0 }}>{desc}</p>
          </div>
        ))}
      </div>

      <div
        style={{
          background: "#1a3c5e",
          borderRadius: "12px",
          padding: "24px",
          color: "white",
        }}
      >
        <h3 style={{ margin: "0 0 8px" }}>About POSH Training</h3>
        <p
          style={{
            margin: 0,
            opacity: 0.85,
            fontSize: "14px",
            lineHeight: 1.6,
          }}
        >
          POSH requires all employees to complete mandatory training. Complete
          your assigned courses, pass the assessments, and download your
          certificate to stay compliant.
        </p>
      </div>
    </div>
  );
}

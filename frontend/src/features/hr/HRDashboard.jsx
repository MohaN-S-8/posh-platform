import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";

export function HRDashboard() {
  const navigate = useNavigate();
  const { clearAuth } = useAuthStore();
  const logout = () => {
    clearAuth();
    navigate("/login");
  };

  const cards = [
    {
      label: "Bulk Employee Upload",
      icon: "📤",
      path: "/hr/upload",
      desc: "Upload Excel/CSV to create employees",
    },
    {
      label: "Assign Training",
      icon: "📋",
      path: "/hr/assign",
      desc: "Assign courses to employees",
    },
    {
      label: "Compliance Dashboard",
      icon: "📊",
      path: "/hr/compliance",
      desc: "Track training completion",
    },
  ];

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
          <h1 style={{ color: "#1a3c5e", margin: 0 }}>HR Portal</h1>
          <p style={{ color: "#666", margin: "4px 0 0" }}>
            Manage employees and training compliance
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
        }}
      >
        {cards.map(({ label, icon, path, desc }) => (
          <div
            key={path}
            onClick={() => navigate(path)}
            style={{
              background: "white",
              borderRadius: "12px",
              padding: "28px",
              boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
              cursor: "pointer",
              borderLeft: "4px solid #1a3c5e",
            }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.transform = "translateY(-2px)")
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.transform = "translateY(0)")
            }
          >
            <div style={{ fontSize: "36px", marginBottom: "12px" }}>{icon}</div>
            <h3 style={{ color: "#1a3c5e", margin: "0 0 6px" }}>{label}</h3>
            <p style={{ color: "#666", fontSize: "13px", margin: 0 }}>{desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

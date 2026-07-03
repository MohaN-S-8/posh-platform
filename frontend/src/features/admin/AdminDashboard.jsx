import { useAuthStore } from "../../store/authStore";
import { useNavigate } from "react-router-dom";

export function AdminDashboard() {
  const { clearAuth } = useAuthStore();
  const navigate = useNavigate();

  const logout = () => {
    clearAuth();
    navigate("/login");
  };

  return (
    <div style={{ padding: "40px" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <h1 style={{ color: "#1a3c5e" }}>Admin Portal</h1>
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
          marginTop: "32px",
        }}
      >
        {[
          { label: "Companies", path: "/admin/companies" },
          { label: "Users", path: "/admin/users" },
          { label: "Videos", path: "/admin/videos" },
        ].map((item) => (
          <div
            key={item.path}
            onClick={() => navigate(item.path)}
            style={{
              background: "white",
              padding: "24px",
              borderRadius: "8px",
              boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
              cursor: "pointer",
              borderLeft: "4px solid #1a3c5e",
            }}
          >
            <h3 style={{ color: "#1a3c5e" }}>{item.label}</h3>
          </div>
        ))}
      </div>
    </div>
  );
}

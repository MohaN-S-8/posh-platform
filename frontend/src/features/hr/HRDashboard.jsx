import { useAuthStore } from "../../store/authStore";
import { useNavigate } from "react-router-dom";

export function HRDashboard() {
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
        <h1 style={{ color: "#1a3c5e" }}>HR Portal</h1>
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
    </div>
  );
}

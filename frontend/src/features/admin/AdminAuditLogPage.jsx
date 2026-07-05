import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import apiClient from "../../api/client";
import { LoadingOverlay } from "../../components/LoadingOverlay";

export function AdminAuditLogPage() {
  const navigate = useNavigate();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadLogs = async () => {
      setLoading(true);
      setError("");
      try {
        const res = await apiClient.get("/admin/audit-logins");
        setLogs(res.data || []);
      } catch (err) {
        setError(err.response?.data?.detail || "Unable to load audit logs.");
      } finally {
        setLoading(false);
      }
    };
    loadLogs();
  }, []);

  return (
    <div style={{ padding: "32px", background: "#f6f8fb", minHeight: "100vh" }}>
      <button type="button" onClick={() => navigate("/admin")} style={backButtonStyle}>
        Back to Dashboard
      </button>
      <h1 style={{ color: "#17324d", margin: "0 0 6px", fontSize: "30px" }}>
        Audit Logs
      </h1>
      <p style={{ color: "#64748b", margin: "0 0 24px" }}>
        Recent login attempts captured with user, email, IP, status, and timestamp.
      </p>

      {error && <div style={errorStyle}>{error}</div>}

      <div style={tableWrapStyle}>
        <table style={{ width: "100%", borderCollapse: "collapse", minWidth: "760px" }}>
          <thead>
            <tr style={{ background: "#17324d", color: "white" }}>
              {["Email", "User ID", "IP Address", "Success", "Timestamp"].map((heading) => (
                <th key={heading} style={thStyle}>
                  {heading}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {logs.length ? (
              logs.map((log) => (
                <tr key={log.id} style={{ borderBottom: "1px solid #eef2f6" }}>
                  <td style={tdStyle}>{log.email_attempted}</td>
                  <td style={tdStyle}>{log.user_id || "-"}</td>
                  <td style={tdStyle}>{log.ip_address || "-"}</td>
                  <td style={{ ...tdStyle, color: log.success ? "#1f7a4d" : "#c0392b" }}>
                    {log.success ? "Success" : "Failed"}
                  </td>
                  <td style={tdStyle}>
                    {log.attempted_at ? new Date(log.attempted_at).toLocaleString() : "-"}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} style={{ padding: "28px", color: "#64748b" }}>
                  No audit log entries found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <LoadingOverlay show={loading} title="Loading audit logs" message="Fetching login events." />
    </div>
  );
}

const backButtonStyle = {
  background: "none",
  border: "none",
  color: "#17324d",
  cursor: "pointer",
  marginBottom: "16px",
  fontWeight: 700,
};

const tableWrapStyle = {
  background: "white",
  borderRadius: "8px",
  boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
  border: "1px solid #e7edf3",
  overflowX: "auto",
};

const thStyle = {
  padding: "12px 14px",
  textAlign: "left",
  fontSize: "13px",
};

const tdStyle = {
  padding: "12px 14px",
  color: "#64748b",
  fontSize: "13px",
};

const errorStyle = {
  background: "#fff7f6",
  border: "1px solid #f3b4ae",
  borderRadius: "8px",
  color: "#c0392b",
  padding: "12px 14px",
  marginBottom: "18px",
};

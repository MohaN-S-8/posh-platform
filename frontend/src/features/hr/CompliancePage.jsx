import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import apiClient from "../../api/client";

export function CompliancePage() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    apiClient
      .get("/hr/compliance/dashboard")
      .then((res) => {
        setData(res.data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const downloadReport = async () => {
    setDownloading(true);
    try {
      const res = await apiClient.get("/hr/reports/employees", {
        responseType: "blob",
      });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = "employee_training_report.xlsx";
      a.click();
    } catch {
      alert("Download failed.");
    } finally {
      setDownloading(false);
    }
  };

  if (loading) return <div style={{ padding: "40px" }}>Loading...</div>;

  return (
    <div style={{ padding: "32px", background: "#f5f7fa", minHeight: "100vh" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "24px",
        }}
      >
        <div>
          <button
            onClick={() => navigate("/hr")}
            style={{
              background: "none",
              border: "none",
              color: "#1a3c5e",
              cursor: "pointer",
              marginBottom: "8px",
            }}
          >
            ← Back to HR Dashboard
          </button>
          <h1 style={{ color: "#1a3c5e", margin: 0 }}>Compliance Dashboard</h1>
        </div>
        <button
          onClick={downloadReport}
          disabled={downloading}
          style={{
            padding: "10px 20px",
            background: "#27ae60",
            color: "white",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
            fontWeight: 600,
          }}
        >
          {downloading ? "Downloading..." : "⬇ Download Excel Report"}
        </button>
      </div>

      {data && (
        <>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(4, 1fr)",
              gap: "16px",
              marginBottom: "24px",
            }}
          >
            {[
              {
                label: "Total Employees",
                value: data.total_employees,
                color: "#1a3c5e",
              },
              { label: "Completed", value: data.completed, color: "#27ae60" },
              {
                label: "In Progress",
                value: data.in_progress,
                color: "#f39c12",
              },
              {
                label: "Not Started",
                value: data.not_started,
                color: "#e74c3c",
              },
            ].map(({ label, value, color }) => (
              <div
                key={label}
                style={{
                  background: "white",
                  borderRadius: "12px",
                  padding: "20px",
                  boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
                  textAlign: "center",
                  borderTop: `4px solid ${color}`,
                }}
              >
                <div style={{ fontSize: "36px", fontWeight: 700, color }}>
                  {value}
                </div>
                <div
                  style={{ fontSize: "13px", color: "#666", marginTop: "4px" }}
                >
                  {label}
                </div>
              </div>
            ))}
          </div>

          <div
            style={{
              background: "white",
              borderRadius: "12px",
              padding: "20px",
              boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
              marginBottom: "20px",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: "12px",
              }}
            >
              <h3 style={{ margin: 0, color: "#1a3c5e" }}>
                Overall Compliance Rate
              </h3>
              <span
                style={{
                  fontSize: "24px",
                  fontWeight: 700,
                  color: data.compliance_rate >= 80 ? "#27ae60" : "#e74c3c",
                }}
              >
                {data.compliance_rate}%
              </span>
            </div>
            <div
              style={{
                height: "12px",
                background: "#f0f0f0",
                borderRadius: "6px",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  height: "100%",
                  width: `${data.compliance_rate}%`,
                  background:
                    data.compliance_rate >= 80 ? "#27ae60" : "#e74c3c",
                  borderRadius: "6px",
                  transition: "width 0.5s",
                }}
              />
            </div>
          </div>

          {data.department_breakdown?.length > 0 && (
            <div
              style={{
                background: "white",
                borderRadius: "12px",
                padding: "20px",
                boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
                marginBottom: "20px",
              }}
            >
              <h3 style={{ marginTop: 0, color: "#1a3c5e" }}>
                Department Breakdown
              </h3>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ background: "#f5f7fa" }}>
                    <th
                      style={{
                        padding: "10px 16px",
                        textAlign: "left",
                        fontSize: "13px",
                        color: "#666",
                      }}
                    >
                      Department
                    </th>
                    <th
                      style={{
                        padding: "10px 16px",
                        textAlign: "right",
                        fontSize: "13px",
                        color: "#666",
                      }}
                    >
                      Employees
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {data.department_breakdown.map((dept, i) => (
                    <tr key={i} style={{ borderBottom: "1px solid #eee" }}>
                      <td style={{ padding: "10px 16px", fontSize: "14px" }}>
                        {dept.department}
                      </td>
                      <td
                        style={{
                          padding: "10px 16px",
                          fontSize: "14px",
                          textAlign: "right",
                          fontWeight: 600,
                        }}
                      >
                        {dept.total}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {data.overdue_employees?.length > 0 && (
            <div
              style={{
                background: "white",
                borderRadius: "12px",
                padding: "20px",
                boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
              }}
            >
              <h3 style={{ marginTop: 0, color: "#e74c3c" }}>
                ⚠ Overdue Employees ({data.overdue_employees.length})
              </h3>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ background: "#fdf0f0" }}>
                    {["Name", "Email", "Due Date"].map((h) => (
                      <th
                        key={h}
                        style={{
                          padding: "10px 16px",
                          textAlign: "left",
                          fontSize: "13px",
                          color: "#e74c3c",
                        }}
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.overdue_employees.map((emp, i) => (
                    <tr key={i} style={{ borderBottom: "1px solid #eee" }}>
                      <td style={{ padding: "10px 16px", fontSize: "14px" }}>
                        {emp.name}
                      </td>
                      <td
                        style={{
                          padding: "10px 16px",
                          fontSize: "14px",
                          color: "#666",
                        }}
                      >
                        {emp.email}
                      </td>
                      <td
                        style={{
                          padding: "10px 16px",
                          fontSize: "14px",
                          color: "#e74c3c",
                        }}
                      >
                        {emp.due_date}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}

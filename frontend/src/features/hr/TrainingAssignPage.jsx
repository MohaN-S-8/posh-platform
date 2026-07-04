import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import apiClient from "../../api/client";

export function TrainingAssignPage() {
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    video_id: "",
    assign_type: "Company-Wide",
    assigned_to_user_id: "",
    assigned_to_department: "",
    due_days: 30,
    passing_score: 70,
  });

  useEffect(() => {
    apiClient
      .get("/users/")
      .then((res) => setUsers(res.data))
      .catch(() => {});
  }, []);

  const departments = [
    ...new Set(users.map((u) => u.department).filter(Boolean)),
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess("");
    try {
      const payload = {
        video_id: parseInt(form.video_id),
        assign_type: form.assign_type,
        due_days: parseInt(form.due_days),
        passing_score: parseFloat(form.passing_score),
      };
      if (form.assign_type === "Individual")
        payload.assigned_to_user_id = parseInt(form.assigned_to_user_id);
      if (form.assign_type === "Department")
        payload.assigned_to_department = form.assigned_to_department;

      const res = await apiClient.post("/hr/training/assign", payload);
      setSuccess(res.data.message);
    } catch (err) {
      setError(err.response?.data?.detail || "Assignment failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "32px", background: "#f5f7fa", minHeight: "100vh" }}>
      <button
        onClick={() => navigate("/hr")}
        style={{
          background: "none",
          border: "none",
          color: "#1a3c5e",
          cursor: "pointer",
          marginBottom: "16px",
        }}
      >
        ← Back to HR Dashboard
      </button>
      <h1 style={{ color: "#1a3c5e", marginBottom: "24px" }}>
        Assign Training
      </h1>

      <div
        style={{
          background: "white",
          borderRadius: "12px",
          padding: "24px",
          boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
          maxWidth: "600px",
        }}
      >
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: "16px" }}>
            <label
              style={{ display: "block", marginBottom: "4px", fontWeight: 500 }}
            >
              Video ID *
            </label>
            <input
              type="number"
              required
              value={form.video_id}
              onChange={(e) => setForm({ ...form, video_id: e.target.value })}
              placeholder="Enter the video ID from admin panel"
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

          <div style={{ marginBottom: "16px" }}>
            <label
              style={{ display: "block", marginBottom: "4px", fontWeight: 500 }}
            >
              Assignment Type *
            </label>
            <div style={{ display: "flex", gap: "12px" }}>
              {["Individual", "Department", "Company-Wide"].map((type) => (
                <label
                  key={type}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                    cursor: "pointer",
                    fontSize: "14px",
                  }}
                >
                  <input
                    type="radio"
                    name="assign_type"
                    value={type}
                    checked={form.assign_type === type}
                    onChange={() => setForm({ ...form, assign_type: type })}
                  />
                  {type}
                </label>
              ))}
            </div>
          </div>

          {form.assign_type === "Individual" && (
            <div style={{ marginBottom: "16px" }}>
              <label
                style={{
                  display: "block",
                  marginBottom: "4px",
                  fontWeight: 500,
                }}
              >
                Select Employee *
              </label>
              <select
                required
                value={form.assigned_to_user_id}
                onChange={(e) =>
                  setForm({ ...form, assigned_to_user_id: e.target.value })
                }
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  border: "1px solid #ddd",
                  borderRadius: "6px",
                  fontSize: "14px",
                  boxSizing: "border-box",
                }}
              >
                <option value="">— Select employee —</option>
                {users
                  .filter((u) => u.role_id === 4)
                  .map((u) => (
                    <option key={u.user_id} value={u.user_id}>
                      {u.first_name} {u.last_name} ({u.email})
                    </option>
                  ))}
              </select>
            </div>
          )}

          {form.assign_type === "Department" && (
            <div style={{ marginBottom: "16px" }}>
              <label
                style={{
                  display: "block",
                  marginBottom: "4px",
                  fontWeight: 500,
                }}
              >
                Department *
              </label>
              <select
                required
                value={form.assigned_to_department}
                onChange={(e) =>
                  setForm({ ...form, assigned_to_department: e.target.value })
                }
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  border: "1px solid #ddd",
                  borderRadius: "6px",
                  fontSize: "14px",
                  boxSizing: "border-box",
                }}
              >
                <option value="">— Select department —</option>
                {departments.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "16px",
              marginBottom: "20px",
            }}
          >
            <div>
              <label
                style={{
                  display: "block",
                  marginBottom: "4px",
                  fontWeight: 500,
                }}
              >
                Due in (days)
              </label>
              <input
                type="number"
                value={form.due_days}
                onChange={(e) => setForm({ ...form, due_days: e.target.value })}
                min={1}
                max={365}
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
                }}
              >
                Passing Score (%)
              </label>
              <input
                type="number"
                value={form.passing_score}
                onChange={(e) =>
                  setForm({ ...form, passing_score: e.target.value })
                }
                min={0}
                max={100}
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

          {error && (
            <div
              style={{
                background: "#fdf0f0",
                border: "1px solid #e74c3c",
                borderRadius: "6px",
                padding: "10px 14px",
                color: "#e74c3c",
                fontSize: "14px",
                marginBottom: "16px",
              }}
            >
              {error}
            </div>
          )}
          {success && (
            <div
              style={{
                background: "#e8f5e9",
                border: "1px solid #27ae60",
                borderRadius: "6px",
                padding: "10px 14px",
                color: "#27ae60",
                fontSize: "14px",
                marginBottom: "16px",
              }}
            >
              ✅ {success}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              padding: "10px 28px",
              background: loading ? "#93b8d4" : "#1a3c5e",
              color: "white",
              border: "none",
              borderRadius: "6px",
              cursor: loading ? "not-allowed" : "pointer",
              fontWeight: 600,
            }}
          >
            {loading ? "Assigning..." : "Assign Training"}
          </button>
        </form>
      </div>
    </div>
  );
}

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import apiClient from "../../api/client";

const ROLES = { 1: "Super Admin", 2: "Company Admin", 3: "HR", 4: "Employee" };

export function UserListPage() {
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get("/users/");
      setUsers(res.data);
    } catch {
      setError("Failed to load users.");
    } finally {
      setLoading(false);
    }
  };

  const toggleStatus = async (user) => {
    const newStatus = user.status === "Active" ? "Inactive" : "Active";
    try {
      await apiClient.patch(
        `/users/${user.user_id}/status?status=${newStatus}`,
      );
      fetchUsers();
    } catch {
      setError("Failed to update user status.");
    }
  };

  const filtered = users.filter((u) =>
    `${u.first_name} ${u.last_name} ${u.email} ${u.department || ""}`
      .toLowerCase()
      .includes(search.toLowerCase()),
  );

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
          <h1 style={{ color: "#1a3c5e", margin: 0 }}>User Management</h1>
        </div>
        <input
          placeholder="Search users..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            padding: "10px 16px",
            border: "1px solid #ddd",
            borderRadius: "6px",
            fontSize: "14px",
            width: "240px",
          }}
        />
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

      {loading ? (
        <p style={{ color: "#666" }}>Loading users...</p>
      ) : (
        <div
          style={{
            background: "white",
            borderRadius: "12px",
            boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
            overflow: "hidden",
          }}
        >
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "#1a3c5e", color: "white" }}>
                {[
                  "Employee ID",
                  "Name",
                  "Email",
                  "Department",
                  "Role",
                  "Status",
                  "Actions",
                ].map((h) => (
                  <th
                    key={h}
                    style={{
                      padding: "12px 16px",
                      textAlign: "left",
                      fontSize: "13px",
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td
                    colSpan={7}
                    style={{
                      padding: "40px",
                      textAlign: "center",
                      color: "#999",
                    }}
                  >
                    No users found.
                  </td>
                </tr>
              ) : (
                filtered.map((u, i) => (
                  <tr
                    key={u.user_id}
                    style={{
                      background: i % 2 === 0 ? "white" : "#f9f9f9",
                      borderBottom: "1px solid #eee",
                    }}
                  >
                    <td
                      style={{
                        padding: "12px 16px",
                        fontSize: "13px",
                        color: "#666",
                      }}
                    >
                      {u.employee_id}
                    </td>
                    <td
                      style={{
                        padding: "12px 16px",
                        fontSize: "14px",
                        fontWeight: 500,
                      }}
                    >
                      {u.first_name} {u.last_name}
                    </td>
                    <td
                      style={{
                        padding: "12px 16px",
                        fontSize: "13px",
                        color: "#666",
                      }}
                    >
                      {u.email}
                    </td>
                    <td
                      style={{
                        padding: "12px 16px",
                        fontSize: "13px",
                        color: "#666",
                      }}
                    >
                      {u.department || "—"}
                    </td>
                    <td style={{ padding: "12px 16px" }}>
                      <span
                        style={{
                          padding: "3px 10px",
                          borderRadius: "12px",
                          fontSize: "12px",
                          fontWeight: 600,
                          background: "#e8f0fe",
                          color: "#1a3c5e",
                        }}
                      >
                        {ROLES[u.role_id] || "Unknown"}
                      </span>
                    </td>
                    <td style={{ padding: "12px 16px" }}>
                      <span
                        style={{
                          padding: "3px 10px",
                          borderRadius: "12px",
                          fontSize: "12px",
                          fontWeight: 600,
                          background:
                            u.status === "Active" ? "#e8f5e9" : "#fdf0f0",
                          color: u.status === "Active" ? "#27ae60" : "#e74c3c",
                        }}
                      >
                        {u.status}
                      </span>
                    </td>
                    <td style={{ padding: "12px 16px" }}>
                      <button
                        onClick={() => toggleStatus(u)}
                        style={{
                          padding: "4px 12px",
                          fontSize: "12px",
                          borderRadius: "4px",
                          cursor: "pointer",
                          border: "none",
                          fontWeight: 600,
                          background:
                            u.status === "Active" ? "#fdf0f0" : "#e8f5e9",
                          color: u.status === "Active" ? "#e74c3c" : "#27ae60",
                        }}
                      >
                        {u.status === "Active" ? "Deactivate" : "Activate"}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

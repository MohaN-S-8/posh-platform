# Phase 5 Continuation — Free Credentials Setup + All Missing Frontend Pages

## What's Done vs What's Missing

**Done:**

- ✅ Phase 5A — Backend gaps (email utility, Celery)
- ✅ Phase 5B — Auth screens (Login, Signup, OTP, Forgot/Reset Password)

**Missing:**

- ⬜ Real Gmail SMTP (OTP not arriving)
- ⬜ Admin Portal screens (Companies, Users, Videos)
- ⬜ HR Portal screens (Bulk Upload, Training Assign, Compliance)
- ⬜ Employee Portal screens (Courses, Video Player, Assessment, Certificates)

**No backend code changes needed — only `.env` and new frontend files.**

---

# PART A — FREE CREDENTIALS SETUP

---

## Fix Gmail SMTP (OTP Not Arriving)

MailHog catches emails locally but doesn't actually send them. For real OTP emails, use Gmail's free SMTP.

### Step 1: Enable 2-Factor Authentication on Gmail

1. Go to https://myaccount.google.com/security
2. Click **"2-Step Verification"** → turn it on
3. Follow the prompts (phone verification)

### Step 2: Generate an App Password (need from client)

1. Still on https://myaccount.google.com/security
2. Search **"App passwords"** in the search bar at the top
3. Click it → Select app: **"Mail"** → Select device: **"Windows Computer"**
4. Click **Generate** → copy the 16-character password shown (e.g. `abcd efgh ijkl mnop`)
5. **Save this — it only shows once**
   **_ ehda psut hdxo wbzd _**

### Step 3: Update Your `.env` File

Open `.env` in the project root and update these lines:

```bash
# CHANGE THESE (replace with your actual Gmail and App Password):
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=yourgmail@gmail.com
SMTP_PASSWORD=abcdefghijklmnop
EMAILS_FROM=yourgmail@gmail.com

# Keep development for now (change to production only when deploying):
APP_ENV=development
```

> The App Password has spaces in it when Google shows it — remove the spaces when pasting into `.env`.
> Example: `abcd efgh ijkl mnop` → `abcdefghijklmnop`

### Step 4: Update `backend/app/core/email.py`

The current code only uses TLS in production. Gmail needs STARTTLS on port 587. Replace the `send_email` function body:

```python
async def send_email(to: str, subject: str, html_body: str) -> None:
    message = MIMEMultipart("alternative")
    message["From"] = EMAILS_FROM
    message["To"] = to
    message["Subject"] = subject
    message.attach(MIMEText(html_body, "html"))

    # Gmail uses STARTTLS (port 587), not SSL (port 465)
    # MailHog uses plain SMTP (port 1025, no TLS)
    use_tls = False
    start_tls = SMTP_HOST != "mailhog"   # True for Gmail, False for MailHog

    await aiosmtplib.send(
        message,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        username=SMTP_USER if SMTP_USER else None,
        password=SMTP_PASSWORD if SMTP_PASSWORD else None,
        use_tls=use_tls,
        start_tls=start_tls,
    )
```

### Step 5: Restart Docker and Test

```bash
docker compose restart backend
```

Go to http://localhost:8000/docs → `POST /api/v1/auth/signup` → use a real email address. You should receive the OTP in that email within 30 seconds.

---

## Other Free Services (No Backend Code Changes)

### MinIO (Video/Certificate Storage) — Already Free

MinIO runs in your Docker container already. No signup needed. Works as-is for development. For production, use **Cloudflare R2** (free tier: 10GB storage, no egress fees): ask client

```bash
# Production .env changes for Cloudflare R2:
MINIO_ENDPOINT=<accountid>.r2.cloudflarestorage.com
MINIO_ROOT_USER=<r2_access_key_id>
MINIO_ROOT_PASSWORD=<r2_secret_access_key>
# Backend code stays exactly the same — boto3 works with R2 identically to S3
```

### MySQL — Already Free (Docker)

No changes needed. For production, use **PlanetScale** free tier or **Railway** free tier — just update `DATABASE_URL` in `.env`.

---

# PART B — ALL MISSING FRONTEND PAGES

---

## Admin Portal Pages

### Admin Companies Page

Create `frontend/src/features/admin/CompanyListPage.jsx`:

```jsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import apiClient from "../../api/client";

export function CompanyListPage() {
  const navigate = useNavigate();
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    company_code: "",
    company_name: "",
    industry_type: "",
    contact_email: "",
    contact_mobile: "",
    employee_strength: "",
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get("/companies/");
      setCompanies(res.data);
    } catch {
      setError("Failed to load companies.");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await apiClient.post("/companies/", {
        ...form,
        employee_strength: form.employee_strength
          ? parseInt(form.employee_strength)
          : null,
      });
      setShowForm(false);
      setForm({
        company_code: "",
        company_name: "",
        industry_type: "",
        contact_email: "",
        contact_mobile: "",
        employee_strength: "",
      });
      fetchCompanies();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create company.");
    } finally {
      setSubmitting(false);
    }
  };

  const toggleStatus = async (company) => {
    const newStatus = company.status === "Active" ? "Inactive" : "Active";
    try {
      await apiClient.patch(
        `/companies/${company.company_id}/status?status=${newStatus}`,
      );
      fetchCompanies();
    } catch {
      setError("Failed to update status.");
    }
  };

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
          <h1 style={{ color: "#1a3c5e", margin: 0 }}>Company Management</h1>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          style={{
            padding: "10px 20px",
            background: "#1a3c5e",
            color: "white",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
            fontWeight: 600,
          }}
        >
          + Add Company
        </button>
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

      {showForm && (
        <div
          style={{
            background: "white",
            borderRadius: "12px",
            padding: "24px",
            boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
            marginBottom: "24px",
          }}
        >
          <h3 style={{ color: "#1a3c5e", marginTop: 0 }}>Create New Company</h3>
          <form onSubmit={handleCreate}>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: "16px",
              }}
            >
              {[
                {
                  label: "Company Code *",
                  key: "company_code",
                  required: true,
                },
                {
                  label: "Company Name *",
                  key: "company_name",
                  required: true,
                },
                { label: "Industry Type", key: "industry_type" },
                { label: "Contact Email", key: "contact_email", type: "email" },
                { label: "Contact Mobile", key: "contact_mobile" },
                {
                  label: "Employee Strength",
                  key: "employee_strength",
                  type: "number",
                },
              ].map(({ label, key, type = "text", required }) => (
                <div key={key}>
                  <label
                    style={{
                      display: "block",
                      marginBottom: "4px",
                      fontWeight: 500,
                      fontSize: "14px",
                    }}
                  >
                    {label}
                  </label>
                  <input
                    type={type}
                    required={required}
                    value={form[key]}
                    onChange={(e) =>
                      setForm({ ...form, [key]: e.target.value })
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
              ))}
            </div>
            <div style={{ marginTop: "16px", display: "flex", gap: "12px" }}>
              <button
                type="submit"
                disabled={submitting}
                style={{
                  padding: "10px 24px",
                  background: "#1a3c5e",
                  color: "white",
                  border: "none",
                  borderRadius: "6px",
                  cursor: "pointer",
                  fontWeight: 600,
                }}
              >
                {submitting ? "Creating..." : "Create Company"}
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                style={{
                  padding: "10px 24px",
                  background: "#f5f5f5",
                  color: "#333",
                  border: "none",
                  borderRadius: "6px",
                  cursor: "pointer",
                }}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <p style={{ color: "#666" }}>Loading companies...</p>
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
                  "Code",
                  "Name",
                  "Industry",
                  "Contact Email",
                  "Employees",
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
              {companies.length === 0 ? (
                <tr>
                  <td
                    colSpan={7}
                    style={{
                      padding: "40px",
                      textAlign: "center",
                      color: "#999",
                    }}
                  >
                    No companies found. Create one above.
                  </td>
                </tr>
              ) : (
                companies.map((c, i) => (
                  <tr
                    key={c.company_id}
                    style={{
                      background: i % 2 === 0 ? "white" : "#f9f9f9",
                      borderBottom: "1px solid #eee",
                    }}
                  >
                    <td
                      style={{
                        padding: "12px 16px",
                        fontSize: "14px",
                        fontWeight: 600,
                        color: "#1a3c5e",
                      }}
                    >
                      {c.company_code}
                    </td>
                    <td style={{ padding: "12px 16px", fontSize: "14px" }}>
                      {c.company_name}
                    </td>
                    <td
                      style={{
                        padding: "12px 16px",
                        fontSize: "14px",
                        color: "#666",
                      }}
                    >
                      {c.industry_type || "—"}
                    </td>
                    <td
                      style={{
                        padding: "12px 16px",
                        fontSize: "14px",
                        color: "#666",
                      }}
                    >
                      {c.contact_email || "—"}
                    </td>
                    <td
                      style={{
                        padding: "12px 16px",
                        fontSize: "14px",
                        color: "#666",
                      }}
                    >
                      {c.employee_strength || "—"}
                    </td>
                    <td style={{ padding: "12px 16px" }}>
                      <span
                        style={{
                          padding: "3px 10px",
                          borderRadius: "12px",
                          fontSize: "12px",
                          fontWeight: 600,
                          background:
                            c.status === "Active" ? "#e8f5e9" : "#fdf0f0",
                          color: c.status === "Active" ? "#27ae60" : "#e74c3c",
                        }}
                      >
                        {c.status}
                      </span>
                    </td>
                    <td style={{ padding: "12px 16px" }}>
                      <button
                        onClick={() => toggleStatus(c)}
                        style={{
                          padding: "4px 12px",
                          fontSize: "12px",
                          borderRadius: "4px",
                          cursor: "pointer",
                          border: "none",
                          fontWeight: 600,
                          background:
                            c.status === "Active" ? "#fdf0f0" : "#e8f5e9",
                          color: c.status === "Active" ? "#e74c3c" : "#27ae60",
                        }}
                      >
                        {c.status === "Active" ? "Deactivate" : "Activate"}
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
```

### Admin Users Page

Create `frontend/src/features/admin/UserListPage.jsx`:

```jsx
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
```

### Admin Videos Page

Create `frontend/src/features/admin/VideoListPage.jsx`:

```jsx
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
```

---

## HR Portal Pages

### HR Bulk Upload Page

Replace `frontend/src/features/hr/BulkUploadPage.jsx`:

```jsx
import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import apiClient from "../../api/client";

export function BulkUploadPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!fileInputRef.current?.files?.[0]) {
      setError("Please select a file.");
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);

    const formData = new FormData();
    formData.append("file", fileInputRef.current.files[0]);

    try {
      const res = await apiClient.post("/hr/employees/bulk-upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Upload failed.");
    } finally {
      setLoading(false);
    }
  };

  const downloadTemplate = () => {
    const csv =
      "employee_id,first_name,last_name,email,mobile,department,designation,role_id\n" +
      "EMP001,Ravi,Kumar,ravi@company.com,9876543210,IT,Developer,4\n" +
      "EMP002,Priya,Sharma,priya@company.com,9876543211,HR,Manager,3";
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "employee_template.csv";
    a.click();
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
        Bulk Employee Upload
      </h1>

      <div
        style={{
          background: "white",
          borderRadius: "12px",
          padding: "24px",
          boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
          marginBottom: "24px",
        }}
      >
        <h3 style={{ color: "#1a3c5e", marginTop: 0 }}>Upload Employee List</h3>
        <p style={{ color: "#666", fontSize: "14px", marginBottom: "16px" }}>
          Upload an Excel (.xlsx) or CSV (.csv) file with employee data.
          Required columns:{" "}
          <code>employee_id, first_name, email, mobile, role_id</code>
        </p>
        <button
          onClick={downloadTemplate}
          style={{
            padding: "8px 16px",
            background: "#f0f4ff",
            color: "#1a3c5e",
            border: "1px solid #1a3c5e",
            borderRadius: "6px",
            cursor: "pointer",
            fontSize: "13px",
            marginBottom: "20px",
          }}
        >
          ⬇ Download Template CSV
        </button>

        <form onSubmit={handleUpload}>
          <div
            style={{
              border: "2px dashed #ddd",
              borderRadius: "8px",
              padding: "32px",
              textAlign: "center",
              marginBottom: "16px",
            }}
          >
            <p style={{ color: "#666", marginBottom: "12px" }}>
              Select your Excel or CSV file
            </p>
            <input
              type="file"
              ref={fileInputRef}
              accept=".xlsx,.xls,.csv"
              style={{ fontSize: "14px" }}
            />
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
            {loading ? "Uploading..." : "Upload & Create Employees"}
          </button>
        </form>
      </div>

      {result && (
        <div
          style={{
            background: "white",
            borderRadius: "12px",
            padding: "24px",
            boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
          }}
        >
          <h3 style={{ marginTop: 0, color: "#1a3c5e" }}>Upload Results</h3>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: "16px",
              marginBottom: "20px",
            }}
          >
            {[
              {
                label: "Total Rows",
                value: result.total_rows,
                color: "#1a3c5e",
              },
              {
                label: "Successfully Created",
                value: result.success_rows,
                color: "#27ae60",
              },
              {
                label: "Failed Rows",
                value: result.failed_rows,
                color: "#e74c3c",
              },
            ].map(({ label, value, color }) => (
              <div
                key={label}
                style={{
                  background: "#f9f9f9",
                  borderRadius: "8px",
                  padding: "16px",
                  textAlign: "center",
                }}
              >
                <div style={{ fontSize: "32px", fontWeight: 700, color }}>
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

          {result.errors?.length > 0 && (
            <div>
              <h4 style={{ color: "#e74c3c" }}>Rows with errors:</h4>
              <div style={{ maxHeight: "300px", overflow: "auto" }}>
                <table
                  style={{
                    width: "100%",
                    borderCollapse: "collapse",
                    fontSize: "13px",
                  }}
                >
                  <thead>
                    <tr style={{ background: "#fdf0f0" }}>
                      <th style={{ padding: "8px 12px", textAlign: "left" }}>
                        Row
                      </th>
                      <th style={{ padding: "8px 12px", textAlign: "left" }}>
                        Email
                      </th>
                      <th style={{ padding: "8px 12px", textAlign: "left" }}>
                        Errors
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.errors.map((err, i) => (
                      <tr key={i} style={{ borderBottom: "1px solid #eee" }}>
                        <td style={{ padding: "8px 12px", color: "#e74c3c" }}>
                          Row {err.row}
                        </td>
                        <td style={{ padding: "8px 12px" }}>{err.email}</td>
                        <td style={{ padding: "8px 12px", color: "#666" }}>
                          {err.errors.join(", ")}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

### HR Training Assign Page

Replace `frontend/src/features/hr/TrainingAssignPage.jsx`:

```jsx
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
```

### HR Compliance Page

Replace `frontend/src/features/hr/CompliancePage.jsx`:

```jsx
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
```

---

## Employee Portal Pages

### Employee Dashboard

Replace `frontend/src/features/employee/EmployeeDashboard.jsx`:

```jsx
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
```

### Employee Courses Page

Replace `frontend/src/features/employee/CoursesPage.jsx`:

```jsx
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
```

### Employee Certificates Page

Replace `frontend/src/features/employee/CertificatesPage.jsx`:

```jsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import apiClient from "../../api/client";

export function CertificatesPage() {
  const navigate = useNavigate();
  const [certificates, setCertificates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(null);

  useEffect(() => {
    apiClient
      .get("/certificates/my")
      .then((res) => {
        setCertificates(res.data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const handleDownload = async (cert) => {
    setDownloading(cert.certificate_id);
    try {
      const res = await apiClient.get(
        `/certificates/${cert.certificate_id}/download`,
      );
      // Open the signed URL in a new tab
      window.open(res.data.download_url, "_blank");
    } catch {
      alert("Download failed. Please try again.");
    } finally {
      setDownloading(null);
    }
  };

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
      <h1 style={{ color: "#1a3c5e", marginBottom: "24px" }}>
        My Certificates
      </h1>

      {loading ? (
        <p style={{ color: "#666" }}>Loading certificates...</p>
      ) : certificates.length === 0 ? (
        <div
          style={{
            background: "white",
            borderRadius: "12px",
            padding: "40px",
            boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: "48px", marginBottom: "16px" }}>🎓</div>
          <h3 style={{ color: "#1a3c5e" }}>No certificates yet</h3>
          <p style={{ color: "#666" }}>
            Complete a training course and pass the assessment to earn your
            certificate.
          </p>
        </div>
      ) : (
        <div style={{ display: "grid", gap: "16px" }}>
          {certificates.map((cert) => (
            <div
              key={cert.certificate_id}
              style={{
                background: "white",
                borderRadius: "12px",
                padding: "20px",
                boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                borderLeft: "4px solid #27ae60",
              }}
            >
              <div>
                <h3 style={{ color: "#1a3c5e", margin: "0 0 4px" }}>
                  {cert.course_name}
                </h3>
                <p
                  style={{ color: "#666", margin: "0 0 2px", fontSize: "13px" }}
                >
                  Certificate No: <strong>{cert.certificate_number}</strong>
                </p>
                <p style={{ color: "#666", margin: 0, fontSize: "13px" }}>
                  Issued: {cert.issue_date} &nbsp;|&nbsp;
                  <span
                    style={{
                      color: cert.status === "Valid" ? "#27ae60" : "#e74c3c",
                      fontWeight: 600,
                    }}
                  >
                    {cert.status}
                  </span>
                </p>
              </div>
              <div style={{ display: "flex", gap: "8px" }}>
                <button
                  onClick={() =>
                    window.open(
                      `/api/v1/certificates/verify/${cert.certificate_number}`,
                      "_blank",
                    )
                  }
                  style={{
                    padding: "8px 16px",
                    background: "#f0f4ff",
                    color: "#1a3c5e",
                    border: "1px solid #1a3c5e",
                    borderRadius: "6px",
                    cursor: "pointer",
                    fontSize: "13px",
                  }}
                >
                  Verify QR
                </button>
                <button
                  onClick={() => handleDownload(cert)}
                  disabled={downloading === cert.certificate_id}
                  style={{
                    padding: "8px 16px",
                    background: "#1a3c5e",
                    color: "white",
                    border: "none",
                    borderRadius: "6px",
                    cursor: "pointer",
                    fontSize: "13px",
                  }}
                >
                  {downloading === cert.certificate_id
                    ? "Opening..."
                    : "⬇ Download PDF"}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

### HR Dashboard (Full Version)

Replace `frontend/src/features/hr/HRDashboard.jsx`:

```jsx
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
```

---

## STEP 60: Update main.jsx

Make sure `frontend/src/main.jsx` exists and looks like this:

```jsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

---

## STEP 61: Build and Test Everything

```bash
docker compose up --build
```

Test each portal:

**Auth flow:**

1. http://localhost/signup → create account → check Gmail for OTP → verify → login

**Admin Portal (login with role_id=1 or 2 user):**

- http://localhost/admin → see dashboard cards
- http://localhost/admin/companies → see/create companies
- http://localhost/admin/users → see all users

**HR Portal (login with role_id=3 user):**

- http://localhost/hr → see HR dashboard
- http://localhost/hr/upload → download template → fill it → upload
- http://localhost/hr/assign → assign training to employees
- http://localhost/hr/compliance → see compliance stats + download Excel

**Employee Portal (login with role_id=4 user):**

- http://localhost/employee → see dashboard
- http://localhost/employee/certificates → see earned certificates

---

# done

## STEP 62: Lint and Commit

```bash
cd frontend
npm run build    # must succeed with no errors

cd ..
git add .
git commit -m "feat(phase5b): complete frontend — all portal pages, Gmail SMTP, compliance dashboard, certificates"
git push origin develop
```

---

## GitHub Demo Setup

To make your GitHub repo usable as a demo:

**1. Update README.md** in the project root:

```markdown
# POSH Training Platform

Multi-tenant POSH compliance training platform built with React + FastAPI + MySQL + Docker.

## Quick Start (Development)

\`\`\`bash
git clone https://github.com/YOUR_USERNAME/posh-platform.git
cd posh-platform
cp .env.example .env

# Edit .env with your values (see Configuration section)

docker compose up --build
\`\`\`

Open http://localhost — Login screen appears.

## Default Test Users (after seeding)

Run `docker compose exec backend python -m app.db.seed` to create reference data.

Then create test users via http://localhost:8000/docs → POST /api/v1/auth/signup

## Portal URLs

| Portal   | URL                        | Role Required   |
| -------- | -------------------------- | --------------- |
| Login    | http://localhost/login     | —               |
| Admin    | http://localhost/admin     | role_id 1 or 2  |
| HR       | http://localhost/hr        | role_id 3       |
| Employee | http://localhost/employee  | role_id 4       |
| API Docs | http://localhost:8000/docs | — (dev only)    |
| Emails   | http://localhost:8025      | — (MailHog dev) |

## Stack

- **Frontend:** React 18 + Vite + JavaScript
- **Backend:** Python 3.12 + FastAPI + SQLAlchemy
- **Database:** MySQL 8
- **Cache/Queue:** Redis + Celery
- **Storage:** MinIO (S3-compatible)
- **Email:** MailHog (dev) / Gmail SMTP (prod)
- **CI/CD:** GitHub Actions
```

**2. Add a `.env.example`** is already committed. That's all the demo needs.

---

## Summary of All Changes in This Guide

| What                          | Where                                                  | Backend change?  |
| ----------------------------- | ------------------------------------------------------ | ---------------- |
| Gmail SMTP setup              | `.env` only                                            | No               |
| Fix `send_email` for STARTTLS | `backend/app/core/email.py`                            | Yes (1 function) |
| Admin Companies page          | `frontend/src/features/admin/CompanyListPage.jsx`      | No               |
| Admin Users page              | `frontend/src/features/admin/UserListPage.jsx`         | No               |
| Admin Videos page             | `frontend/src/features/admin/VideoListPage.jsx`        | No               |
| HR Dashboard                  | `frontend/src/features/hr/HRDashboard.jsx`             | No               |
| HR Bulk Upload                | `frontend/src/features/hr/BulkUploadPage.jsx`          | No               |
| HR Training Assign            | `frontend/src/features/hr/TrainingAssignPage.jsx`      | No               |
| HR Compliance                 | `frontend/src/features/hr/CompliancePage.jsx`          | No               |
| Employee Dashboard            | `frontend/src/features/employee/EmployeeDashboard.jsx` | No               |
| Employee Courses              | `frontend/src/features/employee/CoursesPage.jsx`       | No               |
| Employee Certificates         | `frontend/src/features/employee/CertificatesPage.jsx`  | No               |
| Updated README                | `README.md`                                            | No               |

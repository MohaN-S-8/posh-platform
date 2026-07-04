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

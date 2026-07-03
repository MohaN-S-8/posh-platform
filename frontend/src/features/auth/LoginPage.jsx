import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useNavigate, Link } from "react-router-dom";
import { authApi } from "../../api/auth";
import { useAuthStore } from "../../store/authStore";

// Mirror backend validation exactly
const loginSchema = z.object({
  email: z
    .string()
    .min(1, "Email is required")
    .email("Invalid email format")
    .max(25, "Email must be at most 25 characters")
    .transform((v) => v.trim().toLowerCase()),
  password: z
    .string()
    .min(8, "Minimum 8 characters")
    .max(15, "Maximum 15 characters"),
});

export function LoginPage() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
  } = useForm({
    resolver: zodResolver(loginSchema),
    mode: "onChange",
  });

  const onSubmit = async (data) => {
    setLoading(true);
    setError("");
    try {
      const res = await authApi.login(data);
      const { access_token, user_id, role_id, company_id } = res.data;
      setAuth({ user_id, role_id, company_id }, access_token);

      // Redirect based on role
      if (role_id === 1 || role_id === 2) navigate("/admin");
      else if (role_id === 3) navigate("/hr");
      else navigate("/employee");
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (err.response?.status === 423) {
        setError(detail || "Account locked. Try again later.");
      } else {
        setError(detail || "Invalid email or password.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#f5f7fa",
      }}
    >
      <div
        style={{
          background: "white",
          padding: "40px",
          borderRadius: "12px",
          boxShadow: "0 4px 24px rgba(0,0,0,0.08)",
          width: "100%",
          maxWidth: "420px",
        }}
      >
        <h1
          style={{ color: "#1a3c5e", marginBottom: "8px", textAlign: "center" }}
        >
          POSH Training Platform
        </h1>
        <p
          style={{
            color: "#666",
            textAlign: "center",
            marginBottom: "32px",
          }}
        >
          Sign in to your account
        </p>

        <form onSubmit={handleSubmit(onSubmit)}>
          {/* Email field */}
          <div style={{ marginBottom: "20px" }}>
            <label
              htmlFor="email"
              style={{ display: "block", marginBottom: "6px", fontWeight: 500 }}
            >
              Email Address *
            </label>
            <input
              id="email"
              type="email"
              {...register("email")}
              placeholder="you@company.com"
              aria-describedby={errors.email ? "email-error" : undefined}
              style={{
                width: "100%",
                padding: "10px 14px",
                border: `1px solid ${errors.email ? "#e74c3c" : "#ddd"}`,
                borderRadius: "6px",
                fontSize: "14px",
                boxSizing: "border-box",
              }}
            />
            {errors.email && (
              <p
                id="email-error"
                role="alert"
                style={{ color: "#e74c3c", fontSize: "12px", marginTop: "4px" }}
              >
                {errors.email.message}
              </p>
            )}
          </div>

          {/* Password field */}
          <div style={{ marginBottom: "20px" }}>
            <label
              htmlFor="password"
              style={{ display: "block", marginBottom: "6px", fontWeight: 500 }}
            >
              Password *
            </label>
            <div style={{ position: "relative" }}>
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                {...register("password")}
                placeholder="Your password"
                style={{
                  width: "100%",
                  padding: "10px 44px 10px 14px",
                  border: `1px solid ${errors.password ? "#e74c3c" : "#ddd"}`,
                  borderRadius: "6px",
                  fontSize: "14px",
                  boxSizing: "border-box",
                }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? "Hide password" : "Show password"}
                style={{
                  position: "absolute",
                  right: "12px",
                  top: "50%",
                  transform: "translateY(-50%)",
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  color: "#666",
                }}
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
            {errors.password && (
              <p
                style={{ color: "#e74c3c", fontSize: "12px", marginTop: "4px" }}
              >
                {errors.password.message}
              </p>
            )}
          </div>

          {/* Global error */}
          {error && (
            <div
              role="alert"
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

          {/* Submit button — disabled until form valid */}
          <button
            type="submit"
            disabled={!isValid || loading}
            style={{
              width: "100%",
              padding: "12px",
              background: !isValid || loading ? "#93b8d4" : "#1a3c5e",
              color: "white",
              border: "none",
              borderRadius: "6px",
              fontSize: "16px",
              fontWeight: 600,
              cursor: !isValid || loading ? "not-allowed" : "pointer",
              transition: "background 0.2s",
            }}
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <div style={{ textAlign: "center", marginTop: "20px" }}>
          <Link
            to="/forgot-password"
            style={{ color: "#1a3c5e", fontSize: "14px" }}
          >
            Forgot password?
          </Link>
        </div>
        <div style={{ textAlign: "center", marginTop: "12px" }}>
          <span style={{ fontSize: "14px", color: "#666" }}>
            Don`&#39;t have an account?{" "}
            <Link to="/signup" style={{ color: "#1a3c5e", fontWeight: 600 }}>
              Sign up
            </Link>
          </span>
        </div>
      </div>
    </div>
  );
}

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useNavigate, Link } from "react-router-dom";
import { authApi } from "../../api/auth";

const signupSchema = z
  .object({
    first_name: z
      .string()
      .min(2, "Minimum 2 characters")
      .max(50, "Maximum 50 characters")
      .regex(/^[a-zA-Z\s]+$/, "Only letters allowed"),
    last_name: z.string().regex(/^[a-zA-Z\s]*$/, "Only letters allowed"),
    email: z
      .string()
      .min(1, "Email is required")
      .email("Invalid email format")
      .max(25, "Maximum 25 characters"),
    password: z
      .string()
      .min(8, "Minimum 8 characters")
      .max(15, "Maximum 15 characters")
      .regex(/[A-Z]/, "Must contain uppercase letter")
      .regex(/[a-z]/, "Must contain lowercase letter")
      .regex(/[0-9]/, "Must contain a number")
      .regex(/[!@#$%^&*(),.?":{}|<>]/, "Must contain special character"),
    confirm_password: z.string().min(1, "Please confirm password"),
    mobile: z.string().regex(/^\d{10}$/, "Must be exactly 10 digits"),
  })
  .refine((d) => d.password === d.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

export function SignupPage() {
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
  } = useForm({
    resolver: zodResolver(signupSchema),
    mode: "onChange",
  });

  const onSubmit = async (data) => {
    setLoading(true);
    setError("");
    try {
      await authApi.signup(data);
      // Navigate to OTP page with email in state
      navigate("/verify-otp", { state: { email: data.email } });
    } catch (err) {
      setError(
        err.response?.data?.detail || "Signup failed. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  };

  const inputStyle = (hasError) => ({
    width: "100%",
    padding: "10px 14px",
    border: `1px solid ${hasError ? "#e74c3c" : "#ddd"}`,
    borderRadius: "6px",
    fontSize: "14px",
    boxSizing: "border-box",
  });

  const errorStyle = {
    color: "#e74c3c",
    fontSize: "12px",
    marginTop: "4px",
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#f5f7fa",
        padding: "20px",
      }}
    >
      <div
        style={{
          background: "white",
          padding: "40px",
          borderRadius: "12px",
          boxShadow: "0 4px 24px rgba(0,0,0,0.08)",
          width: "100%",
          maxWidth: "480px",
        }}
      >
        <h1
          style={{ color: "#1a3c5e", marginBottom: "8px", textAlign: "center" }}
        >
          Create Account
        </h1>
        <p style={{ color: "#666", textAlign: "center", marginBottom: "32px" }}>
          Join POSH Training Platform
        </p>

        <form onSubmit={handleSubmit(onSubmit)}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "16px",
            }}
          >
            <div>
              <label
                style={{
                  display: "block",
                  marginBottom: "6px",
                  fontWeight: 500,
                }}
              >
                First Name *
              </label>
              <input
                {...register("first_name")}
                style={inputStyle(!!errors.first_name)}
              />
              {errors.first_name && (
                <p style={errorStyle}>{errors.first_name.message}</p>
              )}
            </div>
            <div>
              <label
                style={{
                  display: "block",
                  marginBottom: "6px",
                  fontWeight: 500,
                }}
              >
                Last Name
              </label>
              <input
                {...register("last_name")}
                style={inputStyle(!!errors.last_name)}
              />
              {errors.last_name && (
                <p style={errorStyle}>{errors.last_name.message}</p>
              )}
            </div>
          </div>

          <div style={{ marginTop: "16px" }}>
            <label
              style={{ display: "block", marginBottom: "6px", fontWeight: 500 }}
            >
              Email Address *
            </label>
            <input
              type="email"
              {...register("email")}
              style={inputStyle(!!errors.email)}
            />
            {errors.email && <p style={errorStyle}>{errors.email.message}</p>}
          </div>

          <div style={{ marginTop: "16px" }}>
            <label
              style={{ display: "block", marginBottom: "6px", fontWeight: 500 }}
            >
              Mobile Number *
            </label>
            <input
              type="tel"
              {...register("mobile")}
              placeholder="10 digit number"
              style={inputStyle(!!errors.mobile)}
            />
            {errors.mobile && <p style={errorStyle}>{errors.mobile.message}</p>}
          </div>

          <div style={{ marginTop: "16px" }}>
            <label
              style={{ display: "block", marginBottom: "6px", fontWeight: 500 }}
            >
              Password *
            </label>
            <input
              type="password"
              {...register("password")}
              style={inputStyle(!!errors.password)}
            />
            {errors.password && (
              <p style={errorStyle}>{errors.password.message}</p>
            )}
            <p style={{ fontSize: "11px", color: "#999", marginTop: "4px" }}>
              8–15 characters, uppercase, lowercase, number, special character
            </p>
          </div>

          <div style={{ marginTop: "16px" }}>
            <label
              style={{ display: "block", marginBottom: "6px", fontWeight: 500 }}
            >
              Confirm Password *
            </label>
            <input
              type="password"
              {...register("confirm_password")}
              style={inputStyle(!!errors.confirm_password)}
            />
            {errors.confirm_password && (
              <p style={errorStyle}>{errors.confirm_password.message}</p>
            )}
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
                marginTop: "16px",
              }}
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={!isValid || loading}
            style={{
              width: "100%",
              padding: "12px",
              marginTop: "24px",
              background: !isValid || loading ? "#93b8d4" : "#1a3c5e",
              color: "white",
              border: "none",
              borderRadius: "6px",
              fontSize: "16px",
              fontWeight: 600,
              cursor: !isValid || loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "Creating account..." : "Create Account"}
          </button>
        </form>

        <div style={{ textAlign: "center", marginTop: "20px" }}>
          <span style={{ fontSize: "14px", color: "#666" }}>
            Already have an account?{" "}
            <Link to="/login" style={{ color: "#1a3c5e", fontWeight: 600 }}>
              Sign in
            </Link>
          </span>
        </div>
      </div>
    </div>
  );
}

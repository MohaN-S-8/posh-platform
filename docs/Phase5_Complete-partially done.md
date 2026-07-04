# Phase 5 — Complete Guide: Gaps + Frontend + Security + Deployment

## Where You Are

| Phase                                | Status           |
| ------------------------------------ | ---------------- |
| Phase 0 — Foundations                | ✅ Complete      |
| Phase 1 — Auth + User Management     | ✅ Complete      |
| Phase 2 — Video + Assessments        | ✅ Complete      |
| Phase 3 — HR Portal                  | ✅ Complete      |
| Phase 4 — Certificates + Analytics   | ✅ Complete      |
| **Phase 5A — Close Backend Gaps**    | ⬜ This document |
| **Phase 5B — React Frontend**        | ⬜ This document |
| **Phase 5C — Security Hardening**    | ⬜ This document |
| **Phase 5D — Production Deployment** | ⬜ This document |

## All Known Gaps to Fix

| File                              | Gap                                      | Fix in Step |
| --------------------------------- | ---------------------------------------- | ----------- |
| `auth_service.py` signup          | `dev_otp` returned in response           | Step 46     |
| `auth_service.py` forgot_password | `dev_reset_token` in response            | Step 46     |
| `user_service.py` create          | Hardcoded `Temp@1234` password           | Step 46     |
| `assessment_service.py`           | Certificate generated inline, not Celery | Step 47     |
| `auth_service.py` signup          | OTP email never actually sent            | Step 46     |
| `user_service.py` create          | Welcome email never sent                 | Step 46     |

---

# PHASE 5A — CLOSE BACKEND GAPS

---

## STEP 46: Real Email Sending via SMTP

### 46.1 Create Email Utility

Create `backend/app/core/email.py`:

```python
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

SMTP_HOST = os.environ.get("SMTP_HOST", "mailhog")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 1025))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
EMAILS_FROM = os.environ.get("EMAILS_FROM", "noreply@posh-platform.com")
APP_ENV = os.environ.get("APP_ENV", "development")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:80")


async def send_email(to: str, subject: str, html_body: str) -> None:
    """
    Send an email via SMTP.
    In development: goes to MailHog (http://localhost:8025)
    In production: goes to real SMTP (configure SMTP_HOST, SMTP_USER, SMTP_PASSWORD)
    """
    message = MIMEMultipart("alternative")
    message["From"] = EMAILS_FROM
    message["To"] = to
    message["Subject"] = subject
    message.attach(MIMEText(html_body, "html"))

    # Use TLS for production SMTP, plain for MailHog
    use_tls = APP_ENV == "production"

    await aiosmtplib.send(
        message,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        username=SMTP_USER if SMTP_USER else None,
        password=SMTP_PASSWORD if SMTP_PASSWORD else None,
        use_tls=use_tls,
    )


async def send_otp_email(to: str, first_name: str, otp: str) -> None:
    """Send OTP verification email."""
    subject = "Your POSH Platform Verification Code"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #1a3c5e;">POSH Training Platform</h2>
        <p>Dear {first_name},</p>
        <p>Your verification code is:</p>
        <div style="background: #f5f5f5; padding: 20px; text-align: center;
                    font-size: 36px; font-weight: bold; letter-spacing: 10px;
                    color: #1a3c5e; border-radius: 8px; margin: 20px 0;">
            {otp}
        </div>
        <p>This code expires in <strong>10 minutes</strong>.</p>
        <p>If you did not request this, please ignore this email.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #999; font-size: 12px;">POSH Training Platform</p>
    </div>
    """
    await send_email(to, subject, html)


async def send_password_reset_email(
    to: str, first_name: str, reset_token: str
) -> None:
    """Send password reset email with a link."""
    reset_url = f"{FRONTEND_URL}/reset-password?token={reset_token}"
    subject = "Reset Your POSH Platform Password"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #1a3c5e;">Password Reset Request</h2>
        <p>Dear {first_name},</p>
        <p>Click the button below to reset your password.
           This link expires in <strong>1 hour</strong>.</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}"
               style="background: #1a3c5e; color: white; padding: 14px 28px;
                      text-decoration: none; border-radius: 6px; font-size: 16px;">
                Reset Password
            </a>
        </div>
        <p>Or copy this link: <a href="{reset_url}">{reset_url}</a></p>
        <p>If you did not request a password reset, please ignore this email.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #999; font-size: 12px;">POSH Training Platform</p>
    </div>
    """
    await send_email(to, subject, html)


async def send_welcome_email(
    to: str, first_name: str, temp_password: str
) -> None:
    """Send welcome email with temporary password to new employee."""
    login_url = f"{FRONTEND_URL}/login"
    subject = "Welcome to POSH Training Platform"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #1a3c5e;">Welcome to POSH Training Platform</h2>
        <p>Dear {first_name},</p>
        <p>Your account has been created. Please log in using the details below
           and change your password immediately.</p>
        <div style="background: #f5f5f5; padding: 20px; border-radius: 8px;
                    margin: 20px 0;">
            <p><strong>Login URL:</strong>
               <a href="{login_url}">{login_url}</a></p>
            <p><strong>Email:</strong> {to}</p>
            <p><strong>Temporary Password:</strong>
               <code style="background: #e8e8e8; padding: 4px 8px;
                            border-radius: 4px;">{temp_password}</code></p>
        </div>
        <p style="color: #e74c3c;">
            ⚠️ Please change your password after first login.
        </p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #999; font-size: 12px;">POSH Training Platform</p>
    </div>
    """
    await send_email(to, subject, html)


async def send_certificate_email(
    to: str,
    first_name: str,
    course_name: str,
    cert_number: str,
    pdf_bytes: bytes,
) -> None:
    """Send certificate email with PDF attachment."""
    from email.mime.application import MIMEApplication

    subject = f"Your POSH Training Certificate — {course_name}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #1a3c5e;">🎉 Congratulations!</h2>
        <p>Dear {first_name},</p>
        <p>You have successfully completed the POSH training course
           <strong>{course_name}</strong>.</p>
        <p>Your certificate is attached to this email.</p>
        <div style="background: #f5f5f5; padding: 20px; border-radius: 8px;
                    margin: 20px 0;">
            <p><strong>Certificate Number:</strong> {cert_number}</p>
        </div>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #999; font-size: 12px;">POSH Training Platform</p>
    </div>
    """

    # Build message with PDF attachment
    message = MIMEMultipart("mixed")
    message["From"] = EMAILS_FROM
    message["To"] = to
    message["Subject"] = subject
    message.attach(MIMEText(html, "html"))

    attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
    attachment.add_header(
        "Content-Disposition",
        "attachment",
        filename=f"certificate_{cert_number}.pdf",
    )
    message.attach(attachment)

    use_tls = APP_ENV == "production"

    await aiosmtplib.send(
        message,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        username=SMTP_USER if SMTP_USER else None,
        password=SMTP_PASSWORD if SMTP_PASSWORD else None,
        use_tls=use_tls,
    )
```

### 46.2 Fix Signup — Remove dev_otp, Send Real Email

Update `backend/app/services/auth_service.py` signup method.

Replace this block:

```python
        # TODO: Send email with reset link (Celery task in Phase 3)
        return {
            "message": "OTP sent to your email. Please verify to complete registration.",
            "dev_otp": raw_otp,  # REMOVE IN PRODUCTION
        }
```

With this:

```python
        # Send OTP via email
        from app.core.email import send_otp_email

        try:
            await send_otp_email(
                to=data.email.lower(),
                first_name=data.first_name,
                otp=raw_otp,
            )
        except Exception:
            # Don't expose email errors to the client
            pass  # MailHog may not be running in some environments

        return {
            "message": "OTP sent to your email. Please verify to complete registration."
            # raw_otp is NOT returned anymore
        }
```

### 46.3 Fix Forgot Password — Remove dev_reset_token, Send Real Email

In the same file, replace:

```python
        return {
            "message": "If this email is registered, you will receive reset instructions.",
            "dev_reset_token": raw_token,  # REMOVE IN PRODUCTION
        }
```

With:

```python
        from app.core.email import send_password_reset_email

        try:
            await send_password_reset_email(
                to=user.email,
                first_name=user.first_name,
                reset_token=raw_token,
            )
        except Exception:
            pass

        return {
            "message": "If this email is registered, you will receive reset instructions."
        }
```

### 46.4 Fix User Creation — Send Welcome Email

In `backend/app/services/user_service.py` create method, replace:

```python
        temp_password = "Temp@1234"  # TODO: send via email in Phase 3
```

With:

```python
        import secrets
        import string

        # Generate a secure random temporary password
        alphabet = string.ascii_letters + string.digits + "!@#$"
        temp_password = (
            secrets.choice(string.ascii_uppercase)
            + secrets.choice(string.digits)
            + secrets.choice("!@#$")
            + "".join(secrets.choice(alphabet) for _ in range(9))
        )
```

And after `await db.commit()`, add:

```python
        # Send welcome email with temporary password
        from app.core.email import send_welcome_email

        try:
            await send_welcome_email(
                to=user.email,
                first_name=user.first_name,
                temp_password=temp_password,
            )
        except Exception:
            pass  # Don't fail user creation if email fails
```

### 46.5 Fix Certificate Service — Send Email After Generation

In `backend/app/services/certificate_service.py`, at the end of `generate_certificate`, before `return certificate`:

```python
        # Send certificate email with PDF attachment
        from app.core.email import send_certificate_email

        try:
            await send_certificate_email(
                to=user.email,
                first_name=user.first_name,
                course_name=video.title,
                cert_number=cert_number,
                pdf_bytes=pdf_bytes,
            )
        except Exception:
            pass  # Don't fail certificate generation if email fails
```

### 46.6 Test Email is Working

Make sure Docker is running, then:

```bash
docker compose up -d mailhog
```

Test signup via Swagger → go to http://localhost:8025 → you should see the OTP email arrive in MailHog inbox.

---

## STEP 47: Move Certificate Generation to Celery

Right now certificate generation happens inline during assessment submission. For large companies this could take 3–5 seconds and block the response. Move it to a background task.

### 47.1 Create the Celery Task

Update `backend/app/workers/celery_app.py`:

```python
import os

from celery import Celery

celery_app = Celery(
    "posh_worker",
    broker=os.environ.get("REDIS_URL", "redis://redis:6379/0"),
    backend=os.environ.get("REDIS_URL", "redis://redis:6379/0"),
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
)


@celery_app.task(bind=True, max_retries=3)
def generate_certificate_task(self, user_id: int, video_id: int, company_id: int):
    """
    Background task: generate certificate after assessment pass.
    Retries up to 3 times if it fails (network issues, DB timeouts etc.)
    """
    import asyncio

    from app.db.session import AsyncSessionLocal
    from app.services.certificate_service import CertificateService

    async def _run():
        async with AsyncSessionLocal() as db:
            service = CertificateService()
            await service.generate_certificate(db, user_id, video_id, company_id)

    try:
        asyncio.run(_run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)  # retry after 60 seconds
```

### 47.2 Update Assessment Service to Use Celery

In `backend/app/services/assessment_service.py`, replace the inline certificate generation:

```python
        # 5. Trigger certificate generation on Pass (via Celery background task)
        if result == "Pass":
            from app.workers.celery_app import generate_certificate_task

            # .delay() sends it to the Celery queue — returns immediately
            generate_certificate_task.delay(user_id, data.video_id, company_id)
            response["message"] = (
                "Congratulations! You passed. "
                "Your certificate is being generated and will be emailed to you."
            )
        else:
            response["message"] = (
                f"Score: {score:.1f}%. "
                f"You need {passing_score}% to pass. Please retry."
            )
```

### 47.3 Verify Celery Worker is Running

```bash
docker compose logs celery-worker
# Should show: [tasks]
#   . app.workers.celery_app.generate_certificate_task
# [2026-07-03 ...] celery@... ready.
```

---

## STEP 48: Add FRONTEND_URL to Config

Update `backend/app/core/config.py` — add one field:

```python
class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+asyncmy://posh_user:password@mysql:3306/posh_db"
    REDIS_URL: str = "redis://redis:6379/0"
    JWT_SECRET_KEY: str = "change-this-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:80"]
    APP_ENV: str = "development"
    FRONTEND_URL: str = "http://localhost:80"   # ← add this

    class Config:
        env_file = ".env"
        case_sensitive = True
```

Add to `.env`:

```
FRONTEND_URL=http://localhost:80
```

---

## STEP 49: Lint, Test, Commit Phase 5A

```bash
cd backend
black .
ruff check --fix .
ruff check .
pytest tests/ -v
cd ..

git add .
git commit -m "feat(phase5a): real email delivery, Celery certificate generation, remove dev tokens"
git push origin develop
```

---

# PHASE 5B — REACT FRONTEND

The frontend calls all the APIs you built. We'll build each portal screen by screen.

---

## STEP 50: Frontend Project Structure

Your `frontend/src/` should be organized like this. Create missing folders:

```
frontend/src/
├── api/                    ← all API call functions
│   ├── auth.ts
│   ├── company.ts
│   ├── users.ts
│   ├── videos.ts
│   ├── hr.ts
│   └── certificates.ts
├── components/
│   ├── ui/                 ← shared: Button, Input, Modal, Table
│   └── layout/             ← Navbar, Sidebar, PageWrapper
├── features/
│   ├── auth/               ← Login, Signup, OTP, ForgotPassword screens
│   ├── admin/              ← Admin portal screens
│   ├── hr/                 ← HR portal screens
│   └── employee/           ← Employee portal screens
├── hooks/
│   ├── useAuth.ts          ← auth state management
│   └── useCurrentUser.ts
├── routes/
│   ├── ProtectedRoute.tsx
│   └── RoleRoute.tsx
├── store/
│   └── authStore.ts        ← Zustand store for auth
├── i18n/
│   ├── en.json
│   ├── hi.json
│   └── ta.json
├── App.tsx
└── main.tsx
```

Run this to create the folders:

```bash
cd frontend/src
mkdir api, components/ui, components/layout, features/auth, features/admin, features/hr, features/employee, hooks, routes, store, i18n
```

---

## STEP 51: Set Up Axios API Client

Create `frontend/src/api/client.ts`:

```typescript
import axios from "axios";

// All API calls go through this instance
const apiClient = axios.create({
  baseURL: "/api/v1", // proxied to backend by Nginx
  withCredentials: true, // sends cookies (JWT tokens) automatically
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor — reads token from localStorage for Swagger-style testing
// In production, tokens are in httpOnly cookies and sent automatically
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor — handle 401 (token expired) globally
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Try to refresh the token
      try {
        await axios.post("/api/v1/auth/refresh", {}, { withCredentials: true });
        // Retry the original request
        return apiClient(error.config);
      } catch {
        // Refresh failed — redirect to login
        localStorage.removeItem("access_token");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

export default apiClient;
```

---

## STEP 52: Create Auth API Functions

Create `frontend/src/api/auth.ts`:

```typescript
import apiClient from "./client";

export interface SignupData {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  confirm_password: string;
  mobile: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export const authApi = {
  signup: (data: SignupData) => apiClient.post("/auth/signup", data),

  verifyOtp: (email: string, otp: string) =>
    apiClient.post("/auth/verify-otp", { email, otp }),

  login: (data: LoginData) => apiClient.post("/auth/login", data),

  logout: () => apiClient.post("/auth/logout"),

  forgotPassword: (email: string) =>
    apiClient.post("/auth/forgot-password", { email }),

  resetPassword: (
    token: string,
    new_password: string,
    confirm_password: string,
  ) =>
    apiClient.post("/auth/reset-password", {
      token,
      new_password,
      confirm_password,
    }),
};
```

---

## STEP 53: Create Auth Store (Zustand)

Create `frontend/src/store/authStore.ts`:

```typescript
import { create } from "zustand";

interface User {
  user_id: number;
  role_id: number;
  company_id: number;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem("access_token"),
  isAuthenticated: !!localStorage.getItem("access_token"),

  setAuth: (user, token) => {
    localStorage.setItem("access_token", token);
    set({ user, token, isAuthenticated: true });
  },

  clearAuth: () => {
    localStorage.removeItem("access_token");
    set({ user: null, token: null, isAuthenticated: false });
  },
}));
```

---

## STEP 54: Create Route Guards

Create `frontend/src/routes/ProtectedRoute.tsx`:

```tsx
import { Navigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";

interface Props {
  children: React.ReactNode;
}

// Blocks unauthenticated users — redirects to /login
export function ProtectedRoute({ children }: Props) {
  const { isAuthenticated } = useAuthStore();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
```

Create `frontend/src/routes/RoleRoute.tsx`:

```tsx
import { Navigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";

interface Props {
  children: React.ReactNode;
  allowedRoles: number[]; // e.g. [1] for Super Admin, [1,2,3] for Admin+HR
}

// Role IDs: 1=Super Admin, 2=Company Admin, 3=HR, 4=Employee
export function RoleRoute({ children, allowedRoles }: Props) {
  const { user } = useAuthStore();
  if (!user || !allowedRoles.includes(user.role_id)) {
    return <Navigate to="/unauthorized" replace />;
  }
  return <>{children}</>;
}
```

---

## STEP 55: Create App Router

Update `frontend/src/App.tsx`:

```tsx
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./routes/ProtectedRoute";
import { RoleRoute } from "./routes/RoleRoute";

// Auth screens
import { LoginPage } from "./features/auth/LoginPage";
import { SignupPage } from "./features/auth/SignupPage";
import { OTPPage } from "./features/auth/OTPPage";
import { ForgotPasswordPage } from "./features/auth/ForgotPasswordPage";
import { ResetPasswordPage } from "./features/auth/ResetPasswordPage";

// Admin portal
import { AdminDashboard } from "./features/admin/AdminDashboard";
import { CompanyListPage } from "./features/admin/CompanyListPage";
import { UserListPage } from "./features/admin/UserListPage";
import { VideoListPage } from "./features/admin/VideoListPage";

// HR portal
import { HRDashboard } from "./features/hr/HRDashboard";
import { BulkUploadPage } from "./features/hr/BulkUploadPage";
import { TrainingAssignPage } from "./features/hr/TrainingAssignPage";
import { CompliancePage } from "./features/hr/CompliancePage";

// Employee portal
import { EmployeeDashboard } from "./features/employee/EmployeeDashboard";
import { CoursesPage } from "./features/employee/CoursesPage";
import { VideoPlayerPage } from "./features/employee/VideoPlayerPage";
import { AssessmentPage } from "./features/employee/AssessmentPage";
import { CertificatesPage } from "./features/employee/CertificatesPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/verify-otp" element={<OTPPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/" element={<Navigate to="/login" replace />} />

        {/* Admin portal — role 1 or 2 only */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              <RoleRoute allowedRoles={[1, 2]}>
                <AdminDashboard />
              </RoleRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/companies"
          element={
            <ProtectedRoute>
              <RoleRoute allowedRoles={[1]}>
                <CompanyListPage />
              </RoleRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/users"
          element={
            <ProtectedRoute>
              <RoleRoute allowedRoles={[1, 2]}>
                <UserListPage />
              </RoleRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/videos"
          element={
            <ProtectedRoute>
              <RoleRoute allowedRoles={[1, 2]}>
                <VideoListPage />
              </RoleRoute>
            </ProtectedRoute>
          }
        />

        {/* HR portal — role 1, 2, or 3 */}
        <Route
          path="/hr"
          element={
            <ProtectedRoute>
              <RoleRoute allowedRoles={[1, 2, 3]}>
                <HRDashboard />
              </RoleRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/hr/upload"
          element={
            <ProtectedRoute>
              <RoleRoute allowedRoles={[1, 2, 3]}>
                <BulkUploadPage />
              </RoleRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/hr/assign"
          element={
            <ProtectedRoute>
              <RoleRoute allowedRoles={[1, 2, 3]}>
                <TrainingAssignPage />
              </RoleRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/hr/compliance"
          element={
            <ProtectedRoute>
              <RoleRoute allowedRoles={[1, 2, 3]}>
                <CompliancePage />
              </RoleRoute>
            </ProtectedRoute>
          }
        />

        {/* Employee portal — all authenticated users */}
        <Route
          path="/employee"
          element={
            <ProtectedRoute>
              <EmployeeDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/employee/courses"
          element={
            <ProtectedRoute>
              <CoursesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/employee/video/:videoId"
          element={
            <ProtectedRoute>
              <VideoPlayerPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/employee/assessment/:videoId"
          element={
            <ProtectedRoute>
              <AssessmentPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/employee/certificates"
          element={
            <ProtectedRoute>
              <CertificatesPage />
            </ProtectedRoute>
          }
        />

        {/* Catch-all */}
        <Route path="/unauthorized" element={<div>Access Denied</div>} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
```

---

## STEP 56: Build Auth Screens

### 56.1 Login Page

Create `frontend/src/features/auth/LoginPage.tsx`:

```tsx
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

type LoginForm = z.infer<typeof loginSchema>;

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
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    mode: "onChange",
  });

  const onSubmit = async (data: LoginForm) => {
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
    } catch (err: any) {
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
            Don't have an account?{" "}
            <Link to="/signup" style={{ color: "#1a3c5e", fontWeight: 600 }}>
              Sign up
            </Link>
          </span>
        </div>
      </div>
    </div>
  );
}
```

### 56.2 Signup Page

Create `frontend/src/features/auth/SignupPage.tsx`:

```tsx
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

type SignupForm = z.infer<typeof signupSchema>;

export function SignupPage() {
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isValid },
  } = useForm<SignupForm>({
    resolver: zodResolver(signupSchema),
    mode: "onChange",
  });

  const onSubmit = async (data: SignupForm) => {
    setLoading(true);
    setError("");
    try {
      await authApi.signup(data);
      // Navigate to OTP page with email in state
      navigate("/verify-otp", { state: { email: data.email } });
    } catch (err: any) {
      setError(
        err.response?.data?.detail || "Signup failed. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  };

  const inputStyle = (hasError: boolean) => ({
    width: "100%",
    padding: "10px 14px",
    border: `1px solid ${hasError ? "#e74c3c" : "#ddd"}`,
    borderRadius: "6px",
    fontSize: "14px",
    boxSizing: "border-box" as const,
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
```

### 56.3 OTP Verification Page

Create `frontend/src/features/auth/OTPPage.tsx`:

```tsx
import { useState, useRef } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { authApi } from "../../api/auth";

export function OTPPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const email = (location.state as any)?.email || "";

  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const inputs = useRef<(HTMLInputElement | null)[]>([]);

  const handleChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return; // digits only
    const newOtp = [...otp];
    newOtp[index] = value.slice(-1); // one digit per box
    setOtp(newOtp);
    if (value && index < 5) inputs.current[index + 1]?.focus();
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      inputs.current[index - 1]?.focus();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const code = otp.join("");
    if (code.length !== 6) {
      setError("Please enter all 6 digits.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await authApi.verifyOtp(email, code);
      navigate("/login", {
        state: { message: "Email verified! You can now log in." },
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || "Invalid or expired OTP.");
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
          maxWidth: "400px",
          textAlign: "center",
        }}
      >
        <h1 style={{ color: "#1a3c5e", marginBottom: "8px" }}>
          Verify Your Email
        </h1>
        <p style={{ color: "#666", marginBottom: "8px" }}>
          Enter the 6-digit code sent to
        </p>
        <p style={{ color: "#1a3c5e", fontWeight: 600, marginBottom: "32px" }}>
          {email}
        </p>

        <form onSubmit={handleSubmit}>
          <div
            style={{
              display: "flex",
              gap: "12px",
              justifyContent: "center",
              marginBottom: "24px",
            }}
          >
            {otp.map((digit, i) => (
              <input
                key={i}
                ref={(el) => (inputs.current[i] = el)}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleChange(i, e.target.value)}
                onKeyDown={(e) => handleKeyDown(i, e)}
                aria-label={`OTP digit ${i + 1}`}
                style={{
                  width: "48px",
                  height: "56px",
                  textAlign: "center",
                  fontSize: "24px",
                  fontWeight: 700,
                  border: "2px solid #ddd",
                  borderRadius: "8px",
                  outline: "none",
                }}
              />
            ))}
          </div>

          {error && (
            <p style={{ color: "#e74c3c", marginBottom: "16px" }}>{error}</p>
          )}

          <button
            type="submit"
            disabled={otp.join("").length !== 6 || loading}
            style={{
              width: "100%",
              padding: "12px",
              background:
                otp.join("").length !== 6 || loading ? "#93b8d4" : "#1a3c5e",
              color: "white",
              border: "none",
              borderRadius: "6px",
              fontSize: "16px",
              fontWeight: 600,
              cursor:
                otp.join("").length !== 6 || loading
                  ? "not-allowed"
                  : "pointer",
            }}
          >
            {loading ? "Verifying..." : "Verify Email"}
          </button>
        </form>

        <p style={{ marginTop: "20px", fontSize: "14px", color: "#666" }}>
          Didn't receive the code?{" "}
          <Link to="/signup" style={{ color: "#1a3c5e" }}>
            Go back to signup
          </Link>
        </p>
      </div>
    </div>
  );
}
```

### 56.4 Forgot Password Page

Create `frontend/src/features/auth/ForgotPasswordPage.tsx`:

```tsx
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link } from "react-router-dom";
import { authApi } from "../../api/auth";

const schema = z.object({
  email: z.string().email("Invalid email format"),
});

export function ForgotPasswordPage() {
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
  } = useForm({ resolver: zodResolver(schema), mode: "onChange" });

  const onSubmit = async (data: any) => {
    setLoading(true);
    try {
      await authApi.forgotPassword(data.email);
      setSubmitted(true);
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
        {submitted ? (
          <div style={{ textAlign: "center" }}>
            <h2 style={{ color: "#27ae60" }}>✓ Email Sent</h2>
            <p style={{ color: "#666", marginTop: "12px" }}>
              If your email is registered, you will receive password reset
              instructions.
            </p>
            <Link
              to="/login"
              style={{
                display: "inline-block",
                marginTop: "24px",
                color: "#1a3c5e",
                fontWeight: 600,
              }}
            >
              Back to Login
            </Link>
          </div>
        ) : (
          <>
            <h1 style={{ color: "#1a3c5e", marginBottom: "8px" }}>
              Forgot Password
            </h1>
            <p style={{ color: "#666", marginBottom: "32px" }}>
              Enter your email and we'll send you reset instructions.
            </p>
            <form onSubmit={handleSubmit(onSubmit)}>
              <label
                style={{
                  display: "block",
                  marginBottom: "6px",
                  fontWeight: 500,
                }}
              >
                Email Address *
              </label>
              <input
                type="email"
                {...register("email")}
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
                  style={{
                    color: "#e74c3c",
                    fontSize: "12px",
                    marginTop: "4px",
                  }}
                >
                  {(errors.email as any).message}
                </p>
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
                {loading ? "Sending..." : "Send Reset Instructions"}
              </button>
            </form>
            <div style={{ textAlign: "center", marginTop: "20px" }}>
              <Link to="/login" style={{ color: "#1a3c5e", fontSize: "14px" }}>
                Back to Login
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
```

### 56.5 Reset Password Page

Create `frontend/src/features/auth/ResetPasswordPage.tsx`:

```tsx
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { authApi } from "../../api/auth";

const schema = z
  .object({
    new_password: z
      .string()
      .min(8)
      .max(15)
      .regex(/[A-Z]/, "Needs uppercase")
      .regex(/[a-z]/, "Needs lowercase")
      .regex(/[0-9]/, "Needs number")
      .regex(/[!@#$%^&*(),.?":{}|<>]/, "Needs special character"),
    confirm_password: z.string(),
  })
  .refine((d) => d.new_password === d.confirm_password, {
    message: "Passwords don't match",
    path: ["confirm_password"],
  });

export function ResetPasswordPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
  } = useForm({ resolver: zodResolver(schema), mode: "onChange" });

  const onSubmit = async (data: any) => {
    setLoading(true);
    setError("");
    try {
      await authApi.resetPassword(
        token,
        data.new_password,
        data.confirm_password,
      );
      navigate("/login", {
        state: { message: "Password reset successfully. Please log in." },
      });
    } catch (err: any) {
      setError(
        err.response?.data?.detail || "Reset failed. Token may have expired.",
      );
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
        <h1 style={{ color: "#1a3c5e", marginBottom: "8px" }}>
          Reset Password
        </h1>
        <p style={{ color: "#666", marginBottom: "32px" }}>
          Enter your new password below.
        </p>

        <form onSubmit={handleSubmit(onSubmit)}>
          <div style={{ marginBottom: "16px" }}>
            <label
              style={{ display: "block", marginBottom: "6px", fontWeight: 500 }}
            >
              New Password *
            </label>
            <input
              type="password"
              {...register("new_password")}
              style={{
                width: "100%",
                padding: "10px 14px",
                border: `1px solid ${errors.new_password ? "#e74c3c" : "#ddd"}`,
                borderRadius: "6px",
                fontSize: "14px",
                boxSizing: "border-box",
              }}
            />
            {errors.new_password && (
              <p
                style={{ color: "#e74c3c", fontSize: "12px", marginTop: "4px" }}
              >
                {(errors.new_password as any).message}
              </p>
            )}
          </div>

          <div>
            <label
              style={{ display: "block", marginBottom: "6px", fontWeight: 500 }}
            >
              Confirm Password *
            </label>
            <input
              type="password"
              {...register("confirm_password")}
              style={{
                width: "100%",
                padding: "10px 14px",
                border: `1px solid ${errors.confirm_password ? "#e74c3c" : "#ddd"}`,
                borderRadius: "6px",
                fontSize: "14px",
                boxSizing: "border-box",
              }}
            />
            {errors.confirm_password && (
              <p
                style={{ color: "#e74c3c", fontSize: "12px", marginTop: "4px" }}
              >
                {(errors.confirm_password as any).message}
              </p>
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
            {loading ? "Resetting..." : "Reset Password"}
          </button>
        </form>
      </div>
    </div>
  );
}
```

---

## STEP 57: Create Placeholder Portal Pages

Create these files now as placeholders. You'll fill them in after the auth screens work.

```bash
# Run from frontend/src/features/
```

Create `frontend/src/features/admin/AdminDashboard.tsx`:

```tsx
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
```

Create similar placeholder files for all other portal pages:

```bash
# Create all placeholder files at once
```

Create `frontend/src/features/admin/CompanyListPage.tsx`:

```tsx
export function CompanyListPage() {
  return (
    <div style={{ padding: "40px" }}>
      <h1>Company Management</h1>
      <p>Coming soon</p>
    </div>
  );
}
```

Create `frontend/src/features/admin/UserListPage.tsx`:

```tsx
export function UserListPage() {
  return (
    <div style={{ padding: "40px" }}>
      <h1>User Management</h1>
      <p>Coming soon</p>
    </div>
  );
}
```

Create `frontend/src/features/admin/VideoListPage.tsx`:

```tsx
export function VideoListPage() {
  return (
    <div style={{ padding: "40px" }}>
      <h1>Video Management</h1>
      <p>Coming soon</p>
    </div>
  );
}
```

Create `frontend/src/features/hr/HRDashboard.tsx`:

```tsx
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
```

Create `frontend/src/features/hr/BulkUploadPage.tsx`:

```tsx
export function BulkUploadPage() {
  return (
    <div style={{ padding: "40px" }}>
      <h1>Bulk Employee Upload</h1>
      <p>Coming soon</p>
    </div>
  );
}
```

Create `frontend/src/features/hr/TrainingAssignPage.tsx`:

```tsx
export function TrainingAssignPage() {
  return (
    <div style={{ padding: "40px" }}>
      <h1>Assign Training</h1>
      <p>Coming soon</p>
    </div>
  );
}
```

Create `frontend/src/features/hr/CompliancePage.tsx`:

```tsx
export function CompliancePage() {
  return (
    <div style={{ padding: "40px" }}>
      <h1>Compliance Dashboard</h1>
      <p>Coming soon</p>
    </div>
  );
}
```

Create `frontend/src/features/employee/EmployeeDashboard.tsx`:

```tsx
import { useAuthStore } from "../../store/authStore";
import { useNavigate } from "react-router-dom";

export function EmployeeDashboard() {
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
        <h1 style={{ color: "#1a3c5e" }}>My Training</h1>
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
```

Create `frontend/src/features/employee/CoursesPage.tsx`:

```tsx
export function CoursesPage() {
  return (
    <div style={{ padding: "40px" }}>
      <h1>My Courses</h1>
      <p>Coming soon</p>
    </div>
  );
}
```

Create `frontend/src/features/employee/VideoPlayerPage.tsx`:

```tsx
export function VideoPlayerPage() {
  return (
    <div style={{ padding: "40px" }}>
      <h1>Video Player</h1>
      <p>Coming soon</p>
    </div>
  );
}
```

Create `frontend/src/features/employee/AssessmentPage.tsx`:

```tsx
export function AssessmentPage() {
  return (
    <div style={{ padding: "40px" }}>
      <h1>Assessment</h1>
      <p>Coming soon</p>
    </div>
  );
}
```

Create `frontend/src/features/employee/CertificatesPage.tsx`:

```tsx
export function CertificatesPage() {
  return (
    <div style={{ padding: "40px" }}>
      <h1>My Certificates</h1>
      <p>Coming soon</p>
    </div>
  );
}
```

---

## STEP 58: Test Auth Flow End-to-End

Rebuild and start everything:

```bash
docker compose up --build
```

Open http://localhost in browser. You should see the Login screen.

Test this full flow:

1. Go to `/signup` → fill in form → submit
2. Check MailHog at http://localhost:8025 → you should see the OTP email
3. Go to `/verify-otp` → enter the OTP
4. Go to `/login` → login
5. You should be redirected based on role (Admin → `/admin`, HR → `/hr`, Employee → `/employee`)
6. Click Logout → redirected to `/login`
7. Try navigating to `/admin` without logging in → redirected to `/login`

---

## STEP 59: Lint, Build, Commit Phase 5B Auth

```bash
cd frontend
npm run build
cd ..

cd backend
black .
ruff check .
cd ..

git add .
git commit -m "feat(phase5b): React frontend — auth screens (login, signup, OTP, forgot/reset password), routing, role guards"
git push origin develop
```

---

# PHASE 5C — SECURITY HARDENING

---

## STEP 60: Add Rate Limiting to Backend

Update `backend/app/main.py` to add rate limiting:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="POSH Training Platform API", version="1.0.0", docs_url="/docs")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

Add rate limits to sensitive endpoints in `backend/app/api/v1/auth.py`:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/login")
@limiter.limit("10/minute")   # max 10 login attempts per minute per IP
async def login(request: Request, data: LoginRequest, db: AsyncSession = Depends(get_db)):
    ip = request.client.host
    return await auth_service.login(db, data, ip)

@router.post("/signup")
@limiter.limit("5/minute")
async def signup(request: Request, data: SignupRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.signup(db, data)
```

## STEP 61: Add Security Headers

Update `backend/app/main.py` — add security headers middleware:

```python
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

## STEP 62: Add HTTPS to Nginx (Let's Encrypt)

Update `frontend/nginx.conf` for production TLS:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$host$request_uri;    # force HTTPS
}

server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Rate limit the public certificate verification endpoint
    location /api/v1/certificates/verify {
        limit_req zone=verify burst=5 nodelay;
        proxy_pass http://backend:8000;
    }

    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'" always;
}
```

---

## STEP 63: Commit Security Hardening

```bash
git add .
git commit -m "feat(phase5c): security headers, rate limiting, HTTPS config"
git push origin develop
```

---

# PHASE 5D — PRODUCTION DEPLOYMENT

---

## STEP 64: Create Production Docker Compose

Create `docker-compose.prod.yml` in project root:

```yaml
version: "3.9"

services:
  mysql:
    image: mysql:8.0
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DATABASE}
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
    # No ports exposed — only accessible internally

  redis:
    image: redis:7-alpine
    restart: always
    # No ports exposed

  minio:
    image: minio/minio:latest
    restart: always
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    volumes:
      - minio_data:/data
    # No ports exposed — only accessible internally

  backend:
    image: ghcr.io/YOUR_USERNAME/posh-backend:latest
    restart: always
    env_file: .env.prod
    depends_on:
      - mysql
      - redis
      - minio
    # No --reload in production
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

  celery-worker:
    image: ghcr.io/YOUR_USERNAME/posh-backend:latest
    restart: always
    env_file: .env.prod
    depends_on:
      - redis
      - mysql
    command: celery -A app.workers.celery_app worker --loglevel=warning --concurrency=4

  frontend:
    image: ghcr.io/YOUR_USERNAME/posh-frontend:latest
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /etc/letsencrypt:/etc/letsencrypt:ro # TLS certificates

volumes:
  mysql_data:
  minio_data:
```

## STEP 65: Create Production .env

Create `.env.prod` (never commit this):

```bash
# Database
MYSQL_ROOT_PASSWORD=<strong_random_password>
MYSQL_DATABASE=posh_db
MYSQL_USER=posh_user
MYSQL_PASSWORD=<strong_random_password>
DATABASE_URL=mysql+asyncmy://posh_user:<password>@mysql:3306/posh_db

# Redis
REDIS_URL=redis://redis:6379/0

# JWT — generate with: python -c "import secrets; print(secrets.token_hex(64))"
JWT_SECRET_KEY=<64_char_random_hex>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Storage
MINIO_ROOT_USER=<strong_user>
MINIO_ROOT_PASSWORD=<strong_password>
MINIO_ENDPOINT=minio:9000
MINIO_BUCKET_VIDEOS=posh-videos
MINIO_BUCKET_CERTIFICATES=posh-certificates

# Email — use real SMTP in production
SMTP_HOST=smtp.yourprovider.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASSWORD=<smtp_password>
EMAILS_FROM=noreply@yourdomain.com

# App
APP_ENV=production
FRONTEND_URL=https://yourdomain.com
BACKEND_CORS_ORIGINS=["https://yourdomain.com"]
```

## STEP 66: Deploy to a Cloud VM

These steps work on any provider (AWS EC2, Azure VM, GCP Compute Engine, DigitalOcean Droplet).

**On the server:**

```bash
# 1. Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 2. Install certbot for TLS
sudo apt install certbot python3-certbot-nginx -y

# 3. Clone your repo
git clone https://github.com/YOUR_USERNAME/posh-platform.git
cd posh-platform

# 4. Get TLS certificate (replace with your domain)
sudo certbot certonly --standalone -d yourdomain.com

# 5. Create .env.prod with production values
nano .env.prod

# 6. Pull latest images and start
docker compose -f docker-compose.prod.yml up -d

# 7. Run migrations
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 8. Seed reference data
docker compose -f docker-compose.prod.yml exec backend python -m app.db.seed

# 9. Verify health
curl https://yourdomain.com/api/v1/health
```

## STEP 67: Set Up Auto-Renewing TLS

```bash
# Add certbot renewal to cron (runs twice daily)
echo "0 12 * * * /usr/bin/certbot renew --quiet && docker compose -f /path/to/posh-platform/docker-compose.prod.yml restart frontend" | sudo tee -a /var/spool/cron/crontabs/root
```

## STEP 68: Final Production Checklist

Go through every item before going live:

```bash
# Check all containers running
docker compose -f docker-compose.prod.yml ps

# Check backend health
curl https://yourdomain.com/api/v1/health

# Check logs for errors
docker compose -f docker-compose.prod.yml logs backend --tail=50
docker compose -f docker-compose.prod.yml logs celery-worker --tail=50
```

- [ ] All `dev_otp` and `dev_reset_token` removed from responses
- [ ] `APP_ENV=production` in `.env.prod`
- [ ] `JWT_SECRET_KEY` is a long random string (not the default)
- [ ] All passwords in `.env.prod` are strong and random
- [ ] HTTPS working — test at https://www.ssllabs.com/ssltest/
- [ ] MailHog removed from production Compose (real SMTP configured)
- [ ] MySQL and Redis ports NOT exposed publicly
- [ ] MinIO port NOT exposed publicly
- [ ] Celery worker running and processing tasks
- [ ] DB backup scheduled (mysqldump to MinIO daily)
- [ ] CI pipeline deploys on Git tag push

---

## STEP 69: Final Commit

```bash
git add .
git commit -m "feat(phase5): complete — email delivery, Celery, React auth UI, security hardening, production deployment config"
git push origin develop

# Merge to main and tag the release
git checkout main
git merge develop
git tag -a v1.0.0 -m "POSH Platform v1.0.0 — first production release"
git push origin main --tags
```

---

## Complete Project Summary

| Phase    | What Was Built                                                                  |
| -------- | ------------------------------------------------------------------------------- |
| Phase 0  | Git repo, Docker Compose, FastAPI skeleton, React skeleton, CI pipeline         |
| Phase 1  | Auth (signup/OTP/login/logout/forgot-password), RBAC, Company CRUD, User CRUD   |
| Phase 2  | Video upload, secure streaming, progress tracking, no-fast-forward, assessments |
| Phase 3  | HR bulk upload, training assignment, compliance dashboard, Excel reports        |
| Phase 4  | Certificate PDF+QR generation, public verification, analytics                   |
| Phase 5A | Real email delivery, Celery background tasks, dev tokens removed                |
| Phase 5B | React frontend — auth screens, routing, role guards                             |
| Phase 5C | Rate limiting, security headers, HTTPS                                          |
| Phase 5D | Production Docker Compose, cloud VM deployment, TLS                             |

**The remaining frontend screens** (Admin Portal tables, HR Portal, Employee Portal, Video Player) follow the exact same pattern as the auth screens — fetch data with TanStack Query, display in a table/form, call the APIs you already built. Let me know when you're ready and I'll write those screen by screen.

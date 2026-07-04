# POSH Platform Overview

## Project Summary

POSH Platform is a multi-tenant training and compliance application for Prevention of Sexual Harassment training. The repo contains a FastAPI backend, a React/Vite frontend, MySQL persistence, Redis/Celery background jobs, MinIO object storage, MailHog for local email testing, and Docker Compose infrastructure.

The main product flow is:

1. Users sign up, verify OTP, or are created by an admin/HR workflow.
2. Admin users create companies, manage users, and upload training videos.
3. Uploaded videos are stored privately in MinIO and published when ready.
4. HR users bulk-upload employees and assign training by individual, department, or company-wide scope.
5. Employees request signed video stream URLs and training progress is tracked.
6. Video completion unlocks assessment submission.
7. Passing an assessment enqueues certificate generation through Celery.
8. Certificates are generated as PDFs, stored in MinIO, emailed to users, and publicly verifiable by certificate number.

## Backend Overview

Backend entry point: `backend/app/main.py`

Framework: FastAPI  
API prefix: `/api/v1`  
Interactive docs: `/docs`  
Health check: `/health`

Backend layers:

- `backend/app/api/v1`: FastAPI route modules.
- `backend/app/schemas`: Pydantic request and response schemas.
- `backend/app/services`: business logic.
- `backend/app/models`: SQLAlchemy ORM models.
- `backend/app/core`: config, auth/security, storage, email, and dependencies.
- `backend/app/db`: async DB session and seed helpers.
- `backend/app/workers`: Celery worker app and tasks.
- `backend/alembic`: database migrations.
- `backend/tests`: backend tests.

## Backend Request Flow

1. A request reaches FastAPI in `backend/app/main.py`.
2. CORS middleware and custom security headers middleware run.
3. The matching router under `/api/v1` handles the request.
4. Protected routes use `get_current_user` or `require_roles`.
5. `get_db` provides an async SQLAlchemy session.
6. Routes delegate domain work to service classes.
7. Services read/write SQLAlchemy models, call MinIO helpers, send email, or enqueue Celery tasks.
8. DB changes are committed by the service methods.

## Authentication and Roles

Role IDs used by the application:

| Role ID | Role |
| --- | --- |
| 1 | Super Admin |
| 2 | Company Admin |
| 3 | HR |
| 4 | Employee |

Implemented security features:

- JWT access tokens.
- Refresh token records stored hashed in the database.
- Password hashing with passlib/bcrypt.
- OTP hashing for signup verification.
- Login attempt logging and temporary account lockout.
- Role-based access checks through `require_roles`.
- SlowAPI rate limiting on signup and login.
- CORS configuration from settings.
- Security response headers for content type, frames, XSS, referrer policy, and permissions policy.

Important auth note: login returns both `access_token` and `refresh_token` in JSON, but `/auth/refresh` and `/auth/logout` read the refresh token from a `refresh_token` cookie. The frontend stores the access token in `localStorage` and does not currently store or set the refresh token cookie itself. This means refresh/logout behavior should be aligned before production use.

## Backend Endpoints

### System

| Method | Endpoint | Purpose | Access |
| --- | --- | --- | --- |
| GET | `/` | API welcome response | Public |
| GET | `/health` | Health check | Public |
| GET | `/docs` | Swagger/OpenAPI docs | Public/dev |

### Authentication: `/api/v1/auth`

| Method | Endpoint | Purpose | Access |
| --- | --- | --- | --- |
| POST | `/signup` | Register employee user and send OTP | Public, rate-limited |
| POST | `/verify-otp` | Verify signup OTP and activate account | Public |
| POST | `/login` | Authenticate and return tokens plus user role/company data | Public, rate-limited |
| POST | `/logout` | Revoke refresh token | Authenticated |
| POST | `/refresh` | Issue new access/refresh tokens from refresh token | Refresh token required |
| POST | `/forgot-password` | Send password reset email if account exists | Public |
| POST | `/reset-password` | Reset password with reset token | Public |

### Companies: `/api/v1/companies`

| Method | Endpoint | Purpose | Access |
| --- | --- | --- | --- |
| GET | `/` | List non-deleted companies | Super Admin |
| POST | `/` | Create company | Super Admin |
| GET | `/{company_id}` | Get company details | Super Admin, Company Admin |
| PUT | `/{company_id}` | Update company | Super Admin, Company Admin |
| PATCH | `/{company_id}/status?status=Active\|Inactive` | Change company status | Super Admin |
| DELETE | `/{company_id}` | Soft-delete company | Super Admin |

### Users: `/api/v1/users`

| Method | Endpoint | Purpose | Access |
| --- | --- | --- | --- |
| GET | `/` | List users; Company Admin is scoped to own company | Super Admin, Company Admin |
| POST | `/` | Create user and email temporary password | Super Admin, Company Admin |
| GET | `/{user_id}` | Get user details | Super Admin, Company Admin, HR |
| PUT | `/{user_id}` | Update user | Super Admin, Company Admin |
| PATCH | `/{user_id}/status?status=Active\|Inactive` | Change user status | Super Admin, Company Admin |
| POST | `/{user_id}/reset-password` | Admin reset of user password | Super Admin, Company Admin |
| DELETE | `/{user_id}` | Soft-delete user | Super Admin |

### Videos: `/api/v1/videos`

| Method | Endpoint | Purpose | Access |
| --- | --- | --- | --- |
| GET | `/` | List all videos for current user's company | Authenticated |
| GET | `/published` | List published company videos for HR assignment dropdown | Super Admin, Company Admin, HR |
| POST | `/upload` | Upload video to MinIO and create draft metadata | Super Admin, Company Admin |
| PATCH | `/{video_id}/publish` | Publish a draft video | Super Admin, Company Admin |
| PATCH | `/{video_id}/archive` | Archive a company video | Super Admin, Company Admin |
| GET | `/{video_id}/stream-url` | Return short-lived signed stream URL | Authenticated |
| POST | `/{video_id}/progress` | Track watch progress and unlock assessment after completion | Authenticated |

Video upload protections include file size validation, magic-byte MIME validation, private MinIO paths, and signed URLs for playback.

### HR: `/api/v1/hr`

| Method | Endpoint | Purpose | Access |
| --- | --- | --- | --- |
| POST | `/employees/bulk-upload` | Upload CSV/XLS/XLSX employee file and create valid rows | Super Admin, Company Admin, HR |
| POST | `/training/assign` | Assign training by employee, department, or company | Super Admin, Company Admin, HR |
| GET | `/compliance/dashboard` | Company compliance summary and overdue employees | Super Admin, Company Admin, HR |
| GET | `/reports/employees` | Download Excel employee training report | Super Admin, Company Admin, HR |

### Assessments: `/api/v1/assessments`

| Method | Endpoint | Purpose | Access |
| --- | --- | --- | --- |
| POST | `/submit` | Submit answers, calculate score, and trigger certificate on pass | Authenticated |

Assessment submission requires completed training history for the related video.

### Certificates: `/api/v1/certificates`

| Method | Endpoint | Purpose | Access |
| --- | --- | --- | --- |
| GET | `/my` | List current user's valid certificates | Authenticated |
| GET | `/{certificate_id}/download` | Return signed PDF download URL | Authenticated certificate owner |
| GET | `/verify/{certificate_number}` | Public certificate verification | Public |
| POST | `/{certificate_id}/revoke` | Revoke certificate | Super Admin |
| POST | `/generate?user_id={id}&video_id={id}` | Manually generate certificate | Super Admin, Company Admin |

### Analytics: `/api/v1/analytics`

| Method | Endpoint | Purpose | Access |
| --- | --- | --- | --- |
| GET | `/overview` | Platform totals for companies, users, certificates, completions, and average score | Super Admin |
| GET | `/company/{company_id}` | Company-level employee, certificate, and compliance stats | Super Admin, Company Admin |

## Frontend Overview

Frontend entry point: `frontend/src/main.jsx`  
Route tree: `frontend/src/App.jsx`  
API client: `frontend/src/api/client.js`  
Auth API wrapper: `frontend/src/api/auth.js`  
Auth state: `frontend/src/store/authStore.js`

Frontend stack:

- React 19 and React DOM.
- Vite for dev/build tooling.
- React Router for navigation.
- Zustand for auth/session state.
- Axios for API calls.
- MUI packages for UI components/icons.
- React Hook Form and Zod are installed for form patterns.
- TanStack React Query is installed, but most current pages still use manual `useEffect` data fetching.
- i18next/react-i18next are installed for internationalization.

The frontend Axios client uses `baseURL: "/api/v1"` and `withCredentials: true`. It adds `Authorization: Bearer <access_token>` from `localStorage` when present. In Docker/Nginx, `/api` is proxied to the backend container.

## Frontend Routes

| Route | Page | Access |
| --- | --- | --- |
| `/login` | Login | Public |
| `/signup` | Signup | Public |
| `/verify-otp` | OTP verification | Public |
| `/forgot-password` | Forgot password | Public |
| `/reset-password` | Reset password | Public |
| `/admin` | Admin dashboard | Roles 1, 2 |
| `/admin/companies` | Company management | Role 1 |
| `/admin/users` | User management | Roles 1, 2 |
| `/admin/videos` | Video upload/management | Roles 1, 2 |
| `/hr` | HR dashboard | Roles 1, 2, 3 |
| `/hr/upload` | Bulk employee upload | Roles 1, 2, 3 |
| `/hr/assign` | Training assignment | Roles 1, 2, 3 |
| `/hr/compliance` | Compliance dashboard/report | Roles 1, 2, 3 |
| `/employee` | Employee dashboard | Authenticated |
| `/employee/courses` | Assigned courses | Authenticated |
| `/employee/video/:videoId` | Video player | Authenticated |
| `/employee/assessment/:videoId` | Assessment | Authenticated |
| `/employee/certificates` | Certificates | Authenticated |

## Frontend Flow

1. Users enter through `/login`, `/signup`, or password recovery screens.
2. Auth screens call `frontend/src/api/auth.js`.
3. Login stores `access_token` and user data in Zustand/localStorage.
4. `ProtectedRoute` blocks unauthenticated users.
5. `RoleRoute` blocks users without the required role ID.
6. Admin pages call company, user, and video endpoints.
7. HR pages call bulk upload, training assignment, compliance dashboard, and report endpoints.
8. Employee certificate page calls certificate listing/download endpoints.
9. Employee dashboard and course pages currently rely on HR compliance data instead of dedicated employee course APIs.
10. Employee video and assessment pages exist in the route tree, but the learning flow still needs full UI/API wiring.

## Infrastructure and Tools Used

Runtime services:

- FastAPI/uvicorn for the backend API.
- MySQL 8.0 for relational persistence.
- SQLAlchemy async ORM with `asyncmy`.
- Alembic for database migrations.
- Redis for Celery broker/result backend.
- Celery for background certificate generation.
- MinIO as S3-compatible object storage for videos, QR codes, and PDFs.
- MailHog for local SMTP/email inspection.
- Nginx for serving the React build and proxying API requests.
- Docker Compose for local multi-service orchestration.

Backend libraries:

- Pydantic and pydantic-settings for schemas/config.
- python-jose for JWT handling.
- passlib/bcrypt for password hashing.
- slowapi for rate limiting.
- pandas/openpyxl for employee uploads and Excel reports.
- boto3 for MinIO/S3 access.
- python-magic for MIME detection.
- reportlab and qrcode for certificate generation.
- aiosmtplib for email sending.
- pytest, pytest-asyncio, pytest-cov, and httpx for testing.
- Ruff and Black for code quality/formatting.

Frontend libraries:

- React, React DOM, and Vite.
- React Router.
- Axios.
- Zustand.
- MUI and MUI icons.
- React Hook Form and Zod.
- TanStack React Query.
- i18next/react-i18next.
- ESLint, Prettier, Vitest, Testing Library, and jsdom tooling.

## Important Data Flows

### Signup/Login Flow

1. User signs up from the frontend.
2. Backend creates an inactive employee user under default `company_id=1`.
3. Backend creates a hashed OTP and emails the raw OTP.
4. User submits OTP.
5. Backend marks OTP verified and activates the user.
6. User logs in.
7. Backend validates password, checks lockout/status, creates access and refresh tokens, and stores the hashed refresh token.
8. Frontend stores the access token and sends it as a bearer token.

### Admin/User Flow

1. Super Admin can create/list/update/delete companies.
2. Super Admin and Company Admin can create and manage users.
3. Temporary passwords are generated and emailed for admin-created users.
4. User records are soft-deleted by setting `is_deleted`.

### Training Flow

1. Admin uploads a video file with title/metadata.
2. Backend validates size and MIME, uploads the file to MinIO, and saves video metadata as `Draft`.
3. Admin publishes the video.
4. HR assigns the video to an individual, department, or company-wide audience.
5. Employee requests a stream URL.
6. Backend checks video publication and whether an assignment exists for the company/video, then returns a 5-minute signed URL.
7. Employee progress is posted during playback.
8. Backend blocks fast-forwarding beyond a small buffer and marks training complete at 95%.

### Assessment and Certificate Flow

1. Employee submits answers for a completed video.
2. Backend confirms completed training history exists.
3. Backend scores answers and stores an assessment result.
4. Passing score enqueues `generate_certificate_task`.
5. Celery generates certificate number, QR code, and PDF.
6. QR/PDF are uploaded to MinIO.
7. Certificate record is saved in MySQL.
8. Certificate email is sent.
9. User can list/download certificate through signed URL.
10. Public verification confirms certificate validity using certificate number.

## Gaps Identified

1. Employee course APIs are missing or incomplete.
   - Frontend employee pages call `/hr/compliance/dashboard`, but employees do not have access to HR endpoints.
   - Add dedicated employee endpoints for assigned courses, training history, and course detail.

2. Assessment question retrieval endpoint is missing.
   - Backend can submit answers, but the frontend needs an endpoint to fetch questions/options for a video.
   - Current assessment model includes questions/options, but only `POST /assessments/submit` is exposed.

3. Employee video player and assessment screens are not fully implemented.
   - The route structure exists.
   - The signed stream URL, progress update, and submit endpoints need to be wired into the UI.

4. Refresh-token handling is inconsistent.
   - Backend refresh/logout expects cookie-based refresh tokens.
   - Login returns refresh token in JSON.
   - Frontend refresh retry calls `/auth/refresh` but does not persist the new access token from the refresh response.

5. Tenant boundaries need additional hardening.
   - Some service methods fetch by ID without always verifying the record belongs to the current user's company.
   - Risk areas include user detail/update/status, manual certificate generation, company analytics, and assignment validation.

6. Assignment authorization is too broad for video streaming.
   - `get_stream_url` checks if any assignment exists for the company/video.
   - It should verify the current user matches the assignment scope: individual, department, or company-wide.

7. HR assignment validation does not confirm target ownership.
   - Individual assignment should confirm the target user belongs to the same company.
   - Department assignment should confirm that department exists in the company.
   - Assignment should confirm the selected video belongs to the same company and is published.

8. Compliance and reports are user-level, not assignment-level.
   - Overdue logic can include users who already completed the specific assigned video.
   - Compliance should calculate status per assignment/video, then aggregate.

9. Certificate generation is not idempotent.
   - Repeated pass/manual generation may create duplicate valid certificates for the same user/video.
   - Certificate numbering is count-based and may race under concurrency.

10. Production security settings need tightening.
    - `JWT_SECRET_KEY` has an insecure default in config.
    - Development CORS/database defaults should be overridden in production.
    - Access tokens in `localStorage` increase XSS impact.
    - Certificate verification base URL is hardcoded to localhost in `certificate_service.py`.

11. Frontend state and data fetching are inconsistent.
    - React Query is installed but not used as the main server-state layer.
    - API calls are mostly embedded inside page components.
    - Some pages still contain instructional text/placeholders instead of complete workflows.

12. Encoding artifacts appear in some source files and generated text.
    - Several comments/UI strings show mojibake-like characters.
    - Standardizing file encoding and cleaning visible UI text would improve polish.

13. Observability is minimal.
    - No structured logging, request tracing, Celery monitoring dashboard, or centralized error reporting is present.

## Recommendations

1. Add employee-focused endpoints:
   - `GET /api/v1/employee/courses`
   - `GET /api/v1/employee/courses/{video_id}`
   - `GET /api/v1/employee/training-history`
   - `GET /api/v1/assessments/{video_id}/questions`

2. Finish the employee training UI:
   - Show assigned courses from employee endpoints.
   - Play videos using signed URLs.
   - Save progress on an interval.
   - Unlock assessment after completion.
   - Fetch questions and submit answers.
   - Show certificate status after passing.

3. Align token handling:
   - Prefer httpOnly, Secure, SameSite refresh-token cookies.
   - Set refresh cookies on login/refresh from the backend.
   - Update Axios refresh logic to store the new access token or move consistently to cookie-backed auth.
   - Clear both frontend state and backend refresh state on logout.

4. Enforce tenant scope in every service:
   - Company Admin and HR should only read/write their own company data.
   - Super Admin can remain platform-wide.
   - Add tests for cross-company access attempts.

5. Tighten assignment logic:
   - Validate video status/company before assignment.
   - Validate target user/company for individual assignment.
   - Match stream authorization to the actual assignment type.
   - Prevent duplicate overlapping assignments where appropriate.

6. Make certificate generation idempotent:
   - Store `video_id` on certificate records if not already planned.
   - Add a uniqueness rule for one valid certificate per user/video.
   - Return the existing valid certificate if generation is retried.
   - Use a collision-resistant certificate number strategy.

7. Improve compliance reporting:
   - Track status per assignment/video.
   - Exclude completed assignments from overdue results.
   - Include course title, due date, completion date, and score in reports.

8. Standardize frontend architecture:
   - Move domain calls into API modules such as `videosApi`, `hrApi`, `employeeApi`, and `certificatesApi`.
   - Use React Query for server state and Zustand only for auth/session state.
   - Normalize loading, error, and empty states across pages.

9. Expand backend tests:
   - Auth refresh/logout flow.
   - Role and company boundary checks.
   - HR upload validation and CSV injection handling.
   - Video assignment authorization.
   - Assessment completion prerequisite.
   - Certificate duplicate prevention.
   - Signed URL ownership/access checks.

10. Prepare production deployment:
    - Set strong secrets via environment variables.
    - Restrict CORS origins.
    - Disable SQL echo in production.
    - Configure real SMTP.
    - Configure external object storage or secured MinIO.
    - Enable HTTPS, HSTS, and a Content Security Policy at Nginx or platform level.
    - Replace hardcoded localhost verification URLs with an environment-driven public app URL.

## Current Status

The backend has most core domain modules in place: authentication, company/user management, video upload/list/publish/archive/stream/progress, HR upload/assignment/compliance/reporting, assessment submission, certificate generation/download/verification, and analytics.

The frontend has auth, admin, HR, and employee route structure in place. Auth/admin/HR screens are partially wired to backend endpoints. The largest remaining product gap is the employee learning experience: assigned course listing, video playback, progress tracking, assessment question retrieval, assessment submission UX, and certificate status feedback.

Highest-priority next work:

1. Add employee course and assessment question APIs.
2. Wire the employee course/video/assessment flow end to end.
3. Fix refresh-token handling.
4. Harden tenant/assignment authorization checks.

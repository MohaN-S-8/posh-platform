# POSH Training Platform — End-to-End Technical Roadmap

**Stack:** React (frontend) · Python + FastAPI (backend) · MySQL (database) · Docker (containerization) · Cloud-agnostic deployment (AWS/Azure/GCP/On-prem)

This document is written for a first-time builder of a multi-tenant SaaS platform. It goes A → Z: architecture, database, APIs, security, testing, version control, Docker, CI/CD, and cloud deployment — using only open-source tools throughout.

---

## 0. What We're Building (Recap from Your Screens)

Four portals sharing one database, separated by role:

| Portal | Primary Users | Core Modules |
|---|---|---|
| **Admin Portal** | Super Admin | Company Mgmt, User Mgmt, Video Mgmt, Certificate Module, Analytics, Reports, Audit Logs |
| **HR Portal** | HR (per company) | Employee Upload (bulk), Training Assignment, Compliance Tracking, Reports |
| **Employee Portal** | Employees | Video Courses, Assessments, Progress Tracking, Certificates, Training History |
| **Auth Screens** | Everyone | Signup, Login, Forgot Password, Session Mgmt |

It is **multi-tenant**: every company's data must be isolated (`company_id` scoping) even though all tenants share one database — this single requirement drives a lot of the security design below.

---

## 1. Tech Stack & Why

| Layer | Choice | Why (all open-source / free-tier friendly) |
|---|---|---|
| Frontend | React 18 + Vite + TypeScript | Faster dev server than CRA, TS catches bugs before runtime |
| State/data | TanStack Query + Zustand (or Redux Toolkit) | Server-state caching + light client state |
| Forms/validation | React Hook Form + Zod | Matches your validation-heavy signup/login screens |
| UI Kit | MUI or shadcn/ui + Tailwind | Accessible components out of the box (you need WCAG compliance) |
| Backend | Python 3.12 + FastAPI | Async, auto OpenAPI docs, Pydantic validation = fewer bugs |
| ORM | SQLAlchemy 2.0 (async) + Alembic | Prevents raw-SQL injection, manages schema migrations |
| DB | MySQL 8 | As specified by you |
| Cache/Queue | Redis | Session/rate-limit store, Celery broker |
| Background jobs | Celery + Redis | Bulk Excel upload, email sending, certificate PDF generation |
| Auth | JWT (access + refresh) via `python-jose`, `passlib[bcrypt]` | Matches your login/session/lockout requirements |
| File storage | MinIO (S3-compatible, self-hostable) or AWS S3 | Video files, certificates, logos — same code works locally and in cloud |
| Containerization | Docker + Docker Compose | Local dev parity with prod |
| Orchestration (prod) | Kubernetes (k3s for small scale) OR Docker Swarm | Cloud-agnostic — works on AWS/Azure/GCP/bare metal identically |
| CI/CD | GitHub Actions | Free for public/private repos, huge ecosystem |
| Reverse proxy/TLS | Nginx or Traefik + Let's Encrypt (cert-manager) | Enforces HTTPS (your requirement #27) |
| Monitoring | Prometheus + Grafana | Open-source, industry standard |
| Logs | Loki + Promtail (or ELK) | Centralized audit/error logs |
| Error tracking | Sentry (self-hosted, open-source edition) | Catches frontend + backend exceptions |

**Why "cloud-agnostic"?** Everything above runs in Docker containers behind a single `docker-compose.yml` (dev) and Kubernetes manifests / Helm charts (prod). Whether you later pick AWS, Azure, or GCP, only 3 things change: (1) the managed MySQL endpoint, (2) the object storage endpoint (S3 vs Azure Blob vs GCS — your `video_master.storage_type` enum already anticipates this), and (3) the Kubernetes provider (EKS/AKS/GKE). The application code never needs to know which cloud it's on if you go through an abstraction layer (see §10.3).

---

## 2. Version Control & Branching Strategy

**Tool:** Git + GitHub (or GitLab/Bitbucket — same workflow).

### 2.1 Repository structure
Use **two repos** (cleaner CI/CD, independent deploy cycles) or a **monorepo** if you prefer single-PR changes across stack. For a newbie team, monorepo is easier to manage:

```
posh-platform/
├── frontend/                 # React app
├── backend/                  # FastAPI app
├── infra/                    # Docker, k8s manifests, terraform (later)
├── docs/                     # ADRs, API docs, this roadmap
├── .github/workflows/        # CI/CD pipelines
├── docker-compose.yml        # local dev — spins up all services
└── README.md
```

### 2.2 Branching model — **GitHub Flow** (simple, fits small teams)
```
main            → always deployable, protected branch
feature/xxx     → one branch per ticket, e.g. feature/login-otp
fix/xxx         → bug fixes
release/x.y.z   → optional, only if you need staged releases
```
Rules:
- No direct commits to `main`. Every change goes through a Pull Request.
- PR requires: 1 review approval + passing CI (lint, tests, build) before merge.
- Squash-merge to keep history clean.

### 2.3 Commit convention — **Conventional Commits**
```
feat(auth): add OTP verification on signup
fix(video): prevent fast-forward seek
chore(deps): bump fastapi to 0.115
docs(readme): add docker setup steps
```
This enables auto-generated changelogs (via `semantic-release` or `git-cliff`, both open-source).

### 2.4 Versioning — **Semantic Versioning (SemVer)**
`MAJOR.MINOR.PATCH` e.g. `1.4.2`
- MAJOR — breaking API/DB schema change
- MINOR — new feature, backward-compatible
- PATCH — bug fix only

Tag every production release: `git tag -a v1.4.2 -m "release notes"`. Maintain `CHANGELOG.md` (auto-generated from commits).

### 2.5 Environment branches → Docker image tags
| Git event | Docker image tag | Deployed to |
|---|---|---|
| Push to `feature/*` | `:pr-<number>` (optional preview) | nothing / ephemeral |
| Merge to `main` | `:dev-<short-sha>` | Dev/staging environment |
| Git tag `v1.4.2` | `:1.4.2` and `:latest-stable` | Production |

---

## 3. High-Level System Architecture

```
                                ┌──────────────────────────┐
                                │      Users (Browser)      │
                                └─────────────┬─────────────┘
                                              │ HTTPS
                                ┌─────────────▼─────────────┐
                                │   Nginx/Traefik (TLS,      │
                                │   reverse proxy, rate      │
                                │   limit, gzip)             │
                                └──────┬───────────┬─────────┘
                                       │            │
                      ┌────────────────▼─┐   ┌──────▼─────────────┐
                      │  React SPA        │   │  FastAPI Backend    │
                      │  (static build,   │   │  (stateless,        │
                      │  served via CDN/  │   │  horizontally       │
                      │  Nginx)           │   │  scalable pods)     │
                      └────────────────────┘   └──────┬───────────┘
                                                        │
                       ┌────────────────────────────────┼─────────────────────┐
                       │                                │                     │
               ┌───────▼───────┐               ┌────────▼────────┐   ┌────────▼────────┐
               │  MySQL 8       │               │  Redis           │   │  Object Storage  │
               │  (Primary +    │               │  (sessions,      │   │  (S3 / Azure     │
               │  Read Replica) │               │  rate-limit,     │   │  Blob / MinIO)   │
               │                │               │  Celery broker)  │   │  — videos, certs │
               └────────────────┘               └────────┬────────┘   └─────────────────┘
                                                            │
                                                    ┌───────▼────────┐
                                                    │ Celery Workers  │
                                                    │ (bulk upload,   │
                                                    │ PDF/cert gen,   │
                                                    │ email/notify)   │
                                                    └────────────────┘
```

Key architectural decisions (and why they avoid "loose ends"):
1. **Stateless backend** — JWT auth means no server-side session pinning, so you can run N backend replicas behind a load balancer with zero sticky-session issues.
2. **Async jobs offloaded to Celery** — Excel bulk upload (HR Portal) and certificate PDF generation are slow; doing them inline would block the API and time out the browser. They go to a queue instead.
3. **Object storage decoupled from app servers** — videos/certificates never touch the backend's local disk, so backend pods stay disposable (you can kill/restart any pod without losing files).
4. **Read replica (later)** — Analytics/Reports queries (heavy aggregation) hit a MySQL read replica so they never slow down login/video-watching for live users.
5. **Single reverse proxy entry point** — only Nginx/Traefik is internet-facing; MySQL, Redis, backend pods are all in a private network with no public IP. This closes the most common "loose end" — an exposed database.

---

## 4. Database Design

### 4.1 Tables you already defined (keep as-is)
`company_master`, `language_master`, `company_languages`, `role_master`, `permission_master`, `role_permission`, `video_master`, `certificate_template`, `certificates`, `audit_logs`, `user_master`.

### 4.2 Gaps to fill before development starts
Your own documents reference tables that aren't in the schema PDF yet. Add these now so nothing blocks development later:

```sql
-- Referenced in Admin Portal doc (Video Module) but missing from schema
CREATE TABLE video_category (
  category_id INT AUTO_INCREMENT PRIMARY KEY,
  category_name VARCHAR(100),
  created_date DATETIME, updated_date DATETIME
);

CREATE TABLE video_language (
  id INT AUTO_INCREMENT PRIMARY KEY,
  video_id INT, language_id INT,
  subtitle_path VARCHAR(255),       -- per-language subtitle file
  audio_url VARCHAR(500),           -- per-language audio track if dubbed
  FOREIGN KEY (video_id) REFERENCES video_master(video_id),
  FOREIGN KEY (language_id) REFERENCES language_master(language_id)
);

-- Referenced in Analytics Module but missing from schema
CREATE TABLE training_history (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT, video_id INT, company_id INT,
  watched_seconds INT DEFAULT 0,
  total_seconds INT,
  completion_percent DECIMAL(5,2) DEFAULT 0,
  status ENUM('Not Started','In Progress','Completed') DEFAULT 'Not Started',
  last_watched_position INT DEFAULT 0,   -- resume playback (your requirement)
  started_at DATETIME, completed_at DATETIME,
  FOREIGN KEY (user_id) REFERENCES user_master(user_id),
  FOREIGN KEY (video_id) REFERENCES video_master(video_id)
);

CREATE TABLE assessment_result (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT, video_id INT,
  total_questions INT, correct_answers INT,
  score DECIMAL(5,2), passing_score DECIMAL(5,2),
  result ENUM('Pass','Fail'), attempt_number INT DEFAULT 1,
  attempted_at DATETIME,
  FOREIGN KEY (user_id) REFERENCES user_master(user_id)
);

CREATE TABLE analytics_summary (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  company_id INT, report_date DATE,
  total_employees INT, completed INT, in_progress INT, not_started INT,
  compliance_rate DECIMAL(5,2),
  FOREIGN KEY (company_id) REFERENCES company_master(company_id)
);

-- Needed for HR "Training Assignment" module (not modeled yet)
CREATE TABLE course_assignment (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  video_id INT, assigned_by BIGINT, company_id INT,
  assigned_to_user_id BIGINT NULL,        -- individual assignment
  assigned_to_department VARCHAR(100) NULL, -- department-wide
  assign_type ENUM('Individual','Department','Company-Wide'),
  due_date DATE, passing_score DECIMAL(5,2),
  created_date DATETIME,
  FOREIGN KEY (video_id) REFERENCES video_master(video_id),
  FOREIGN KEY (assigned_by) REFERENCES user_master(user_id)
);

-- Needed for Login Portal security requirements (lockout, brute-force, audit)
CREATE TABLE login_attempts (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NULL, email_attempted VARCHAR(100),
  ip_address VARCHAR(45), success BOOLEAN,
  attempted_at DATETIME
);

CREATE TABLE account_lockout (
  user_id BIGINT PRIMARY KEY,
  failed_attempts INT DEFAULT 0,
  locked_until DATETIME NULL,
  FOREIGN KEY (user_id) REFERENCES user_master(user_id)
);

CREATE TABLE password_reset_tokens (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT, token_hash VARCHAR(255),
  expires_at DATETIME, used BOOLEAN DEFAULT FALSE,
  created_date DATETIME,
  FOREIGN KEY (user_id) REFERENCES user_master(user_id)
);

CREATE TABLE refresh_tokens (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT, token_hash VARCHAR(255),
  device_info VARCHAR(255), ip_address VARCHAR(45),
  expires_at DATETIME, revoked BOOLEAN DEFAULT FALSE,
  created_date DATETIME,
  FOREIGN KEY (user_id) REFERENCES user_master(user_id)
);

-- Signup OTP requirement
CREATE TABLE otp_verification (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(100), otp_hash VARCHAR(255),
  purpose ENUM('Signup','PasswordReset'),
  expires_at DATETIME, verified BOOLEAN DEFAULT FALSE,
  created_date DATETIME
);

-- Bulk employee upload tracking (HR Portal)
CREATE TABLE employee_upload_batch (
  batch_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  company_id INT, uploaded_by BIGINT,
  file_name VARCHAR(255), total_rows INT,
  success_rows INT, failed_rows INT,
  error_report_path VARCHAR(255),
  status ENUM('Processing','Completed','Failed'),
  created_date DATETIME,
  FOREIGN KEY (company_id) REFERENCES company_master(company_id)
);
```

### 4.3 Schema-level integrity rules (close the "loose ends")
- Every FK uses `ON DELETE RESTRICT` for master data (don't allow deleting a company that has users) and `ON DELETE CASCADE` only for true child records (e.g., `company_languages`).
- Add `INDEX` on every foreign key column and on frequently-filtered columns: `user_master(company_id, status)`, `training_history(user_id, status)`, `certificates(certificate_number)`.
- Add a `CHECK` constraint (MySQL 8.0.16+) on `assessment_result.score BETWEEN 0 AND 100`.
- All `password_hash` columns store **bcrypt/argon2 hashes only** — never plaintext, never reversible encryption.
- Soft-delete pattern: add `is_deleted BOOLEAN DEFAULT FALSE` to `user_master` and `company_master` instead of hard deletes, so audit trail and certificates referencing old users still resolve.

### 4.4 Migrations
Use **Alembic** from day one. Never hand-edit the production schema. Every schema change = one Alembic migration file, committed to Git, applied via CI/CD pipeline before the new backend version deploys.

---

## 5. Backend Architecture (FastAPI)

### 5.1 Project structure (layered, no circular imports)
```
backend/
├── app/
│   ├── main.py                  # FastAPI app instance, middleware registration
│   ├── core/
│   │   ├── config.py            # Pydantic Settings (reads env vars)
│   │   ├── security.py          # JWT encode/decode, password hashing
│   │   └── logging.py
│   ├── db/
│   │   ├── session.py           # async SQLAlchemy engine/session
│   │   └── base.py
│   ├── models/                  # SQLAlchemy ORM models (1 file per table group)
│   ├── schemas/                 # Pydantic request/response models
│   ├── repositories/            # raw DB query layer (no business logic)
│   ├── services/                # business logic (validation, workflows)
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── company.py
│   │       ├── users.py
│   │       ├── videos.py
│   │       ├── assessments.py
│   │       ├── certificates.py
│   │       ├── reports.py
│   │       └── router.py        # combines all routers
│   ├── workers/                 # Celery tasks
│   └── tests/
├── alembic/
├── Dockerfile
├── requirements.txt
└── pyproject.toml               # ruff/black/mypy config
```
**Why layered:** Routers (`api/`) never talk to the DB directly — they call `services/`, which call `repositories/`. This means you can unit-test business logic without spinning up a database, and swapping MySQL for Postgres later only touches `repositories/`.

### 5.2 API versioning
All routes prefixed `/api/v1/...`. When breaking changes are needed later, ship `/api/v2/...` alongside it rather than breaking existing clients — this is the standard way to avoid "loose ends" in API contracts.

### 5.3 Endpoint map (high-level, by portal)

**Auth (public)**
```
POST /api/v1/auth/signup
POST /api/v1/auth/verify-otp
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
POST /api/v1/auth/forgot-password
POST /api/v1/auth/reset-password
```

**Admin Portal** (`role: Super Admin`)
```
POST/GET/PUT  /api/v1/companies
PATCH         /api/v1/companies/{id}/status
GET/POST/PUT  /api/v1/users
POST          /api/v1/users/{id}/reset-password
GET/POST/PUT  /api/v1/videos
PATCH         /api/v1/videos/{id}/publish
GET/POST      /api/v1/certificate-templates
GET           /api/v1/analytics/*
GET           /api/v1/audit-logs
```

**HR Portal** (`role: HR`, scoped to own `company_id`)
```
POST  /api/v1/hr/employees/bulk-upload
GET   /api/v1/hr/employees
POST  /api/v1/hr/training/assign
GET   /api/v1/hr/compliance/dashboard
GET   /api/v1/hr/reports/{type}
```

**Employee Portal** (`role: Employee`, scoped to own `user_id`)
```
GET   /api/v1/employee/courses
GET   /api/v1/employee/videos/{id}/stream-url     # short-lived signed URL
POST  /api/v1/employee/videos/{id}/progress
POST  /api/v1/employee/assessments/{id}/submit
GET   /api/v1/employee/certificates
GET   /api/v1/employee/certificates/{id}/download
GET   /api/v1/employee/training-history
```

**Public**
```
GET   /api/v1/certificates/verify/{certificate_number}   # QR code landing page
```

### 5.4 RBAC enforcement
Every protected endpoint uses a FastAPI dependency:
```python
def require_permission(permission_name: str):
    def checker(current_user = Depends(get_current_user)):
        if permission_name not in current_user.permissions:
            raise HTTPException(403, "Forbidden")
        return current_user
    return checker

@router.post("/videos", dependencies=[Depends(require_permission("Training_Assign"))])
```
Permissions come from `role_permission` joined at login time and embedded as claims in the JWT (re-validated against DB on sensitive actions, since JWT claims can go stale if an admin revokes access mid-session — see §7.4).

### 5.5 Tenant isolation (critical — prevents cross-company data leaks)
Add a SQLAlchemy-level guard so **every** query for company-scoped tables automatically filters by `company_id` from the authenticated user's token — never trust a `company_id` passed in the request body/query params for non-Super-Admin roles.

---

## 6. Authentication, Authorization & Session Management

### 6.1 Signup flow (matches your Signup Screen doc)
```
User fills form → client-side validation (Zod) → POST /signup
  → server re-validates everything (never trust client validation alone)
  → check duplicate email (case-insensitive)
  → hash password (bcrypt, cost factor 12)
  → generate 6-digit OTP, hash it, store in otp_verification, expire in 10 min
  → send OTP via email (Celery async task)
  → user submits OTP → POST /verify-otp → mark user Active
```

### 6.2 Login flow (matches your Login Screen doc)
```
POST /login {email, password}
  → trim/normalize email
  → check account_lockout: if locked_until > now → reject (423 Locked)
  → fetch user, verify bcrypt hash
  → on failure: increment login_attempts, log to login_attempts table
      if failed_attempts >= 5 → set locked_until = now + 15 min
  → on success: reset failed_attempts, issue JWT access (15 min) + refresh (7 days)
      store refresh token hash in refresh_tokens, log to audit_logs
  → check user.status == 'Active' and company.status == 'Active', else reject
```

### 6.3 JWT design
- **Access token**: 15 min expiry, contains `user_id, company_id, role_id, permissions[]`.
- **Refresh token**: 7 day expiry, opaque random string, **hashed before storing in DB** (so a DB leak doesn't leak usable tokens), rotated on every use (old one revoked = prevents replay).
- Tokens transmitted via **httpOnly, Secure, SameSite=Strict cookies** (not localStorage) — this single decision blocks the most common XSS-token-theft attack.

### 6.4 SSO / Entra ID
`user_master.login_type` already supports `SSO`/`Entra ID`. Implement via OAuth2/OIDC using `python-jose` + Microsoft's OIDC discovery endpoint (Entra ID = Azure AD). Open-source library: `authlib`.

### 6.5 Session/logout
- Logout: revoke refresh token in DB, clear cookies. Access token still valid until natural 15-min expiry (acceptable — keep it short).
- "No back-button access after logout" (your requirement #21): enforced client-side via route guards checking auth state on every navigation + server-side because the access token genuinely expires/refresh is revoked.

---

## 7. Security Checklist (mapped to your documents + OWASP Top 10)

| # | Requirement (from your docs) | Implementation |
|---|---|---|
| 1 | SQL Injection prevention | SQLAlchemy ORM only — **never** string-concatenate SQL. Parameterized queries everywhere. |
| 2 | HTTPS enforced | TLS terminated at Nginx/Traefik; HTTP→HTTPS redirect; HSTS header. |
| 3 | Brute-force lockout (5 attempts/15 min) | `account_lockout` table + Redis-backed rate limiter (`slowapi`) per IP and per email. |
| 4 | Password never plaintext | bcrypt hash only, `password_hash` column, never logged, never returned in any API response. |
| 5 | Password complexity (8–15 chars, mixed case, number, special char) | Enforced both client-side (Zod regex) and server-side (Pydantic validator) — server is the real gate. |
| 6 | XSS | React auto-escapes by default; never use `dangerouslySetInnerHTML`; CSP header set at Nginx. |
| 7 | CSRF | SameSite=Strict cookies + CSRF token for state-changing requests as defense-in-depth. |
| 8 | Video URL not publicly accessible | Pre-signed, short-lived (5 min) S3/Blob URLs generated per request; never store permanent public URLs. |
| 9 | Unauthorized video access blocked | Backend checks `course_assignment` + `training_history` before issuing a signed URL. |
| 10 | File upload validation (video formats, 500MB limit) | MIME-type + magic-byte check (not just extension) server-side; size limit enforced at Nginx (`client_max_body_size`) and FastAPI. |
| 11 | Excel bulk upload validation | Schema validation (pandas + pydantic) for every row; reject `.exe`/script-injection in cell values (CSV injection defense: prefix `=`, `+`, `-`, `@` with `'`). |
| 12 | Audit logging | Every create/update/delete/login/download writes to `audit_logs` with `user_id, action, table_name, record_id, ip_address, timestamp`. |
| 13 | Secrets management | Never commit `.env`. Use Docker secrets / Kubernetes Secrets / cloud Secret Manager (AWS Secrets Manager, Azure Key Vault, GCP Secret Manager — pick based on cloud). |
| 14 | Data isolation per company | Tenant-scoping guard (§5.5) on every query touching company-scoped tables. |
| 15 | Encryption at rest | MySQL TDE / disk encryption (cloud-managed DB handles this); S3/Blob server-side encryption enabled by default. |
| 16 | Dependency vulnerabilities | `pip-audit` + `npm audit` run in CI on every PR; Dependabot enabled (free, GitHub-native). |
| 17 | Container security | Run containers as non-root user; scan images with `trivy` (open-source) in CI before push. |
| 18 | Rate limiting (general API abuse) | `slowapi` (FastAPI) + Nginx `limit_req` as a second layer. |
| 19 | Security headers | `secure` headers middleware: `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Content-Security-Policy`. |
| 20 | Certificate QR verification can't be spoofed | `certificate_number` is a UUID/non-sequential token; verification endpoint is read-only and rate-limited. |

---

## 8. Frontend Architecture (React)

```
frontend/
├── src/
│   ├── app/                  # app shell, providers, router config
│   ├── features/             # feature-sliced: auth, admin, hr, employee, video, certificates
│   │   └── auth/
│   │       ├── components/
│   │       ├── hooks/
│   │       ├── api.ts        # TanStack Query hooks calling backend
│   │       └── schema.ts     # Zod validation schema
│   ├── components/ui/        # shared design-system components
│   ├── lib/                  # axios instance, auth interceptor, utils
│   ├── routes/                # role-based route guards
│   └── i18n/                  # English/Hindi/Tamil/Telugu/Kannada/Malayalam (matches your multi-language requirement)
├── Dockerfile
├── nginx.conf                 # serves the built static files
└── package.json
```

Key practices:
- **Role-based route guarding**: a `<ProtectedRoute role="HR">` wrapper checks the decoded JWT claims before rendering — combined with backend RBAC, never frontend-only.
- **Axios interceptor** auto-refreshes the access token on 401 using the refresh-token cookie, retries the original request once, and force-logs-out on second failure.
- **Accessibility**: every form field has a linked `<label>`, uses `aria-*` attributes, color contrast checked with `axe-core` in CI (your requirement #35–38).
- **i18n**: `react-i18next` for all six languages from day one — retrofitting i18n later is painful.
- **Video player**: `video.js` or `plyr` (open-source) wrapping HTML5 `<video>`, custom controls to disable fast-forward seeking (your requirement: backward seek allowed, forward blocked) by intercepting the `seeking` event and comparing against `furthestWatchedTime`.

---

## 9. Video Streaming & Certificate Module Flows

### 9.1 Secure video streaming sequence
```
Employee opens course
  → frontend calls GET /employee/videos/{id}/stream-url
  → backend verifies: user assigned this course + company active + user active
  → backend generates pre-signed S3/Blob URL (expires in 5 min)
  → frontend loads URL into video.js player
  → player POSTs progress every 10s to /employee/videos/{id}/progress
  → backend updates training_history.last_watched_position + completion_percent
  → on completion_percent >= 95% → status = Completed → assessment unlocked
```

### 9.2 Certificate generation flow
```
Employee passes assessment (score >= passing_score)
  → Celery task triggered: generate_certificate(user_id, video_id)
      1. Generate unique certificate_number (e.g., POSH-2026-000123, via DB sequence/UUID)
      2. Generate QR code (qrcode library, open-source) encoding verification URL
      3. Render PDF (WeasyPrint or ReportLab, both open-source) using certificate_template
      4. Upload PDF to object storage, store path in certificates.pdf_path
      5. Insert row into certificates table, status='Valid'
      6. Send email with PDF attached (Celery + SMTP, or SES/SendGrid)
      7. Write audit_logs entry
```

### 9.3 QR verification (public endpoint)
```
GET /api/v1/certificates/verify/{certificate_number}
  → public, rate-limited, read-only
  → returns: employee name (masked partially if you want privacy), course, date, status
  → if status == 'Revoked' → show revoked clearly
```

---

## 10. Docker & Deployment

### 10.1 Local development — `docker-compose.yml`
Services: `frontend`, `backend`, `mysql`, `redis`, `celery-worker`, `minio` (local S3 substitute), `nginx`. One command (`docker compose up`) gives a newbie a fully working environment identical to production — this is the single most important thing for "no loose ends" in dev/prod parity.

```yaml
version: "3.9"
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_DATABASE: posh_db
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
    volumes: [mysql_data:/var/lib/mysql]
  redis:
    image: redis:7-alpine
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
  backend:
    build: ./backend
    env_file: .env
    depends_on: [mysql, redis, minio]
  celery-worker:
    build: ./backend
    command: celery -A app.workers.celery_app worker --loglevel=info
    depends_on: [redis, mysql]
  frontend:
    build: ./frontend
    depends_on: [backend]
  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    depends_on: [frontend, backend]
volumes:
  mysql_data:
```

### 10.2 Dockerfiles (multi-stage, minimal images)
- **Backend**: `python:3.12-slim` base, multi-stage to keep image small, non-root user, `HEALTHCHECK` directive hitting `/health`.
- **Frontend**: stage 1 `node:20-alpine` builds static assets (`npm run build`), stage 2 `nginx:alpine` just serves the `dist/` folder — final image has no Node.js or source code in it at all.

### 10.3 Cloud-agnostic abstraction
- **Storage**: use `boto3` against any S3-compatible endpoint — works unmodified against AWS S3, MinIO (self-hosted), or Azure Blob (via its S3-compatible gateway) / Backblaze B2. Only the endpoint URL + credentials change per environment via env vars.
- **Database**: standard MySQL connection string — works against AWS RDS, Azure Database for MySQL, GCP Cloud SQL, or a self-managed MySQL container, unchanged.
- **Secrets**: read from env vars at runtime; injected differently per platform (Kubernetes Secrets, AWS Secrets Manager via CSI driver, Azure Key Vault, Docker Swarm secrets) but the app code only ever does `os.environ["DB_PASSWORD"]`.

### 10.4 Production orchestration
Recommended path for a newbie team: start with **Docker Compose on a single VM** (cheapest, simplest, works on any cloud's basic compute instance) → migrate to **Kubernetes (managed: EKS/AKS/GKE, or k3s on VMs for cost control)** once you need auto-scaling/multi-region. The same Docker images work in both — only the deployment manifest changes, never the app.

### 10.5 Deployment checklist
- [ ] TLS certificates via Let's Encrypt (`cert-manager` in k8s, or `certbot` on a single VM)
- [ ] Database backups: automated daily MySQL dumps to object storage, tested restore monthly
- [ ] Horizontal pod autoscaling on backend (CPU/memory threshold)
- [ ] Readiness/liveness probes on every container
- [ ] Blue-green or rolling deployment (zero downtime)
- [ ] Environment-specific config via `.env.dev`, `.env.staging`, `.env.prod` — never hardcoded

---

## 11. CI/CD Pipeline (GitHub Actions)

```
.github/workflows/
├── ci.yml          # on every PR: lint, type-check, unit test, build
├── security.yml     # on every PR: trivy image scan, pip-audit, npm audit
└── deploy.yml        # on merge to main / tag: build images, push to registry, deploy
```

**ci.yml stages:**
1. `ruff` + `black --check` + `mypy` (backend) / `eslint` + `tsc --noEmit` (frontend)
2. `pytest --cov` (backend) / `vitest run --coverage` (frontend) — fail if coverage drops below threshold (e.g. 80%)
3. `docker build` both images (catches Dockerfile errors early)
4. Alembic migration dry-run against a throwaway MySQL container

**deploy.yml stages (on tag push):**
1. Build + tag Docker images with the Git tag
2. Push to container registry (GitHub Container Registry — free, open — or Docker Hub)
3. Run `trivy` scan — block deploy on HIGH/CRITICAL vulnerabilities
4. Apply Alembic migrations against target DB
5. Roll out new image (`kubectl set image` / `docker compose pull && up -d` / Helm upgrade)
6. Smoke test `/health` endpoint post-deploy; auto-rollback on failure

---

## 12. Testing Strategy

| Layer | Tool (open-source) | What's tested |
|---|---|---|
| Backend unit | `pytest` + `pytest-asyncio` | Service-layer business logic, validators, RBAC checks — mocked DB |
| Backend integration | `pytest` + `testcontainers` (spins real MySQL in Docker) | Repository layer, actual SQL, migrations |
| API/contract | `pytest` + FastAPI `TestClient` | Every endpoint: happy path + each validation rule from your docs (e.g. all 42 login requirements as individual test cases) |
| Frontend unit | `Vitest` + `React Testing Library` | Components, form validation logic |
| E2E | `Playwright` | Full user journeys: signup→OTP→login→watch video→assessment→certificate download, across Chrome/Firefox/Safari/Edge (your requirement #12) |
| Accessibility | `axe-core` (via Playwright plugin) | WCAG contrast, labels, keyboard nav |
| Security | OWASP ZAP (automated baseline scan in CI), `pip-audit`, `npm audit`, `trivy` | Known CVEs, basic pentest checks |
| Load/perf | `Locust` (Python, open-source) | Concurrent video streaming, login under brute-force simulation, bulk upload of 10k+ rows |
| Manual exploratory | — | Run your existing test-case documents (Login, Signup, Video) as a manual regression checklist before each release |

**Test data strategy**: seed scripts (`backend/app/db/seed.py`) create deterministic fake companies/users/videos for local + CI testing — never test against production-like real data.

---

## 13. Open-Source Tooling Summary (everything used above)

| Purpose | Tool |
|---|---|
| Backend framework | FastAPI |
| ORM/migrations | SQLAlchemy, Alembic |
| Validation | Pydantic, Zod |
| Auth | python-jose, passlib, authlib |
| Background jobs | Celery, Redis |
| Object storage | MinIO (self-host) / boto3 (S3-compatible) |
| PDF/QR generation | WeasyPrint or ReportLab, `qrcode` |
| Frontend framework | React, Vite, TypeScript |
| UI components | MUI or shadcn/ui + Tailwind |
| Forms | React Hook Form |
| i18n | react-i18next |
| Video player | video.js / plyr |
| Containerization | Docker, Docker Compose |
| Orchestration | Kubernetes (k3s), Helm |
| TLS | cert-manager / certbot |
| CI/CD | GitHub Actions |
| Container scanning | Trivy |
| Monitoring | Prometheus, Grafana |
| Logs | Loki + Promtail (or ELK stack) |
| Error tracking | Sentry (self-hosted) |
| Load testing | Locust |
| Security scanning | OWASP ZAP, pip-audit, npm audit |

Every single item above is free and open-source — no paid licenses required to build, test, or run the full stack.

---

## 14. Phased Delivery Roadmap

**Phase 0 — Foundations (Week 1–2)**
- [ ] Git repo created, branching/commit conventions documented in `CONTRIBUTING.md`
- [ ] Docker Compose skeleton running (empty FastAPI "hello world" + empty React app + MySQL)
- [ ] CI pipeline running lint+test on a trivial commit
- [ ] Finalize full ERD including the gap tables from §4.2; run first Alembic migration

**Phase 1 — Auth & User Management (Week 3–5)**
- [ ] Signup + OTP + Login + Forgot Password (all 42 requirements from your Login doc as test cases)
- [ ] JWT + refresh token rotation + account lockout
- [ ] RBAC middleware + role/permission seed data
- [ ] Admin: Company CRUD, User CRUD

**Phase 2 — Content & Learning (Week 6–9)**
- [ ] Video upload/publish (Admin), pre-signed streaming URLs
- [ ] Employee video player with resume/no-fast-forward/subtitles
- [ ] Assessment engine (MCQ/scenario/true-false), scoring, pass/fail
- [ ] Progress tracking dashboard

**Phase 3 — HR Operations (Week 10–12)**
- [ ] Bulk Excel/CSV employee upload + validation + error report
- [ ] Training assignment (individual/department/company-wide)
- [ ] Compliance dashboard + reports (Excel/CSV/PDF export)

**Phase 4 — Certificates & Analytics (Week 13–15)**
- [ ] Certificate template management
- [ ] Auto certificate generation (Celery) + QR + email
- [ ] Public verification endpoint
- [ ] Admin analytics module + audit log viewer

**Phase 5 — Hardening & Launch (Week 16–18)**
- [ ] Full security checklist (§7) verified
- [ ] Load testing with Locust at expected peak concurrency
- [ ] Penetration test (OWASP ZAP automated + manual review)
- [ ] Production Kubernetes/Compose setup, monitoring/alerting live
- [ ] Backup/restore drill completed
- [ ] Soft launch with one pilot company → monitor → full rollout

---

## 15. Master Checklist (Quick Reference)

- [ ] **Repo & Git**: monorepo created, GitHub Flow branching, Conventional Commits, branch protection on `main`
- [ ] **Database**: all 11 original + 9 gap tables created, indexes on every FK, Alembic migrations versioned
- [ ] **Backend**: layered architecture (routers/services/repositories), `/api/v1` versioned, async SQLAlchemy
- [ ] **Auth**: bcrypt hashing, JWT access+refresh, httpOnly cookies, OTP signup, lockout after 5 attempts/15 min
- [ ] **RBAC**: role_permission enforced via dependency injection on every endpoint, tenant isolation guard
- [ ] **Frontend**: feature-sliced React+TS, RHF+Zod validation matching every rule in your Signup/Login docs, i18n for 6 languages, accessibility tested
- [ ] **Video**: pre-signed URLs, no public access, resume playback, no-forward-seek, multi-language subtitles
- [ ] **Certificates**: Celery-generated PDF+QR, public verification endpoint, revocation support
- [ ] **Security**: full §7 checklist signed off, dependency + container scanning in CI
- [ ] **Docker**: multi-stage Dockerfiles, non-root users, Compose for local dev, health checks
- [ ] **CI/CD**: lint/test/build/scan on every PR, automated deploy on tag, smoke test + rollback
- [ ] **Cloud**: storage and DB access abstracted behind env-var config, deployable to any of AWS/Azure/GCP unchanged
- [ ] **Monitoring**: Prometheus+Grafana dashboards, centralized logs, Sentry error tracking, audit_logs populated for every sensitive action
- [ ] **Testing**: unit + integration + E2E (Playwright) + accessibility + load + security scans, all automated in CI
- [ ] **Docs**: README with one-command local setup, API docs auto-generated (FastAPI's built-in OpenAPI/Swagger UI), this roadmap kept updated as source of truth

---

*Next step suggestion: start with Phase 0 — get `docker compose up` running an empty FastAPI + React + MySQL stack with CI green on a trivial PR. Everything else builds on that foundation being solid.*

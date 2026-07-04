# POSH Training Platform — What You Built & How to Run It

A quick-reference guide pulled together from your Phase 0–5 build docs.

---

## 1. What This Project Actually Is

A **multi-tenant SaaS platform** for companies to deliver mandatory **POSH (Prevention of Sexual Harassment) training** to their employees: upload training videos, run assessments, track completion, and issue verifiable certificates.

"Multi-tenant" = many companies share one deployment, but each company's data is walled off by `company_id`.

**Tech stack:**
| Layer | Tech |
|---|---|
| Backend | FastAPI (Python, async) |
| Database | MySQL + SQLAlchemy (ORM) + Alembic (migrations) |
| Auth | JWT (access + refresh tokens) + bcrypt password hashing |
| Background jobs | Celery + Redis |
| File storage | MinIO (S3-compatible) — for videos/certificates |
| Email | SMTP in prod, MailHog in dev (fake inbox you can view in browser) |
| Frontend | React (Vite, plain JavaScript) |
| Containerization | Docker Compose (7 services) |
| Deployment | Cloud VM, Nginx, Let's Encrypt TLS |

---

## 2. The 4 Roles — Who Can Do What

| Role | role_id | What they do |
|---|---|---|
| **Super Admin** | 1 | Manages the whole platform. Creates/activates/deactivates **companies**. Sees platform-wide analytics. |
| **Company Admin** | 2 | Manages their own company. Can manage users within their company. |
| **HR** | 3 | Bulk-uploads employees, assigns training, views compliance dashboards & Excel reports for their company. |
| **Employee** | 4 | Watches assigned training videos (no fast-forwarding allowed), takes assessments, downloads their certificate. |

Role is embedded in the JWT at login (`role_id`, `permissions`, `company_id`), and every protected endpoint checks it via `require_roles([...])` — this is enforced server-side, not just hidden in the UI.

**Important default:** anyone who signs up via the public `/auth/signup` form is automatically created as an **Employee** (role_id=4). Admin/HR/Company Admin accounts are *not* self-service — they have to be created by a Super Admin/Admin through the user-management API (or manually in the DB, see §4.4 below for your very first admin).

---

## 3. Feature Map (what exists, by phase)

| Phase | Delivered |
|---|---|
| Phase 0 | Repo, Docker Compose, FastAPI skeleton, React skeleton, CI pipeline |
| Phase 1 | Signup/OTP/login/logout/forgot-password, JWT + RBAC, brute-force lockout, Company CRUD, User CRUD |
| Phase 2 | Video upload, secure streaming, watch-progress tracking, no-fast-forward enforcement, assessments (submit/score/pass-fail) |
| Phase 3 | HR bulk employee upload, training assignment, compliance dashboard, Excel reports |
| Phase 4 | Certificate generation (PDF + QR code), public certificate verification, analytics module |
| Phase 5A | Real SMTP email delivery, certificate generation moved to Celery (background), dev-only OTP shortcuts removed |
| Phase 5B | React frontend — **auth screens only** (login/signup/OTP/forgot-password), routing, role-based route guards |
| Phase 5C | Rate limiting, security headers, HTTPS |
| Phase 5D | Production Docker Compose, cloud VM deployment guide, TLS |

### Backend API surface
| Prefix | Covers | Who can call it |
|---|---|---|
| `/api/v1/auth` | Signup, login, OTP, logout, password reset | Public |
| `/api/v1/companies` | Company CRUD, activate/deactivate | Super Admin |
| `/api/v1/users` | User CRUD, reset password | Admin, HR |
| `/api/v1/videos` | Upload, publish, stream, progress | Admin (upload) / Employee (watch) |
| `/api/v1/assessments` | Submit answers, scoring | Employee |
| `/api/v1/hr` | Bulk upload, assign training, compliance | HR |
| `/api/v1/certificates` | List/download/verify/revoke | Employee / Public (verify) / Admin (revoke) |
| `/api/v1/analytics` | Platform + company stats | Admin |

### ⚠️ What's *not* built yet
Only the **auth screens** exist in the React frontend so far. The Admin Portal, HR Portal, Employee Portal, and Video Player are all backend-complete but currently just placeholder pages in React — the actual tables/forms/dashboards for those haven't been built. So right now you can fully exercise the platform via the Swagger docs (`/docs`), but not yet click through a finished UI for HR/Admin/Employee workflows.

---

## 4. Running It Locally

### 4.1 Start everything
```bash
cd posh-platform
docker compose up --build
```
This starts 7 containers: backend, mysql, redis, minio, mailhog, celery worker, frontend.

### 4.2 URLs once it's running
| URL | What it is |
|---|---|
| http://localhost | React frontend |
| http://localhost:8000/docs | Swagger — interactive API docs, use this to test any endpoint as any role |
| http://localhost:8000/health | Backend health check |
| http://localhost:8025 | MailHog — view OTP/reset/certificate emails sent in dev |
| http://localhost:9001 | MinIO console (login `minioadmin` / `minioadmin123`) — see uploaded videos/certs |

### 4.3 First-time database setup
```bash
cd backend
python -m app.db.seed
```
This inserts the 4 roles (Super Admin/Company Admin/HR/Employee) and a default company. Run `alembic upgrade head` first if migrations haven't been applied.

### 4.4 Getting your first Admin/HR account (since signup only creates Employees)
Two options:
1. **Quick/dev way:** connect to MySQL directly and bump a user's `role_id` after they sign up:
   ```bash
   docker exec -it posh_mysql mysql -u posh_user -pchangeme_password posh_db
   UPDATE user_master SET role_id = 1 WHERE email = 'you@test.com';  -- 1 = Super Admin
   ```
2. **Proper way, once you have one admin:** log in as that admin and use `POST /api/v1/users/` (Swagger `/docs`) to create HR/Employee accounts for the company with the desired `role_id`.

### 4.5 Testing as each role
1. Sign up a user at `/docs` → `POST /api/v1/auth/signup` (or via the frontend).
2. Check MailHog (`localhost:8025`) for the OTP email, verify it via `/verify-otp`.
3. Log in via `/login` — the JWT you get back encodes that user's `role_id`/`company_id`/permissions.
4. In Swagger, use the "Authorize" button and paste the token to test role-protected endpoints (you'll get `403 Forbidden` if you try an endpoint your role doesn't have permission for — that's expected behavior, not a bug).
5. To act as a different role, either promote a user via the DB (§4.4) or have your Super Admin/Admin account create one with the role you want.

---

## 5. How Backend & Frontend Fit Together

```
React (Vite, port 80)  →  calls  →  FastAPI (port 8000)  →  queries  →  MySQL
                                          │
                                          ├── Celery worker (async jobs: emails, certificate PDFs)
                                          ├── Redis (job queue + rate limiting)
                                          └── MinIO (video files, generated certificate PDFs)
```

- Every backend request flows: **Router → dependency injection (auth/DB) → Pydantic validation → Service layer (business logic) → SQLAlchemy (DB) → JSON response.**
- The frontend never talks to MySQL/MinIO directly — everything goes through the FastAPI JSON API.
- Auth: JWT is issued at login and used on every subsequent request to identify the user's role and company — this is what makes the RBAC and multi-tenant isolation actually enforceable.

---

## 6. Suggested Next Step

Since backend is fully built through Phase 5 but the frontend only has auth screens, the natural next step is building out the **Admin/HR/Employee portal screens** in React — each one just needs to call APIs you've already built (TanStack Query + a table/form), following the exact pattern used for the auth screens.

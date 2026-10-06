# POSH Platform Project Overview

This document is a current, LLM-friendly map of the repository. It is intended to be supplied with a change request so another developer or LLM can understand the system boundaries, important files, workflows, and validation commands quickly.

## Product Summary

POSH Platform is a multi-role workplace POSH (Prevention of Sexual Harassment) compliance portal. It supports company/work-order management, user hierarchy and role-based access, employee training videos, assessments, certificates, concerns, POSH policies, notifications, analytics, annual returns, and report downloads.

The application is a Docker-oriented full-stack system:

- Frontend: React 19 + Vite + React Router + Material UI + Zustand + Axios.
- Backend: FastAPI + SQLAlchemy async + Pydantic + Alembic.
- Database: MySQL, accessed through `asyncmy` at runtime and `pymysql` for migrations.
- Background infrastructure: Redis and Celery.
- File/object storage: MinIO or S3-compatible storage for videos, PDFs, and certificates.
- Email: SMTP through `aiosmtplib`.
- Browser verification: Selenium smoke tests.

## Repository Tree

Generated build output, dependency directories, local environment files, and large E2E report artifacts are intentionally excluded from this prompt-friendly tree. The source and configuration files are listed below.

```text
posh-platform/
|-- .agents/                         Agent/project metadata
|-- .codex/                          Local Codex metadata, if present
|-- .github/
|   `-- workflows/
|       `-- ci.yml                   CI workflow
|-- backend/
|   |-- app/
|   |   |-- api/v1/                  FastAPI route modules
|   |   |-- core/                    Settings, auth, email, storage, dependencies
|   |   |-- db/                      Async session, metadata, seed helpers
|   |   |-- models/                  SQLAlchemy models
|   |   |-- repositories/            Repository package placeholder
|   |   |-- schemas/                 Pydantic request/response schemas
|   |   |-- services/                Domain/business logic
|   |   |-- workers/                 Celery configuration
|   |   `-- main.py                  FastAPI app, middleware, routers, startup seed
|   |-- alembic/
|   |   |-- versions/                Database migration history
|   |   |-- env.py
|   |   |-- README
|   |   `-- script.py.mako
|   |-- migrations/                  Legacy/alternate migration directory
|   |   |-- env.py
|   |   |-- README
|   |   `-- script.py.mako
|   |-- scripts/
|   |   `-- repair_legacy_schema.py  Schema repair utility
|   |-- tests/                       Pytest tests
|   |   |-- test_auth.py
|   |   |-- test_certificates.py
|   |   |-- test_health.py
|   |   |-- test_hr.py
|   |   `-- test_video.py
|   |-- Dockerfile
|   |-- alembic.ini
|   |-- pyproject.toml
|   `-- requirements.txt
|-- docs/
|   `-- DEPLOYMENT_COST_COMPARISON.md
|-- e2e/
|   |-- selenium_full_project_smoke.py
|   |-- requirements.txt
|   |-- README.md
|   `-- reports/                    Generated JSON, screenshots, downloads
|-- frontend/
|   |-- public/
|   |   |-- config.js               Runtime frontend configuration
|   |   |-- favicon.svg
|   |   `-- icons.svg
|   |-- src/
|   |   |-- api/                    Axios client and API helpers
|   |   |-- assets/                 Images and SVG assets
|   |   |-- components/             Shared shell/loading/session UI
|   |   |-- features/               Page modules by role/domain
|   |   |-- routes/                 Protected and role route guards
|   |   |-- store/                  Zustand auth state
|   |   |-- styles/                 Shared style helpers
|   |   |-- utils/                  Access-control helpers
|   |   |-- App.jsx                 Frontend route definitions
|   |   |-- App.css
|   |   |-- index.css
|   |   `-- main.jsx                React bootstrap
|   |-- Dockerfile
|   |-- docker-entrypoint.sh
|   |-- eslint.config.js
|   |-- folder-structure.md         Older frontend-focused structure notes
|   |-- index.html
|   |-- nginx.conf
|   |-- nginx.prod.conf.template
|   |-- package.json
|   |-- package-lock.json
|   |-- railway.json
|   |-- vercel.json
|   `-- vite.config.js
|-- .env                            Local secrets/config; never paste into an LLM
|-- .env.example                    Safe environment variable template
|-- .env.prod                       Production-style environment config
|-- .gitignore
|-- docker-compose.yml              Local stack
|-- docker-compose.prod.yml         Production-oriented stack
`-- posh_schema.sql                 SQL schema file; currently empty in this checkout
```

## Backend File Map

### API routes: `backend/app/api/v1/`

| File | Responsibility |
|---|---|
| `auth.py` | Login, refresh/logout, signup, OTP, password reset, Entra SSO. |
| `company.py` | Companies, work orders, approval, registration, employee master, client admin creation. |
| `users.py` | User hierarchy and user CRUD. |
| `admin.py` | Admin utility endpoints. |
| `admin_config.py` | Master codes, POSH offices, role-access matrix. |
| `videos.py` | Video upload, metadata, publishing, language/quality, playback. |
| `hr.py` | Bulk upload, employee listing, training assignment, compliance. |
| `employee.py` | Employee courses, history, certificates, progress. |
| `assessments.py` | Questions, attempts, scoring, assessment results. |
| `certificates.py` | Certificate templates, issue/download, public verification. |
| `concerns.py` | Employee concern submission and admin review/closure. |
| `policy.py` | Company POSH policy upload/view/update and acknowledgements. |
| `notifications.py` | Notification listing and status operations. |
| `analytics.py` | Analytics and dashboard/report data. |
| `annual_returns.py` | Annual-return workflows and report data. |

All routers are mounted by `backend/app/main.py` below the `/api/v1` prefix. The app also configures CORS, rate limiting, production HTTPS redirect, and a health endpoint. API documentation is disabled in the current app configuration.

### Core and persistence

| Path | Responsibility |
|---|---|
| `app/core/config.py` | Pydantic settings loaded from `.env`. |
| `app/core/security.py` | Bcrypt password hashing, JWT access tokens, refresh-token hashing, OTP generation. |
| `app/core/dependencies.py` | Current-user lookup and role/permission authorization dependencies. |
| `app/core/email.py` | SMTP messages for OTP, reset, welcome, certificate, and approval flows. |
| `app/core/storage.py` | MinIO/S3-compatible file storage helper. |
| `app/db/session.py` | Async SQLAlchemy engine and transaction-scoped session dependency. |
| `app/db/base.py` | SQLAlchemy metadata/model imports. |
| `app/db/seed.py` | Reference data and default-user seeding helpers. |
| `app/models/*.py` | Database models for auth, users, companies, roles, training, videos, HR, policies, concerns, notifications, certificates, analytics, and annual returns. |
| `app/schemas/*.py` | Typed API input/output contracts grouped by domain. |

### Services

The route modules handle HTTP concerns and delegate substantial business logic to services:

| File | Main domain |
|---|---|
| `assessment_service.py` | Assessment attempts, scoring, completion/certificate triggers. |
| `auth_service.py` | Login lifecycle, OTP, lockout, refresh, password reset. |
| `certificate_service.py` | Certificate templates, PDF generation, issuance and verification. |
| `company_service.py` | Company/work-order/registration/employee-master workflows. |
| `employee_service.py` | Employee course and training-history operations. |
| `hr_service.py` | Bulk employee import, assignments, compliance, HR reports. |
| `notification_service.py` | Notification creation and retrieval. |
| `policy_ack_service.py` | Policy acknowledgement behavior. |
| `user_service.py` | User creation, hierarchy, credentials, and password support. |
| `video_service.py` | Video metadata, files, languages, qualities, publishing, progress. |
| `audit_service.py` | Audit log writes. |

### Migrations and tests

`backend/alembic/versions/` contains the migration history, including initial company/role/user tables, video/training, HR/notifications, certificates/analytics, and auth changes. There are also newer migration-support files under `backend/migrations/`; check the configured Alembic path before adding a migration.

Backend tests currently cover health, auth, certificates, HR, and videos. They use pytest and pytest-asyncio as configured in `backend/pyproject.toml`.

## Frontend File Map

### Shared application infrastructure

| Path | Responsibility |
|---|---|
| `src/main.jsx` | Creates the React root and loads global CSS. |
| `src/App.jsx` | Defines public, protected, role-specific, and feature routes. |
| `src/api/client.js` | Axios instance, `/api/v1` base path, bearer-token injection, refresh-on-401. |
| `src/api/auth.js` | Authentication API helpers. |
| `src/api/errors.js` | Normalizes API errors for UI display. |
| `src/store/authStore.js` | Persists auth user/token in local storage and handles logout. |
| `src/routes/ProtectedRoute.jsx` | Redirects unauthenticated users to login. |
| `src/routes/RoleRoute.jsx` | Enforces role, permission, and role-access-matrix rules. |
| `src/utils/accessControl.js` | Frontend access checks. |
| `src/components/PortalShell.jsx` | Main authenticated layout, navigation, notifications, search, concern UI. |
| `src/components/SessionTimeout.jsx` | Session timeout behavior. |
| `src/components/LoadingOverlay.jsx` | Shared loading state. |
| `src/index.css`, `src/App.css` | Global and app-specific styling. |

### Feature pages

| Folder | Main screens |
|---|---|
| `features/auth/` | Login, signup, OTP, forgot/reset/change password, owner setup, Entra callback, unauthorized. |
| `features/landing/` | Public landing page and POSH service page. |
| `features/dashboard/` | Common statistics/home dashboard. |
| `features/admin/` | Admin/Super Admin dashboards, companies, work orders, users, employee master, masters, policies, videos, reports, analytics, concerns, annual returns, certificates, role access. |
| `features/hr/` | HR dashboard, bulk upload, training assignment, compliance, reports. |
| `features/employee/` | Employee dashboard, courses, video player, assessment, history, certificates, concerns. |
| `features/certificates/` | Public certificate verification. |
| `features/policy/` | POSH policy view/upload/update and acknowledgement UI. |

## Main User Roles and Flows

- Super Admin: platform-level companies, admins, master data, role access, analytics, reports, audit, videos, certificates.
- Admin: company/work-order operations, approval-related workflows, client management, users, employees, training and reports.
- Client/Mgmt: company-specific management and compliance operations.
- HR: employee import, training assignment, compliance monitoring, reports.
- IC: Internal Committee-focused training, history, certificates, concerns and policy access.
- Employee: assigned courses, video progress, assessments, certificates, policy and concerns.

Typical cross-layer mappings:

| Workflow | Frontend | Backend |
|---|---|---|
| Authentication | `features/auth/*`, `api/auth.js`, `store/authStore.js` | `api/v1/auth.py`, `services/auth_service.py`, `core/security.py`, `core/email.py` |
| Role-based navigation | `PortalShell.jsx`, `RoleRoute.jsx`, `accessControl.js` | `core/dependencies.py`, `api/v1/admin_config.py` |
| Company/work order | `CompanyListPage.jsx`, `CompanyRegistrationPage.jsx` | `api/v1/company.py`, `services/company_service.py` |
| User hierarchy | `UserListPage.jsx`, `CreateAdminPage.jsx`, `CreateIcPage.jsx` | `api/v1/users.py`, `services/user_service.py` |
| Training | `VideoListPage.jsx`, `TrainingAssignPage.jsx`, `VideoPlayerPage.jsx` | `api/v1/videos.py`, `api/v1/hr.py`, `services/video_service.py`, `services/hr_service.py` |
| Assessment/certificate | `AssessmentPage.jsx`, `CertificatesPage.jsx`, `CertificateVerifyPage.jsx` | `api/v1/assessments.py`, `api/v1/certificates.py`, related services |
| POSH policy | `PoshPolicyPage.jsx`, `PortalShell.jsx` | `api/v1/policy.py`, `policy_ack_service.py` |
| Concerns/notifications | employee/admin concern pages and `PortalShell.jsx` | `api/v1/concerns.py`, `api/v1/notifications.py` |
| Analytics/reports | admin and HR report pages | `api/v1/analytics.py`, `api/v1/annual_returns.py`, `hr_service.py` |

## Runtime and Configuration

The local Compose stack is intended to provide MySQL, Redis, MinIO, MailHog, backend, Celery worker, and frontend. Important environment variables are defined in `.env.example`, including database, Redis, JWT, MinIO, SMTP, CORS, public URLs, and Microsoft Entra settings.

Never include `.env`, `.env.prod`, credentials, JWT secrets, SMTP passwords, MinIO passwords, or generated user passwords in a prompt to another LLM. Use `.env.example` and redact values when sharing configuration.

The frontend normally calls `/api/v1`, with the frontend web server/proxy routing requests to the backend. The backend reads environment settings from `.env`. Runtime file storage is configured for video and certificate assets.

## Commands

From the repository root:

```powershell
docker compose up --build
```

Backend:

```powershell
cd backend
pytest
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```powershell
cd frontend
npm.cmd run lint
npm.cmd run build
npm.cmd run dev
```

Browser smoke tests:

```powershell
python -m pip install -r e2e/requirements.txt
python e2e/selenium_full_project_smoke.py
```

The E2E script writes generated output to `e2e/reports/`. It can test selected roles, Edge, headed mode, shared browser mode, and optional seeded client data; see `e2e/README.md` for the full options.

## Guidance for Requesting Changes from Another LLM

Give the LLM this file plus the smallest relevant source files. Include:

1. The requested behavior and the user role(s) affected.
2. The exact page, API route, model, or workflow that should change.
3. Current behavior, desired behavior, and acceptance criteria.
4. Whether database schema/data changes are allowed; if yes, request a migration.
5. Any compatibility constraints for existing roles, tenants, files, or API responses.
6. The validation commands to run, usually backend tests plus frontend lint/build.

Useful prompt template:

```text
You are modifying the POSH Platform repository described in PROJECT_OVERVIEW.md.

Task:
<describe the change precisely>

Affected role(s): <Super Admin/Admin/Client-Mgmt/HR/IC/Employee/public>
Affected workflow/page/API: <names and paths if known>

Current behavior:
<what happens now>

Desired behavior and acceptance criteria:
- <criterion>
- <criterion>

Constraints:
- Preserve existing roles and tenant/company isolation.
- Do not expose secrets or commit environment values.
- Add/update migrations for schema changes.
- Preserve existing API contracts unless a breaking change is explicitly requested.

Please inspect the relevant files first, implement the smallest coherent change,
and run the appropriate tests/lint/build commands. Report changed files,
validation results, and any remaining risks.
```

## Current Repository Notes

- The root currently has no `README.md`; this document is the root-level project guide.
- `frontend/folder-structure.md` is an older frontend-oriented guide and may mention folders not present in the current checkout.
- `backend/app/main.py` is also responsible for a large amount of startup schema/seed compatibility work, so changes to startup behavior should be reviewed carefully.
- The project has both `backend/alembic/` and `backend/migrations/`; verify the active migration configuration before creating or applying migrations.
- `posh_schema.sql` is present but empty in this checkout; the authoritative schema is currently represented by the models, migrations, startup compatibility SQL, and seed logic.
- E2E screenshots, CSV downloads, JSON reports, and Python cache files are generated artifacts and should not be treated as application source.

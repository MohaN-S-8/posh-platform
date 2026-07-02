# POSH Platform Build Plan

This document is a practical plan for building the full POSH training platform from zero to production.
It focuses on:
- what to build,
- how to organize the folders,
- the order to build things in,
- and the minimum structure needed so the project stays maintainable.

---

## 1. Goal

Build a multi-tenant POSH training platform with:
- Admin Portal
- HR Portal
- Employee Portal
- Authentication screens

The platform should support:
- company-level isolation
- user signup and login
- role-based access control
- training video management
- employee assignment and tracking
- assessments
- certificates
- reports and analytics
- audit logs
- secure file handling

---

## 2. Recommended Repo Layout

Use a monorepo so frontend, backend, and infra stay together.

```text
posh-platform/
├── frontend/
├── backend/
├── infra/
├── docs/
├── scripts/
├── tests/
├── docker-compose.yml
├── .env.example
├── README.md
└── CONTRIBUTING.md
```

### What each folder is for

- `frontend/` - React app for all portals
- `backend/` - FastAPI app and business logic
- `infra/` - Docker, Nginx, Kubernetes, CI/CD, deployment files
- `docs/` - architecture notes, API notes, database notes, decision records
- `scripts/` - seed data, setup scripts, backup helpers, maintenance scripts
- `tests/` - shared test assets or end-to-end test helpers

---

## 3. Frontend Folder Structure

Keep the frontend feature-based so the app does not turn into one large component pile.

```text
frontend/
├── public/
├── src/
│   ├── app/
│   │   ├── providers/
│   │   ├── router/
│   │   └── layout/
│   ├── features/
│   │   ├── auth/
│   │   ├── admin/
│   │   ├── hr/
│   │   ├── employee/
│   │   ├── video/
│   │   ├── certificates/
│   │   └── reports/
│   ├── components/
│   │   └── ui/
│   ├── hooks/
│   ├── lib/
│   ├── routes/
│   ├── store/
│   ├── types/
│   ├── styles/
│   └── i18n/
├── index.html
├── vite.config.ts
├── package.json
└── tsconfig.json
```

### Frontend feature breakdown

#### Auth
- Signup
- OTP verification
- Login
- Forgot password
- Reset password
- Session handling

#### Admin
- Company management
- User management
- Role and permission management
- Video management
- Certificate template management
- Reports and analytics
- Audit logs

#### HR
- Bulk employee upload
- Training assignment
- Compliance tracking
- Progress reports

#### Employee
- Dashboard
- Assigned videos
- Video player
- Progress tracking
- Assessments
- Certificates
- Training history

#### Shared UI
- forms
- modals
- tables
- alerts
- badges
- loaders
- layout shell
- navigation

---

## 4. Backend Folder Structure

Keep the backend layered so business logic does not live inside route handlers.

```text
backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── logging.py
│   │   └── constants.py
│   ├── db/
│   │   ├── session.py
│   │   ├── base.py
│   │   └── init_db.py
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── admin.py
│   │       ├── hr.py
│   │       ├── employee.py
│   │       ├── videos.py
│   │       ├── certificates.py
│   │       └── reports.py
│   ├── tasks/
│   ├── middleware/
│   ├── dependencies/
│   ├── utils/
│   └── exceptions/
├── alembic/
├── tests/
├── Dockerfile
├── pyproject.toml
└── .env.example
```

### Backend layer responsibilities

- `api/` - request/response layer only
- `services/` - business rules and workflows
- `repositories/` - database access
- `models/` - ORM tables
- `schemas/` - Pydantic validation models
- `tasks/` - Celery background jobs
- `middleware/` - auth, tenant checks, logging, rate limiting

---

## 5. Infra Folder Structure

This is where deployment and environment setup live.

```text
infra/
├── docker/
│   ├── nginx/
│   ├── mysql/
│   ├── redis/
│   └── minio/
├── compose/
├── k8s/
│   ├── base/
│   ├── dev/
│   ├── staging/
│   └── prod/
├── ci/
├── monitoring/
└── security/
```

### Infra components to plan for

- Docker Compose for local development
- Nginx reverse proxy
- MySQL database
- Redis for cache and queues
- Celery worker
- Object storage for video and certificate files
- Kubernetes manifests for later production scaling
- CI/CD pipelines
- monitoring and logging

---

## 6. What to Build

This is the actual product scope, broken into modules.

### 6.1 Foundation
- project setup
- environment configuration
- base layout
- database connection
- auth scaffolding
- CI pipeline
- Docker Compose

### 6.2 Authentication and Security
- signup flow
- OTP verification
- login flow
- forgot/reset password
- JWT access and refresh tokens
- role-based access control
- tenant isolation
- brute-force lockout
- audit logging

### 6.3 Admin Portal
- company CRUD
- user CRUD
- role and permission setup
- video upload and publishing
- certificate templates
- audit log viewer
- analytics dashboard
- report downloads

### 6.4 HR Portal
- employee bulk upload
- employee list and grouping
- training assignment
- due date tracking
- compliance dashboard
- export reports

### 6.5 Employee Portal
- assigned course dashboard
- course detail page
- secure video player
- progress tracking
- assessment flow
- certificate downloads
- training history

### 6.6 Video and Content
- upload video files
- generate secure playback URLs
- subtitles/language support
- progress save and resume
- block unauthorized access

### 6.7 Assessments
- question bank
- MCQ/scenario/true-false support
- scoring rules
- pass/fail logic
- attempt tracking

### 6.8 Certificates
- certificate generation
- QR verification
- PDF output
- certificate status
- email delivery

### 6.9 Reporting and Analytics
- per-company compliance view
- user progress reports
- completion summaries
- assessment summaries
- audit report export

### 6.10 Background Jobs
- send OTP emails
- process bulk uploads
- generate certificates
- send notification emails
- create async report files

---

## 7. Suggested Database Areas

These are the main groups of tables to create or finalize.

### Core tenant and access tables
- `company_master`
- `user_master`
- `role_master`
- `permission_master`
- `role_permission`
- `audit_logs`

### Auth and session tables
- `login_attempts`
- `account_lockout`
- `otp_verification`
- `password_reset_tokens`
- `refresh_tokens`

### Learning and content tables
- `video_master`
- `video_category`
- `video_language`
- `training_history`
- `course_assignment`
- `assessment_result`

### Certificates and reporting tables
- `certificate_template`
- `certificates`
- `analytics_summary`

### HR upload tables
- `employee_upload_batch`

---

## 8. Build Order

Build in this order so each step unlocks the next one.

### Phase 0 - Setup
- create monorepo folders
- add Docker Compose
- connect FastAPI to MySQL
- create React shell
- add environment files
- set up linting and tests

### Phase 1 - Auth
- signup
- OTP verification
- login/logout
- password reset
- refresh tokens
- role guards
- tenant checks

### Phase 2 - Admin Core
- company management
- user management
- roles and permissions
- audit logs

### Phase 3 - Learning Core
- video upload
- secure streaming
- employee assignment
- playback progress
- assessment engine

### Phase 4 - HR Workflows
- employee bulk upload
- training assignment
- compliance reports

### Phase 5 - Certificates and Analytics
- certificate generation
- QR verification
- analytics dashboards
- report exports

### Phase 6 - Hardening
- security checks
- load testing
- backups
- monitoring
- deployment

---

## 9. API Areas to Build

### Auth APIs
- signup
- verify OTP
- login
- logout
- refresh token
- forgot password
- reset password

### Admin APIs
- companies
- users
- roles
- permissions
- audit logs
- reports

### HR APIs
- employee upload
- training assignment
- compliance status
- export reports

### Employee APIs
- assigned courses
- stream URL
- progress update
- assessments
- certificates
- training history

### Public APIs
- certificate verification
- health check

---

## 10. Security Rules

These are non-negotiable for the platform.

- hash all passwords
- never expose another company’s records
- validate all inputs on backend
- use signed or short-lived links for files
- store refresh tokens hashed
- rate limit login and verification endpoints
- keep audit logs for sensitive actions
- avoid public access to raw video files
- use secure cookies for tokens
- protect file uploads with size and type checks

---

## 11. Recommended Deliverables

If you want the project to feel complete, these are the files and pieces you should expect to have:

- `README.md` with setup steps
- `CONTRIBUTING.md` with branch and commit rules
- `docker-compose.yml` for local startup
- backend app with auth and portal APIs
- frontend app with all portal routes
- Alembic migrations
- seed scripts
- tests for auth, RBAC, and tenant isolation
- deployment manifests
- monitoring and logging setup

---

## 12. Practical MVP Definition

Before trying to build everything, the first working version should include:

- login and signup
- company and user model
- admin portal shell
- employee portal shell
- HR portal shell
- secure role-based routing
- one video upload and one video playback flow
- progress tracking
- certificate generation for one completed course

That gives you a real end-to-end system instead of isolated features.

---

## 13. Final Recommendation

Start with:
1. repo structure
2. database schema
3. auth
4. portal shells
5. video flow
6. assignments and assessments
7. certificates and reporting
8. deployment and hardening

This keeps the work buildable and avoids getting stuck in feature chaos.


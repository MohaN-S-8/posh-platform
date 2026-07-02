# POSH Training Platform — Complete Beginner's Step-by-Step Guide

**Who this is for:** Someone who has never built a full-stack web application before.  
**What you will build:** A multi-tenant POSH Training Platform with Admin, HR, and Employee portals.  
**Stack:** React + FastAPI + MySQL + Docker  
**Estimated time:** 18 weeks following the phases below.

> **How to use this guide:** Follow every step in order. Do not skip ahead. Each step assumes the previous one is done. Commands shown in `code blocks` are typed exactly as written in your terminal.

---

# PART 1 — COMPUTER SETUP (Before Writing Any Code)

---

## STEP 1: Install Required Software (Do This Once)

### 1.1 Install Git

Git is the version control tool that tracks every change you make to your code.

**Windows:**

1. Go to https://git-scm.com/download/win
2. Download and run the installer
3. Accept all defaults during installation
4. Open "Git Bash" from your Start Menu — this is your terminal for the whole project

**Verify installation:**

```bash
git --version
# Expected output: git version 2.x.x
```

---

### 1.2 Install Python 3.12

Python is the language your backend (FastAPI) is written in.

**Windows:**

1. Go to https://www.python.org/downloads/
2. Download Python 3.12.x
3. Run installer — **CHECK the box "Add Python to PATH"** before clicking Install
4. Click "Install Now"

**Verify installation:**

```bash
python --version        # Windows
python3 --version       # Mac/Linux
# Expected output: Python 3.12.x
```

---

### 1.3 Install Node.js 20

Node.js is required to build the React frontend.

**All platforms:**

1. Go to https://nodejs.org/
2. Download the **LTS** version (20.x)
3. Run the installer with all defaults

**Verify installation:**

```bash
node --version
# Expected output: v20.x.x

npm --version
# Expected output: 10.x.x
```

---

### 1.4 Install Docker Desktop

Docker runs your entire application in containers — the same way it will run in production.

**Windows & Mac:**

1. Go to https://www.docker.com/products/docker-desktop/
2. Download Docker Desktop for your OS
3. Install and restart your computer when asked
4. Open Docker Desktop — wait for the whale icon in your taskbar to stop animating (it's ready)

**Verify installation:**

```bash
docker --version
# Expected: Docker version 24.x.x

docker compose version
# Expected: Docker Compose version v2.x.x

# Test Docker works
docker run hello-world
# Expected: "Hello from Docker!" message
```

---

### 1.5 Install VS Code (Code Editor)

1. Go to https://code.visualstudio.com/
2. Download and install for your OS

**After installing, open VS Code and install these extensions:**

- Press `Ctrl+Shift+X` (Windows/Linux) or `Cmd+Shift+X` (Mac) to open Extensions
- Search and install each:
  1. **Python** (by Microsoft)
  2. **Pylance** (by Microsoft)
  3. **ESLint** (by Microsoft)
  4. **Prettier - Code formatter** (by Prettier)
  5. **Docker** (by Microsoft)
  6. **GitLens** (by GitKraken)
  7. **Thunder Client** (REST API testing, like Postman but inside VS Code)

---

### 1.6 Configure Git (One-Time Setup)

Tell Git who you are. Replace the name and email with your own.

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
git config --global core.editor "code --wait"
git config --global init.defaultBranch main
```

**Verify:**

```bash
git config --list
# You should see your name and email in the output
```

---

## STEP 2: Create Your GitHub Account and Repository

### 2.1 Create GitHub Account

1. Go to https://github.com
2. Click "Sign up" and create a free account
3. Verify your email address

### 2.2 Create the Repository

1. Click the **+** icon (top right) → "New repository"
2. Fill in:
   - Repository name: `posh-platform`
   - Description: `POSH Training Platform - Multi-tenant SaaS`
   - Visibility: **Private** (your code, keep it private)
   - ✅ Check "Add a README file"
   - ✅ Check "Add .gitignore" → select **Python** from dropdown
3. Click **"Create repository"**

### 2.3 Clone the Repository to Your Computer

This downloads the repo to your computer so you can work on it.

```bash
# Navigate to where you want to store the project
# Windows (Git Bash):
cd /c/Users/YourName/Documents

# Clone the repo (replace YOUR_USERNAME with your GitHub username)
git clone https://github.com/YOUR_USERNAME/posh-platform.git

# Go into the project folder
cd posh-platform

# Verify you're inside it
ls
# Should show: README.md  .gitignore
```

### 2.4 Open the Project in VS Code

```bash
# While inside the posh-platform folder:
code .
```

VS Code will open with your project. You'll work here from now on.

---

## STEP 3: Create the Folder Structure

In your terminal (inside the `posh-platform` folder):

```bash
# Create all project folders
mkdir -p frontend
mkdir -p backend/app/core
mkdir -p backend/app/api/v1
mkdir -p backend/app/models
mkdir -p backend/app/schemas
mkdir -p backend/app/services
mkdir -p backend/app/repositories
mkdir -p backend/app/workers
mkdir -p backend/app/db
mkdir -p backend/tests
mkdir -p backend/alembic
mkdir -p infra
mkdir -p docs
mkdir -p .github/workflows

# Verify the structure
ls -la
```

Your folder should now look like:

```
posh-platform/
├── .github/
│   └── workflows/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── workers/
│   ├── alembic/
│   └── tests/
├── frontend/
├── infra/
├── docs/
├── .gitignore
└── README.md
```

---

## STEP 4: Set Up Branch Protection

### 4.1 Create the `develop` Branch

```bash
# Make sure you're in the posh-platform folder
git checkout -b develop
git push origin develop
```

### 4.2 Protect the `main` Branch on GitHub

1. Go to your GitHub repo → **Settings** → **Branches**
2. Click **"Add branch protection rule"**
3. Branch name pattern: `main`
4. Check:
   - ✅ Require a pull request before merging
   - ✅ Require approvals: 1
   - ✅ Require status checks to pass before merging
5. Click **"Create"**

---

# PART 2 — PHASE 0: SKELETON (Week 1–2)

---

## STEP 5: Create the .gitignore File

Open VS Code. Find the `.gitignore` file in the root of your project and **replace its entire content** with:

```
# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python
.venv/
venv/
env/
.env
*.egg-info/
dist/
build/
.pytest_cache/
.mypy_cache/
.ruff_cache/
htmlcov/
.coverage

# Node.js / React
node_modules/
dist/
build/
.next/
.nuxt/
*.local

# Environment files (NEVER commit these)
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# VS Code
.vscode/
*.code-workspace

# OS files
.DS_Store
Thumbs.db
desktop.ini

# Docker
*.log
```

Save the file (`Ctrl+S`).

---

## STEP 6: Create the Environment Variables File

In the root of `posh-platform/`, create a file called `.env.example`:

```bash
# Copy this file to .env and fill in your values
# NEVER commit .env — only commit .env.example

# Database
MYSQL_ROOT_PASSWORD=changeme_root
MYSQL_DATABASE=posh_db
MYSQL_USER=posh_user
MYSQL_PASSWORD=changeme_password
DATABASE_URL=mysql+asyncmy://posh_user:changeme_password@mysql:3306/posh_db

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# MinIO (Object Storage)
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123
MINIO_ENDPOINT=minio:9000
MINIO_BUCKET_VIDEOS=posh-videos
MINIO_BUCKET_CERTIFICATES=posh-certificates

# Email (for OTP and notifications)
SMTP_HOST=mailhog
SMTP_PORT=1025
SMTP_USER=
SMTP_PASSWORD=
EMAILS_FROM=noreply@posh-platform.com

# App
APP_ENV=development
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:80"]
```

Now create the actual `.env` file (this one is NOT committed to Git):

```bash
# Copy the example file to create your actual .env
cp .env.example .env
```

Open `.env` and set real values. For development, the defaults above work fine.

---

## STEP 7: Build the FastAPI Backend Skeleton

### 7.1 Create the Requirements File

Create `backend/requirements.txt`:

```
# Web framework
fastapi==0.115.0
uvicorn[standard]==0.30.0

# Database
sqlalchemy[asyncio]==2.0.36
alembic==1.13.3
asyncmy==0.2.9            # async MySQL driver
pymysql==1.1.1            # sync MySQL driver (for Alembic)

# Validation
pydantic==2.9.2
pydantic-settings==2.5.2
email-validator==2.2.0

# Auth
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.12

# Background jobs
celery==5.4.0
redis==5.1.1

# File handling
python-magic==0.4.27      # MIME type detection
openpyxl==3.1.5           # Excel read/write
pandas==2.2.3

# PDF and QR
reportlab==4.2.5
qrcode[pil]==8.0

# Email
aiosmtplib==3.0.2

# HTTP client
httpx==0.27.2

# Rate limiting
slowapi==0.1.9

# Testing
pytest==8.3.3
pytest-asyncio==0.24.0
pytest-cov==5.0.0
httpx==0.27.2

# Code quality
ruff==0.7.0
black==24.10.0
```

### 7.2 Create the Main App File

Create `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

# Create the FastAPI app
app = FastAPI(
    title="POSH Training Platform API",
    description="API for POSH Training Platform",
    version="1.0.0",
    docs_url="/docs",       # Swagger UI — visit this in browser to test APIs
    redoc_url="/redoc",
)

# CORS — allows the React frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint — used by Docker and CI to verify the app is running
@app.get("/health")
async def health_check():
    return {"status": "ok", "app": "POSH Training Platform"}

# Root endpoint
@app.get("/")
async def root():
    return {"message": "POSH Platform API is running. Visit /docs for API documentation."}
```

### 7.3 Create the Config File

Create `backend/app/core/config.py`:

```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "mysql+asyncmy://posh_user:password@mysql:3306/posh_db"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "change-this-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # App
    APP_ENV: str = "development"

    class Config:
        env_file = ".env"          # reads from the .env file automatically
        case_sensitive = True

# Create a single instance used throughout the app
settings = Settings()
```

### 7.4 Create the `__init__.py` Files

Python requires `__init__.py` in every folder to treat it as a module.

```bash
#CMD
cd backend\app && type nul > __init__.py && type nul > core\__init__.py && type nul > api\__init__.py && type nul > api\v1\__init__.py && type nul > models\__init__.py && type nul > schemas\__init__.py && type nul > services\__init__.py && type nul > repositories\__init__.py && type nul > workers\__init__.py && type nul > db\__init__.py

#powercell
"__init__.py", "core/__init__.py", "api/__init__.py", "api/v1/__init__.py", "models/__init__.py", "schemas/__init__.py", "services/__init__.py", "repositories/__init__.py", "workers/__init__.py", "db/__init__.py" | ForEach-Object { New-Item -ItemType File -Path "backend/app/$_" -Force }

```

### 7.5 Create the Backend Dockerfile

Create `backend/Dockerfile`:

```dockerfile
# Stage 1: Install dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies needed by some Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Final image (smaller, no build tools)
FROM python:3.12-slim

WORKDIR /app

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y \
    libmagic1 \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create a non-root user for security
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Copy application code
COPY --chown=appuser:appuser . .

# Health check — Docker will call this to verify the container is healthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Start the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## STEP 8: Build the React Frontend Skeleton

### 8.1 Scaffold the React App

```bash
# Navigate to the frontend folder
cd frontend

# Create the Vite + React + TypeScript app
npm create vite@latest . -- --template react-ts

# When prompted "Current directory is not empty. Remove existing files and continue?"
# Type: y  then press Enter

# Install dependencies
npm install
```

### 8.2 Install Frontend Dependencies

```bash
# Still inside the frontend/ folder
npm install react-router-dom axios @tanstack/react-query   zustand react-hook-form zod @hookform/resolvers react-i18next i18next @mui/material @mui/icons-material @emotion/react @emotion/styled

# Dev dependencies
npm install -D eslint@^9

npm install -D @types/react-router-dom eslint prettier @typescript-eslint/eslint-plugin @typescript-eslint/parser eslint-config-prettier eslint-plugin-react eslint-plugin-react-hooks vitest @vitest/coverage-v8 @testing-library/react @testing-library/jest-dom jsdom
```

### 8.3 Create the Main App Component

Replace the content of `frontend/src/App.tsx` with:

```tsx
function App() {
  return (
    <div style={{ padding: "2rem", fontFamily: "Arial, sans-serif" }}>
      <h1>POSH Training Platform</h1>
      <p>
        Frontend is running. Backend API:{" "}
        <a href="http://localhost:8000/docs">http://localhost:8000/docs</a>
      </p>
    </div>
  );
}

export default App;
```

### 8.4 Create the Frontend Dockerfile

Create `frontend/Dockerfile`:

```dockerfile
# Stage 1: Build the React app
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first (for Docker layer caching — faster rebuilds)
COPY package*.json ./
RUN npm ci                    # 'ci' is faster and more reliable than 'install' in Docker

# Copy source code and build
COPY . .
RUN npm run build             # Creates the 'dist/' folder with static files

# Stage 2: Serve static files with Nginx (tiny image, no Node.js)
FROM nginx:alpine

# Remove default nginx page
RUN rm -rf /usr/share/nginx/html/*

# Copy built React app
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy our custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 8.5 Create the Frontend Nginx Config

Create `frontend/nginx.conf`:

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # This is critical for React Router — all routes serve index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API calls to the backend
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Enable gzip compression for faster loading
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
}
```

---

## STEP 9: Create the Docker Compose File

Go back to the root of your project and create `docker-compose.yml`:

```yaml
version: "3.9"

services:
  # ─── Database ─────────────────────────────────────────────
  mysql:
    image: mysql:8.0
    container_name: posh_mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DATABASE}
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    ports:
      - "3306:3306" # expose so you can connect with MySQL Workbench
    volumes:
      - mysql_data:/var/lib/mysql # data persists even if container restarts
    healthcheck:
      test:
        [
          "CMD",
          "mysqladmin",
          "ping",
          "-h",
          "localhost",
          "-u",
          "root",
          "-p${MYSQL_ROOT_PASSWORD}",
        ]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 30s

  # ─── Cache / Queue ────────────────────────────────────────
  redis:
    image: redis:7-alpine
    container_name: posh_redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ─── Object Storage (local S3 replacement) ────────────────
  minio:
    image: minio/minio:latest
    container_name: posh_minio
    restart: unless-stopped
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    ports:
      - "9000:9000" # API port
      - "9001:9001" # Web console — visit http://localhost:9001
    volumes:
      - minio_data:/data

  # ─── Email Testing (catches all emails locally) ───────────
  mailhog:
    image: mailhog/mailhog:latest
    container_name: posh_mailhog
    ports:
      - "1025:1025" # SMTP port (backend sends to this)
      - "8025:8025" # Web UI — visit http://localhost:8025 to see emails
    restart: unless-stopped

  # ─── Backend ──────────────────────────────────────────────
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: posh_backend
    restart: unless-stopped
    env_file: .env
    environment:
      DATABASE_URL: mysql+asyncmy://${MYSQL_USER}:${MYSQL_PASSWORD}@mysql:3306/${MYSQL_DATABASE}
      REDIS_URL: redis://redis:6379/0
    ports:
      - "8000:8000" # visit http://localhost:8000/docs for Swagger
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app # live code reloading in development
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # ─── Background Job Worker ────────────────────────────────
  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: posh_celery
    restart: unless-stopped
    env_file: .env
    environment:
      DATABASE_URL: mysql+asyncmy://${MYSQL_USER}:${MYSQL_PASSWORD}@mysql:3306/${MYSQL_DATABASE}
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - redis
      - mysql
    volumes:
      - ./backend:/app
    command: celery -A app.workers.celery_app worker --loglevel=info

  # ─── Frontend ─────────────────────────────────────────────
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: posh_frontend
    restart: unless-stopped
    ports:
      - "80:80" # visit http://localhost to see the React app
    depends_on:
      - backend

volumes:
  mysql_data:
  minio_data:
```

---

## STEP 10: Create the Celery Worker File (Minimal Skeleton)

The Celery worker is referenced in docker-compose. Create a minimal version now so it doesn't fail.

Create `backend/app/workers/celery_app.py`:

```python
from celery import Celery
import os

# Create the Celery app
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

# Placeholder task — real tasks will be added per feature
@celery_app.task
def test_task(x, y):
    return x + y
```

---

## STEP 11: First Docker Build — Make Everything Run

```bash
# Make sure you're in the posh-platform/ root folder
cd /path/to/posh-platform

# Build all images and start containers
docker compose up --build

# This will take 5-10 minutes the first time (downloading images + installing packages)
# Watch for errors. It should end with all services running.
```

**What you should see when it's working:**

```
posh_mysql     | ready for connections
posh_redis     | Ready to accept connections
posh_backend   | Uvicorn running on http://0.0.0.0:8000
posh_frontend  | nginx started
```

**Verify everything works — open these URLs in your browser:**
| URL | What you should see |
|-----|---------------------|
| http://localhost | React app ("POSH Training Platform") |
| http://localhost:8000/health | `{"status":"ok"}` |
| http://localhost:8000/docs | Swagger API documentation |
| http://localhost:9001 | MinIO console (login: minioadmin/minioadmin123) |
| http://localhost:8025 | MailHog (email testing inbox) |

**If something fails:** Run `docker compose logs backend` (or `frontend`, `mysql`) to see error messages.

---

## STEP 12: Set Up the Database with Alembic

Alembic manages database schema changes using migration files.

### 12.1 Install Python Dependencies Locally

You need Python packages on your local machine too (for running Alembic commands):

```bash
# Go into the backend folder
cd backend

# Create a virtual environment (isolated Python environment for this project)
python -m venv .venv          # Windows

# Activate it
.venv\Scripts\activate         # Windows

# You should now see (.venv) at the start of your terminal prompt

# Install packages
pip install -r requirements.txt
```

### 12.2 Initialize Alembic

```bash
# Still inside backend/ with .venv activated
alembic init alembic
```

This creates an `alembic/` folder and an `alembic.ini` file.

### 12.3 Configure Alembic

Open `backend/alembic.ini` and find this line:

```
sqlalchemy.url = driver://user:pass@localhost/dbname
```

Replace it with:

```
sqlalchemy.url = mysql+pymysql://posh_user:changeme_password@localhost:3306/posh_db
```

> Note: this is for LOCAL migration running (port 3306 is exposed by docker-compose). Inside Docker it would use `mysql:3306`.

Open `backend/alembic/env.py` and replace the content with:

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
import os

# This adds the backend/ folder to Python's path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── CRITICAL: Import Base AND all models ──────────────────────────────────────
# Alembic can only detect tables that have been imported before it reads metadata.
# If you add a new model file later, add its import here too.
from app.db.base import Base

# Import every model so Alembic knows about their tables
from app.models.company import CompanyMaster
from app.models.role import RoleMaster
from app.models.user import UserMaster
# ─────────────────────────────────────────────────────────────────────────────

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 12.4 Create the Database Base Class

Create `backend/app/db/base.py`:

```python
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    Every model file will import from this.
    """
    pass
```

Create `backend/app/db/session.py`:

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# Create the async database engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,          # prints SQL queries to console — helpful for debugging
    pool_pre_ping=True, # checks connection is alive before using it
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Dependency used in FastAPI route handlers
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### 12.5 Create the First Three Database Models

Create `backend/app/models/company.py`:

```python
from sqlalchemy import Column, Integer, String, Enum, DateTime, Text
from sqlalchemy.sql import func
from app.db.base import Base

class CompanyMaster(Base):
    __tablename__ = "company_master"

    company_id = Column(Integer, primary_key=True, autoincrement=True)
    company_code = Column(String(20), unique=True)
    company_name = Column(String(200))
    industry_type = Column(String(100))
    website = Column(String(200))
    registration_number = Column(String(50))
    gst_number = Column(String(50))
    employee_strength = Column(Integer)
    address = Column(Text)
    contact_person = Column(String(100))
    contact_email = Column(String(100))
    contact_mobile = Column(String(20))
    status = Column(Enum("Active", "Inactive"), default="Active")
    is_deleted = Column(String(1), default="N")   # soft delete
    created_date = Column(DateTime, server_default=func.now())
    updated_date = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

Create `backend/app/models/role.py`:

```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.db.base import Base

class RoleMaster(Base):
    __tablename__ = "role_master"

    role_id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String(50))
    created_date = Column(DateTime, server_default=func.now())
    updated_date = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

Create `backend/app/models/user.py`:

```python
from sqlalchemy import Column, BigInteger, Integer, String, Enum, DateTime, Date, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base

class UserMaster(Base):
    __tablename__ = "user_master"

    user_id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("company_master.company_id"), nullable=False)
    employee_id = Column(String(30), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100))
    email = Column(String(100), unique=True, nullable=False)
    mobile = Column(String(20))
    department = Column(String(100))
    designation = Column(String(100))
    role_id = Column(Integer, ForeignKey("role_master.role_id"), nullable=False)
    manager_id = Column(BigInteger, ForeignKey("user_master.user_id"), nullable=True)
    login_type = Column(Enum("Email", "SSO", "Entra ID"), default="Email")
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255))
    language_preference = Column(Integer)
    status = Column(Enum("Active", "Inactive"), default="Active")
    is_deleted = Column(String(1), default="N")   # soft delete
    joining_date = Column(Date)
    created_date = Column(DateTime, server_default=func.now())
    updated_date = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

Update `backend/app/models/__init__.py` to import all models (so Alembic sees them):

```python
from app.models.company import CompanyMaster
from app.models.role import RoleMaster
from app.models.user import UserMaster
```

### 12.6 Generate and Run the First Migration

Make sure Docker is running (`docker compose up -d` in another terminal), then:

```bash
# Activate it
.venv\Scripts\activate         # Windows

# Inside backend/ with .venv activated
alembic revision --autogenerate -m "initial_tables_company_role_user"
```

This creates a file in `alembic/versions/` — open it and look at it. You should see SQL to create your 3 tables.

```bash
# Apply the migration (creates the tables in MySQL)
alembic upgrade head
```

**Verify the tables were created:**

```bash
# Connect to MySQL inside Docker
docker exec -it posh_mysql mysql -u posh_user -pchangeme_password posh_db

4.2 Gaps to fill before development starts
Your own documents reference tables that arent in the schema PDF yet. Add these now so nothing blocks development later:

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

# Inside MySQL:
SHOW TABLES;
# Should show: company_master, role_master, user_master

DESCRIBE company_master;
# Should show all columns

EXIT;
```

---

## STEP 13: Commit Your Work

This is your first real commit. You should commit regularly — at minimum after every step that works.

```bash
# Make sure you're in the posh-platform/ root
cd ..

# See what files have changed
git status

# Stage all changes
git add .

# Commit with a meaningful message
git commit -m "feat: Phase 0 skeleton — FastAPI + React + MySQL + Docker Compose running"

# Push to GitHub
git push origin develop
```

---

## STEP 14: Set Up the CI Pipeline

This runs automated checks on every Pull Request, catching problems before they reach `main`.

Create `.github/workflows/ci.yml`:

```yaml
name: CI — Lint, Test, Build

"on":
  push:
    branches: [develop, main]
  pull_request:
    branches: [develop, main]

jobs:
  # ─── Backend Checks ────────────────────────────────────────
  backend:
    name: Backend (Python)
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"
          cache-dependency-path: backend/requirements.txt

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run linter (ruff)
        run: |
          cd backend
          ruff check .

      - name: Run formatter check (black)
        run: |
          cd backend
          black --check .

      - name: Run tests
        run: |
          cd backend
          pytest tests/ -v
        continue-on-error: true

      - name: Build Docker image
        run: docker build -t posh-backend:test ./backend

  # ─── Frontend Checks ───────────────────────────────────────
  frontend:
    name: Frontend (Node/React)
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Node.js 24
        uses: actions/setup-node@v4
        with:
          node-version: "24"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Run TypeScript check
        run: |
          cd frontend
          npx tsc --noEmit

      - name: Build production bundle
        run: |
          cd frontend
          npm run build

      - name: Build Docker image
        run: docker build -t posh-frontend:test ./frontend
```

Create a config file for the linter. Create `backend/pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I"]      # errors, pyflakes, imports
ignore = ["E501"]              # ignore line-too-long (handled by black)

[tool.black]
line-length = 100
target-version = ["py312"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

Create a placeholder test so pytest doesn't fail with "no tests":

Create `backend/tests/__init__.py` (empty file):

```bash
touch backend/tests/__init__.py
```

Create `backend/tests/test_health.py`:

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """The /health endpoint should return 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_root():
    """The root endpoint should return 200 OK."""
    response = client.get("/")
    assert response.status_code == 200
```

Commit and push to trigger CI:

```bash
git add .
git commit -m "chore: add CI pipeline and health check test"
git push origin develop
```

Go to your GitHub repo → **Actions** tab → you should see your CI workflow running. It should turn green.

---

# `DONE`

## STEP 15: Phase 0 Complete ✅

You should now have:

- ✅ Git repo with branch protection
- ✅ `docker compose up` → all 7 services running
- ✅ http://localhost → React app visible
- ✅ http://localhost:8000/health → `{"status":"ok"}`
- ✅ MySQL with 3 tables created via Alembic migration
- ✅ CI pipeline running green on GitHub Actions

**Before moving to Phase 1, verify all of the above are working. Fix any issues now.**

---

# PART 3 — PHASE 1: AUTH & USER MANAGEMENT (Week 3–5)

This is the most important phase — every other feature depends on auth working correctly.

---

## STEP 16: Add All Database Tables (Auth-Related)

Add these new models before writing any auth code.

Create `backend/app/models/auth.py`:

```python
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy import BigInteger
from sqlalchemy.sql import func

from app.db.base import Base


class OTPVerification(Base):
    __tablename__ = "otp_verification"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    email = Column(String(100))
    otp_hash = Column(String(255))
    purpose = Column(Enum("Signup", "PasswordReset"))
    expires_at = Column(DateTime)
    verified = Column(Boolean, default=False)
    created_date = Column(DateTime, server_default=func.now())


class AccountLockout(Base):
    __tablename__ = "account_lockout"

    user_id = Column(BigInteger, ForeignKey("user_master.user_id"), primary_key=True)
    failed_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)


class LoginAttempts(Base):
    __tablename__ = "login_attempts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=True)
    email_attempted = Column(String(100))
    ip_address = Column(String(45))
    success = Column(Boolean)
    attempted_at = Column(DateTime, server_default=func.now())


class RefreshTokens(Base):
    __tablename__ = "refresh_tokens"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user_master.user_id"))
    token_hash = Column(String(255))
    device_info = Column(String(255))
    ip_address = Column(String(45))
    expires_at = Column(DateTime)
    revoked = Column(Boolean, default=False)
    created_date = Column(DateTime, server_default=func.now())


class PasswordResetTokens(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user_master.user_id"))
    token_hash = Column(String(255))
    expires_at = Column(DateTime)
    used = Column(Boolean, default=False)
    created_date = Column(DateTime, server_default=func.now())
```

Update `backend/app/models/__init__.py`:

```python
from app.models.company import CompanyMaster
from app.models.role import RoleMaster
from app.models.user import UserMaster
from app.models.auth import OTPVerification, AccountLockout, LoginAttempts, RefreshTokens, PasswordResetTokens
```

Generate and apply the migration:

```bash
alembic revision --autogenerate -m "add_auth_tables"
alembic upgrade head
```

---

## STEP 17: Create the Security Utilities

Create `backend/app/core/security.py`:

```python
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token() -> tuple[str, str]:
    raw_token = secrets.token_urlsafe(64)
    hashed = hashlib.sha256(raw_token.encode()).hexdigest()
    return raw_token, hashed


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def generate_otp() -> tuple[str, str]:
    raw_otp = str(secrets.randbelow(900000) + 100000)
    hashed = hashlib.sha256(raw_otp.encode()).hexdigest()
    return raw_otp, hashed
```

---

## STEP 18: Create the Signup Endpoint

### 18.1 Create Pydantic Schemas for Auth

Create `backend/app/schemas/auth.py`:

```python
import re
from pydantic import BaseModel, EmailStr, field_validator


class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    confirm_password: str
    mobile: str

    @field_validator("first_name")
    @classmethod
    def validate_first_name(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("First name must be at least 2 characters")
        if len(v) > 50:
            raise ValueError("First name must be at most 50 characters")
        if not re.match(r"^[a-zA-Z\s]+$", v):
            raise ValueError("First name must contain only letters")
        return v

    @field_validator("last_name")
    @classmethod
    def validate_last_name(cls, v):
        v = v.strip()
        if not re.match(r"^[a-zA-Z\s]+$", v):
            raise ValueError("Last name must contain only letters")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        v = v.strip().lower()
        if len(v) > 25:
            raise ValueError("Email must be at most 25 characters")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(v) > 15:
            raise ValueError("Password must be at most 15 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")
        return v

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v):
        v = v.strip()
        if not re.match(r"^\d{10}$", v):
            raise ValueError("Mobile must be exactly 10 digits")
        return v

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v):
        return v.strip().lower()


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role_id: int
    company_id: int
```

### 18.2 Create the Auth Service

Create `backend/app/services/auth_service.py`:

```python
import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_otp,
    hash_password,
    verify_password,
)
from app.models.auth import AccountLockout, LoginAttempts, OTPVerification, RefreshTokens
from app.models.user import UserMaster
from app.schemas.auth import LoginRequest, SignupRequest

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


class AuthService:
    async def signup(self, db: AsyncSession, data: SignupRequest) -> dict:
        # Check duplicate email
        result = await db.execute(
            select(UserMaster).where(UserMaster.email == data.email.lower())
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists.",
            )

        password_hash = hash_password(data.password)

        user = UserMaster(
            company_id=1,
            employee_id=f"EMP{data.mobile}",
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email.lower(),
            mobile=data.mobile,
            role_id=4,
            username=data.email.lower(),
            password_hash=password_hash,
            status="Inactive",
        )
        db.add(user)
        await db.flush()

        raw_otp, otp_hash = generate_otp()

        otp_record = OTPVerification(
            email=data.email.lower(),
            otp_hash=otp_hash,
            purpose="Signup",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )
        db.add(otp_record)
        await db.commit()

        return {
            "message": "OTP sent to your email. Please verify to complete registration.",
            "dev_otp": raw_otp,  # REMOVE IN PRODUCTION
        }

    async def verify_otp(self, db: AsyncSession, email: str, otp: str) -> dict:
        otp_hash = hashlib.sha256(otp.encode()).hexdigest()

        result = await db.execute(
            select(OTPVerification).where(
                OTPVerification.email == email.lower(),
                OTPVerification.otp_hash == otp_hash,
                OTPVerification.purpose == "Signup",
                OTPVerification.verified == False,  # noqa: E712
                OTPVerification.expires_at > datetime.now(timezone.utc),
            )
        )
        otp_record = result.scalar_one_or_none()

        if not otp_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP.",
            )

        otp_record.verified = True
        await db.execute(
            update(UserMaster)
            .where(UserMaster.email == email.lower())
            .values(status="Active")
        )
        await db.commit()
        return {"message": "Email verified successfully. You can now log in."}

    async def login(
        self, db: AsyncSession, data: LoginRequest, ip_address: str
    ) -> dict:
        result = await db.execute(
            select(UserMaster).where(UserMaster.email == data.email.lower())
        )
        user = result.scalar_one_or_none()

        if not user:
            await self._log_attempt(db, None, data.email, ip_address, False)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        lockout_result = await db.execute(
            select(AccountLockout).where(AccountLockout.user_id == user.user_id)
        )
        lockout = lockout_result.scalar_one_or_none()

        if (
            lockout
            and lockout.locked_until
            and lockout.locked_until > datetime.now(timezone.utc)
        ):
            minutes_left = (
                int(
                    (lockout.locked_until - datetime.now(timezone.utc)).total_seconds()
                    / 60
                )
                + 1
            )
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account locked. Try again in {minutes_left} minutes.",
            )

        if not verify_password(data.password, user.password_hash):
            await self._log_attempt(db, user.user_id, data.email, ip_address, False)
            await self._increment_lockout(db, user.user_id, lockout)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if user.status != "Active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is inactive. Contact your administrator.",
            )

        if lockout:
            lockout.failed_attempts = 0
            lockout.locked_until = None

        access_token = create_access_token(
            {
                "user_id": user.user_id,
                "company_id": user.company_id,
                "role_id": user.role_id,
            }
        )
        raw_refresh, hashed_refresh = create_refresh_token()

        refresh_record = RefreshTokens(
            user_id=user.user_id,
            token_hash=hashed_refresh,
            ip_address=ip_address,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        db.add(refresh_record)
        await self._log_attempt(db, user.user_id, data.email, ip_address, True)
        await db.commit()

        return {
            "access_token": access_token,
            "refresh_token": raw_refresh,
            "user_id": user.user_id,
            "role_id": user.role_id,
            "company_id": user.company_id,
        }

    async def _log_attempt(self, db, user_id, email, ip, success):
        attempt = LoginAttempts(
            user_id=user_id,
            email_attempted=email,
            ip_address=ip,
            success=success,
        )
        db.add(attempt)

    async def _increment_lockout(self, db, user_id, lockout):
        if not lockout:
            lockout = AccountLockout(user_id=user_id, failed_attempts=0)
            db.add(lockout)

        lockout.failed_attempts = (lockout.failed_attempts or 0) + 1

        if lockout.failed_attempts >= MAX_FAILED_ATTEMPTS:
            lockout.locked_until = datetime.now(timezone.utc) + timedelta(
                minutes=LOCKOUT_MINUTES
            )
```

### 18.3 Create the Auth Router

Create `backend/app/api/v1/auth.py`:

```python
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.auth import SignupRequest, OTPVerifyRequest, LoginRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()

@router.post("/signup")
async def signup(data: SignupRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user. Sends OTP to email for verification."""
    return await auth_service.signup(db, data)

@router.post("/verify-otp")
async def verify_otp(data: OTPVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Verify OTP and activate account."""
    return await auth_service.verify_otp(db, data.email, data.otp)

@router.post("/login")
async def login(data: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Login with email and password. Returns JWT tokens."""
    ip = request.client.host
    return await auth_service.login(db, data, ip)
```

### 18.4 Register the Router in main.py

Update `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.auth import router as auth_router

app = FastAPI(
    title="POSH Training Platform API",
    version="1.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(auth_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "ok", "app": "POSH Training Platform"}

@app.get("/")
async def root():
    return {"message": "POSH Platform API. Visit /docs for documentation."}
```

```
Fix: Create a Seed Script
Create backend/app/db/seed.py:

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "mysql+asyncmy://posh_user:changeme_password@localhost:3306/posh_db",
)

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def seed():
    async with AsyncSessionLocal() as db:
        # ── 1. Roles ──────────────────────────────────────────────────────
        await db.execute(
            text("""
                INSERT IGNORE INTO role_master (role_id, role_name)
                VALUES
                    (1, 'Super Admin'),
                    (2, 'Company Admin'),
                    (3, 'HR'),
                    (4, 'Employee')
            """)
        )

        # ── 2. Default company (needed for signup FK) ─────────────────────
        await db.execute(
            text("""
                INSERT IGNORE INTO company_master
                    (company_id, company_code, company_name, status)
                VALUES
                    (1, 'DEFAULT', 'Default Company', 'Active')
            """)
        )

        await db.commit()
        print("✅ Seed complete — roles and default company inserted.")


if __name__ == "__main__":
    asyncio.run(seed())

Run the Seed Script
bash# Inside backend/ with .venv activated
cd backend
python -m app.db.seed

Expected output:
✅ Seed complete — roles and default company inserted.

Verify in MySQL
bashdocker exec -it posh_mysql mysql -u posh_user -pchangeme_password posh_db
sqlSELECT * FROM role_master;
SELECT * FROM company_master;
EXIT;

You should see 4 roles and 1 company.
Now Test Signup Again
Go to http://localhost:8000/docs → POST /api/v1/auth/signup → try it out with:
json{
  "first_name": "Arjun",
  "last_name": "Kumar",
  "email": "arjun@test.com",
  "password": "Test@1234",
  "confirm_password": "Test@1234",
  "mobile": "9876543210"
}
You should get back:
json{
  "message": "OTP sent to your email. Please verify to complete registration.",
  "dev_otp": "123456"
}
```

**Test the signup endpoint:**

1. Open http://localhost:8000/docs in your browser
2. Click on `POST /api/v1/auth/signup`
3. Click "Try it out"
4. Fill in valid data and click "Execute"
5. You should see a response with `"dev_otp"` — use that OTP to test `/verify-otp`
6. Then test `/login` with your credentials

---

## STEP 19: Add Auth Tests

Create `backend/tests/test_auth.py`:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ── Signup Validation Tests (from your Signup Screen doc) ──────────

def test_signup_empty_first_name():
    response = client.post("/api/v1/auth/signup", json={
        "first_name": "",
        "last_name": "Kumar",
        "email": "test@example.com",
        "password": "Test@1234",
        "confirm_password": "Test@1234",
        "mobile": "9876543210"
    })
    assert response.status_code == 422

def test_signup_numbers_in_first_name():
    response = client.post("/api/v1/auth/signup", json={
        "first_name": "Ravi123",
        "last_name": "Kumar",
        "email": "test@example.com",
        "password": "Test@1234",
        "confirm_password": "Test@1234",
        "mobile": "9876543210"
    })
    assert response.status_code == 422

def test_signup_invalid_email_format():
    response = client.post("/api/v1/auth/signup", json={
        "first_name": "Ravi",
        "last_name": "Kumar",
        "email": "not-an-email",
        "password": "Test@1234",
        "confirm_password": "Test@1234",
        "mobile": "9876543210"
    })
    assert response.status_code == 422

def test_signup_email_too_long():
    response = client.post("/api/v1/auth/signup", json={
        "first_name": "Ravi",
        "last_name": "Kumar",
        "email": "averylongemail123456@example.com",   # > 25 chars
        "password": "Test@1234",
        "confirm_password": "Test@1234",
        "mobile": "9876543210"
    })
    assert response.status_code == 422

def test_signup_password_too_short():
    response = client.post("/api/v1/auth/signup", json={
        "first_name": "Ravi",
        "last_name": "Kumar",
        "email": "ravi@test.com",
        "password": "Ab@1",      # < 8 chars
        "confirm_password": "Ab@1",
        "mobile": "9876543210"
    })
    assert response.status_code == 422

def test_signup_passwords_do_not_match():
    response = client.post("/api/v1/auth/signup", json={
        "first_name": "Ravi",
        "last_name": "Kumar",
        "email": "ravi@test.com",
        "password": "Test@1234",
        "confirm_password": "Test@5678",
        "mobile": "9876543210"
    })
    assert response.status_code == 422

def test_signup_invalid_mobile():
    response = client.post("/api/v1/auth/signup", json={
        "first_name": "Ravi",
        "last_name": "Kumar",
        "email": "ravi@test.com",
        "password": "Test@1234",
        "confirm_password": "Test@1234",
        "mobile": "123"           # not 10 digits
    })
    assert response.status_code == 422

# ── Login Validation Tests (from your Login Screen doc) ───────────

def test_login_empty_email():
    response = client.post("/api/v1/auth/login", json={
        "email": "",
        "password": "Test@1234"
    })
    assert response.status_code == 422

def test_login_invalid_credentials():
    response = client.post("/api/v1/auth/login", json={
        "email": "nobody@nowhere.com",
        "password": "WrongPass@1"
    })
    assert response.status_code == 401
```

Run the tests:

```bash
cd backend
pytest tests/ -v
```

---

## STEP 20: Commit Phase 1 Auth Work

```bash
git add .
git commit -m "feat(auth): signup, OTP verification, login with lockout — all validation rules implemented"
git push origin develop
```

---

_The guide continues in the same format through Phase 2 (Video), Phase 3 (HR Portal), Phase 4 (Certificates), and Phase 5 (Deployment). Each step follows the same pattern: create the model → create the schema → create the service → create the router → test → commit._

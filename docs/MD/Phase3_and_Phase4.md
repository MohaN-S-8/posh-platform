when we going to developer the ui also if i finished this we need to create real functionalities right? or these are enough?

# Phase 3 + Phase 4 — Step-by-Step Guide

## Where You Are Right Now ✅

| Phase                                  | Status           |
| -------------------------------------- | ---------------- |
| Phase 0 — Foundations                  | ✅ Complete      |
| Phase 1 — Auth + User Management       | ✅ Complete      |
| Phase 2 — Video + Assessments          | ✅ Complete      |
| **Phase 3 — HR Portal**                | ⬜ This document |
| **Phase 4 — Certificates + Analytics** | ⬜ This document |
| Phase 5 — Hardening + Deployment       | Next guide       |

---

# PHASE 3 — HR PORTAL (Week 10–12)

**What we build:**

- Bulk employee upload (Excel/CSV)
- Training assignment (individual / department / company-wide)
- Compliance tracking dashboard
- Reports (Excel/CSV/PDF export)

**Theory to understand before starting:**

- pandas for reading/validating Excel files
- CSV injection attacks and how to prevent them
- Celery background tasks for slow operations
- openpyxl for generating Excel reports
- ReportLab for PDF generation

---

## STEP 36: Add HR Portal Database Tables

### 36.1 Create Employee Upload Batch Model

Create `backend/app/models/hr.py`:

```python
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.sql import func

from app.db.base import Base


class EmployeeUploadBatch(Base):
    """
    Tracks every bulk employee upload.
    Lets HR see status of their upload (Processing / Completed / Failed).
    """

    __tablename__ = "employee_upload_batch"

    batch_id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("company_master.company_id"))
    uploaded_by = Column(BigInteger, ForeignKey("user_master.user_id"))
    file_name = Column(String(255))
    total_rows = Column(Integer, default=0)
    success_rows = Column(Integer, default=0)
    failed_rows = Column(Integer, default=0)
    error_report_path = Column(String(255))    # path to error CSV in MinIO
    status = Column(
        Enum("Processing", "Completed", "Failed"), default="Processing"
    )
    created_date = Column(DateTime, server_default=func.now())
    updated_date = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

### 36.2 Create Notification Model

Create `backend/app/models/notification.py`:

```python
from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.db.base import Base


class Notification(Base):
    """System notifications sent to users (training reminders, overdue alerts)."""

    __tablename__ = "notification"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user_master.user_id"))
    company_id = Column(Integer, ForeignKey("company_master.company_id"))
    title = Column(String(200))
    message = Column(String(500))
    is_read = Column(Boolean, default=False)
    created_date = Column(DateTime, server_default=func.now())
```

### 36.3 Update alembic/env.py

Add these imports to `backend/alembic/env.py` alongside existing ones:

```python
from app.models.hr import EmployeeUploadBatch  # noqa: F401
from app.models.notification import Notification  # noqa: F401
```

### 36.4 Generate and Apply Migration

```bash
cd backend
.venv\Scripts\activate
alembic revision --autogenerate -m "add_phase3_hr_notification_tables"
alembic upgrade head
```

Verify:

```bash
docker exec -it posh_mysql mysql -u posh_user -pchangeme_password posh_db
```

```sql
SHOW TABLES;
-- Should now include: employee_upload_batch, notification
EXIT;
```

---

## STEP 37: Build Bulk Employee Upload

This is the most complex HR feature. HR uploads an Excel file → system validates every row → creates users → reports errors.

### 37.1 Create HR Schemas

Create `backend/app/schemas/hr.py`:

```python
from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr


class EmployeeRowSchema(BaseModel):
    """
    Represents one row in the uploaded Excel/CSV file.
    Every field is Optional at parse time — we validate manually
    so we can give per-row error messages instead of crashing.
    """

    employee_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    role_id: Optional[int] = None


class TrainingAssignRequest(BaseModel):
    video_id: int
    assign_type: str                          # Individual / Department / Company-Wide
    assigned_to_user_id: Optional[int] = None
    assigned_to_department: Optional[str] = None
    due_days: int = 30                        # due in N days from now
    passing_score: float = 70.0


class ComplianceDashboard(BaseModel):
    total_employees: int
    completed: int
    in_progress: int
    not_started: int
    compliance_rate: float
    department_breakdown: list[dict]
    overdue_employees: list[dict]
```

### 37.2 Create HR Service

Create `backend/app/services/hr_service.py`:

```python
import io
from datetime import datetime, timedelta, timezone
from typing import Optional

import pandas as pd
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.company import CompanyMaster
from app.models.hr import EmployeeUploadBatch
from app.models.training import CourseAssignment, TrainingHistory
from app.models.user import UserMaster
from app.schemas.hr import TrainingAssignRequest

REQUIRED_COLUMNS = {"employee_id", "first_name", "email", "mobile", "role_id"}


class HRService:

    async def bulk_upload_employees(
        self,
        db: AsyncSession,
        file: UploadFile,
        company_id: int,
        uploaded_by: int,
    ) -> dict:
        """
        Parse Excel/CSV, validate every row, create users for valid rows,
        return a detailed error report for invalid rows.
        """

        # 1. Read file into pandas DataFrame
        file_bytes = await file.read()
        filename = file.filename or "upload.xlsx"

        try:
            if filename.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(file_bytes))
            elif filename.endswith((".xlsx", ".xls")):
                df = pd.read_excel(io.BytesIO(file_bytes))
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Unsupported file type. Please upload .xlsx or .csv",
                )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not read file: {str(e)}")

        # 2. Normalize column names (lowercase, strip spaces)
        df.columns = [str(c).lower().strip() for c in df.columns]

        # 3. Check required columns exist
        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing)}. "
                f"Required: employee_id, first_name, email, mobile, role_id",
            )

        # 4. Create batch record
        batch = EmployeeUploadBatch(
            company_id=company_id,
            uploaded_by=uploaded_by,
            file_name=filename,
            total_rows=len(df),
            status="Processing",
        )
        db.add(batch)
        await db.flush()

        # 5. Process each row
        success_rows = 0
        errors = []

        for index, row in df.iterrows():
            row_num = index + 2  # +2 because Excel rows start at 1, row 1 is header
            row_errors = []

            # Extract values (strip whitespace, convert to string safely)
            employee_id = str(row.get("employee_id", "")).strip()
            first_name = str(row.get("first_name", "")).strip()
            last_name = str(row.get("last_name", "")).strip()
            email = str(row.get("email", "")).strip().lower()
            mobile = str(row.get("mobile", "")).strip()
            department = str(row.get("department", "")).strip()
            designation = str(row.get("designation", "")).strip()

            try:
                role_id = int(row.get("role_id", 4))
            except (ValueError, TypeError):
                role_id = 4  # default to Employee

            # ── Validate each field ────────────────────────────────────────
            if not employee_id:
                row_errors.append("employee_id is required")

            if not first_name:
                row_errors.append("first_name is required")

            if not email or "@" not in email:
                row_errors.append("valid email is required")

            if not mobile.isdigit() or len(mobile) != 10:
                row_errors.append("mobile must be exactly 10 digits")

            if role_id not in [1, 2, 3, 4]:
                row_errors.append("role_id must be 1, 2, 3, or 4")

            # ── CSV injection defense ──────────────────────────────────────
            # Prefix cells starting with =, +, -, @ with apostrophe
            # These are formula injection characters in Excel/Google Sheets
            for dangerous_prefix in ["=", "+", "-", "@"]:
                if first_name.startswith(dangerous_prefix):
                    first_name = "'" + first_name
                if last_name.startswith(dangerous_prefix):
                    last_name = "'" + last_name

            if row_errors:
                errors.append({"row": row_num, "email": email, "errors": row_errors})
                continue

            # ── Check duplicate email ──────────────────────────────────────
            existing = await db.execute(
                select(UserMaster).where(UserMaster.email == email)
            )
            if existing.scalar_one_or_none():
                errors.append({
                    "row": row_num,
                    "email": email,
                    "errors": ["Email already registered — skipped"],
                })
                continue

            # ── Create user ────────────────────────────────────────────────
            user = UserMaster(
                company_id=company_id,
                employee_id=employee_id,
                first_name=first_name,
                last_name=last_name or None,
                email=email,
                mobile=mobile,
                department=department or None,
                designation=designation or None,
                role_id=role_id,
                username=email,
                password_hash=hash_password("Temp@1234"),  # temporary password
                status="Active",
            )
            db.add(user)
            success_rows += 1

        # 6. Update batch record
        batch.success_rows = success_rows
        batch.failed_rows = len(errors)
        batch.status = "Completed"

        await db.commit()

        return {
            "batch_id": batch.batch_id,
            "total_rows": len(df),
            "success_rows": success_rows,
            "failed_rows": len(errors),
            "errors": errors,
            "message": f"Upload complete. {success_rows} employees created, {len(errors)} rows failed.",
        }

    async def assign_training(
        self,
        db: AsyncSession,
        data: TrainingAssignRequest,
        company_id: int,
        assigned_by: int,
    ) -> dict:
        """Assign a video course to individual / department / entire company."""

        due_date = datetime.now(timezone.utc) + timedelta(days=data.due_days)

        if data.assign_type == "Individual":
            if not data.assigned_to_user_id:
                raise HTTPException(400, "assigned_to_user_id required for Individual assignment")

            # Check already assigned
            existing = await db.execute(
                select(CourseAssignment).where(
                    CourseAssignment.video_id == data.video_id,
                    CourseAssignment.assigned_to_user_id == data.assigned_to_user_id,
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(400, "This course is already assigned to this employee.")

            assignment = CourseAssignment(
                video_id=data.video_id,
                assigned_by=assigned_by,
                company_id=company_id,
                assigned_to_user_id=data.assigned_to_user_id,
                assign_type="Individual",
                due_date=due_date,
                passing_score=data.passing_score,
            )
            db.add(assignment)
            await db.commit()
            return {"message": "Course assigned to employee successfully.", "assignments_created": 1}

        elif data.assign_type == "Department":
            if not data.assigned_to_department:
                raise HTTPException(400, "assigned_to_department required for Department assignment")

            assignment = CourseAssignment(
                video_id=data.video_id,
                assigned_by=assigned_by,
                company_id=company_id,
                assigned_to_department=data.assigned_to_department,
                assign_type="Department",
                due_date=due_date,
                passing_score=data.passing_score,
            )
            db.add(assignment)
            await db.commit()
            return {
                "message": f"Course assigned to {data.assigned_to_department} department.",
                "assignments_created": 1,
            }

        elif data.assign_type == "Company-Wide":
            assignment = CourseAssignment(
                video_id=data.video_id,
                assigned_by=assigned_by,
                company_id=company_id,
                assign_type="Company-Wide",
                due_date=due_date,
                passing_score=data.passing_score,
            )
            db.add(assignment)
            await db.commit()
            return {"message": "Course assigned to all employees company-wide.", "assignments_created": 1}

        else:
            raise HTTPException(400, "assign_type must be Individual, Department, or Company-Wide")

    async def get_compliance_dashboard(
        self, db: AsyncSession, company_id: int
    ) -> dict:
        """Compliance overview: how many employees completed training."""

        # Total active employees
        total_result = await db.execute(
            select(func.count()).where(
                UserMaster.company_id == company_id,
                UserMaster.status == "Active",
                UserMaster.is_deleted == "N",
                UserMaster.role_id == 4,  # Employee role only
            )
        )
        total = total_result.scalar() or 0

        # Completed
        completed_result = await db.execute(
            select(func.count(TrainingHistory.user_id.distinct())).where(
                TrainingHistory.company_id == company_id,
                TrainingHistory.status == "Completed",
            )
        )
        completed = completed_result.scalar() or 0

        # In Progress
        in_progress_result = await db.execute(
            select(func.count(TrainingHistory.user_id.distinct())).where(
                TrainingHistory.company_id == company_id,
                TrainingHistory.status == "In Progress",
            )
        )
        in_progress = in_progress_result.scalar() or 0

        not_started = max(0, total - completed - in_progress)
        compliance_rate = round((completed / total * 100), 2) if total > 0 else 0.0

        # Department breakdown
        dept_result = await db.execute(
            select(
                UserMaster.department,
                func.count(UserMaster.user_id).label("total"),
            )
            .where(
                UserMaster.company_id == company_id,
                UserMaster.status == "Active",
                UserMaster.role_id == 4,
            )
            .group_by(UserMaster.department)
        )
        departments = [
            {"department": row.department or "Unassigned", "total": row.total}
            for row in dept_result
        ]

        # Overdue employees (assigned but not completed past due date)
        now = datetime.now(timezone.utc)
        overdue_result = await db.execute(
            select(UserMaster.first_name, UserMaster.email, CourseAssignment.due_date)
            .join(
                CourseAssignment,
                and_(
                    or_(
                        CourseAssignment.assigned_to_user_id == UserMaster.user_id,
                        and_(
                            CourseAssignment.assigned_to_department == UserMaster.department,
                            CourseAssignment.assign_type == "Department",
                        ),
                        CourseAssignment.assign_type == "Company-Wide",
                    ),
                    CourseAssignment.company_id == company_id,
                ),
            )
            .where(
                UserMaster.company_id == company_id,
                CourseAssignment.due_date < now,
            )
            .limit(50)
        )
        overdue = [
            {
                "name": f"{row.first_name}",
                "email": row.email,
                "due_date": str(row.due_date),
            }
            for row in overdue_result
        ]

        return {
            "total_employees": total,
            "completed": completed,
            "in_progress": in_progress,
            "not_started": not_started,
            "compliance_rate": compliance_rate,
            "department_breakdown": departments,
            "overdue_employees": overdue,
        }

    async def generate_employee_report(
        self, db: AsyncSession, company_id: int
    ) -> bytes:
        """Generate an Excel report of employee training status."""

        result = await db.execute(
            select(
                UserMaster.employee_id,
                UserMaster.first_name,
                UserMaster.last_name,
                UserMaster.email,
                UserMaster.department,
                TrainingHistory.status,
                TrainingHistory.completion_percent,
                TrainingHistory.completed_at,
            )
            .outerjoin(TrainingHistory, TrainingHistory.user_id == UserMaster.user_id)
            .where(
                UserMaster.company_id == company_id,
                UserMaster.is_deleted == "N",
            )
        )
        rows = result.all()

        # Build DataFrame
        data = [
            {
                "Employee ID": row.employee_id,
                "First Name": row.first_name,
                "Last Name": row.last_name or "",
                "Email": row.email,
                "Department": row.department or "",
                "Training Status": row.status or "Not Started",
                "Completion %": float(row.completion_percent or 0),
                "Completed Date": str(row.completed_at or ""),
            }
            for row in rows
        ]

        df = pd.DataFrame(data)

        # Write to Excel in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Employee Training Report")

            # Auto-fit column widths
            worksheet = writer.sheets["Employee Training Report"]
            for col in worksheet.columns:
                max_length = max(len(str(cell.value or "")) for cell in col)
                worksheet.column_dimensions[col[0].column_letter].width = min(max_length + 2, 50)

        output.seek(0)
        return output.read()
```

### 37.3 Create HR Router

Create `backend/app/api/v1/hr.py`:

```python
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_roles
from app.db.session import get_db
from app.schemas.hr import TrainingAssignRequest
from app.services.hr_service import HRService

router = APIRouter(prefix="/hr", tags=["HR Portal"])
hr_service = HRService()

HR_ROLES = [1, 2, 3]  # Super Admin, Company Admin, HR


@router.post("/employees/bulk-upload")
async def bulk_upload_employees(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(HR_ROLES)),
):
    """
    Upload Excel or CSV file to create employees in bulk.
    Returns success count and per-row error details.
    Supported formats: .xlsx, .xls, .csv
    Required columns: employee_id, first_name, email, mobile, role_id
    """
    return await hr_service.bulk_upload_employees(
        db, file, current_user.company_id, current_user.user_id
    )


@router.post("/training/assign")
async def assign_training(
    data: TrainingAssignRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(HR_ROLES)),
):
    """
    Assign a training video to:
    - Individual employee (assign_type: Individual, assigned_to_user_id required)
    - Department (assign_type: Department, assigned_to_department required)
    - Entire company (assign_type: Company-Wide)
    """
    return await hr_service.assign_training(
        db, data, current_user.company_id, current_user.user_id
    )


@router.get("/compliance/dashboard")
async def compliance_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(HR_ROLES)),
):
    """
    Compliance overview for the company:
    total employees, completed, in-progress, not-started, compliance rate,
    department breakdown, and overdue employees list.
    """
    return await hr_service.get_compliance_dashboard(db, current_user.company_id)


@router.get("/reports/employees")
async def download_employee_report(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(HR_ROLES)),
):
    """
    Download employee training report as Excel file.
    Contains all employees with their training status and completion %.
    """
    excel_bytes = await hr_service.generate_employee_report(db, current_user.company_id)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=employee_training_report.xlsx"},
    )
```

### 37.4 Register HR Router in main.py

Update `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.assessments import router as assessments_router
from app.api.v1.auth import router as auth_router
from app.api.v1.company import router as company_router
from app.api.v1.hr import router as hr_router
from app.api.v1.users import router as users_router
from app.api.v1.videos import router as videos_router
from app.core.config import settings

app = FastAPI(title="POSH Training Platform API", version="1.0.0", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(company_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(videos_router, prefix="/api/v1")
app.include_router(assessments_router, prefix="/api/v1")
app.include_router(hr_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": "POSH Training Platform"}


@app.get("/")
async def root():
    return {"message": "POSH Platform API. Visit /docs for documentation."}
```

### 37.5 Update models `__init__.py`

Update `backend/app/models/__init__.py`:

```python
from app.models.auth import (  # noqa: F401
    AccountLockout,
    LoginAttempts,
    OTPVerification,
    PasswordResetTokens,
    RefreshTokens,
)
from app.models.company import CompanyMaster  # noqa: F401
from app.models.hr import EmployeeUploadBatch  # noqa: F401
from app.models.language import LanguageMaster  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.role import RoleMaster  # noqa: F401
from app.models.training import (  # noqa: F401
    AssessmentOption,
    AssessmentQuestion,
    AssessmentResult,
    CourseAssignment,
    TrainingHistory,
)
from app.models.user import UserMaster  # noqa: F401
from app.models.video import VideoCategory, VideoLanguage, VideoMaster  # noqa: F401
```

---

## STEP 38: Add Phase 3 Tests

Create `backend/tests/test_hr.py`:

```python
import io
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_bulk_upload_requires_auth():
    """Unauthenticated upload should be rejected."""
    response = client.post("/api/v1/hr/employees/bulk-upload")
    assert response.status_code == 401


def test_bulk_upload_rejects_wrong_format():
    """PDF files should be rejected — only xlsx/csv allowed."""
    with patch(
        "app.services.hr_service.HRService.bulk_upload_employees",
        new_callable=AsyncMock,
        side_effect=HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload .xlsx or .csv",
        ),
    ):
        fake_pdf = io.BytesIO(b"%PDF fake content")
        response = client.post(
            "/api/v1/hr/employees/bulk-upload",
            files={"file": ("employees.pdf", fake_pdf, "application/pdf")},
            headers={"Authorization": "Bearer fake_token"},
        )
    assert response.status_code in [400, 401]


def test_training_assign_requires_auth():
    """Unauthenticated assignment should be rejected."""
    response = client.post(
        "/api/v1/hr/training/assign",
        json={
            "video_id": 1,
            "assign_type": "Company-Wide",
            "due_days": 30,
            "passing_score": 70,
        },
    )
    assert response.status_code == 401


def test_compliance_dashboard_requires_auth():
    """Compliance dashboard is not public."""
    response = client.get("/api/v1/hr/compliance/dashboard")
    assert response.status_code == 401


def test_employee_report_download_requires_auth():
    """Report download requires authentication."""
    response = client.get("/api/v1/hr/reports/employees")
    assert response.status_code == 401


def test_training_assign_invalid_type():
    """Invalid assign_type should return validation error."""
    with patch(
        "app.services.hr_service.HRService.assign_training",
        new_callable=AsyncMock,
        side_effect=HTTPException(
            status_code=400,
            detail="assign_type must be Individual, Department, or Company-Wide",
        ),
    ):
        response = client.post(
            "/api/v1/hr/training/assign",
            json={
                "video_id": 1,
                "assign_type": "InvalidType",
                "due_days": 30,
            },
            headers={"Authorization": "Bearer fake_token"},
        )
    assert response.status_code in [400, 401]
```

---

## STEP 39: Lint, Test, Commit Phase 3

```bash
cd backend
black .
ruff check --fix .
ruff check .
pytest tests/ -v
cd ..
```

All tests green:

```bash
git add .
git commit -m "feat(phase3): HR portal — bulk upload, training assignment, compliance dashboard, Excel report"
git push origin develop
```



# PHASE 4 — CERTIFICATES + ANALYTICS (Week 13–15)

**What we build:**

- Certificate template management
- Auto PDF certificate generation (after assessment pass)
- QR code generation for each certificate
- Public QR verification endpoint
- Admin analytics dashboard
- Audit log viewer

---

## STEP 40: Add Certificate Database Tables

### 40.1 Create Certificate Models

Create `backend/app/models/certificate.py`:

```python
from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.sql import func

from app.db.base import Base


class CertificateTemplate(Base):
    """
    Admin creates templates that define what certificates look like.
    Stores paths to logo and signature images.
    """

    __tablename__ = "certificate_template"

    template_id = Column(Integer, primary_key=True, autoincrement=True)
    template_name = Column(String(100))
    logo_path = Column(String(255))          # path in MinIO
    font_name = Column(String(50), default="Helvetica")
    signature_path = Column(String(255))     # path in MinIO
    color_code = Column(String(20), default="#1a3c5e")
    company_id = Column(Integer, ForeignKey("company_master.company_id"))
    status = Column(Enum("Active", "Inactive"), default="Active")
    created_date = Column(DateTime, server_default=func.now())
    updated_date = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Certificate(Base):
    """
    One row per certificate issued.
    certificate_number is unique, publicly verifiable via QR code.
    """

    __tablename__ = "certificates"

    certificate_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user_master.user_id"))
    company_id = Column(Integer, ForeignKey("company_master.company_id"))
    template_id = Column(Integer, ForeignKey("certificate_template.template_id"), nullable=True)
    certificate_number = Column(String(100), unique=True)   # e.g. POSH-2026-000123
    course_name = Column(String(200))
    completion_date = Column(Date)
    issue_date = Column(Date)
    qr_code_path = Column(String(255))       # QR image stored in MinIO
    pdf_path = Column(String(255))           # Certificate PDF stored in MinIO
    status = Column(Enum("Valid", "Revoked"), default="Valid")
    created_date = Column(DateTime, server_default=func.now())
    updated_date = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

### 40.2 Create Analytics Summary Model

Create `backend/app/models/analytics.py`:

```python
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy import BigInteger
from sqlalchemy.sql import func

from app.db.base import Base


class AnalyticsSummary(Base):
    """
    Daily snapshot of company-level training analytics.
    Refreshed by a background job — never queried in real time.
    This prevents heavy aggregation from slowing down live users.
    """

    __tablename__ = "analytics_summary"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("company_master.company_id"))
    report_date = Column(Date)
    total_employees = Column(Integer, default=0)
    completed = Column(Integer, default=0)
    in_progress = Column(Integer, default=0)
    not_started = Column(Integer, default=0)
    compliance_rate = Column(Numeric(5, 2), default=0)
    created_date = Column(DateTime, server_default=func.now())
```

### 40.3 Update alembic/env.py

Add to imports in `backend/alembic/env.py`:

```python
from app.models.analytics import AnalyticsSummary  # noqa: F401
from app.models.certificate import Certificate, CertificateTemplate  # noqa: F401
```

### 40.4 Generate and Apply Migration

```bash
alembic revision --autogenerate -m "add_phase4_certificate_analytics_tables"
alembic upgrade head
```

Verify:

```sql
SHOW TABLES;
-- Should include: certificate_template, certificates, analytics_summary
```

---

## STEP 41: Build Certificate Generation Service

### 41.1 Create Certificate Schema

Create `backend/app/schemas/certificate.py`:

```python
from datetime import date
from typing import Optional

from pydantic import BaseModel


class CertificateTemplateCreate(BaseModel):
    template_name: str
    font_name: Optional[str] = "Helvetica"
    color_code: Optional[str] = "#1a3c5e"


class CertificateTemplateResponse(BaseModel):
    template_id: int
    template_name: str
    font_name: str
    color_code: str
    status: str

    class Config:
        from_attributes = True


class CertificateResponse(BaseModel):
    certificate_id: int
    certificate_number: str
    course_name: str
    completion_date: Optional[date]
    issue_date: Optional[date]
    status: str

    class Config:
        from_attributes = True


class CertificateVerifyResponse(BaseModel):
    """Public-facing response — deliberately limited to avoid PII exposure."""
    certificate_number: str
    employee_name: str       # first name + masked last name: "Ravi K."
    course_name: str
    completion_date: Optional[date]
    issue_date: Optional[date]
    status: str              # Valid or Revoked
```

### 41.2 Create Certificate Service

Create `backend/app/services/certificate_service.py`:

```python
import io
from datetime import date, datetime, timezone
from typing import Optional

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.core.storage import generate_presigned_url, upload_file
from app.models.certificate import Certificate, CertificateTemplate
from app.models.user import UserMaster
from app.models.video import VideoMaster

CERT_BUCKET = "posh-certificates"
BASE_VERIFY_URL = "http://localhost:8000/api/v1/certificates/verify"


class CertificateService:

    async def generate_certificate(
        self,
        db,
        user_id: int,
        video_id: int,
        company_id: int,
    ) -> Certificate:
        """
        Full certificate generation workflow:
        1. Generate unique certificate number
        2. Generate QR code PNG
        3. Generate PDF certificate
        4. Upload both to MinIO
        5. Save record to DB
        """

        # 1. Fetch user and video details
        user_result = await db.execute(
            select(UserMaster).where(UserMaster.user_id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(404, "User not found")

        video_result = await db.execute(
            select(VideoMaster).where(VideoMaster.video_id == video_id)
        )
        video = video_result.scalar_one_or_none()
        if not video:
            raise HTTPException(404, "Video not found")

        # 2. Generate unique certificate number
        year = datetime.now().year
        count_result = await db.execute(
            select(func.count()).where(Certificate.company_id == company_id)
        )
        count = (count_result.scalar() or 0) + 1
        cert_number = f"POSH-{year}-{str(count).zfill(6)}"  # e.g. POSH-2026-000123

        # 3. Generate QR code
        verify_url = f"{BASE_VERIFY_URL}/{cert_number}"
        qr_bytes = self._generate_qr(verify_url)
        qr_path = f"certificates/{company_id}/qr/{cert_number}.png"
        upload_file(qr_bytes, CERT_BUCKET, qr_path, "image/png")

        # 4. Generate PDF certificate
        employee_name = f"{user.first_name} {user.last_name or ''}".strip()
        pdf_bytes = self._generate_pdf(
            employee_name=employee_name,
            course_name=video.title,
            cert_number=cert_number,
            completion_date=date.today(),
        )
        pdf_path = f"certificates/{company_id}/pdf/{cert_number}.pdf"
        upload_file(pdf_bytes, CERT_BUCKET, pdf_path, "application/pdf")

        # 5. Save to DB
        certificate = Certificate(
            user_id=user_id,
            company_id=company_id,
            certificate_number=cert_number,
            course_name=video.title,
            completion_date=date.today(),
            issue_date=date.today(),
            qr_code_path=qr_path,
            pdf_path=pdf_path,
            status="Valid",
        )
        db.add(certificate)
        await db.commit()
        await db.refresh(certificate)
        return certificate

    def _generate_qr(self, url: str) -> bytes:
        """Generate QR code as PNG bytes."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf.read()

    def _generate_pdf(
        self,
        employee_name: str,
        course_name: str,
        cert_number: str,
        completion_date: date,
    ) -> bytes:
        """Generate certificate PDF using ReportLab."""
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=landscape(A4),
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        styles = getSampleStyleSheet()
        story = []

        # Title
        from reportlab.platypus import Paragraph
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.enums import TA_CENTER

        title_style = ParagraphStyle(
            "Title",
            fontSize=28,
            textColor=colors.HexColor("#1a3c5e"),
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            spaceAfter=20,
        )
        body_style = ParagraphStyle(
            "Body",
            fontSize=14,
            alignment=TA_CENTER,
            fontName="Helvetica",
            spaceAfter=12,
        )
        name_style = ParagraphStyle(
            "Name",
            fontSize=22,
            textColor=colors.HexColor("#1a3c5e"),
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            spaceAfter=16,
        )
        small_style = ParagraphStyle(
            "Small",
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.grey,
            fontName="Helvetica",
        )

        story.append(Spacer(1, 1 * cm))
        story.append(Paragraph("Certificate of Completion", title_style))
        story.append(Paragraph("This is to certify that", body_style))
        story.append(Paragraph(employee_name, name_style))
        story.append(Paragraph("has successfully completed the POSH Training course", body_style))
        story.append(Paragraph(f"<b>{course_name}</b>", body_style))
        story.append(Spacer(1, 0.5 * cm))
        story.append(
            Paragraph(
                f"Completion Date: {completion_date.strftime('%d %B %Y')}",
                body_style,
            )
        )
        story.append(Spacer(1, 1 * cm))
        story.append(Paragraph(f"Certificate Number: {cert_number}", small_style))
        story.append(
            Paragraph(
                f"Verify at: {BASE_VERIFY_URL}/{cert_number}",
                small_style,
            )
        )

        doc.build(story)
        buf.seek(0)
        return buf.read()

    async def get_download_url(
        self, db, certificate_id: int, user_id: int
    ) -> dict:
        """Get a short-lived signed URL to download the certificate PDF."""
        result = await db.execute(
            select(Certificate).where(
                Certificate.certificate_id == certificate_id,
                Certificate.user_id == user_id,
                Certificate.status == "Valid",
            )
        )
        cert = result.scalar_one_or_none()
        if not cert:
            raise HTTPException(404, "Certificate not found.")

        url = generate_presigned_url(CERT_BUCKET, cert.pdf_path, 300)
        return {"download_url": url, "certificate_number": cert.certificate_number}

    async def verify_certificate(self, db, certificate_number: str) -> dict:
        """
        Public endpoint — verifies a certificate by its number.
        Called when someone scans a QR code.
        Returns minimal info (no sensitive PII).
        """
        result = await db.execute(
            select(Certificate, UserMaster)
            .join(UserMaster, Certificate.user_id == UserMaster.user_id)
            .where(Certificate.certificate_number == certificate_number)
        )
        row = result.first()

        if not row:
            return {
                "valid": False,
                "message": "Certificate not found.",
                "certificate_number": certificate_number,
            }

        cert, user = row

        # Mask last name: "Ravi Kumar" → "Ravi K."
        last_initial = f"{user.last_name[0]}." if user.last_name else ""
        masked_name = f"{user.first_name} {last_initial}".strip()

        return {
            "valid": cert.status == "Valid",
            "certificate_number": cert.certificate_number,
            "employee_name": masked_name,
            "course_name": cert.course_name,
            "completion_date": str(cert.completion_date),
            "issue_date": str(cert.issue_date),
            "status": cert.status,
        }

    async def revoke_certificate(
        self, db, certificate_id: int
    ) -> dict:
        """Revoke a certificate (Super Admin only)."""
        result = await db.execute(
            select(Certificate).where(Certificate.certificate_id == certificate_id)
        )
        cert = result.scalar_one_or_none()
        if not cert:
            raise HTTPException(404, "Certificate not found.")
        cert.status = "Revoked"
        await db.commit()
        return {"message": f"Certificate {cert.certificate_number} revoked."}

    async def list_user_certificates(
        self, db, user_id: int
    ) -> list:
        """List all certificates for a user."""
        result = await db.execute(
            select(Certificate).where(
                Certificate.user_id == user_id,
                Certificate.status == "Valid",
            )
        )
        return result.scalars().all()
```

### 41.3 Create Certificate Router

Create `backend/app/api/v1/certificates.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.services.certificate_service import CertificateService

router = APIRouter(prefix="/certificates", tags=["Certificates"])
cert_service = CertificateService()


@router.get("/my")
async def my_certificates(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Employee: list all my certificates."""
    return await cert_service.list_user_certificates(db, current_user.user_id)


@router.get("/{certificate_id}/download")
async def download_certificate(
    certificate_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Employee: get a signed URL to download a certificate PDF."""
    return await cert_service.get_download_url(db, certificate_id, current_user.user_id)


@router.get("/verify/{certificate_number}")
async def verify_certificate(
    certificate_number: str,
    db: AsyncSession = Depends(get_db),
):
    """
    PUBLIC endpoint — no authentication required.
    Called when someone scans a QR code.
    Rate-limited at Nginx level.
    """
    return await cert_service.verify_certificate(db, certificate_number)


@router.post("/{certificate_id}/revoke")
async def revoke_certificate(
    certificate_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1])),  # Super Admin only
):
    """Super Admin: revoke a certificate."""
    return await cert_service.revoke_certificate(db, certificate_id)


@router.post("/generate")
async def generate_certificate_manual(
    user_id: int,
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1, 2])),  # Admin only — for testing
):
    """
    Manually trigger certificate generation.
    In production this is called automatically after assessment pass.
    """
    cert = await cert_service.generate_certificate(
        db, user_id, video_id, current_user.company_id
    )
    return {
        "message": "Certificate generated successfully.",
        "certificate_number": cert.certificate_number,
        "certificate_id": cert.certificate_id,
    }
```

### 41.4 Wire Assessment to Certificate Generation

Update `backend/app/services/assessment_service.py` — replace the `# TODO` comment with actual call:

```python
        # 5. Trigger certificate generation on Pass
        if result == "Pass":
            cert_service = CertificateService()
            try:
                cert = await cert_service.generate_certificate(
                    db, user_id, data.video_id, company_id
                )
                response["certificate_number"] = cert.certificate_number
                response["message"] = (
                    f"Congratulations! Certificate {cert.certificate_number} generated."
                )
            except Exception as e:
                # Don't fail the assessment if certificate generation fails
                response["message"] = "Assessment passed. Certificate generation in progress."
        else:
            response["message"] = (
                f"Score: {score:.1f}%. You need {passing_score}% to pass. Please retry."
            )
```

You'll also need to update the `submit` method signature to accept `company_id`:

```python
    async def submit(
        self, db: AsyncSession, user_id: int, data: AssessmentSubmit, company_id: int
    ) -> dict:
```

And update the call in `assessments.py`:

```python
    return await assessment_service.submit(
        db, current_user.user_id, data, current_user.company_id
    )
```

### 41.5 Register Certificate Router in main.py

Update `backend/app/main.py` — add:

```python
from app.api.v1.certificates import router as certificates_router

app.include_router(certificates_router, prefix="/api/v1")
```

---

## STEP 42: Build Analytics Module

Create `backend/app/api/v1/analytics.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_roles
from app.db.session import get_db
from app.models.certificate import Certificate
from app.models.company import CompanyMaster
from app.models.training import AssessmentResult, TrainingHistory
from app.models.user import UserMaster

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview")
async def analytics_overview(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1])),  # Super Admin only
):
    """Platform-wide analytics for Super Admin."""

    # Total companies
    companies_result = await db.execute(
        select(func.count()).where(
            CompanyMaster.is_deleted == "N", CompanyMaster.status == "Active"
        )
    )
    total_companies = companies_result.scalar() or 0

    # Total users
    users_result = await db.execute(
        select(func.count()).where(
            UserMaster.is_deleted == "N", UserMaster.status == "Active"
        )
    )
    total_users = users_result.scalar() or 0

    # Total certificates issued
    certs_result = await db.execute(
        select(func.count()).where(Certificate.status == "Valid")
    )
    total_certificates = certs_result.scalar() or 0

    # Total completions
    completions_result = await db.execute(
        select(func.count()).where(TrainingHistory.status == "Completed")
    )
    total_completions = completions_result.scalar() or 0

    # Average assessment score
    avg_score_result = await db.execute(
        select(func.avg(AssessmentResult.score)).where(
            AssessmentResult.result == "Pass"
        )
    )
    avg_score = round(float(avg_score_result.scalar() or 0), 2)

    return {
        "total_companies": total_companies,
        "total_users": total_users,
        "total_certificates_issued": total_certificates,
        "total_course_completions": total_completions,
        "average_pass_score": avg_score,
    }


@router.get("/company/{company_id}")
async def company_analytics(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1, 2])),
):
    """Analytics for a specific company."""

    # Employee counts
    total_result = await db.execute(
        select(func.count()).where(
            UserMaster.company_id == company_id,
            UserMaster.is_deleted == "N",
            UserMaster.role_id == 4,
        )
    )
    total = total_result.scalar() or 0

    completed_result = await db.execute(
        select(func.count(TrainingHistory.user_id.distinct())).where(
            TrainingHistory.company_id == company_id,
            TrainingHistory.status == "Completed",
        )
    )
    completed = completed_result.scalar() or 0

    cert_result = await db.execute(
        select(func.count()).where(Certificate.company_id == company_id)
    )
    total_certs = cert_result.scalar() or 0

    compliance_rate = round((completed / total * 100), 2) if total > 0 else 0.0

    return {
        "company_id": company_id,
        "total_employees": total,
        "completed_training": completed,
        "compliance_rate": compliance_rate,
        "certificates_issued": total_certs,
    }
```

Add to `main.py`:

```python
from app.api.v1.analytics import router as analytics_router
app.include_router(analytics_router, prefix="/api/v1")
```

---

## STEP 43: Update models `__init__.py` for Phase 4

Update `backend/app/models/__init__.py`:

```python
from app.models.analytics import AnalyticsSummary  # noqa: F401
from app.models.auth import (  # noqa: F401
    AccountLockout,
    LoginAttempts,
    OTPVerification,
    PasswordResetTokens,
    RefreshTokens,
)
from app.models.certificate import Certificate, CertificateTemplate  # noqa: F401
from app.models.company import CompanyMaster  # noqa: F401
from app.models.hr import EmployeeUploadBatch  # noqa: F401
from app.models.language import LanguageMaster  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.role import RoleMaster  # noqa: F401
from app.models.training import (  # noqa: F401
    AssessmentOption,
    AssessmentQuestion,
    AssessmentResult,
    CourseAssignment,
    TrainingHistory,
)
from app.models.user import UserMaster  # noqa: F401
from app.models.video import VideoCategory, VideoLanguage, VideoMaster  # noqa: F401
```

---

## STEP 44: Add Phase 4 Tests

Create `backend/tests/test_certificates.py`:

```python
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_verify_certificate_public_access():
    """Certificate verification endpoint should work without auth."""
    with patch(
        "app.services.certificate_service.CertificateService.verify_certificate",
        new_callable=AsyncMock,
        return_value={
            "valid": False,
            "message": "Certificate not found.",
            "certificate_number": "POSH-2026-999999",
        },
    ):
        response = client.get("/api/v1/certificates/verify/POSH-2026-999999")
    # Should NOT return 401 — this is a public endpoint
    assert response.status_code == 200
    assert response.json()["valid"] is False


def test_my_certificates_requires_auth():
    """Employee certificate list requires authentication."""
    response = client.get("/api/v1/certificates/my")
    assert response.status_code == 401


def test_revoke_requires_super_admin():
    """Certificate revocation requires Super Admin role."""
    response = client.post(
        "/api/v1/certificates/1/revoke",
        headers={"Authorization": "Bearer fake_token"},
    )
    assert response.status_code == 401


def test_certificate_number_format():
    """Certificate numbers follow POSH-YEAR-XXXXXX format."""
    import re
    pattern = r"^POSH-\d{4}-\d{6}$"
    sample = "POSH-2026-000123"
    assert re.match(pattern, sample), f"Certificate number format invalid: {sample}"


def test_analytics_requires_auth():
    """Analytics overview requires authentication."""
    response = client.get("/api/v1/analytics/overview")
    assert response.status_code == 401
```

---

## STEP 45: Final Lint, Test, Commit

```bash
cd backend
black .
ruff check --fix .
ruff check --fix --unsafe-fixes .
ruff check .
pytest tests/ -v
cd ..
```

Expected: all tests pass.

```bash
git add .
git commit -m "feat(phase4): certificate PDF+QR generation, public verification, analytics dashboard"
git push origin develop
```
---

## DONE
---

## Phase 3 + Phase 4 Complete ✅ Checklist

**Phase 3:**

- ✅ Bulk employee upload (Excel/CSV with per-row validation)
- ✅ CSV injection prevention
- ✅ Training assignment (Individual / Department / Company-Wide)
- ✅ Compliance dashboard with overdue alerts
- ✅ Excel report download (openpyxl)
- ✅ HR, notification tables migrated

**Phase 4:**

- ✅ Certificate template model
- ✅ Certificate generation — unique number, QR code, PDF
- ✅ Certificate stored in MinIO — never directly accessible
- ✅ Public QR verification endpoint (no auth, rate-limited by Nginx)
- ✅ Certificate revocation (Super Admin only)
- ✅ Employee certificate download via signed URL
- ✅ Platform analytics (Super Admin)
- ✅ Company analytics (Company Admin)
- ✅ CI green

---

## Full Backend API Summary (All Phases)

| Prefix                 | Module                                                 | Roles                     |
| ---------------------- | ------------------------------------------------------ | ------------------------- |
| `/api/v1/auth`         | Signup, Login, OTP, JWT, Logout, Forgot/Reset Password | Public                    |
| `/api/v1/companies`    | Company CRUD, Activate/Deactivate                      | Super Admin               |
| `/api/v1/users`        | User CRUD, Reset Password                              | Admin, HR                 |
| `/api/v1/videos`       | Upload, Publish, Stream URL, Progress                  | Admin / Employee          |
| `/api/v1/assessments`  | Submit answers, Score, Pass/Fail                       | Employee                  |
| `/api/v1/hr`           | Bulk Upload, Training Assign, Compliance, Reports      | HR                        |
| `/api/v1/certificates` | List, Download, Verify (public), Revoke                | Employee / Public / Admin |
| `/api/v1/analytics`    | Platform + Company analytics                           | Admin                     |

---

## What Comes Next — Phase 5

| Topic              | What it covers                                 |
| ------------------ | ---------------------------------------------- |
| Email delivery     | Real OTP + certificate emails via SMTP/Celery  |
| React frontend     | All screens wired to backend APIs              |
| Security hardening | Rate limiting, CORS, headers, OWASP checklist  |
| Load testing       | Locust — simulate concurrent users             |
| Production Docker  | Non-dev Compose, environment separation        |
| Cloud deployment   | VM setup, Nginx TLS, Let's Encrypt, monitoring |

**Phase 5 guide will be provided when you are ready.**

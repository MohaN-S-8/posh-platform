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
            existing = await db.execute(select(UserMaster).where(UserMaster.email == email))
            if existing.scalar_one_or_none():
                errors.append(
                    {
                        "row": row_num,
                        "email": email,
                        "errors": ["Email already registered — skipped"],
                    }
                )
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
            return {
                "message": "Course assigned to employee successfully.",
                "assignments_created": 1,
            }

        elif data.assign_type == "Department":
            if not data.assigned_to_department:
                raise HTTPException(
                    400, "assigned_to_department required for Department assignment"
                )

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
            return {
                "message": "Course assigned to all employees company-wide.",
                "assignments_created": 1,
            }

        else:
            raise HTTPException(400, "assign_type must be Individual, Department, or Company-Wide")

    async def get_compliance_dashboard(self, db: AsyncSession, company_id: int) -> dict:
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

    async def generate_employee_report(self, db: AsyncSession, company_id: int) -> bytes:
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

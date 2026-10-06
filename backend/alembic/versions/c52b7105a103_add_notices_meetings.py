"""Persist branch notice status and quarterly IC meetings."""

import sqlalchemy as sa

from alembic import op

revision = "c52b7105a103"
down_revision = "c52b7105a102"
branch_labels = None
depends_on = None


def upgrade():
    if not sa.inspect(op.get_bind()).has_table("posh_notice_displays"):
        op.create_table(
            "posh_notice_displays",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column(
                "company_id",
                sa.Integer,
                sa.ForeignKey("company_master.company_id"),
                nullable=False,
                index=True,
            ),
            sa.Column("branch_id", sa.String(50), nullable=False),
            sa.Column("branch_name", sa.String(150), nullable=False),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("notes", sa.String(2000), nullable=False),
            sa.Column("updated_by", sa.Integer, nullable=False),
            sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("company_id", "branch_id", name="uq_notice_company_branch"),
            sa.CheckConstraint("status IN ('Pending', 'Completed')", name="ck_notice_status"),
        )
    if not sa.inspect(op.get_bind()).has_table("posh_quarterly_meetings"):
        op.create_table(
            "posh_quarterly_meetings",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column(
                "company_id",
                sa.Integer,
                sa.ForeignKey("company_master.company_id"),
                nullable=False,
                index=True,
            ),
            sa.Column("branch_id", sa.String(50), nullable=False),
            sa.Column("branch_name", sa.String(150), nullable=False),
            sa.Column("year", sa.Integer, nullable=False),
            sa.Column("quarter", sa.Integer, nullable=False),
            sa.Column("meeting_date", sa.Date, nullable=False),
            sa.Column("meeting_time", sa.Time, nullable=False),
            sa.Column("presiding_officer", sa.String(150), nullable=False),
            sa.Column("venue", sa.String(500), nullable=False),
            sa.Column("attendees", sa.String(4000), nullable=False),
            *[sa.Column(f"agenda{i}", sa.Text, nullable=False) for i in range(1, 6)],
            sa.Column("photo_key", sa.String(500)),
            sa.Column("signed_key", sa.String(500)),
            sa.Column("signed_filename", sa.String(200)),
            sa.Column("created_by", sa.Integer, nullable=False),
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint(
                "company_id", "branch_id", "year", "quarter", name="uq_meeting_branch_quarter"
            ),
            sa.CheckConstraint("quarter BETWEEN 1 AND 4", name="ck_meeting_quarter"),
            sa.CheckConstraint("year BETWEEN 2000 AND 2100", name="ck_meeting_year"),
        )


def downgrade():
    op.drop_table("posh_quarterly_meetings")
    op.drop_table("posh_notice_displays")

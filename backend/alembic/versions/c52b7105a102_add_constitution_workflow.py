"""Add company external members and IC constitution letters."""

import sqlalchemy as sa

from alembic import op

revision = "c52b7105a102"
down_revision = "8f4d2b6c1a90"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("posh_external_members"):
        op.create_table(
            "posh_external_members",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column(
                "company_id",
                sa.Integer,
                sa.ForeignKey("company_master.company_id"),
                nullable=False,
                index=True,
            ),
            sa.Column("name", sa.String(150), nullable=False),
            sa.Column("organization", sa.String(200), nullable=False),
            sa.Column("designation", sa.String(150), nullable=False),
            sa.Column("location", sa.String(150), nullable=False),
            sa.Column("contact", sa.String(25), nullable=False),
            sa.Column("email", sa.String(254), nullable=False),
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("company_id", "email", name="uq_external_member_email"),
        )
    if not sa.inspect(bind).has_table("posh_constitution_letters"):
        op.create_table(
            "posh_constitution_letters",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column(
                "company_id",
                sa.Integer,
                sa.ForeignKey("company_master.company_id"),
                nullable=False,
                index=True,
            ),
            sa.Column(
                "member_id",
                sa.Integer,
                sa.ForeignKey("posh_external_members.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("filename", sa.String(200), nullable=False),
            sa.Column("object_key", sa.String(500), nullable=False),
            sa.Column("approver_name", sa.String(150), nullable=False),
            sa.Column("approver_email", sa.String(254), nullable=False),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("delivery_status", sa.String(20), nullable=False),
            sa.Column("token_hash", sa.String(64), unique=True),
            sa.Column("token_expires_at", sa.DateTime, nullable=False),
            sa.Column("reviewed_at", sa.DateTime),
            sa.Column("approved_at", sa.DateTime),
            sa.Column("submitted_by", sa.Integer, nullable=False),
            sa.Column("submitted_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.CheckConstraint("status IN ('Pending', 'Completed')", name="ck_constitution_status"),
        )


def downgrade():
    op.drop_table("posh_constitution_letters")
    op.drop_table("posh_external_members")

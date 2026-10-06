"""Separate Co-Partner permission records from Super Admin."""

from alembic import op
from app.core.role_matrix import SEED_COPARTNER

revision = "c52b7105a104"
down_revision = "c52b7105a103"
branch_labels = None
depends_on = None


def upgrade():
    op.get_bind().execute(SEED_COPARTNER)


def downgrade():
    # Preserve configured permissions on downgrade.
    pass

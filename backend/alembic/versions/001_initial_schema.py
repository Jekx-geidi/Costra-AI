"""001 initial schema

Revision ID: 001
Revises:
Create Date: 2026-10-16
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(32), nullable=False, server_default="viewer"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ai_billing_accounts
    op.create_table(
        "ai_billing_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("account_reference", sa.String(255), nullable=False),
        sa.Column("account_name", sa.String(255), nullable=False),
        sa.Column("ownership_type", sa.String(32), nullable=False),
        sa.Column("collection_method", sa.String(16), nullable=False),
        sa.Column("default_currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("authorization_status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_billing_accounts_provider", "ai_billing_accounts", ["provider"])

    # ai_billing_sources
    op.create_table(
        "ai_billing_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_billing_accounts.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_type", sa.String(16), nullable=False),
        sa.Column("source_reference", sa.String(512), nullable=True),
        sa.Column("source_hash", sa.String(64), nullable=True),
        sa.Column("billing_period_start", sa.Date(), nullable=True),
        sa.Column("billing_period_end", sa.Date(), nullable=True),
        sa.Column("imported_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="imported"),
    )
    op.create_index("ix_ai_billing_sources_account_id", "ai_billing_sources", ["account_id"])
    op.create_unique_constraint("uq_billing_source_hash", "ai_billing_sources", ["source_hash"])

    # ai_billing_records
    op.create_table(
        "ai_billing_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_billing_accounts.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_billing_sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("external_record_id", sa.String(512), nullable=True),
        sa.Column("expense_category", sa.String(32), nullable=False),
        sa.Column("financial_basis", sa.String(32), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("quantity", sa.Numeric(20, 6), nullable=True),
        sa.Column("amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("validation_status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_billing_records_account_id", "ai_billing_records", ["account_id"])
    op.create_index("ix_ai_billing_records_provider", "ai_billing_records", ["provider"])
    op.create_index("ix_ai_billing_records_period_start", "ai_billing_records", ["period_start"])
    op.create_unique_constraint("uq_billing_record_dedup", "ai_billing_records", ["account_id", "external_record_id"])

    # ai_billing_reconciliations
    op.create_table(
        "ai_billing_reconciliations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("billing_record_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_billing_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("financial_reference", sa.String(512), nullable=True),
        sa.Column("expected_amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("observed_amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("variance", sa.Numeric(20, 6), nullable=False),
        sa.Column("reconciliation_status", sa.String(16), nullable=False, server_default="unmatched"),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_billing_reconciliations_billing_record_id", "ai_billing_reconciliations", ["billing_record_id"])

    # ai_sync_runs
    op.create_table(
        "ai_sync_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_billing_accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("job_type", sa.String(32), nullable=False, server_default="api_sync"),
        sa.Column("requested_period_start", sa.Date(), nullable=True),
        sa.Column("requested_period_end", sa.Date(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="running"),
        sa.Column("capability_status", sa.String(16), nullable=False, server_default="unknown"),
        sa.Column("records_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_summary", sa.Text(), nullable=True),
    )
    op.create_index("ix_ai_sync_runs_account_id", "ai_sync_runs", ["account_id"])
    op.create_index("ix_ai_sync_runs_provider", "ai_sync_runs", ["provider"])

    # ai_audit_events
    op.create_table(
        "ai_audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("principal_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("principal_email", sa.String(255), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("resource_type", sa.String(64), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("outcome", sa.String(16), nullable=False, server_default="success"),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_audit_events_principal_id", "ai_audit_events", ["principal_id"])
    op.create_index("ix_ai_audit_events_action", "ai_audit_events", ["action"])
    op.create_index("ix_ai_audit_events_created_at", "ai_audit_events", ["created_at"])


def downgrade() -> None:
    op.drop_table("ai_audit_events")
    op.drop_table("ai_sync_runs")
    op.drop_table("ai_billing_reconciliations")
    op.drop_table("ai_billing_records")
    op.drop_table("ai_billing_sources")
    op.drop_table("ai_billing_accounts")
    op.drop_table("users")

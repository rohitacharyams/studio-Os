"""Add theme_settings column to studios table

Revision ID: 003_add_theme_settings
Revises: 002_booking_payment
Create Date: 2026-01-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '003_add_theme_settings'
down_revision = '002_booking_payment'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add theme_settings column to studios table
    # For SQLite, JSON is stored as TEXT
    # For PostgreSQL, JSON is native
    op.add_column(
        'studios',
        sa.Column('theme_settings', sa.JSON(), nullable=True, server_default='{}')
    )


def downgrade() -> None:
    # Remove theme_settings column
    op.drop_column('studios', 'theme_settings')

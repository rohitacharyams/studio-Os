"""Add instructor fields to dance_classes and class_sessions

Revision ID: 005_add_instructor_fields
Revises: 004_add_media_fields
Create Date: 2026-01-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '005_add_instructor_fields'
down_revision = '004_add_media_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add instructor fields to dance_classes table
    bind = op.get_bind()
    
    # For SQLite, use raw SQL with try/except to handle existing columns
    if bind.dialect.name == 'sqlite':
        try:
            op.execute('ALTER TABLE dance_classes ADD COLUMN instructor_name VARCHAR(255)')
        except Exception:
            pass  # Column might already exist
        try:
            op.execute('ALTER TABLE dance_classes ADD COLUMN instructor_description TEXT')
        except Exception:
            pass
        try:
            op.execute('ALTER TABLE dance_classes ADD COLUMN instructor_instagram_handle VARCHAR(100)')
        except Exception:
            pass
        try:
            op.execute('ALTER TABLE class_sessions ADD COLUMN instructor_name VARCHAR(255)')
        except Exception:
            pass
        try:
            op.execute('ALTER TABLE class_sessions ADD COLUMN substitute_instructor_name VARCHAR(255)')
        except Exception:
            pass
    else:
        # For PostgreSQL and other databases, use standard Alembic operations
        op.add_column(
            'dance_classes',
            sa.Column('instructor_name', sa.String(255), nullable=True)
        )
        op.add_column(
            'dance_classes',
            sa.Column('instructor_description', sa.Text(), nullable=True)
        )
        op.add_column(
            'dance_classes',
            sa.Column('instructor_instagram_handle', sa.String(100), nullable=True)
        )
        
        op.add_column(
            'class_sessions',
            sa.Column('instructor_name', sa.String(255), nullable=True)
        )
        op.add_column(
            'class_sessions',
            sa.Column('substitute_instructor_name', sa.String(255), nullable=True)
        )


def downgrade() -> None:
    # Remove instructor fields from class_sessions
    op.drop_column('class_sessions', 'substitute_instructor_name')
    op.drop_column('class_sessions', 'instructor_name')
    
    # Remove instructor fields from dance_classes
    op.drop_column('dance_classes', 'instructor_instagram_handle')
    op.drop_column('dance_classes', 'instructor_description')
    op.drop_column('dance_classes', 'instructor_name')

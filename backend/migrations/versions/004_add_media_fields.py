"""Add media fields to studios table

Revision ID: 004_add_media_fields
Revises: 003_add_theme_settings
Create Date: 2026-01-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '004_add_media_fields'
down_revision = '003_add_theme_settings'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add media fields to studios table
    # For SQLite, JSON is stored as TEXT
    # For PostgreSQL, JSON is native
    
    op.add_column(
        'studios',
        sa.Column('photos', sa.JSON(), nullable=True, server_default='[]')
    )
    op.add_column(
        'studios',
        sa.Column('videos', sa.JSON(), nullable=True, server_default='[]')
    )
    op.add_column(
        'studios',
        sa.Column('testimonials', sa.JSON(), nullable=True, server_default='[]')
    )
    op.add_column(
        'studios',
        sa.Column('amenities', sa.JSON(), nullable=True, server_default='[]')
    )
    op.add_column(
        'studios',
        sa.Column('social_links', sa.JSON(), nullable=True, server_default='{}')
    )
    op.add_column(
        'studios',
        sa.Column('about', sa.Text(), nullable=True)
    )


def downgrade() -> None:
    # Remove media fields columns
    op.drop_column('studios', 'about')
    op.drop_column('studios', 'social_links')
    op.drop_column('studios', 'amenities')
    op.drop_column('studios', 'testimonials')
    op.drop_column('studios', 'videos')
    op.drop_column('studios', 'photos')

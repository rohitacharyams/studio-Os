"""Add Razorpay payment ID fields to bookings table

Revision ID: 006_add_razorpay_fields_to_bookings
Revises: 005_add_instructor_fields
Create Date: 2026-01-14

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006_add_razorpay_fields_to_bookings'
down_revision = '005_add_instructor_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add Razorpay payment ID fields to bookings table
    bind = op.get_bind()
    
    # For SQLite, use raw SQL with try/except to handle existing columns
    if bind.dialect.name == 'sqlite':
        try:
            op.execute('ALTER TABLE bookings ADD COLUMN razorpay_payment_id VARCHAR(100)')
        except Exception:
            pass  # Column might already exist
        try:
            op.execute('ALTER TABLE bookings ADD COLUMN razorpay_order_id VARCHAR(100)')
        except Exception:
            pass
    else:
        # For PostgreSQL and other databases, use standard Alembic operations
        op.add_column(
            'bookings',
            sa.Column('razorpay_payment_id', sa.String(100), nullable=True)
        )
        op.add_column(
            'bookings',
            sa.Column('razorpay_order_id', sa.String(100), nullable=True)
        )


def downgrade() -> None:
    # Remove Razorpay payment ID fields from bookings table
    bind = op.get_bind()
    
    if bind.dialect.name == 'sqlite':
        # SQLite doesn't support DROP COLUMN directly, so we skip it
        # In production, you'd need to recreate the table
        pass
    else:
        op.drop_column('bookings', 'razorpay_order_id')
        op.drop_column('bookings', 'razorpay_payment_id')

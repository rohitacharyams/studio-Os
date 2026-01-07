"""Add booking and payment models

Revision ID: 002_booking_payment
Revises: 001_initial
Create Date: 2024-01-15

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_booking_payment'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create booking_status enum
    op.execute("CREATE TYPE bookingstatus AS ENUM ('PENDING', 'CONFIRMED', 'CANCELLED', 'ATTENDED', 'NO_SHOW', 'WAITLIST')")
    
    # Create payment_status enum
    op.execute("CREATE TYPE paymentstatus AS ENUM ('PENDING', 'COMPLETED', 'FAILED', 'REFUNDED', 'PARTIALLY_REFUNDED')")
    
    # Create payment_method enum
    op.execute("CREATE TYPE paymentmethod AS ENUM ('RAZORPAY', 'CASH', 'WALLET', 'CLASS_PACK', 'SUBSCRIPTION', 'FREE')")
    
    # Create refund_status enum
    op.execute("CREATE TYPE refundstatus AS ENUM ('PENDING', 'PROCESSED', 'FAILED')")
    
    # Create subscription_status enum
    op.execute("CREATE TYPE subscriptionstatus AS ENUM ('ACTIVE', 'PAUSED', 'CANCELLED', 'EXPIRED')")
    
    # Create transaction_type enum
    op.execute("CREATE TYPE transactiontype AS ENUM ('CREDIT', 'DEBIT', 'REFUND')")

    # Create class_types table
    op.create_table(
        'class_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('studio_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), server_default='60', nullable=True),
        sa.Column('capacity', sa.Integer(), server_default='20', nullable=True),
        sa.Column('price', sa.Numeric(10, 2), server_default='0', nullable=True),
        sa.Column('color', sa.String(length=7), server_default='#6366f1', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['studio_id'], ['studios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_class_types_studio_id'), 'class_types', ['studio_id'], unique=False)

    # Create class_sessions table
    op.create_table(
        'class_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('studio_id', sa.Integer(), nullable=False),
        sa.Column('class_type_id', sa.Integer(), nullable=False),
        sa.Column('instructor_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('capacity', sa.Integer(), server_default='20', nullable=True),
        sa.Column('booked_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('waitlist_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('price', sa.Numeric(10, 2), server_default='0', nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('is_cancelled', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['class_type_id'], ['class_types.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['instructor_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['studio_id'], ['studios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_class_sessions_start_time'), 'class_sessions', ['start_time'], unique=False)
    op.create_index(op.f('ix_class_sessions_studio_id'), 'class_sessions', ['studio_id'], unique=False)

    # Create bookings table
    op.create_table(
        'bookings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('studio_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('contact_id', sa.Integer(), nullable=False),
        sa.Column('booking_number', sa.String(length=50), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'CONFIRMED', 'CANCELLED', 'ATTENDED', 'NO_SHOW', 'WAITLIST', name='bookingstatus'), server_default='PENDING', nullable=True),
        sa.Column('payment_method', sa.Enum('RAZORPAY', 'CASH', 'WALLET', 'CLASS_PACK', 'SUBSCRIPTION', 'FREE', name='paymentmethod'), nullable=True),
        sa.Column('amount_paid', sa.Numeric(10, 2), server_default='0', nullable=True),
        sa.Column('booked_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('checked_in_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['class_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['studio_id'], ['studios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('booking_number')
    )
    op.create_index(op.f('ix_bookings_session_id'), 'bookings', ['session_id'], unique=False)
    op.create_index(op.f('ix_bookings_contact_id'), 'bookings', ['contact_id'], unique=False)
    op.create_index(op.f('ix_bookings_studio_id'), 'bookings', ['studio_id'], unique=False)

    # Create waitlists table
    op.create_table(
        'waitlists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('studio_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('contact_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('joined_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('notified_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['class_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['studio_id'], ['studios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_waitlists_session_id'), 'waitlists', ['session_id'], unique=False)

    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('studio_id', sa.Integer(), nullable=False),
        sa.Column('contact_id', sa.Integer(), nullable=False),
        sa.Column('booking_id', sa.Integer(), nullable=True),
        sa.Column('razorpay_order_id', sa.String(length=100), nullable=True),
        sa.Column('razorpay_payment_id', sa.String(length=100), nullable=True),
        sa.Column('razorpay_signature', sa.String(length=255), nullable=True),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(length=10), server_default='INR', nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'COMPLETED', 'FAILED', 'REFUNDED', 'PARTIALLY_REFUNDED', name='paymentstatus'), server_default='PENDING', nullable=True),
        sa.Column('payment_method', sa.Enum('RAZORPAY', 'CASH', 'WALLET', 'CLASS_PACK', 'SUBSCRIPTION', 'FREE', name='paymentmethod'), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['studio_id'], ['studios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_razorpay_order_id'), 'payments', ['razorpay_order_id'], unique=False)
    op.create_index(op.f('ix_payments_razorpay_payment_id'), 'payments', ['razorpay_payment_id'], unique=False)
    op.create_index(op.f('ix_payments_studio_id'), 'payments', ['studio_id'], unique=False)

    # Create refunds table
    op.create_table(
        'refunds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('payment_id', sa.Integer(), nullable=False),
        sa.Column('razorpay_refund_id', sa.String(length=100), nullable=True),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSED', 'FAILED', name='refundstatus'), server_default='PENDING', nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create class_packs table
    op.create_table(
        'class_packs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('studio_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('class_count', sa.Integer(), nullable=False),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('validity_days', sa.Integer(), server_default='90', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['studio_id'], ['studios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_class_packs_studio_id'), 'class_packs', ['studio_id'], unique=False)

    # Create class_pack_purchases table
    op.create_table(
        'class_pack_purchases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('class_pack_id', sa.Integer(), nullable=False),
        sa.Column('contact_id', sa.Integer(), nullable=False),
        sa.Column('payment_id', sa.Integer(), nullable=True),
        sa.Column('classes_remaining', sa.Integer(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('purchased_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['class_pack_id'], ['class_packs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_class_pack_purchases_contact_id'), 'class_pack_purchases', ['contact_id'], unique=False)

    # Create subscription_plans table
    op.create_table(
        'subscription_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('studio_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('billing_period', sa.String(length=50), server_default='monthly', nullable=True),
        sa.Column('classes_per_period', sa.Integer(), nullable=True),
        sa.Column('unlimited', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('features', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['studio_id'], ['studios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscription_plans_studio_id'), 'subscription_plans', ['studio_id'], unique=False)

    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('studio_id', sa.Integer(), nullable=False),
        sa.Column('contact_id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'PAUSED', 'CANCELLED', 'EXPIRED', name='subscriptionstatus'), server_default='ACTIVE', nullable=True),
        sa.Column('razorpay_subscription_id', sa.String(length=100), nullable=True),
        sa.Column('current_period_start', sa.DateTime(), nullable=True),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('classes_used_this_period', sa.Integer(), server_default='0', nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['plan_id'], ['subscription_plans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['studio_id'], ['studios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscriptions_contact_id'), 'subscriptions', ['contact_id'], unique=False)
    op.create_index(op.f('ix_subscriptions_studio_id'), 'subscriptions', ['studio_id'], unique=False)

    # Create wallets table
    op.create_table(
        'wallets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('studio_id', sa.Integer(), nullable=False),
        sa.Column('contact_id', sa.Integer(), nullable=False),
        sa.Column('balance', sa.Numeric(10, 2), server_default='0', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['studio_id'], ['studios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('studio_id', 'contact_id', name='unique_wallet')
    )

    # Create wallet_transactions table
    op.create_table(
        'wallet_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('wallet_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('transaction_type', sa.Enum('CREDIT', 'DEBIT', 'REFUND', name='transactiontype'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('reference_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['wallet_id'], ['wallets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_wallet_transactions_wallet_id'), 'wallet_transactions', ['wallet_id'], unique=False)

    # Create discount_codes table
    op.create_table(
        'discount_codes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('studio_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('discount_type', sa.String(length=20), server_default='percentage', nullable=True),
        sa.Column('discount_value', sa.Numeric(10, 2), nullable=False),
        sa.Column('min_purchase', sa.Numeric(10, 2), server_default='0', nullable=True),
        sa.Column('max_discount', sa.Numeric(10, 2), nullable=True),
        sa.Column('usage_limit', sa.Integer(), nullable=True),
        sa.Column('usage_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('valid_from', sa.DateTime(), nullable=True),
        sa.Column('valid_until', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['studio_id'], ['studios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('studio_id', 'code', name='unique_discount_code')
    )
    op.create_index(op.f('ix_discount_codes_code'), 'discount_codes', ['code'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_discount_codes_code'), table_name='discount_codes')
    op.drop_table('discount_codes')
    
    op.drop_index(op.f('ix_wallet_transactions_wallet_id'), table_name='wallet_transactions')
    op.drop_table('wallet_transactions')
    
    op.drop_table('wallets')
    
    op.drop_index(op.f('ix_subscriptions_studio_id'), table_name='subscriptions')
    op.drop_index(op.f('ix_subscriptions_contact_id'), table_name='subscriptions')
    op.drop_table('subscriptions')
    
    op.drop_index(op.f('ix_subscription_plans_studio_id'), table_name='subscription_plans')
    op.drop_table('subscription_plans')
    
    op.drop_index(op.f('ix_class_pack_purchases_contact_id'), table_name='class_pack_purchases')
    op.drop_table('class_pack_purchases')
    
    op.drop_index(op.f('ix_class_packs_studio_id'), table_name='class_packs')
    op.drop_table('class_packs')
    
    op.drop_table('refunds')
    
    op.drop_index(op.f('ix_payments_studio_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_razorpay_payment_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_razorpay_order_id'), table_name='payments')
    op.drop_table('payments')
    
    op.drop_index(op.f('ix_waitlists_session_id'), table_name='waitlists')
    op.drop_table('waitlists')
    
    op.drop_index(op.f('ix_bookings_studio_id'), table_name='bookings')
    op.drop_index(op.f('ix_bookings_contact_id'), table_name='bookings')
    op.drop_index(op.f('ix_bookings_session_id'), table_name='bookings')
    op.drop_table('bookings')
    
    op.drop_index(op.f('ix_class_sessions_studio_id'), table_name='class_sessions')
    op.drop_index(op.f('ix_class_sessions_start_time'), table_name='class_sessions')
    op.drop_table('class_sessions')
    
    op.drop_index(op.f('ix_class_types_studio_id'), table_name='class_types')
    op.drop_table('class_types')
    
    # Drop enums
    op.execute('DROP TYPE transactiontype')
    op.execute('DROP TYPE subscriptionstatus')
    op.execute('DROP TYPE refundstatus')
    op.execute('DROP TYPE paymentmethod')
    op.execute('DROP TYPE paymentstatus')
    op.execute('DROP TYPE bookingstatus')

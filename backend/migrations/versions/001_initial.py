"""Initial migration - create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    channel_enum = postgresql.ENUM('EMAIL', 'WHATSAPP', 'INSTAGRAM', 'MANUAL', name='channel')
    channel_enum.create(op.get_bind())
    
    lead_status_enum = postgresql.ENUM('NEW', 'CONTACTED', 'ENGAGED', 'QUALIFIED', 'CONVERTED', 'LOST', name='leadstatus')
    lead_status_enum.create(op.get_bind())
    
    message_direction_enum = postgresql.ENUM('INBOUND', 'OUTBOUND', name='messagedirection')
    message_direction_enum.create(op.get_bind())

    # Create studios table
    op.create_table(
        'studios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('timezone', sa.String(length=50), server_default='UTC', nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_studios_email'), 'studios', ['email'], unique=False)

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('studio_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('role', sa.String(length=50), server_default='staff', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['studio_id'], ['studios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_studio_id'), 'users', ['studio_id'], unique=False)

    # Create contacts table
    op.create_table(
        'contacts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('studio_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('instagram_handle', sa.String(length=100), nullable=True),
        sa.Column('lead_status', sa.Enum('NEW', 'CONTACTED', 'ENGAGED', 'QUALIFIED', 'CONVERTED', 'LOST', name='leadstatus'), server_default='NEW', nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['studio_id'], ['studios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contacts_email'), 'contacts', ['email'], unique=False)
    op.create_index(op.f('ix_contacts_phone'), 'contacts', ['phone'], unique=False)
    op.create_index(op.f('ix_contacts_studio_id'), 'contacts', ['studio_id'], unique=False)

    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('studio_id', sa.Integer(), nullable=False),
        sa.Column('contact_id', sa.Integer(), nullable=False),
        sa.Column('channel', sa.Enum('EMAIL', 'WHATSAPP', 'INSTAGRAM', 'MANUAL', name='channel'), nullable=False),
        sa.Column('channel_identifier', sa.String(length=255), nullable=True),
        sa.Column('subject', sa.String(length=500), nullable=True),
        sa.Column('last_message_at', sa.DateTime(), nullable=True),
        sa.Column('last_message_preview', sa.String(length=255), nullable=True),
        sa.Column('is_unread', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('is_archived', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['studio_id'], ['studios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversations_channel'), 'conversations', ['channel'], unique=False)
    op.create_index(op.f('ix_conversations_contact_id'), 'conversations', ['contact_id'], unique=False)
    op.create_index(op.f('ix_conversations_studio_id'), 'conversations', ['studio_id'], unique=False)

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('direction', sa.Enum('INBOUND', 'OUTBOUND', name='messagedirection'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_html', sa.Text(), nullable=True),
        sa.Column('sent_by', sa.Integer(), nullable=True),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='sent', nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sent_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_conversation_id'), 'messages', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_messages_external_id'), 'messages', ['external_id'], unique=False)

    # Create lead_status_history table
    op.create_table(
        'lead_status_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contact_id', sa.Integer(), nullable=False),
        sa.Column('from_status', sa.Enum('NEW', 'CONTACTED', 'ENGAGED', 'QUALIFIED', 'CONVERTED', 'LOST', name='leadstatus'), nullable=True),
        sa.Column('to_status', sa.Enum('NEW', 'CONTACTED', 'ENGAGED', 'QUALIFIED', 'CONVERTED', 'LOST', name='leadstatus'), nullable=False),
        sa.Column('changed_by', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lead_status_history_contact_id'), 'lead_status_history', ['contact_id'], unique=False)

    # Create studio_knowledge table
    op.create_table(
        'studio_knowledge',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('studio_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['studio_id'], ['studios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_studio_knowledge_studio_id'), 'studio_knowledge', ['studio_id'], unique=False)

    # Create message_templates table
    op.create_table(
        'message_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('studio_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('subject', sa.String(length=500), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('channels', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['studio_id'], ['studios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_message_templates_studio_id'), 'message_templates', ['studio_id'], unique=False)

    # Create analytics_daily table
    op.create_table(
        'analytics_daily',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('studio_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('messages_received', sa.Integer(), server_default='0', nullable=True),
        sa.Column('messages_sent', sa.Integer(), server_default='0', nullable=True),
        sa.Column('new_leads', sa.Integer(), server_default='0', nullable=True),
        sa.Column('leads_converted', sa.Integer(), server_default='0', nullable=True),
        sa.Column('response_time_avg', sa.Integer(), nullable=True),
        sa.Column('channel_breakdown', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['studio_id'], ['studios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analytics_daily_date'), 'analytics_daily', ['date'], unique=False)
    op.create_index(op.f('ix_analytics_daily_studio_id'), 'analytics_daily', ['studio_id'], unique=False)
    op.create_unique_constraint('uq_analytics_daily_studio_date', 'analytics_daily', ['studio_id', 'date'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('analytics_daily')
    op.drop_table('message_templates')
    op.drop_table('studio_knowledge')
    op.drop_table('lead_status_history')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('contacts')
    op.drop_table('users')
    op.drop_table('studios')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS messagedirection')
    op.execute('DROP TYPE IF EXISTS leadstatus')
    op.execute('DROP TYPE IF EXISTS channel')

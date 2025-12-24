from datetime import datetime
from enum import Enum
from app import db
from werkzeug.security import generate_password_hash, check_password_hash


class Channel(str, Enum):
    """Communication channel types."""
    EMAIL = 'EMAIL'
    WHATSAPP = 'WHATSAPP'
    INSTAGRAM = 'INSTAGRAM'


class LeadStatus(str, Enum):
    """Lead status types."""
    NEW = 'NEW'
    CONTACTED = 'CONTACTED'
    QUALIFIED = 'QUALIFIED'
    TRIAL_SCHEDULED = 'TRIAL_SCHEDULED'
    CONVERTED = 'CONVERTED'
    LOST = 'LOST'


class MessageDirection(str, Enum):
    """Message direction."""
    INBOUND = 'INBOUND'
    OUTBOUND = 'OUTBOUND'


class Studio(db.Model):
    """Studio model - represents a dance studio."""
    __tablename__ = 'studios'
    
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone = db.Column(db.String(50))
    address = db.Column(db.Text)
    timezone = db.Column(db.String(50), default='America/New_York')
    
    # Integration settings (JSON fields)
    email_settings = db.Column(db.JSON, default=dict)
    whatsapp_settings = db.Column(db.JSON, default=dict)
    instagram_settings = db.Column(db.JSON, default=dict)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='studio', lazy='dynamic')
    contacts = db.relationship('Contact', backref='studio', lazy='dynamic')
    conversations = db.relationship('Conversation', backref='studio', lazy='dynamic')
    knowledge = db.relationship('StudioKnowledge', backref='studio', lazy='dynamic')
    templates = db.relationship('MessageTemplate', backref='studio', lazy='dynamic')
    analytics = db.relationship('AnalyticsDaily', backref='studio', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'timezone': self.timezone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class User(db.Model):
    """User model - studio staff members."""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True)
    studio_id = db.Column(db.String(36), db.ForeignKey('studios.id'), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='staff')  # owner, admin, staff
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    messages = db.relationship('Message', backref='sender', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_studio=False):
        data = {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }
        if include_studio and self.studio:
            data['studio'] = self.studio.to_dict()
        return data


class Contact(db.Model):
    """Contact model - leads and customers."""
    __tablename__ = 'contacts'
    
    id = db.Column(db.String(36), primary_key=True)
    studio_id = db.Column(db.String(36), db.ForeignKey('studios.id'), nullable=False)
    
    # Contact info
    name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    instagram_handle = db.Column(db.String(100))
    
    # Lead tracking
    lead_status = db.Column(db.String(50), default=LeadStatus.NEW.value)
    lead_source = db.Column(db.String(100))  # website, referral, walk-in, social
    
    # Additional info
    notes = db.Column(db.Text)
    tags = db.Column(db.JSON, default=list)  # List of tags
    extra_data = db.Column(db.JSON, default=dict)  # Extra contact data
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    conversations = db.relationship('Conversation', backref='contact', lazy='dynamic')
    status_history = db.relationship('LeadStatusHistory', backref='contact', lazy='dynamic')
    
    def to_dict(self, include_conversations=False):
        data = {
            'id': self.id,
            'studio_id': self.studio_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'instagram_handle': self.instagram_handle,
            'lead_status': self.lead_status,
            'lead_source': self.lead_source,
            'notes': self.notes,
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_conversations:
            data['conversations'] = [c.to_dict() for c in self.conversations]
        return data


class Conversation(db.Model):
    """Conversation model - thread of messages with a contact."""
    __tablename__ = 'conversations'
    
    id = db.Column(db.String(36), primary_key=True)
    studio_id = db.Column(db.String(36), db.ForeignKey('studios.id'), nullable=False)
    contact_id = db.Column(db.String(36), db.ForeignKey('contacts.id'), nullable=False)
    
    channel = db.Column(db.String(20), nullable=False)  # EMAIL, WHATSAPP, INSTAGRAM
    subject = db.Column(db.String(500))  # For email threads
    
    # Status
    is_unread = db.Column(db.Boolean, default=True)
    is_archived = db.Column(db.Boolean, default=False)
    is_starred = db.Column(db.Boolean, default=False)
    
    # External IDs for channel-specific tracking
    external_id = db.Column(db.String(255))  # Thread ID, conversation ID, etc.
    
    last_message_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = db.relationship('Message', backref='conversation', lazy='dynamic', 
                               order_by='Message.created_at')
    
    def to_dict(self, include_messages=False, include_contact=False):
        data = {
            'id': self.id,
            'studio_id': self.studio_id,
            'contact_id': self.contact_id,
            'channel': self.channel,
            'subject': self.subject,
            'is_unread': self.is_unread,
            'is_archived': self.is_archived,
            'is_starred': self.is_starred,
            'last_message_at': self.last_message_at.isoformat() if self.last_message_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_messages:
            data['messages'] = [m.to_dict() for m in self.messages]
        if include_contact and self.contact:
            data['contact'] = self.contact.to_dict()
        return data


class Message(db.Model):
    """Message model - individual messages in a conversation."""
    __tablename__ = 'messages'
    
    id = db.Column(db.String(36), primary_key=True)
    conversation_id = db.Column(db.String(36), db.ForeignKey('conversations.id'), nullable=False)
    sender_id = db.Column(db.String(36), db.ForeignKey('users.id'))  # Null for inbound
    
    direction = db.Column(db.String(20), nullable=False)  # INBOUND, OUTBOUND
    content = db.Column(db.Text, nullable=False)
    content_html = db.Column(db.Text)  # For rich email content
    
    # Status
    is_read = db.Column(db.Boolean, default=False)
    is_ai_generated = db.Column(db.Boolean, default=False)
    
    # Attachments
    attachments = db.Column(db.JSON, default=list)  # List of attachment objects
    
    # External IDs
    external_id = db.Column(db.String(255))  # Message ID from channel
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'sender_id': self.sender_id,
            'direction': self.direction,
            'content': self.content,
            'content_html': self.content_html,
            'is_read': self.is_read,
            'is_ai_generated': self.is_ai_generated,
            'attachments': self.attachments,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
        }


class LeadStatusHistory(db.Model):
    """Track lead status changes over time."""
    __tablename__ = 'lead_status_history'
    
    id = db.Column(db.String(36), primary_key=True)
    contact_id = db.Column(db.String(36), db.ForeignKey('contacts.id'), nullable=False)
    
    from_status = db.Column(db.String(50))
    to_status = db.Column(db.String(50), nullable=False)
    changed_by_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    changed_by = db.relationship('User', backref='status_changes')
    
    def to_dict(self):
        return {
            'id': self.id,
            'contact_id': self.contact_id,
            'from_status': self.from_status,
            'to_status': self.to_status,
            'changed_by_id': self.changed_by_id,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class StudioKnowledge(db.Model):
    """Studio knowledge base for AI context."""
    __tablename__ = 'studio_knowledge'
    
    id = db.Column(db.String(36), primary_key=True)
    studio_id = db.Column(db.String(36), db.ForeignKey('studios.id'), nullable=False)
    
    category = db.Column(db.String(100), nullable=False)  # pricing, schedule, policies, faq
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    
    # For semantic search
    embedding = db.Column(db.JSON)  # Store embedding vector
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'studio_id': self.studio_id,
            'category': self.category,
            'title': self.title,
            'content': self.content,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class MessageTemplate(db.Model):
    """Reusable message templates."""
    __tablename__ = 'message_templates'
    
    id = db.Column(db.String(36), primary_key=True)
    studio_id = db.Column(db.String(36), db.ForeignKey('studios.id'), nullable=False)
    
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100))  # welcome, follow-up, scheduling, etc.
    subject = db.Column(db.String(500))  # For email templates
    content = db.Column(db.Text, nullable=False)
    
    # Variables like {{name}}, {{studio_name}}
    variables = db.Column(db.JSON, default=list)
    
    # Applicable channels
    channels = db.Column(db.JSON, default=list)  # ['EMAIL', 'WHATSAPP']
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'studio_id': self.studio_id,
            'name': self.name,
            'category': self.category,
            'subject': self.subject,
            'content': self.content,
            'variables': self.variables,
            'channels': self.channels,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class AnalyticsDaily(db.Model):
    """Daily analytics aggregation."""
    __tablename__ = 'analytics_daily'
    
    id = db.Column(db.String(36), primary_key=True)
    studio_id = db.Column(db.String(36), db.ForeignKey('studios.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    
    # Message metrics
    messages_received = db.Column(db.Integer, default=0)
    messages_sent = db.Column(db.Integer, default=0)
    
    # Lead metrics
    new_leads = db.Column(db.Integer, default=0)
    leads_converted = db.Column(db.Integer, default=0)
    
    # Channel breakdown (JSON)
    channel_breakdown = db.Column(db.JSON, default=dict)
    
    # Response metrics
    avg_response_time_minutes = db.Column(db.Float)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('studio_id', 'date', name='unique_studio_date'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'studio_id': self.studio_id,
            'date': self.date.isoformat() if self.date else None,
            'messages_received': self.messages_received,
            'messages_sent': self.messages_sent,
            'new_leads': self.new_leads,
            'leads_converted': self.leads_converted,
            'channel_breakdown': self.channel_breakdown,
            'avg_response_time_minutes': self.avg_response_time_minutes,
        }


class ChannelIntegration(db.Model):
    """Channel integration credentials and status."""
    __tablename__ = 'channel_integrations'
    
    id = db.Column(db.String(36), primary_key=True)
    studio_id = db.Column(db.String(36), db.ForeignKey('studios.id'), nullable=False)
    channel = db.Column(db.String(20), nullable=False)  # WHATSAPP, INSTAGRAM, EMAIL
    status = db.Column(db.String(20), default='not_connected')
    credentials = db.Column(db.JSON, default=dict)  # Encrypted in production
    
    # Integration-specific identifiers
    external_account_id = db.Column(db.String(255))  # Phone ID, Page ID, etc.
    external_account_name = db.Column(db.String(255))  # Display name
    
    # Webhook configuration
    webhook_url = db.Column(db.String(500))
    webhook_secret = db.Column(db.String(255))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_sync_at = db.Column(db.DateTime)
    
    __table_args__ = (
        db.UniqueConstraint('studio_id', 'channel', name='unique_studio_channel'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'studio_id': self.studio_id,
            'channel': self.channel,
            'status': self.status,
            'external_account_id': self.external_account_id,
            'external_account_name': self.external_account_name,
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class DanceClass(db.Model):
    """Dance class definition for scheduling."""
    __tablename__ = 'dance_classes'
    
    id = db.Column(db.String(36), primary_key=True)
    studio_id = db.Column(db.String(36), db.ForeignKey('studios.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    dance_style = db.Column(db.String(100))  # Salsa, Hip-Hop, Ballet, etc.
    level = db.Column(db.String(50))  # Beginner, Intermediate, Advanced
    duration_minutes = db.Column(db.Integer, default=60)
    max_capacity = db.Column(db.Integer, default=20)
    min_capacity = db.Column(db.Integer, default=3)
    price = db.Column(db.Float)
    
    # Instructor info
    instructor_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    
    # Active status
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    schedules = db.relationship('ClassSchedule', backref='dance_class', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'studio_id': self.studio_id,
            'name': self.name,
            'description': self.description,
            'dance_style': self.dance_style,
            'level': self.level,
            'duration_minutes': self.duration_minutes,
            'max_capacity': self.max_capacity,
            'min_capacity': self.min_capacity,
            'price': self.price,
            'instructor_id': self.instructor_id,
            'is_active': self.is_active,
        }


class ClassSchedule(db.Model):
    """Scheduled class instances."""
    __tablename__ = 'class_schedules'
    
    id = db.Column(db.String(36), primary_key=True)
    studio_id = db.Column(db.String(36), db.ForeignKey('studios.id'), nullable=False)
    class_id = db.Column(db.String(36), db.ForeignKey('dance_classes.id'), nullable=False)
    
    # Schedule details
    day_of_week = db.Column(db.Integer)  # 0=Monday, 6=Sunday (for recurring)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    
    # For specific date scheduling
    specific_date = db.Column(db.Date)
    
    # Room/location
    room = db.Column(db.String(100))
    
    # Override instructor
    instructor_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    
    # Recurring settings
    is_recurring = db.Column(db.Boolean, default=True)
    recurrence_end_date = db.Column(db.Date)
    
    # Status
    is_cancelled = db.Column(db.Boolean, default=False)
    cancellation_reason = db.Column(db.Text)
    
    # Current enrollment
    current_enrollment = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'studio_id': self.studio_id,
            'class_id': self.class_id,
            'day_of_week': self.day_of_week,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'specific_date': self.specific_date.isoformat() if self.specific_date else None,
            'room': self.room,
            'instructor_id': self.instructor_id,
            'is_recurring': self.is_recurring,
            'is_cancelled': self.is_cancelled,
            'current_enrollment': self.current_enrollment,
        }


class InstructorAvailability(db.Model):
    """Instructor availability for scheduling optimization."""
    __tablename__ = 'instructor_availability'
    
    id = db.Column(db.String(36), primary_key=True)
    instructor_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    
    # For specific date overrides (unavailable)
    specific_date = db.Column(db.Date)
    is_available = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'instructor_id': self.instructor_id,
            'day_of_week': self.day_of_week,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'specific_date': self.specific_date.isoformat() if self.specific_date else None,
            'is_available': self.is_available,
        }


class Room(db.Model):
    """Studio rooms for class scheduling."""
    __tablename__ = 'rooms'
    
    id = db.Column(db.String(36), primary_key=True)
    studio_id = db.Column(db.String(36), db.ForeignKey('studios.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer, default=20)
    features = db.Column(db.JSON, default=list)  # ['mirrors', 'sound_system', 'sprung_floor']
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'studio_id': self.studio_id,
            'name': self.name,
            'capacity': self.capacity,
            'features': self.features,
            'is_active': self.is_active,
        }

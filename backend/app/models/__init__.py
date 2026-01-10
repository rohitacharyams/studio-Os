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
    slug = db.Column(db.String(255), unique=True)  # URL-friendly name for public booking page
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone = db.Column(db.String(50))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    website = db.Column(db.String(255))
    logo_url = db.Column(db.String(500))
    timezone = db.Column(db.String(50), default='Asia/Kolkata')
    currency = db.Column(db.String(10), default='INR')
    
    # Business hours
    business_hours_open = db.Column(db.String(10), default='09:00')
    business_hours_close = db.Column(db.String(10), default='21:00')
    
    # Onboarding status
    onboarding_completed = db.Column(db.Boolean, default=False)
    onboarding_step = db.Column(db.Integer, default=0)
    
    # Integration settings (JSON fields)
    email_settings = db.Column(db.JSON, default=dict)
    whatsapp_settings = db.Column(db.JSON, default=dict)
    instagram_settings = db.Column(db.JSON, default=dict)
    payment_settings = db.Column(db.JSON, default=dict)
    
    # Payment settings (legacy)
    razorpay_key_id = db.Column(db.String(255))
    razorpay_key_secret = db.Column(db.String(255))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='studio', lazy='dynamic')
    contacts = db.relationship('Contact', backref='studio', lazy='dynamic')
    conversations = db.relationship('Conversation', backref='studio', lazy='dynamic')
    knowledge = db.relationship('StudioKnowledge', backref='studio', lazy='dynamic')
    templates = db.relationship('MessageTemplate', backref='studio', lazy='dynamic')
    analytics = db.relationship('AnalyticsDaily', backref='studio', lazy='dynamic')

    def generate_slug(self):
        """Generate URL-friendly slug from studio name."""
        import re
        slug = self.name.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug).strip('-')
        return slug

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'website': self.website,
            'logo_url': self.logo_url,
            'timezone': self.timezone,
            'currency': self.currency,
            'business_hours_open': self.business_hours_open,
            'business_hours_close': self.business_hours_close,
            'onboarding_completed': self.onboarding_completed,
            'onboarding_step': self.onboarding_step,
            'whatsapp_connected': bool(self.whatsapp_settings and self.whatsapp_settings.get('connected')),
            'email_connected': bool(self.email_settings and self.email_settings.get('connected')),
            'instagram_connected': bool(self.instagram_settings and self.instagram_settings.get('connected')),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class User(db.Model):
    """User model - studio staff members and customers."""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True)
    studio_id = db.Column(db.String(36), db.ForeignKey('studios.id'), nullable=True)  # Nullable for customers
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50))  # Customer phone for bookings
    role = db.Column(db.String(50), default='staff')  # owner, admin, staff
    user_type = db.Column(db.String(20), default='studio_owner')  # studio_owner, customer
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    messages = db.relationship('Message', backref='sender', lazy='dynamic')
    bookings = db.relationship('Booking', backref='user', lazy='dynamic', foreign_keys='Booking.user_id')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_studio=False):
        data = {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'phone': self.phone,
            'role': self.role,
            'user_type': self.user_type,
            'is_active': self.is_active,
            'studio_id': self.studio_id,
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
    
    # Enhanced media & details (JSON fields)
    images = db.Column(db.JSON, default=list)  # List of image URLs
    videos = db.Column(db.JSON, default=list)  # List of video URLs (YouTube, etc.)
    
    # Artist/Instructor details (beyond the FK)
    artist_details = db.Column(db.JSON, default=dict)  # {bio, specialties, experience, achievements, socials: {instagram, youtube, etc.}}
    
    # Additional class info
    what_to_bring = db.Column(db.Text)  # What students should bring
    prerequisites = db.Column(db.Text)  # Prerequisites for the class
    tags = db.Column(db.JSON, default=list)  # Tags for filtering
    
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
            'images': self.images or [],
            'videos': self.videos or [],
            'artist_details': self.artist_details or {},
            'what_to_bring': self.what_to_bring,
            'prerequisites': self.prerequisites,
            'tags': self.tags or [],
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


# ============================================================
# BOOKING SYSTEM MODELS
# ============================================================

class BookingStatus(str, Enum):
    """Booking status types."""
    PENDING = 'PENDING'
    CONFIRMED = 'CONFIRMED'
    WAITLIST = 'WAITLIST'
    CANCELLED = 'CANCELLED'
    NO_SHOW = 'NO_SHOW'
    ATTENDED = 'ATTENDED'


class ClassSession(db.Model):
    """Individual class session (instance of a scheduled class)."""
    __tablename__ = 'class_sessions'
    
    id = db.Column(db.String(36), primary_key=True)
    studio_id = db.Column(db.String(36), db.ForeignKey('studios.id'), nullable=False)
    schedule_id = db.Column(db.String(36), db.ForeignKey('class_schedules.id'))
    class_id = db.Column(db.String(36), db.ForeignKey('dance_classes.id'))
    
    # Session timing
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    
    # Capacity
    max_capacity = db.Column(db.Integer, default=15)
    booked_count = db.Column(db.Integer, default=0)
    waitlist_count = db.Column(db.Integer, default=0)
    
    # Instructor (references users table - instructors are users with instructor role)
    instructor_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    substitute_instructor_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    
    # Room
    room_id = db.Column(db.String(36), db.ForeignKey('rooms.id'))
    
    # Status
    status = db.Column(db.String(20), default='SCHEDULED')  # SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED
    cancellation_reason = db.Column(db.String(255))
    
    # Notes
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='session', lazy='dynamic')
    waitlist = db.relationship('Waitlist', backref='session', lazy='dynamic')
    
    @property
    def available_spots(self):
        return max(0, self.max_capacity - self.booked_count)
    
    @property
    def is_full(self):
        return self.booked_count >= self.max_capacity
    
    def to_dict(self, include_bookings=False):
        data = {
            'id': self.id,
            'studio_id': self.studio_id,
            'schedule_id': self.schedule_id,
            'class_id': self.class_id,
            'date': self.date.isoformat() if self.date else None,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'max_capacity': self.max_capacity,
            'booked_count': self.booked_count,
            'waitlist_count': self.waitlist_count,
            'available_spots': self.available_spots,
            'is_full': self.is_full,
            'instructor_id': self.instructor_id,
            'room_id': self.room_id,
            'status': self.status,
        }
        if include_bookings:
            data['bookings'] = [b.to_dict() for b in self.bookings.all()]
        return data


class Booking(db.Model):
    """Class booking by a contact/student or registered user."""
    __tablename__ = 'bookings'
    
    id = db.Column(db.String(36), primary_key=True)
    booking_number = db.Column(db.String(20), unique=True, nullable=False)  # BK-2025-0001
    
    studio_id = db.Column(db.String(36), db.ForeignKey('studios.id'), nullable=False)
    contact_id = db.Column(db.String(36), db.ForeignKey('contacts.id'), nullable=True)  # For guest bookings
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)  # For logged-in users
    session_id = db.Column(db.String(36), db.ForeignKey('class_sessions.id'), nullable=False)
    
    # Status
    status = db.Column(db.String(20), default='PENDING')  # PENDING, CONFIRMED, WAITLIST, CANCELLED, NO_SHOW, ATTENDED
    waitlist_position = db.Column(db.Integer, nullable=True)
    
    # Payment
    payment_id = db.Column(db.String(36), db.ForeignKey('payments.id'))
    payment_method = db.Column(db.String(20))  # drop_in, class_pack, subscription, wallet
    class_pack_purchase_id = db.Column(db.String(36), db.ForeignKey('class_pack_purchases.id'))
    
    # Timestamps
    booked_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    checked_in_at = db.Column(db.DateTime)
    
    # Cancellation
    cancellation_reason = db.Column(db.String(255))
    refund_amount = db.Column(db.Numeric(10, 2), default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self, include_session=False, include_contact=False):
        data = {
            'id': self.id,
            'booking_number': self.booking_number,
            'studio_id': self.studio_id,
            'contact_id': self.contact_id,
            'session_id': self.session_id,
            'status': self.status,
            'waitlist_position': self.waitlist_position,
            'payment_method': self.payment_method,
            'booked_at': self.booked_at.isoformat() if self.booked_at else None,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'checked_in_at': self.checked_in_at.isoformat() if self.checked_in_at else None,
        }
        if include_session and self.session:
            data['session'] = self.session.to_dict()
        return data


class Waitlist(db.Model):
    """Waitlist for full class sessions."""
    __tablename__ = 'waitlists'
    
    id = db.Column(db.String(36), primary_key=True)
    studio_id = db.Column(db.String(36), db.ForeignKey('studios.id'), nullable=False)
    session_id = db.Column(db.String(36), db.ForeignKey('class_sessions.id'), nullable=False)
    contact_id = db.Column(db.String(36), db.ForeignKey('contacts.id'), nullable=False)
    
    position = db.Column(db.Integer, nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    notified_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)  # Time limit to respond
    
    # Status
    status = db.Column(db.String(20), default='WAITING')  # WAITING, NOTIFIED, CONVERTED, EXPIRED, CANCELLED
    auto_book = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'contact_id': self.contact_id,
            'position': self.position,
            'status': self.status,
            'auto_book': self.auto_book,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
        }


# ============================================================
# PAYMENT SYSTEM MODELS
# ============================================================

class PaymentStatus(str, Enum):
    """Payment status types."""
    PENDING = 'PENDING'
    PROCESSING = 'PROCESSING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    REFUNDED = 'REFUNDED'
    PARTIALLY_REFUNDED = 'PARTIALLY_REFUNDED'


class PaymentProvider(str, Enum):
    """Payment provider types."""
    RAZORPAY = 'RAZORPAY'
    STRIPE = 'STRIPE'
    WALLET = 'WALLET'
    CASH = 'CASH'
    BANK_TRANSFER = 'BANK_TRANSFER'


class Payment(db.Model):
    """Payment transaction record."""
    __tablename__ = 'payments'
    
    id = db.Column(db.String(36), primary_key=True)
    payment_number = db.Column(db.String(20), unique=True, nullable=False)  # PAY-2025-0001
    
    studio_id = db.Column(db.String(36), db.ForeignKey('studios.id'), nullable=False)
    contact_id = db.Column(db.String(36), db.ForeignKey('contacts.id'), nullable=False)
    
    # Amount
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='INR')
    
    # Tax
    tax_amount = db.Column(db.Numeric(10, 2), default=0)
    tax_rate = db.Column(db.Numeric(5, 2), default=18)  # GST 18%
    
    # Discount
    discount_code = db.Column(db.String(20))
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    
    # Total
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Provider
    provider = db.Column(db.String(20), default='RAZORPAY')
    provider_order_id = db.Column(db.String(100))  # razorpay_order_id
    provider_payment_id = db.Column(db.String(100))  # razorpay_payment_id
    provider_signature = db.Column(db.String(255))
    
    # Payment method
    payment_method = db.Column(db.String(20))  # upi, card, netbanking, wallet
    payment_method_details = db.Column(db.JSON)  # {"bank": "HDFC", "last4": "1234"}
    
    # Status
    status = db.Column(db.String(20), default='PENDING')
    failure_reason = db.Column(db.String(255))
    
    # Purchase reference
    purchase_type = db.Column(db.String(20))  # DROP_IN, CLASS_PACK, SUBSCRIPTION, PRIVATE_SESSION
    purchase_description = db.Column(db.String(255))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Invoice
    invoice_number = db.Column(db.String(20))
    invoice_url = db.Column(db.String(255))
    
    # Relationships
    bookings = db.relationship('Booking', backref='payment', lazy='dynamic')
    refunds = db.relationship('Refund', backref='payment', lazy='dynamic')
    
    def to_dict(self, include_bookings=False):
        data = {
            'id': self.id,
            'payment_number': self.payment_number,
            'studio_id': self.studio_id,
            'contact_id': self.contact_id,
            'amount': float(self.amount) if self.amount else 0,
            'currency': self.currency,
            'tax_amount': float(self.tax_amount) if self.tax_amount else 0,
            'discount_amount': float(self.discount_amount) if self.discount_amount else 0,
            'total_amount': float(self.total_amount) if self.total_amount else 0,
            'provider': self.provider,
            'payment_method': self.payment_method,
            'status': self.status,
            'purchase_type': self.purchase_type,
            'purchase_description': self.purchase_description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'invoice_number': self.invoice_number,
        }
        return data


class Refund(db.Model):
    """Refund record."""
    __tablename__ = 'refunds'
    
    id = db.Column(db.String(36), primary_key=True)
    payment_id = db.Column(db.String(36), db.ForeignKey('payments.id'), nullable=False)
    
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    reason = db.Column(db.String(255))
    
    # Provider refund ID
    provider_refund_id = db.Column(db.String(100))
    
    # Status
    status = db.Column(db.String(20), default='PENDING')  # PENDING, PROCESSED, FAILED
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'payment_id': self.payment_id,
            'amount': float(self.amount) if self.amount else 0,
            'reason': self.reason,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ClassPack(db.Model):
    """Class pack product definition."""
    __tablename__ = 'class_packs'
    
    id = db.Column(db.String(36), primary_key=True)
    studio_id = db.Column(db.String(36), db.ForeignKey('studios.id'), nullable=False)
    
    name = db.Column(db.String(100), nullable=False)  # "10 Class Pack"
    description = db.Column(db.Text)
    
    # Pack details
    class_count = db.Column(db.Integer, nullable=False)  # Number of classes
    price = db.Column(db.Numeric(10, 2), nullable=False)
    validity_days = db.Column(db.Integer, default=60)  # Valid for X days
    
    # Restrictions
    class_types = db.Column(db.JSON)  # ["salsa", "hip-hop"] or null for all
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    purchases = db.relationship('ClassPackPurchase', backref='class_pack', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'studio_id': self.studio_id,
            'name': self.name,
            'description': self.description,
            'class_count': self.class_count,
            'price': float(self.price) if self.price else 0,
            'validity_days': self.validity_days,
            'class_types': self.class_types,
            'is_active': self.is_active,
        }


class ClassPackPurchase(db.Model):
    """Purchased class pack instance."""
    __tablename__ = 'class_pack_purchases'
    
    id = db.Column(db.String(36), primary_key=True)
    
    studio_id = db.Column(db.String(36), db.ForeignKey('studios.id'), nullable=False)
    contact_id = db.Column(db.String(36), db.ForeignKey('contacts.id'), nullable=False)
    class_pack_id = db.Column(db.String(36), db.ForeignKey('class_packs.id'), nullable=False)
    payment_id = db.Column(db.String(36), db.ForeignKey('payments.id'))
    
    # Usage tracking
    classes_total = db.Column(db.Integer, nullable=False)
    classes_used = db.Column(db.Integer, default=0)
    
    # Validity
    purchased_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    # Status
    status = db.Column(db.String(20), default='ACTIVE')  # ACTIVE, EXHAUSTED, EXPIRED, REFUNDED
    
    @property
    def classes_remaining(self):
        return max(0, self.classes_total - self.classes_used)
    
    def to_dict(self):
        return {
            'id': self.id,
            'contact_id': self.contact_id,
            'class_pack_id': self.class_pack_id,
            'classes_total': self.classes_total,
            'classes_used': self.classes_used,
            'classes_remaining': self.classes_remaining,
            'purchased_at': self.purchased_at.isoformat() if self.purchased_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'status': self.status,
        }


class SubscriptionPlan(db.Model):
    """Subscription plan definition."""
    __tablename__ = 'subscription_plans'
    
    id = db.Column(db.String(36), primary_key=True)
    studio_id = db.Column(db.String(36), db.ForeignKey('studios.id'), nullable=False)
    
    name = db.Column(db.String(100), nullable=False)  # "Monthly Unlimited"
    description = db.Column(db.Text)
    
    # Pricing
    price = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='INR')
    billing_cycle = db.Column(db.String(20), default='MONTHLY')  # MONTHLY, QUARTERLY, YEARLY
    
    # Benefits
    classes_per_month = db.Column(db.Integer)  # null = unlimited
    includes_private = db.Column(db.Integer, default=0)  # Private sessions included
    
    # Razorpay Plan ID (for recurring billing)
    provider_plan_id = db.Column(db.String(100))
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'studio_id': self.studio_id,
            'name': self.name,
            'description': self.description,
            'price': float(self.price) if self.price else 0,
            'currency': self.currency,
            'billing_cycle': self.billing_cycle,
            'classes_per_month': self.classes_per_month,
            'includes_private': self.includes_private,
            'is_active': self.is_active,
        }


class Subscription(db.Model):
    """Customer subscription instance."""
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.String(36), primary_key=True)
    
    studio_id = db.Column(db.String(36), db.ForeignKey('studios.id'), nullable=False)
    contact_id = db.Column(db.String(36), db.ForeignKey('contacts.id'), nullable=False)
    plan_id = db.Column(db.String(36), db.ForeignKey('subscription_plans.id'), nullable=False)
    
    # Provider subscription
    provider = db.Column(db.String(20), default='RAZORPAY')
    provider_subscription_id = db.Column(db.String(100))
    provider_customer_id = db.Column(db.String(100))
    
    # Billing dates
    started_at = db.Column(db.DateTime, nullable=False)
    current_period_start = db.Column(db.DateTime)
    current_period_end = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    
    # Usage this period
    classes_used_this_period = db.Column(db.Integer, default=0)
    
    # Status
    status = db.Column(db.String(20), default='ACTIVE')  # ACTIVE, PAUSED, CANCELLED, PAST_DUE, EXPIRED
    auto_renew = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    plan = db.relationship('SubscriptionPlan', backref='subscriptions')
    
    def to_dict(self, include_plan=False):
        data = {
            'id': self.id,
            'contact_id': self.contact_id,
            'plan_id': self.plan_id,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'current_period_start': self.current_period_start.isoformat() if self.current_period_start else None,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
            'classes_used_this_period': self.classes_used_this_period,
            'auto_renew': self.auto_renew,
        }
        if include_plan and self.plan:
            data['plan'] = self.plan.to_dict()
        return data


class Wallet(db.Model):
    """Customer wallet for credits/refunds."""
    __tablename__ = 'wallets'
    
    id = db.Column(db.String(36), primary_key=True)
    
    studio_id = db.Column(db.String(36), db.ForeignKey('studios.id'), nullable=False)
    contact_id = db.Column(db.String(36), db.ForeignKey('contacts.id'), nullable=False, unique=True)
    
    balance = db.Column(db.Numeric(10, 2), default=0)
    currency = db.Column(db.String(3), default='INR')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('WalletTransaction', backref='wallet', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'contact_id': self.contact_id,
            'balance': float(self.balance) if self.balance else 0,
            'currency': self.currency,
        }


class WalletTransaction(db.Model):
    """Wallet credit/debit history."""
    __tablename__ = 'wallet_transactions'
    
    id = db.Column(db.String(36), primary_key=True)
    wallet_id = db.Column(db.String(36), db.ForeignKey('wallets.id'), nullable=False)
    
    type = db.Column(db.String(10), nullable=False)  # CREDIT, DEBIT
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    balance_after = db.Column(db.Numeric(10, 2), nullable=False)
    
    description = db.Column(db.String(255))
    reference_type = db.Column(db.String(50))  # booking, payment, refund, manual
    reference_id = db.Column(db.String(36))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'wallet_id': self.wallet_id,
            'type': self.type,
            'amount': float(self.amount) if self.amount else 0,
            'balance_after': float(self.balance_after) if self.balance_after else 0,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class DiscountCode(db.Model):
    """Discount/promo codes."""
    __tablename__ = 'discount_codes'
    
    id = db.Column(db.String(36), primary_key=True)
    studio_id = db.Column(db.String(36), db.ForeignKey('studios.id'), nullable=False)
    
    code = db.Column(db.String(20), nullable=False, unique=True)  # NEW2025
    description = db.Column(db.String(255))
    
    # Discount type
    discount_type = db.Column(db.String(20), default='PERCENTAGE')  # PERCENTAGE, FIXED
    discount_value = db.Column(db.Numeric(10, 2), nullable=False)  # 10 for 10% or ₹10
    
    # Limits
    max_uses = db.Column(db.Integer)  # null = unlimited
    uses_count = db.Column(db.Integer, default=0)
    max_uses_per_user = db.Column(db.Integer, default=1)
    
    # Minimum purchase
    minimum_amount = db.Column(db.Numeric(10, 2), default=0)
    
    # Validity
    valid_from = db.Column(db.DateTime)
    valid_until = db.Column(db.DateTime)
    
    # Restrictions
    applicable_to = db.Column(db.JSON)  # ["CLASS_PACK", "SUBSCRIPTION"] or null for all
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'description': self.description,
            'discount_type': self.discount_type,
            'discount_value': float(self.discount_value) if self.discount_value else 0,
            'max_uses': self.max_uses,
            'uses_count': self.uses_count,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'is_active': self.is_active,
        }


class NotificationType(str, Enum):
    """Notification types."""
    BOOKING = 'BOOKING'
    PAYMENT = 'PAYMENT'
    CANCELLATION = 'CANCELLATION'
    REMINDER = 'REMINDER'
    SYSTEM = 'SYSTEM'


class Notification(db.Model):
    """Notification model - stores notifications for studio owners."""
    __tablename__ = 'notifications'
    
    id = db.Column(db.String(36), primary_key=True)
    studio_id = db.Column(db.String(36), db.ForeignKey('studios.id'), nullable=False)
    
    type = db.Column(db.String(20), default='SYSTEM')  # BOOKING, PAYMENT, CANCELLATION, REMINDER, SYSTEM
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text)
    
    # Reference to related entity (optional)
    reference_type = db.Column(db.String(50))  # 'booking', 'contact', 'payment'
    reference_id = db.Column(db.String(36))
    
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    
    # Relationships
    studio = db.relationship('Studio', backref=db.backref('notifications', lazy='dynamic'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'studio_id': self.studio_id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'reference_type': self.reference_type,
            'reference_id': self.reference_id,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
        }
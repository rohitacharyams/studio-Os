"""
Routes package - exports all API blueprints
"""

from .auth import auth_bp
from .conversations import conversations_bp
from .messages import messages_bp
from .ai import ai_bp
from .analytics import analytics_bp
from .webhooks import webhooks_bp
from .studio import studio_bp
from .templates import templates_bp
from .contacts import contacts_bp
from .location import location_bp

__all__ = [
    'auth_bp',
    'conversations_bp',
    'messages_bp',
    'ai_bp',
    'analytics_bp',
    'webhooks_bp',
    'studio_bp',
    'templates_bp',
    'contacts_bp',
    'location_bp',
]

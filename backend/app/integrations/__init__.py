# Channel Integrations Module
# Supports WhatsApp Business, Instagram, Gmail integrations

from .base import BaseChannelIntegration, IntegrationStatus
from .whatsapp import WhatsAppIntegration
from .instagram import InstagramIntegration
from .gmail import GmailIntegration
from .manager import IntegrationManager

__all__ = [
    'BaseChannelIntegration',
    'IntegrationStatus',
    'WhatsAppIntegration',
    'InstagramIntegration',
    'GmailIntegration',
    'IntegrationManager'
]

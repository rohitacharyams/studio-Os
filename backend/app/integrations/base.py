# Base Channel Integration Interface
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import uuid


class IntegrationStatus(Enum):
    """Status of a channel integration."""
    NOT_CONNECTED = "not_connected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    EXPIRED = "expired"  # Token expired, needs refresh


@dataclass
class IncomingMessage:
    """Standardized incoming message from any channel."""
    id: str
    channel: str  # WHATSAPP, INSTAGRAM, EMAIL
    sender_id: str
    sender_name: Optional[str]
    sender_email: Optional[str]
    sender_phone: Optional[str]
    content: str
    timestamp: datetime
    raw_data: Dict[str, Any]  # Original payload for reference
    attachments: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []


@dataclass
class OutgoingMessage:
    """Standardized outgoing message to any channel."""
    recipient_id: str
    content: str
    channel: str
    attachments: List[Dict[str, Any]] = None
    template_id: Optional[str] = None  # For WhatsApp templates
    
    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []


class BaseChannelIntegration(ABC):
    """
    Abstract base class for all channel integrations.
    Each integration (WhatsApp, Instagram, Gmail) must implement these methods.
    """
    
    def __init__(self, studio_id: str, credentials: Dict[str, Any] = None):
        self.studio_id = studio_id
        self.credentials = credentials or {}
        self.status = IntegrationStatus.NOT_CONNECTED
        self.last_sync: Optional[datetime] = None
        
    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Return the channel name (WHATSAPP, INSTAGRAM, EMAIL)."""
        pass
    
    @property
    @abstractmethod
    def requires_oauth(self) -> bool:
        """Whether this integration requires OAuth flow."""
        pass
    
    @abstractmethod
    def get_oauth_url(self, redirect_uri: str, state: str) -> str:
        """
        Generate OAuth authorization URL for user to connect their account.
        
        Args:
            redirect_uri: Where to redirect after auth
            state: CSRF token/state parameter
            
        Returns:
            Authorization URL string
        """
        pass
    
    @abstractmethod
    async def handle_oauth_callback(self, code: str, state: str) -> Dict[str, Any]:
        """
        Handle OAuth callback and exchange code for tokens.
        
        Args:
            code: Authorization code from OAuth provider
            state: State parameter for verification
            
        Returns:
            Dict with access_token, refresh_token, expires_at, etc.
        """
        pass
    
    @abstractmethod
    async def refresh_token(self) -> bool:
        """
        Refresh the access token if expired.
        
        Returns:
            True if refresh successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def verify_connection(self) -> bool:
        """
        Verify the integration is properly connected and working.
        
        Returns:
            True if connected and functional
        """
        pass
    
    @abstractmethod
    async def fetch_messages(self, since: Optional[datetime] = None) -> List[IncomingMessage]:
        """
        Fetch new messages from the channel.
        
        Args:
            since: Only fetch messages after this timestamp
            
        Returns:
            List of standardized IncomingMessage objects
        """
        pass
    
    @abstractmethod
    async def send_message(self, message: OutgoingMessage) -> Dict[str, Any]:
        """
        Send a message through the channel.
        
        Args:
            message: OutgoingMessage to send
            
        Returns:
            Dict with message_id, status, timestamp
        """
        pass
    
    @abstractmethod
    def parse_webhook(self, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
        """
        Parse incoming webhook payload into standardized message.
        
        Args:
            payload: Raw webhook payload from the service
            
        Returns:
            IncomingMessage or None if not a message event
        """
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get current integration status."""
        return {
            'channel': self.channel_name,
            'status': self.status.value,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'studio_id': self.studio_id
        }
    
    def disconnect(self) -> bool:
        """Disconnect and clear credentials."""
        self.credentials = {}
        self.status = IntegrationStatus.NOT_CONNECTED
        return True

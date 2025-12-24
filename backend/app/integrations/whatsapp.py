# WhatsApp Business API Integration
import os
import hmac
import hashlib
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from urllib.parse import urlencode

from .base import BaseChannelIntegration, IncomingMessage, OutgoingMessage, IntegrationStatus


class WhatsAppIntegration(BaseChannelIntegration):
    """
    WhatsApp Business API Integration using Meta's Cloud API.
    
    Setup Requirements:
    1. Create a Meta Business Account
    2. Create a WhatsApp Business App in Meta Developers
    3. Get Phone Number ID and Business Account ID
    4. Configure webhook URL for incoming messages
    
    Environment Variables:
    - WHATSAPP_APP_ID: Meta App ID
    - WHATSAPP_APP_SECRET: Meta App Secret
    - WHATSAPP_VERIFY_TOKEN: Webhook verification token (you create this)
    """
    
    BASE_URL = "https://graph.facebook.com/v18.0"
    
    def __init__(self, studio_id: str, credentials: Dict[str, Any] = None):
        super().__init__(studio_id, credentials)
        self.app_id = os.getenv('WHATSAPP_APP_ID')
        self.app_secret = os.getenv('WHATSAPP_APP_SECRET')
        self.verify_token = os.getenv('WHATSAPP_VERIFY_TOKEN', 'studio_os_verify')
        
    @property
    def channel_name(self) -> str:
        return "WHATSAPP"
    
    @property
    def requires_oauth(self) -> bool:
        return True
    
    def get_oauth_url(self, redirect_uri: str, state: str) -> str:
        """
        Generate Facebook OAuth URL for WhatsApp Business.
        User needs to grant permissions for WhatsApp Business Management.
        """
        params = {
            'client_id': self.app_id,
            'redirect_uri': redirect_uri,
            'state': state,
            'scope': 'whatsapp_business_management,whatsapp_business_messaging',
            'response_type': 'code'
        }
        return f"https://www.facebook.com/v18.0/dialog/oauth?{urlencode(params)}"
    
    async def handle_oauth_callback(self, code: str, state: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        async with httpx.AsyncClient() as client:
            # Exchange code for token
            token_url = f"{self.BASE_URL}/oauth/access_token"
            params = {
                'client_id': self.app_id,
                'client_secret': self.app_secret,
                'code': code,
                'redirect_uri': self.credentials.get('redirect_uri')
            }
            
            response = await client.get(token_url, params=params)
            if response.status_code != 200:
                raise Exception(f"OAuth failed: {response.text}")
            
            token_data = response.json()
            
            # Get long-lived token
            long_lived_url = f"{self.BASE_URL}/oauth/access_token"
            ll_params = {
                'grant_type': 'fb_exchange_token',
                'client_id': self.app_id,
                'client_secret': self.app_secret,
                'fb_exchange_token': token_data['access_token']
            }
            
            ll_response = await client.get(long_lived_url, params=ll_params)
            if ll_response.status_code == 200:
                token_data = ll_response.json()
            
            # Get WhatsApp Business Account info
            waba_response = await client.get(
                f"{self.BASE_URL}/me/businesses",
                params={'access_token': token_data['access_token']}
            )
            
            self.credentials = {
                'access_token': token_data['access_token'],
                'expires_at': (datetime.utcnow() + timedelta(days=60)).isoformat(),
                'waba_data': waba_response.json() if waba_response.status_code == 200 else {}
            }
            self.status = IntegrationStatus.CONNECTED
            
            return self.credentials
    
    async def refresh_token(self) -> bool:
        """WhatsApp long-lived tokens don't need refresh for 60 days."""
        if not self.credentials.get('access_token'):
            return False
            
        expires_at = datetime.fromisoformat(self.credentials.get('expires_at', '2000-01-01'))
        if datetime.utcnow() > expires_at:
            self.status = IntegrationStatus.EXPIRED
            return False
            
        return True
    
    async def verify_connection(self) -> bool:
        """Verify WhatsApp connection by checking phone number status."""
        if not self.credentials.get('access_token'):
            self.status = IntegrationStatus.NOT_CONNECTED
            return False
            
        phone_id = self.credentials.get('phone_number_id')
        if not phone_id:
            return False
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/{phone_id}",
                params={'access_token': self.credentials['access_token']}
            )
            
            if response.status_code == 200:
                self.status = IntegrationStatus.CONNECTED
                return True
            else:
                self.status = IntegrationStatus.ERROR
                return False
    
    async def fetch_messages(self, since: Optional[datetime] = None) -> List[IncomingMessage]:
        """
        Fetch messages from WhatsApp.
        Note: WhatsApp primarily uses webhooks for real-time messages.
        This method is for initial sync or recovery.
        """
        # WhatsApp Cloud API doesn't have a "fetch all messages" endpoint
        # Messages come via webhooks. This is a placeholder for any
        # conversation history that might be available.
        return []
    
    async def send_message(self, message: OutgoingMessage) -> Dict[str, Any]:
        """Send a WhatsApp message."""
        phone_id = self.credentials.get('phone_number_id')
        access_token = self.credentials.get('access_token')
        
        if not phone_id or not access_token:
            raise Exception("WhatsApp not properly configured")
        
        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}/{phone_id}/messages"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Build message payload
            payload = {
                'messaging_product': 'whatsapp',
                'to': message.recipient_id,
                'type': 'text',
                'text': {'body': message.content}
            }
            
            # Use template if specified (required for initiating conversations)
            if message.template_id:
                payload = {
                    'messaging_product': 'whatsapp',
                    'to': message.recipient_id,
                    'type': 'template',
                    'template': {
                        'name': message.template_id,
                        'language': {'code': 'en'}
                    }
                }
            
            response = await client.post(url, json=payload, headers=headers)
            result = response.json()
            
            if response.status_code in [200, 201]:
                return {
                    'success': True,
                    'message_id': result.get('messages', [{}])[0].get('id'),
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', {}).get('message', 'Unknown error')
                }
    
    def parse_webhook(self, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
        """Parse WhatsApp webhook payload."""
        try:
            entry = payload.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})
            
            # Check if this is a message event
            messages = value.get('messages', [])
            if not messages:
                return None
            
            msg = messages[0]
            contact = value.get('contacts', [{}])[0]
            
            # Handle different message types
            content = ""
            if msg.get('type') == 'text':
                content = msg.get('text', {}).get('body', '')
            elif msg.get('type') == 'image':
                content = "[Image received]"
            elif msg.get('type') == 'document':
                content = "[Document received]"
            elif msg.get('type') == 'audio':
                content = "[Audio message received]"
            
            return IncomingMessage(
                id=msg.get('id'),
                channel='WHATSAPP',
                sender_id=msg.get('from'),
                sender_name=contact.get('profile', {}).get('name'),
                sender_email=None,
                sender_phone=msg.get('from'),
                content=content,
                timestamp=datetime.fromtimestamp(int(msg.get('timestamp', 0))),
                raw_data=payload
            )
            
        except Exception as e:
            print(f"Error parsing WhatsApp webhook: {e}")
            return None
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature from Meta."""
        expected = hmac.new(
            self.app_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature)
    
    def get_webhook_verification_response(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Handle webhook verification request from Meta."""
        if mode == 'subscribe' and token == self.verify_token:
            return challenge
        return None

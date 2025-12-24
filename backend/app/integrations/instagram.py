# Instagram Graph API Integration
import os
import hmac
import hashlib
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from urllib.parse import urlencode

from .base import BaseChannelIntegration, IncomingMessage, OutgoingMessage, IntegrationStatus


class InstagramIntegration(BaseChannelIntegration):
    """
    Instagram Messaging API Integration using Meta's Graph API.
    
    Setup Requirements:
    1. Create a Meta Business Account
    2. Connect Instagram Professional Account to Facebook Page
    3. Create an App in Meta Developers with Instagram permissions
    4. Configure webhook for messaging events
    
    Environment Variables:
    - INSTAGRAM_APP_ID: Meta App ID (same as WhatsApp if using same app)
    - INSTAGRAM_APP_SECRET: Meta App Secret
    - INSTAGRAM_VERIFY_TOKEN: Webhook verification token
    """
    
    BASE_URL = "https://graph.facebook.com/v18.0"
    
    def __init__(self, studio_id: str, credentials: Dict[str, Any] = None):
        super().__init__(studio_id, credentials)
        self.app_id = os.getenv('INSTAGRAM_APP_ID') or os.getenv('META_APP_ID')
        self.app_secret = os.getenv('INSTAGRAM_APP_SECRET') or os.getenv('META_APP_SECRET')
        self.verify_token = os.getenv('INSTAGRAM_VERIFY_TOKEN', 'studio_os_ig_verify')
        
    @property
    def channel_name(self) -> str:
        return "INSTAGRAM"
    
    @property
    def requires_oauth(self) -> bool:
        return True
    
    def get_oauth_url(self, redirect_uri: str, state: str) -> str:
        """
        Generate Instagram OAuth URL.
        Uses Facebook Login since Instagram messaging requires Facebook Page connection.
        """
        params = {
            'client_id': self.app_id,
            'redirect_uri': redirect_uri,
            'state': state,
            'scope': 'instagram_basic,instagram_manage_messages,pages_messaging,pages_manage_metadata',
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
            access_token = token_data['access_token']
            
            # Get long-lived token
            ll_url = f"{self.BASE_URL}/oauth/access_token"
            ll_params = {
                'grant_type': 'fb_exchange_token',
                'client_id': self.app_id,
                'client_secret': self.app_secret,
                'fb_exchange_token': access_token
            }
            
            ll_response = await client.get(ll_url, params=ll_params)
            if ll_response.status_code == 200:
                token_data = ll_response.json()
                access_token = token_data['access_token']
            
            # Get connected Instagram account
            pages_response = await client.get(
                f"{self.BASE_URL}/me/accounts",
                params={'access_token': access_token}
            )
            
            page_data = pages_response.json().get('data', [])
            instagram_account = None
            page_access_token = None
            
            # Find page with connected Instagram
            for page in page_data:
                page_token = page.get('access_token')
                ig_response = await client.get(
                    f"{self.BASE_URL}/{page['id']}",
                    params={
                        'fields': 'instagram_business_account',
                        'access_token': page_token
                    }
                )
                ig_data = ig_response.json()
                if 'instagram_business_account' in ig_data:
                    instagram_account = ig_data['instagram_business_account']
                    page_access_token = page_token
                    break
            
            self.credentials = {
                'access_token': page_access_token or access_token,
                'user_access_token': access_token,
                'instagram_account_id': instagram_account.get('id') if instagram_account else None,
                'expires_at': (datetime.utcnow() + timedelta(days=60)).isoformat(),
                'pages': page_data
            }
            
            if instagram_account:
                self.status = IntegrationStatus.CONNECTED
            else:
                self.status = IntegrationStatus.ERROR
            
            return self.credentials
    
    async def refresh_token(self) -> bool:
        """Refresh long-lived token (valid for 60 days)."""
        if not self.credentials.get('access_token'):
            return False
            
        expires_at = datetime.fromisoformat(self.credentials.get('expires_at', '2000-01-01'))
        
        # Refresh if expiring within 7 days
        if datetime.utcnow() > expires_at - timedelta(days=7):
            async with httpx.AsyncClient() as client:
                url = f"{self.BASE_URL}/oauth/access_token"
                params = {
                    'grant_type': 'fb_exchange_token',
                    'client_id': self.app_id,
                    'client_secret': self.app_secret,
                    'fb_exchange_token': self.credentials['access_token']
                }
                
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    self.credentials['access_token'] = data['access_token']
                    self.credentials['expires_at'] = (datetime.utcnow() + timedelta(days=60)).isoformat()
                    return True
                else:
                    self.status = IntegrationStatus.EXPIRED
                    return False
        
        return True
    
    async def verify_connection(self) -> bool:
        """Verify Instagram connection."""
        ig_account_id = self.credentials.get('instagram_account_id')
        access_token = self.credentials.get('access_token')
        
        if not ig_account_id or not access_token:
            self.status = IntegrationStatus.NOT_CONNECTED
            return False
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/{ig_account_id}",
                params={
                    'fields': 'username,name',
                    'access_token': access_token
                }
            )
            
            if response.status_code == 200:
                self.status = IntegrationStatus.CONNECTED
                return True
            else:
                self.status = IntegrationStatus.ERROR
                return False
    
    async def fetch_messages(self, since: Optional[datetime] = None) -> List[IncomingMessage]:
        """
        Fetch Instagram DM conversations.
        Note: Instagram primarily uses webhooks. This fetches conversation history.
        """
        ig_account_id = self.credentials.get('instagram_account_id')
        access_token = self.credentials.get('access_token')
        
        if not ig_account_id or not access_token:
            return []
        
        messages = []
        
        async with httpx.AsyncClient() as client:
            # Get conversations
            conv_response = await client.get(
                f"{self.BASE_URL}/{ig_account_id}/conversations",
                params={
                    'platform': 'instagram',
                    'access_token': access_token
                }
            )
            
            if conv_response.status_code != 200:
                return []
            
            conversations = conv_response.json().get('data', [])
            
            for conv in conversations[:10]:  # Limit to recent 10 conversations
                # Get messages in conversation
                msg_response = await client.get(
                    f"{self.BASE_URL}/{conv['id']}",
                    params={
                        'fields': 'messages{message,from,created_time}',
                        'access_token': access_token
                    }
                )
                
                if msg_response.status_code == 200:
                    msg_data = msg_response.json().get('messages', {}).get('data', [])
                    
                    for msg in msg_data:
                        created_time = datetime.strptime(
                            msg.get('created_time', ''),
                            '%Y-%m-%dT%H:%M:%S%z'
                        ) if msg.get('created_time') else datetime.utcnow()
                        
                        if since and created_time < since:
                            continue
                        
                        messages.append(IncomingMessage(
                            id=msg.get('id'),
                            channel='INSTAGRAM',
                            sender_id=msg.get('from', {}).get('id'),
                            sender_name=msg.get('from', {}).get('name'),
                            sender_email=None,
                            sender_phone=None,
                            content=msg.get('message', ''),
                            timestamp=created_time,
                            raw_data=msg
                        ))
        
        return messages
    
    async def send_message(self, message: OutgoingMessage) -> Dict[str, Any]:
        """Send an Instagram DM."""
        ig_account_id = self.credentials.get('instagram_account_id')
        access_token = self.credentials.get('access_token')
        
        if not ig_account_id or not access_token:
            raise Exception("Instagram not properly configured")
        
        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}/{ig_account_id}/messages"
            
            payload = {
                'recipient': {'id': message.recipient_id},
                'message': {'text': message.content},
                'access_token': access_token
            }
            
            response = await client.post(url, json=payload)
            result = response.json()
            
            if response.status_code in [200, 201]:
                return {
                    'success': True,
                    'message_id': result.get('message_id'),
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', {}).get('message', 'Unknown error')
                }
    
    def parse_webhook(self, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
        """Parse Instagram webhook payload."""
        try:
            entry = payload.get('entry', [{}])[0]
            messaging = entry.get('messaging', [{}])[0]
            
            # Check if this is a message event
            message = messaging.get('message')
            if not message:
                return None
            
            sender = messaging.get('sender', {})
            
            return IncomingMessage(
                id=message.get('mid'),
                channel='INSTAGRAM',
                sender_id=sender.get('id'),
                sender_name=None,  # Need to fetch from profile
                sender_email=None,
                sender_phone=None,
                content=message.get('text', ''),
                timestamp=datetime.fromtimestamp(messaging.get('timestamp', 0) / 1000),
                raw_data=payload,
                attachments=message.get('attachments', [])
            )
            
        except Exception as e:
            print(f"Error parsing Instagram webhook: {e}")
            return None
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature from Meta."""
        expected = hmac.new(
            self.app_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature)

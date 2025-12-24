# Gmail API Integration
import os
import base64
import json
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from urllib.parse import urlencode

from .base import BaseChannelIntegration, IncomingMessage, OutgoingMessage, IntegrationStatus


class GmailIntegration(BaseChannelIntegration):
    """
    Gmail API Integration for email inbox management.
    
    Setup Requirements:
    1. Create a Google Cloud Project
    2. Enable Gmail API
    3. Create OAuth 2.0 credentials (Web Application)
    4. Add authorized redirect URIs
    5. Configure Gmail Push Notifications (Pub/Sub) for real-time updates
    
    Environment Variables:
    - GOOGLE_CLIENT_ID: OAuth Client ID
    - GOOGLE_CLIENT_SECRET: OAuth Client Secret
    - GOOGLE_PUBSUB_TOPIC: Pub/Sub topic for push notifications (optional)
    """
    
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    API_URL = "https://gmail.googleapis.com/gmail/v1"
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    def __init__(self, studio_id: str, credentials: Dict[str, Any] = None):
        super().__init__(studio_id, credentials)
        self.client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        
    @property
    def channel_name(self) -> str:
        return "EMAIL"
    
    @property
    def requires_oauth(self) -> bool:
        return True
    
    def get_oauth_url(self, redirect_uri: str, state: str) -> str:
        """Generate Google OAuth URL for Gmail access."""
        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(self.SCOPES),
            'access_type': 'offline',
            'prompt': 'consent',
            'state': state
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"
    
    async def handle_oauth_callback(self, code: str, state: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'code': code,
                    'grant_type': 'authorization_code',
                    'redirect_uri': self.credentials.get('redirect_uri')
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"OAuth failed: {response.text}")
            
            token_data = response.json()
            
            # Get user profile
            profile_response = await client.get(
                f"{self.API_URL}/users/me/profile",
                headers={'Authorization': f"Bearer {token_data['access_token']}"}
            )
            
            profile = profile_response.json() if profile_response.status_code == 200 else {}
            
            self.credentials = {
                'access_token': token_data['access_token'],
                'refresh_token': token_data.get('refresh_token'),
                'expires_at': (datetime.utcnow() + timedelta(seconds=token_data.get('expires_in', 3600))).isoformat(),
                'email': profile.get('emailAddress'),
                'history_id': profile.get('historyId')
            }
            self.status = IntegrationStatus.CONNECTED
            
            return self.credentials
    
    async def refresh_token(self) -> bool:
        """Refresh the access token."""
        refresh_token = self.credentials.get('refresh_token')
        if not refresh_token:
            self.status = IntegrationStatus.EXPIRED
            return False
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'refresh_token': refresh_token,
                    'grant_type': 'refresh_token'
                }
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.credentials['access_token'] = token_data['access_token']
                self.credentials['expires_at'] = (
                    datetime.utcnow() + timedelta(seconds=token_data.get('expires_in', 3600))
                ).isoformat()
                self.status = IntegrationStatus.CONNECTED
                return True
            else:
                self.status = IntegrationStatus.EXPIRED
                return False
    
    async def _ensure_token_valid(self):
        """Ensure access token is valid, refresh if needed."""
        expires_at = datetime.fromisoformat(self.credentials.get('expires_at', '2000-01-01'))
        if datetime.utcnow() > expires_at - timedelta(minutes=5):
            await self.refresh_token()
    
    async def verify_connection(self) -> bool:
        """Verify Gmail connection."""
        if not self.credentials.get('access_token'):
            self.status = IntegrationStatus.NOT_CONNECTED
            return False
        
        await self._ensure_token_valid()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_URL}/users/me/profile",
                headers={'Authorization': f"Bearer {self.credentials['access_token']}"}
            )
            
            if response.status_code == 200:
                self.status = IntegrationStatus.CONNECTED
                return True
            else:
                self.status = IntegrationStatus.ERROR
                return False
    
    async def fetch_messages(self, since: Optional[datetime] = None) -> List[IncomingMessage]:
        """Fetch emails from Gmail inbox."""
        await self._ensure_token_valid()
        
        messages = []
        access_token = self.credentials.get('access_token')
        
        async with httpx.AsyncClient() as client:
            # Build query
            query_parts = ['in:inbox', '-from:me']
            if since:
                query_parts.append(f"after:{int(since.timestamp())}")
            
            # List messages
            list_response = await client.get(
                f"{self.API_URL}/users/me/messages",
                params={
                    'q': ' '.join(query_parts),
                    'maxResults': 50
                },
                headers={'Authorization': f"Bearer {access_token}"}
            )
            
            if list_response.status_code != 200:
                return []
            
            message_list = list_response.json().get('messages', [])
            
            # Fetch each message details
            for msg_ref in message_list[:20]:  # Limit to 20
                msg_response = await client.get(
                    f"{self.API_URL}/users/me/messages/{msg_ref['id']}",
                    params={'format': 'full'},
                    headers={'Authorization': f"Bearer {access_token}"}
                )
                
                if msg_response.status_code == 200:
                    msg_data = msg_response.json()
                    parsed = self._parse_email(msg_data)
                    if parsed:
                        messages.append(parsed)
        
        self.last_sync = datetime.utcnow()
        return messages
    
    def _parse_email(self, msg_data: Dict[str, Any]) -> Optional[IncomingMessage]:
        """Parse Gmail message into IncomingMessage."""
        try:
            headers = {h['name'].lower(): h['value'] for h in msg_data.get('payload', {}).get('headers', [])}
            
            # Get email body
            body = ""
            payload = msg_data.get('payload', {})
            
            if 'body' in payload and payload['body'].get('data'):
                body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
            elif 'parts' in payload:
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain' and part.get('body', {}).get('data'):
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
            
            # Parse sender
            from_header = headers.get('from', '')
            sender_name = None
            sender_email = from_header
            
            if '<' in from_header:
                parts = from_header.split('<')
                sender_name = parts[0].strip().strip('"')
                sender_email = parts[1].rstrip('>')
            
            # Parse timestamp
            internal_date = int(msg_data.get('internalDate', 0)) / 1000
            timestamp = datetime.fromtimestamp(internal_date) if internal_date else datetime.utcnow()
            
            return IncomingMessage(
                id=msg_data.get('id'),
                channel='EMAIL',
                sender_id=sender_email,
                sender_name=sender_name,
                sender_email=sender_email,
                sender_phone=None,
                content=body[:5000],  # Limit content length
                timestamp=timestamp,
                raw_data={
                    'subject': headers.get('subject', ''),
                    'thread_id': msg_data.get('threadId'),
                    'labels': msg_data.get('labelIds', [])
                }
            )
            
        except Exception as e:
            print(f"Error parsing email: {e}")
            return None
    
    async def send_message(self, message: OutgoingMessage) -> Dict[str, Any]:
        """Send an email via Gmail."""
        await self._ensure_token_valid()
        
        access_token = self.credentials.get('access_token')
        from_email = self.credentials.get('email')
        
        if not access_token or not from_email:
            raise Exception("Gmail not properly configured")
        
        # Create email message
        email_msg = MIMEMultipart()
        email_msg['to'] = message.recipient_id
        email_msg['from'] = from_email
        email_msg['subject'] = message.attachments[0].get('subject', 'Re: Your inquiry') if message.attachments else 'Re: Your inquiry'
        
        email_msg.attach(MIMEText(message.content, 'plain'))
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(email_msg.as_bytes()).decode('utf-8')
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.API_URL}/users/me/messages/send",
                json={'raw': raw_message},
                headers={
                    'Authorization': f"Bearer {access_token}",
                    'Content-Type': 'application/json'
                }
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    'success': True,
                    'message_id': result.get('id'),
                    'thread_id': result.get('threadId'),
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': response.json().get('error', {}).get('message', 'Unknown error')
                }
    
    def parse_webhook(self, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
        """
        Parse Gmail Pub/Sub push notification.
        Note: Gmail push notifications only indicate new mail, 
        you need to fetch the actual message separately.
        """
        try:
            # Decode Pub/Sub message
            if 'message' in payload:
                data = payload['message'].get('data')
                if data:
                    decoded = json.loads(base64.b64decode(data).decode('utf-8'))
                    # This contains historyId - use it to fetch new messages
                    return None  # Need to call fetch_messages with history_id
            
            return None
            
        except Exception as e:
            print(f"Error parsing Gmail webhook: {e}")
            return None
    
    async def setup_push_notifications(self, webhook_url: str) -> Dict[str, Any]:
        """
        Set up Gmail push notifications via Pub/Sub.
        Requires a Google Cloud Pub/Sub topic.
        """
        await self._ensure_token_valid()
        
        topic = os.getenv('GOOGLE_PUBSUB_TOPIC')
        if not topic:
            return {'success': False, 'error': 'GOOGLE_PUBSUB_TOPIC not configured'}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.API_URL}/users/me/watch",
                json={
                    'topicName': topic,
                    'labelIds': ['INBOX']
                },
                headers={'Authorization': f"Bearer {self.credentials['access_token']}"}
            )
            
            if response.status_code == 200:
                result = response.json()
                self.credentials['history_id'] = result.get('historyId')
                return {'success': True, 'expiration': result.get('expiration')}
            else:
                return {'success': False, 'error': response.text}

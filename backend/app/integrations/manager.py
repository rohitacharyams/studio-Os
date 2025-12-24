# Integration Manager - Handles all channel integrations for a studio
import os
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from flask import current_app

from .base import BaseChannelIntegration, IncomingMessage, IntegrationStatus
from .whatsapp import WhatsAppIntegration
from .instagram import InstagramIntegration
from .gmail import GmailIntegration
from app.models import db, Studio, Contact, Conversation, Message, ChannelIntegration


class IntegrationManager:
    """
    Central manager for all channel integrations.
    Handles setup, message routing, and synchronization.
    """
    
    INTEGRATION_CLASSES = {
        'WHATSAPP': WhatsAppIntegration,
        'INSTAGRAM': InstagramIntegration,
        'EMAIL': GmailIntegration
    }
    
    def __init__(self, studio_id: str):
        self.studio_id = studio_id
        self._integrations: Dict[str, BaseChannelIntegration] = {}
        self._load_integrations()
    
    def _load_integrations(self):
        """Load existing integrations from database."""
        stored = ChannelIntegration.query.filter_by(studio_id=self.studio_id).all()
        
        for integration in stored:
            if integration.channel in self.INTEGRATION_CLASSES:
                cls = self.INTEGRATION_CLASSES[integration.channel]
                instance = cls(
                    studio_id=self.studio_id,
                    credentials=integration.credentials or {}
                )
                instance.status = IntegrationStatus(integration.status)
                self._integrations[integration.channel] = instance
    
    def get_integration(self, channel: str) -> Optional[BaseChannelIntegration]:
        """Get a specific channel integration."""
        return self._integrations.get(channel)
    
    def list_integrations(self) -> List[Dict[str, Any]]:
        """List all integrations with their status."""
        result = []
        
        for channel, cls in self.INTEGRATION_CLASSES.items():
            if channel in self._integrations:
                integration = self._integrations[channel]
                result.append({
                    'channel': channel,
                    'status': integration.status.value,
                    'connected': integration.status == IntegrationStatus.CONNECTED
                })
            else:
                result.append({
                    'channel': channel,
                    'status': 'not_connected',
                    'connected': False
                })
        
        return result
    
    def get_oauth_url(self, channel: str, redirect_uri: str) -> Optional[str]:
        """Get OAuth URL for connecting a channel."""
        if channel not in self.INTEGRATION_CLASSES:
            return None
        
        cls = self.INTEGRATION_CLASSES[channel]
        instance = cls(studio_id=self.studio_id, credentials={'redirect_uri': redirect_uri})
        
        state = f"{self.studio_id}:{channel}:{uuid.uuid4().hex[:8]}"
        return instance.get_oauth_url(redirect_uri, state)
    
    async def handle_oauth_callback(self, channel: str, code: str, state: str, redirect_uri: str) -> Dict[str, Any]:
        """Handle OAuth callback for a channel."""
        if channel not in self.INTEGRATION_CLASSES:
            return {'success': False, 'error': 'Unknown channel'}
        
        try:
            cls = self.INTEGRATION_CLASSES[channel]
            instance = cls(studio_id=self.studio_id, credentials={'redirect_uri': redirect_uri})
            
            credentials = await instance.handle_oauth_callback(code, state)
            
            # Save to database
            existing = ChannelIntegration.query.filter_by(
                studio_id=self.studio_id,
                channel=channel
            ).first()
            
            if existing:
                existing.credentials = credentials
                existing.status = instance.status.value
                existing.updated_at = datetime.utcnow()
            else:
                new_integration = ChannelIntegration(
                    id=str(uuid.uuid4()),
                    studio_id=self.studio_id,
                    channel=channel,
                    credentials=credentials,
                    status=instance.status.value
                )
                db.session.add(new_integration)
            
            db.session.commit()
            
            self._integrations[channel] = instance
            
            return {'success': True, 'channel': channel, 'status': instance.status.value}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def disconnect(self, channel: str) -> bool:
        """Disconnect a channel integration."""
        if channel in self._integrations:
            self._integrations[channel].disconnect()
            del self._integrations[channel]
        
        existing = ChannelIntegration.query.filter_by(
            studio_id=self.studio_id,
            channel=channel
        ).first()
        
        if existing:
            db.session.delete(existing)
            db.session.commit()
        
        return True
    
    async def sync_messages(self, channel: Optional[str] = None) -> Dict[str, Any]:
        """
        Sync messages from connected channels.
        
        Args:
            channel: Specific channel to sync, or None for all channels
        """
        results = {}
        channels_to_sync = [channel] if channel else list(self._integrations.keys())
        
        for ch in channels_to_sync:
            if ch not in self._integrations:
                results[ch] = {'success': False, 'error': 'Not connected'}
                continue
            
            integration = self._integrations[ch]
            
            try:
                # Get last sync time
                last_message = Message.query.join(Conversation).filter(
                    Conversation.studio_id == self.studio_id,
                    Conversation.channel == ch
                ).order_by(Message.created_at.desc()).first()
                
                since = last_message.created_at if last_message else None
                
                # Fetch new messages
                messages = await integration.fetch_messages(since=since)
                
                # Process each message
                processed = 0
                for msg in messages:
                    await self._process_incoming_message(msg)
                    processed += 1
                
                results[ch] = {'success': True, 'messages_processed': processed}
                
            except Exception as e:
                results[ch] = {'success': False, 'error': str(e)}
        
        return results
    
    async def _process_incoming_message(self, message: IncomingMessage) -> None:
        """Process and store an incoming message."""
        # Find or create contact
        contact = self._find_or_create_contact(message)
        
        # Find or create conversation
        conversation = self._find_or_create_conversation(contact, message.channel)
        
        # Check for duplicate message
        existing = Message.query.filter_by(external_id=message.id).first()
        if existing:
            return
        
        # Create message record
        new_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            external_id=message.id,
            direction='INBOUND',
            content=message.content,
            channel=message.channel,
            status='DELIVERED',
            created_at=message.timestamp,
            raw_payload=message.raw_data
        )
        
        # Update conversation
        conversation.last_message_at = message.timestamp
        conversation.unread_count = (conversation.unread_count or 0) + 1
        
        db.session.add(new_message)
        db.session.commit()
    
    def _find_or_create_contact(self, message: IncomingMessage) -> Contact:
        """Find existing contact or create new one."""
        # Try to find by email or phone
        contact = None
        
        if message.sender_email:
            contact = Contact.query.filter_by(
                studio_id=self.studio_id,
                email=message.sender_email
            ).first()
        
        if not contact and message.sender_phone:
            contact = Contact.query.filter_by(
                studio_id=self.studio_id,
                phone=message.sender_phone
            ).first()
        
        if not contact:
            # Create new contact
            contact = Contact(
                id=str(uuid.uuid4()),
                studio_id=self.studio_id,
                name=message.sender_name or 'Unknown',
                email=message.sender_email,
                phone=message.sender_phone,
                source=message.channel,
                lead_status='NEW'
            )
            db.session.add(contact)
            db.session.flush()
        
        return contact
    
    def _find_or_create_conversation(self, contact: Contact, channel: str) -> Conversation:
        """Find existing conversation or create new one."""
        conversation = Conversation.query.filter_by(
            studio_id=self.studio_id,
            contact_id=contact.id,
            channel=channel
        ).first()
        
        if not conversation:
            conversation = Conversation(
                id=str(uuid.uuid4()),
                studio_id=self.studio_id,
                contact_id=contact.id,
                channel=channel,
                status='OPEN'
            )
            db.session.add(conversation)
            db.session.flush()
        
        return conversation
    
    async def send_message(self, channel: str, recipient_id: str, content: str, 
                          conversation_id: str = None, **kwargs) -> Dict[str, Any]:
        """
        Send a message through a specific channel.
        
        Args:
            channel: Channel to send through
            recipient_id: Recipient identifier (phone, email, user_id)
            content: Message content
            conversation_id: Optional conversation to link message to
        """
        if channel not in self._integrations:
            return {'success': False, 'error': f'{channel} not connected'}
        
        integration = self._integrations[channel]
        
        from .base import OutgoingMessage
        message = OutgoingMessage(
            recipient_id=recipient_id,
            content=content,
            channel=channel,
            **kwargs
        )
        
        try:
            result = await integration.send_message(message)
            
            if result.get('success') and conversation_id:
                # Store sent message
                new_message = Message(
                    id=str(uuid.uuid4()),
                    conversation_id=conversation_id,
                    external_id=result.get('message_id'),
                    direction='OUTBOUND',
                    content=content,
                    channel=channel,
                    status='SENT',
                    sent_at=datetime.utcnow()
                )
                db.session.add(new_message)
                db.session.commit()
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_webhook(self, channel: str, payload: Dict[str, Any], 
                       signature: str = None) -> Dict[str, Any]:
        """
        Handle incoming webhook from a channel.
        
        Args:
            channel: Source channel
            payload: Webhook payload
            signature: Optional signature for verification
        """
        if channel not in self._integrations:
            return {'success': False, 'error': 'Channel not configured'}
        
        integration = self._integrations[channel]
        
        # Verify signature if provided
        if signature and hasattr(integration, 'verify_webhook_signature'):
            payload_bytes = json.dumps(payload).encode() if isinstance(payload, dict) else payload
            if not integration.verify_webhook_signature(payload_bytes, signature):
                return {'success': False, 'error': 'Invalid signature'}
        
        # Parse message
        message = integration.parse_webhook(payload)
        
        if message:
            # Process asynchronously in production
            # For now, process synchronously
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            loop.run_until_complete(self._process_incoming_message(message))
            return {'success': True, 'message_id': message.id}
        
        return {'success': True, 'message': 'No message in payload'}


def get_integration_manager(studio_id: str) -> IntegrationManager:
    """Factory function to get integration manager for a studio."""
    return IntegrationManager(studio_id)

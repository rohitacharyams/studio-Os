from twilio.rest import Client
from flask import current_app
from typing import Optional


class WhatsAppService:
    """Service for sending WhatsApp messages via Twilio."""
    
    def __init__(self):
        self.account_sid = current_app.config.get('TWILIO_ACCOUNT_SID', '')
        self.auth_token = current_app.config.get('TWILIO_AUTH_TOKEN', '')
        self.whatsapp_number = current_app.config.get('TWILIO_WHATSAPP_NUMBER', '')
        
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            self.client = None
    
    def send_message(
        self,
        to_phone: str,
        message: str,
        studio_id: Optional[str] = None,
        media_url: Optional[str] = None
    ) -> Optional[str]:
        """Send a WhatsApp message and return message SID."""
        if not self.client:
            current_app.logger.warning("Twilio credentials not configured")
            return None
        
        if not self.whatsapp_number:
            current_app.logger.warning("WhatsApp number not configured")
            return None
        
        try:
            # Format phone numbers for WhatsApp
            from_whatsapp = f"whatsapp:{self.whatsapp_number}"
            to_whatsapp = f"whatsapp:{to_phone}"
            
            # Send message
            message_params = {
                'from_': from_whatsapp,
                'to': to_whatsapp,
                'body': message
            }
            
            if media_url:
                message_params['media_url'] = [media_url]
            
            sent_message = self.client.messages.create(**message_params)
            
            return sent_message.sid
            
        except Exception as e:
            current_app.logger.error(f"Failed to send WhatsApp message: {str(e)}")
            raise
    
    def get_message_status(self, message_sid: str) -> Optional[str]:
        """Get the delivery status of a message."""
        if not self.client:
            return None
        
        try:
            message = self.client.messages(message_sid).fetch()
            return message.status
        except Exception as e:
            current_app.logger.error(f"Failed to get message status: {str(e)}")
            return None
    
    def send_template_message(
        self,
        to_phone: str,
        template_sid: str,
        template_variables: dict = None
    ) -> Optional[str]:
        """Send a WhatsApp template message (for initiating conversations)."""
        if not self.client:
            current_app.logger.warning("Twilio credentials not configured")
            return None
        
        try:
            from_whatsapp = f"whatsapp:{self.whatsapp_number}"
            to_whatsapp = f"whatsapp:{to_phone}"
            
            # Build content variables for template
            content_variables = {}
            if template_variables:
                for i, (key, value) in enumerate(template_variables.items(), 1):
                    content_variables[str(i)] = value
            
            message = self.client.messages.create(
                from_=from_whatsapp,
                to=to_whatsapp,
                content_sid=template_sid,
                content_variables=content_variables if content_variables else None
            )
            
            return message.sid
            
        except Exception as e:
            current_app.logger.error(f"Failed to send template message: {str(e)}")
            raise

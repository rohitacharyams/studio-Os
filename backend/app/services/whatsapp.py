"""
WhatsApp Business API Integration using Twilio
This service handles sending and receiving WhatsApp messages via Twilio's WhatsApp Business API
"""

from flask import current_app
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import logging
from datetime import datetime
from typing import Optional, Dict, List
from ..models import Message, Conversation, Contact, Studio, db

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service for WhatsApp Business API integration via Twilio"""
    
    def __init__(self, account_sid: str = None, auth_token: str = None, whatsapp_number: str = None):
        """
        Initialize WhatsApp service with Twilio credentials
        
        Args:
            account_sid: Twilio Account SID (or from config)
            auth_token: Twilio Auth Token (or from config)
            whatsapp_number: WhatsApp Business number (format: whatsapp:+1234567890)
        """
        self.account_sid = account_sid or current_app.config.get('TWILIO_ACCOUNT_SID')
        self.auth_token = auth_token or current_app.config.get('TWILIO_AUTH_TOKEN')
        self.whatsapp_number = whatsapp_number or current_app.config.get('TWILIO_WHATSAPP_NUMBER')
        
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            self.client = None
            logger.warning("Twilio credentials not configured. WhatsApp integration disabled.")
    
    def format_whatsapp_number(self, phone: str) -> str:
        """
        Format phone number for WhatsApp
        
        Args:
            phone: Phone number (can be in various formats)
            
        Returns:
            WhatsApp formatted number (whatsapp:+1234567890)
        """
        # Remove any existing whatsapp: prefix
        phone = phone.replace('whatsapp:', '')
        
        # Remove spaces, dashes, parentheses
        phone = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        # Add + if not present (assuming Indian number)
        if not phone.startswith('+'):
            if phone.startswith('91'):
                phone = '+' + phone
            elif len(phone) == 10:
                phone = '+91' + phone
            else:
                phone = '+' + phone
        
        return f'whatsapp:{phone}'
    
    def send_message(self, to: str, body: str, media_url: str = None) -> Dict:
        """
        Send a WhatsApp message
        
        Args:
            to: Recipient phone number
            body: Message text
            media_url: Optional URL of media to send
            
        Returns:
            Dict with status and message details
        """
        if not self.client:
            logger.warning("WhatsApp client not initialized")
            return {'success': False, 'error': 'WhatsApp not configured'}
        
        try:
            to_formatted = self.format_whatsapp_number(to)
            
            message_params = {
                'from_': self.whatsapp_number,
                'to': to_formatted,
                'body': body
            }
            
            if media_url:
                message_params['media_url'] = [media_url]
            
            message = self.client.messages.create(**message_params)
            
            logger.info(f"WhatsApp message sent: {message.sid} to {to_formatted}")
            
            return {
                'success': True,
                'message_sid': message.sid,
                'status': message.status,
                'to': to_formatted
            }
            
        except TwilioRestException as e:
            logger.error(f"Twilio error sending WhatsApp: {e.code} - {e.msg}")
            return {
                'success': False,
                'error': str(e.msg),
                'error_code': e.code
            }
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_template_message(self, to: str, template_name: str, variables: Dict = None) -> Dict:
        """
        Send a pre-approved WhatsApp template message
        Template messages can be sent outside the 24-hour window
        
        Args:
            to: Recipient phone number
            template_name: Name of approved template
            variables: Template variables
            
        Returns:
            Dict with status and message details
        """
        if not self.client:
            return {'success': False, 'error': 'WhatsApp not configured'}
        
        # Build template body
        templates = {
            'booking_confirmation': """🎉 *Booking Confirmed!*

Hi {{1}},

Your class booking is confirmed:
📚 *Class:* {{2}}
📅 *Date:* {{3}}
⏰ *Time:* {{4}}

See you at the studio!

Reply with:
• *CANCEL* to cancel this booking
• *HELP* for assistance""",
            
            'booking_reminder': """⏰ *Class Reminder*

Hi {{1}},

Reminder: You have a class tomorrow!
📚 *Class:* {{2}}
📅 *Date:* {{3}}
⏰ *Time:* {{4}}

Looking forward to seeing you!""",
            
            'payment_received': """✅ *Payment Received*

Hi {{1}},

We've received your payment of ₹{{2}} for {{3}}.

Thank you for booking with us!""",
            
            'class_cancelled': """📢 *Class Update*

Hi {{1}},

Unfortunately, the {{2}} class on {{3}} has been cancelled.

We apologize for any inconvenience. Your payment will be refunded within 3-5 business days.

Reply *REBOOK* to book another class."""
        }
        
        template_body = templates.get(template_name)
        if not template_body:
            return {'success': False, 'error': f'Template {template_name} not found'}
        
        # Replace variables
        if variables:
            for key, value in variables.items():
                template_body = template_body.replace(f'{{{{{key}}}}}', str(value))
        
        return self.send_message(to, template_body)
    
    def send_booking_confirmation(self, booking) -> Dict:
        """
        Send booking confirmation via WhatsApp
        
        Args:
            booking: Booking object with contact and session info
        """
        contact = booking.contact
        session = booking.class_session
        
        if not contact or not contact.phone:
            return {'success': False, 'error': 'No phone number for contact'}
        
        variables = {
            '1': contact.name or 'there',
            '2': session.dance_class.name if session and session.dance_class else 'Your class',
            '3': session.start_time.strftime('%A, %d %B') if session else 'TBD',
            '4': session.start_time.strftime('%I:%M %p') if session else 'TBD'
        }
        
        return self.send_template_message(contact.phone, 'booking_confirmation', variables)
    
    def send_payment_confirmation(self, payment) -> Dict:
        """
        Send payment confirmation via WhatsApp
        
        Args:
            payment: Payment object
        """
        booking = payment.booking
        contact = booking.contact if booking else None
        
        if not contact or not contact.phone:
            return {'success': False, 'error': 'No phone number for contact'}
        
        variables = {
            '1': contact.name or 'there',
            '2': str(payment.amount),
            '3': booking.class_session.dance_class.name if booking and booking.class_session else 'your booking'
        }
        
        return self.send_template_message(contact.phone, 'payment_received', variables)
    
    def send_class_reminder(self, booking, hours_before: int = 24) -> Dict:
        """
        Send class reminder via WhatsApp
        
        Args:
            booking: Booking object
            hours_before: Hours before class (for message context)
        """
        contact = booking.contact
        session = booking.class_session
        
        if not contact or not contact.phone:
            return {'success': False, 'error': 'No phone number for contact'}
        
        variables = {
            '1': contact.name or 'there',
            '2': session.dance_class.name if session and session.dance_class else 'Your class',
            '3': session.start_time.strftime('%A, %d %B') if session else 'tomorrow',
            '4': session.start_time.strftime('%I:%M %p') if session else 'TBD'
        }
        
        return self.send_template_message(contact.phone, 'booking_reminder', variables)
    
    def process_incoming_message(self, message_data: Dict) -> Dict:
        """
        Process incoming WhatsApp message from Twilio webhook
        
        Args:
            message_data: Webhook data from Twilio
            
        Returns:
            Dict with processed message info
        """
        try:
            from_number = message_data.get('From', '').replace('whatsapp:', '')
            to_number = message_data.get('To', '').replace('whatsapp:', '')
            body = message_data.get('Body', '').strip()
            message_sid = message_data.get('MessageSid')
            media_url = message_data.get('MediaUrl0')
            media_type = message_data.get('MediaContentType0')
            
            # Get or create contact
            contact = Contact.query.filter_by(phone=from_number).first()
            if not contact:
                # Get default studio
                studio = Studio.query.first()
                contact = Contact(
                    studio_id=studio.id if studio else 1,
                    phone=from_number,
                    name=message_data.get('ProfileName', f'WhatsApp User'),
                    source='whatsapp'
                )
                db.session.add(contact)
            
            # Get or create conversation
            conversation = Conversation.query.filter_by(
                contact_id=contact.id,
                channel='whatsapp'
            ).first()
            
            if not conversation:
                conversation = Conversation(
                    studio_id=contact.studio_id,
                    contact_id=contact.id,
                    channel='whatsapp',
                    status='open',
                    last_message_at=datetime.utcnow()
                )
                db.session.add(conversation)
            else:
                conversation.last_message_at = datetime.utcnow()
                if conversation.status == 'closed':
                    conversation.status = 'open'
            
            # Create message record
            message = Message(
                conversation_id=conversation.id,
                direction='inbound',
                content=body,
                channel='whatsapp',
                external_id=message_sid,
                metadata={
                    'from': from_number,
                    'to': to_number,
                    'media_url': media_url,
                    'media_type': media_type
                }
            )
            db.session.add(message)
            
            conversation.unread_count = (conversation.unread_count or 0) + 1
            conversation.last_message = body[:100] if body else '[Media]'
            
            db.session.commit()
            
            # Process automated responses
            auto_response = self._process_auto_response(body, contact)
            if auto_response:
                self.send_message(from_number, auto_response)
            
            return {
                'success': True,
                'contact_id': contact.id,
                'conversation_id': conversation.id,
                'message_id': message.id,
                'body': body
            }
            
        except Exception as e:
            logger.error(f"Error processing incoming WhatsApp message: {str(e)}")
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_auto_response(self, body: str, contact: Contact) -> Optional[str]:
        """
        Generate automatic response based on message content
        
        Args:
            body: Message text
            contact: Contact who sent the message
            
        Returns:
            Auto-response text or None
        """
        body_lower = body.lower().strip()
        
        # Check for keywords
        if body_lower in ['hi', 'hello', 'hey', 'hii']:
            return f"""👋 Hi {contact.name or 'there'}!

Welcome to our studio! How can we help you today?

Reply with:
• *CLASSES* - View upcoming classes
• *BOOK* - Book a class
• *SCHEDULE* - See this week's schedule
• *HELP* - Get assistance"""
        
        if body_lower == 'classes' or body_lower == 'schedule':
            return """📅 *This Week's Classes*

🔴 Salsa Beginner - Mon & Wed 7PM
🟣 Bachata Intermediate - Tue & Thu 8PM
🟡 Hip-Hop Basics - Sat 11AM
🔵 Contemporary Flow - Sun 10AM

Reply *BOOK* followed by class name to book!
e.g., *BOOK Salsa*"""
        
        if body_lower == 'help':
            return """🆘 *Need Help?*

Here are things I can help with:
• View class schedule
• Book a class
• Cancel a booking
• Payment queries

For urgent matters, please call us directly.

Reply *SPEAK TO HUMAN* to connect with our team."""
        
        if body_lower == 'cancel':
            return """To cancel a booking, please reply with:

*CANCEL #[BookingID]*

You can find your booking ID in your confirmation message.

Note: Cancellations made less than 4 hours before class may not be eligible for refund."""
        
        # No auto-response for other messages
        return None
    
    def get_conversation_history(self, phone: str, limit: int = 50) -> List[Dict]:
        """
        Get WhatsApp conversation history for a phone number
        
        Args:
            phone: Phone number
            limit: Max messages to return
            
        Returns:
            List of message dictionaries
        """
        contact = Contact.query.filter_by(phone=phone).first()
        if not contact:
            return []
        
        conversation = Conversation.query.filter_by(
            contact_id=contact.id,
            channel='whatsapp'
        ).first()
        
        if not conversation:
            return []
        
        messages = Message.query.filter_by(
            conversation_id=conversation.id
        ).order_by(Message.created_at.desc()).limit(limit).all()
        
        return [{
            'id': m.id,
            'direction': m.direction,
            'content': m.content,
            'timestamp': m.created_at.isoformat(),
            'status': m.status
        } for m in reversed(messages)]


# Singleton instance
_whatsapp_service = None

def get_whatsapp_service() -> WhatsAppService:
    """Get WhatsApp service singleton"""
    global _whatsapp_service
    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppService()
    return _whatsapp_service

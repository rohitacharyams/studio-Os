"""
Notification service for booking confirmations, reminders, and alerts.
Supports Email (via SendGrid/SMTP) and SMS (via Twilio/MSG91).
"""

import os
from datetime import datetime
from typing import Optional
from flask import current_app, render_template_string
import logging

logger = logging.getLogger(__name__)


# Email Templates
BOOKING_CONFIRMATION_EMAIL = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #6366f1; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
        .content { background: #f9fafb; padding: 20px; border-radius: 0 0 8px 8px; }
        .booking-details { background: white; padding: 15px; border-radius: 8px; margin: 15px 0; }
        .detail-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e5e7eb; }
        .detail-row:last-child { border-bottom: none; }
        .label { color: #6b7280; }
        .value { font-weight: 600; }
        .footer { text-align: center; margin-top: 20px; color: #6b7280; font-size: 12px; }
        .btn { background: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Booking Confirmed! 🎉</h1>
        </div>
        <div class="content">
            <p>Hi {{ contact_name }},</p>
            <p>Your class booking has been confirmed. Here are the details:</p>
            
            <div class="booking-details">
                <div class="detail-row">
                    <span class="label">Booking #</span>
                    <span class="value">{{ booking_number }}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Class</span>
                    <span class="value">{{ class_name }}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Date</span>
                    <span class="value">{{ session_date }}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Time</span>
                    <span class="value">{{ session_time }}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Instructor</span>
                    <span class="value">{{ instructor_name }}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Location</span>
                    <span class="value">{{ location }}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Amount Paid</span>
                    <span class="value">₹{{ amount_paid }}</span>
                </div>
            </div>
            
            <p style="text-align: center;">
                <a href="{{ cancel_url }}" class="btn">View/Manage Booking</a>
            </p>
            
            <p><strong>Important Reminders:</strong></p>
            <ul>
                <li>Please arrive 10 minutes before class starts</li>
                <li>Bring a water bottle and towel</li>
                <li>Cancellations made less than 12 hours before class may be charged</li>
            </ul>
            
            <p>See you at the studio!</p>
            <p>- {{ studio_name }} Team</p>
        </div>
        <div class="footer">
            <p>{{ studio_name }} | {{ studio_address }}</p>
            <p>Questions? Reply to this email or call {{ studio_phone }}</p>
        </div>
    </div>
</body>
</html>
"""

BOOKING_CANCELLATION_EMAIL = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #ef4444; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
        .content { background: #f9fafb; padding: 20px; border-radius: 0 0 8px 8px; }
        .booking-details { background: white; padding: 15px; border-radius: 8px; margin: 15px 0; }
        .detail-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e5e7eb; }
        .footer { text-align: center; margin-top: 20px; color: #6b7280; font-size: 12px; }
        .btn { background: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Booking Cancelled</h1>
        </div>
        <div class="content">
            <p>Hi {{ contact_name }},</p>
            <p>Your booking has been cancelled as requested. Here are the details:</p>
            
            <div class="booking-details">
                <div class="detail-row">
                    <span>Booking #</span>
                    <span>{{ booking_number }}</span>
                </div>
                <div class="detail-row">
                    <span>Class</span>
                    <span>{{ class_name }}</span>
                </div>
                <div class="detail-row">
                    <span>Original Date</span>
                    <span>{{ session_date }}</span>
                </div>
                {% if refund_amount > 0 %}
                <div class="detail-row">
                    <span>Refund Amount</span>
                    <span>₹{{ refund_amount }}</span>
                </div>
                {% endif %}
            </div>
            
            {% if refund_amount > 0 %}
            <p>Your refund of ₹{{ refund_amount }} will be processed within 5-7 business days.</p>
            {% endif %}
            
            <p style="text-align: center;">
                <a href="{{ booking_url }}" class="btn">Book Another Class</a>
            </p>
            
            <p>We hope to see you again soon!</p>
            <p>- {{ studio_name }} Team</p>
        </div>
        <div class="footer">
            <p>{{ studio_name }}</p>
        </div>
    </div>
</body>
</html>
"""

BOOKING_REMINDER_EMAIL = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #f59e0b; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
        .content { background: #f9fafb; padding: 20px; border-radius: 0 0 8px 8px; }
        .booking-details { background: white; padding: 15px; border-radius: 8px; margin: 15px 0; }
        .footer { text-align: center; margin-top: 20px; color: #6b7280; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Class Reminder ⏰</h1>
        </div>
        <div class="content">
            <p>Hi {{ contact_name }},</p>
            <p>Just a friendly reminder that your class is coming up {{ reminder_time }}!</p>
            
            <div class="booking-details">
                <p><strong>{{ class_name }}</strong></p>
                <p>📅 {{ session_date }} at {{ session_time }}</p>
                <p>📍 {{ location }}</p>
                <p>👤 Instructor: {{ instructor_name }}</p>
            </div>
            
            <p><strong>Don't forget:</strong></p>
            <ul>
                <li>Arrive 10 minutes early</li>
                <li>Bring water and towel</li>
            </ul>
            
            <p>See you soon!</p>
            <p>- {{ studio_name }} Team</p>
        </div>
    </div>
</body>
</html>
"""

WAITLIST_NOTIFICATION_EMAIL = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #10b981; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
        .content { background: #f9fafb; padding: 20px; border-radius: 0 0 8px 8px; }
        .btn { background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 10px 0; }
        .urgent { background: #fef3c7; border-left: 4px solid #f59e0b; padding: 10px; margin: 15px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Spot Available! 🎉</h1>
        </div>
        <div class="content">
            <p>Hi {{ contact_name }},</p>
            <p>Great news! A spot has opened up for the class you were waiting for:</p>
            
            <p><strong>{{ class_name }}</strong><br>
            {{ session_date }} at {{ session_time }}</p>
            
            <div class="urgent">
                <strong>⚡ Act Fast!</strong> This spot is reserved for you for the next 30 minutes.
            </div>
            
            <p style="text-align: center;">
                <a href="{{ booking_url }}" class="btn">Confirm Your Spot Now</a>
            </p>
            
            <p>If you don't confirm within 30 minutes, the spot will be offered to the next person on the waitlist.</p>
            
            <p>- {{ studio_name }} Team</p>
        </div>
    </div>
</body>
</html>
"""

# SMS Templates
SMS_TEMPLATES = {
    'booking_confirmation': "Hi {contact_name}! Your booking for {class_name} on {session_date} at {session_time} is confirmed. Booking #{booking_number}. See you at {studio_name}!",
    'booking_cancellation': "Hi {contact_name}, your booking #{booking_number} for {class_name} has been cancelled. {refund_message} - {studio_name}",
    'booking_reminder': "Reminder: Your {class_name} class is {reminder_time}! {session_date} at {session_time}. Don't forget to arrive 10 mins early. - {studio_name}",
    'waitlist_notification': "Good news {contact_name}! A spot opened for {class_name} on {session_date}. Confirm within 30 mins: {booking_url} - {studio_name}",
    'payment_confirmation': "Payment of ₹{amount} received for {description}. Transaction ID: {transaction_id}. Thank you! - {studio_name}",
}


class NotificationService:
    """Service for sending email and SMS notifications."""
    
    def __init__(self, app=None):
        self.app = app
        self.email_provider = None
        self.sms_provider = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize notification providers based on config."""
        self.app = app
        
        # Initialize email provider
        email_provider = app.config.get('EMAIL_PROVIDER', 'smtp')
        if email_provider == 'sendgrid':
            self.email_provider = SendGridProvider(app.config.get('SENDGRID_API_KEY'))
        else:
            self.email_provider = SMTPProvider(
                host=app.config.get('SMTP_HOST', 'smtp.gmail.com'),
                port=app.config.get('SMTP_PORT', 587),
                username=app.config.get('SMTP_USERNAME'),
                password=app.config.get('SMTP_PASSWORD'),
                from_email=app.config.get('SMTP_FROM_EMAIL'),
                from_name=app.config.get('SMTP_FROM_NAME', 'Studio OS')
            )
        
        # Initialize SMS provider
        sms_provider = app.config.get('SMS_PROVIDER', 'twilio')
        if sms_provider == 'msg91':
            self.sms_provider = MSG91Provider(
                auth_key=app.config.get('MSG91_AUTH_KEY'),
                sender_id=app.config.get('MSG91_SENDER_ID')
            )
        else:
            self.sms_provider = TwilioProvider(
                account_sid=app.config.get('TWILIO_ACCOUNT_SID'),
                auth_token=app.config.get('TWILIO_AUTH_TOKEN'),
                from_number=app.config.get('TWILIO_FROM_NUMBER')
            )
    
    def send_booking_confirmation(self, booking, session, contact, studio):
        """Send booking confirmation email and SMS."""
        context = self._build_booking_context(booking, session, contact, studio)
        
        # Send email
        if contact.email:
            try:
                html = render_template_string(BOOKING_CONFIRMATION_EMAIL, **context)
                self.email_provider.send(
                    to_email=contact.email,
                    to_name=f"{contact.first_name} {contact.last_name}",
                    subject=f"Booking Confirmed - {context['class_name']} on {context['session_date']}",
                    html=html
                )
                logger.info(f"Sent booking confirmation email to {contact.email}")
            except Exception as e:
                logger.error(f"Failed to send booking confirmation email: {e}")
        
        # Send SMS
        if contact.phone:
            try:
                sms_text = SMS_TEMPLATES['booking_confirmation'].format(**context)
                self.sms_provider.send(contact.phone, sms_text)
                logger.info(f"Sent booking confirmation SMS to {contact.phone}")
            except Exception as e:
                logger.error(f"Failed to send booking confirmation SMS: {e}")
    
    def send_booking_cancellation(self, booking, session, contact, studio, refund_amount=0):
        """Send booking cancellation email and SMS."""
        context = self._build_booking_context(booking, session, contact, studio)
        context['refund_amount'] = refund_amount
        context['refund_message'] = f"Refund of ₹{refund_amount} will be processed in 5-7 days." if refund_amount > 0 else ""
        
        # Send email
        if contact.email:
            try:
                html = render_template_string(BOOKING_CANCELLATION_EMAIL, **context)
                self.email_provider.send(
                    to_email=contact.email,
                    to_name=f"{contact.first_name} {contact.last_name}",
                    subject=f"Booking Cancelled - #{booking.booking_number}",
                    html=html
                )
                logger.info(f"Sent cancellation email to {contact.email}")
            except Exception as e:
                logger.error(f"Failed to send cancellation email: {e}")
        
        # Send SMS
        if contact.phone:
            try:
                sms_text = SMS_TEMPLATES['booking_cancellation'].format(**context)
                self.sms_provider.send(contact.phone, sms_text)
                logger.info(f"Sent cancellation SMS to {contact.phone}")
            except Exception as e:
                logger.error(f"Failed to send cancellation SMS: {e}")
    
    def send_booking_reminder(self, booking, session, contact, studio, reminder_time="tomorrow"):
        """Send booking reminder email and SMS."""
        context = self._build_booking_context(booking, session, contact, studio)
        context['reminder_time'] = reminder_time
        
        # Send email
        if contact.email:
            try:
                html = render_template_string(BOOKING_REMINDER_EMAIL, **context)
                self.email_provider.send(
                    to_email=contact.email,
                    to_name=f"{contact.first_name} {contact.last_name}",
                    subject=f"Reminder: {context['class_name']} {reminder_time}",
                    html=html
                )
                logger.info(f"Sent reminder email to {contact.email}")
            except Exception as e:
                logger.error(f"Failed to send reminder email: {e}")
        
        # Send SMS
        if contact.phone:
            try:
                sms_text = SMS_TEMPLATES['booking_reminder'].format(**context)
                self.sms_provider.send(contact.phone, sms_text)
                logger.info(f"Sent reminder SMS to {contact.phone}")
            except Exception as e:
                logger.error(f"Failed to send reminder SMS: {e}")
    
    def send_waitlist_notification(self, waitlist_entry, session, contact, studio, booking_url):
        """Send waitlist spot available notification."""
        context = self._build_booking_context(None, session, contact, studio)
        context['booking_url'] = booking_url
        
        # Send email
        if contact.email:
            try:
                html = render_template_string(WAITLIST_NOTIFICATION_EMAIL, **context)
                self.email_provider.send(
                    to_email=contact.email,
                    to_name=f"{contact.first_name} {contact.last_name}",
                    subject=f"🎉 Spot Available - {context['class_name']}!",
                    html=html
                )
                logger.info(f"Sent waitlist notification email to {contact.email}")
            except Exception as e:
                logger.error(f"Failed to send waitlist notification email: {e}")
        
        # Send SMS
        if contact.phone:
            try:
                sms_text = SMS_TEMPLATES['waitlist_notification'].format(**context)
                self.sms_provider.send(contact.phone, sms_text)
                logger.info(f"Sent waitlist notification SMS to {contact.phone}")
            except Exception as e:
                logger.error(f"Failed to send waitlist notification SMS: {e}")
    
    def send_class_update_notification(self, contact, class_name, changes, new_date, new_time, studio):
        """Send class update notification to booked customers."""
        context = {
            'contact_name': contact.name or 'there',
            'class_name': class_name,
            'changes': ', '.join(changes),
            'new_date': new_date.strftime('%A, %B %d, %Y') if new_date else 'TBA',
            'new_time': new_time.strftime('%I:%M %p') if new_time else 'TBA',
            'studio_name': studio.name if studio else 'Studio'
        }
        
        # Send email
        if contact.email:
            try:
                html = f"""
                <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2>Class Update Notice</h2>
                    <p>Hi {context['contact_name']},</p>
                    <p>Your upcoming class <strong>{context['class_name']}</strong> has been updated:</p>
                    <p><strong>Changes:</strong> {context['changes']}</p>
                    <p><strong>New Date:</strong> {context['new_date']}<br>
                    <strong>New Time:</strong> {context['new_time']}</p>
                    <p>If you can no longer attend, please cancel your booking.</p>
                    <p>Thank you,<br>{context['studio_name']} Team</p>
                </body>
                </html>
                """
                if self.email_provider:
                    self.email_provider.send(
                        to_email=contact.email,
                        to_name=contact.name or 'Customer',
                        subject=f"Class Update: {class_name}",
                        html=html
                    )
                logger.info(f"Sent class update email to {contact.email}")
            except Exception as e:
                logger.error(f"Failed to send class update email: {e}")
        
        # Send SMS
        if contact.phone and self.sms_provider:
            try:
                sms_text = f"Hi {context['contact_name']}, your {class_name} class has been updated: {context['changes']}. New time: {context['new_date']} at {context['new_time']}. - {context['studio_name']}"
                self.sms_provider.send(contact.phone, sms_text)
                logger.info(f"Sent class update SMS to {contact.phone}")
            except Exception as e:
                logger.error(f"Failed to send class update SMS: {e}")
    
    def send_class_cancellation_notification(self, contact, class_name, session_date, session_time, reason, studio):
        """Send class cancellation notification to booked customers."""
        context = {
            'contact_name': contact.name or 'there',
            'class_name': class_name,
            'session_date': session_date.strftime('%A, %B %d, %Y') if session_date else 'TBA',
            'session_time': session_time.strftime('%I:%M %p') if session_time else 'TBA',
            'reason': reason,
            'studio_name': studio.name if studio else 'Studio'
        }
        
        # Send email
        if contact.email:
            try:
                html = f"""
                <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #dc2626;">Class Cancelled</h2>
                    <p>Hi {context['contact_name']},</p>
                    <p>We regret to inform you that the following class has been cancelled:</p>
                    <p><strong>Class:</strong> {context['class_name']}<br>
                    <strong>Date:</strong> {context['session_date']}<br>
                    <strong>Time:</strong> {context['session_time']}</p>
                    <p><strong>Reason:</strong> {context['reason']}</p>
                    <p>Your booking has been automatically cancelled. If you had paid for this class, a refund will be processed.</p>
                    <p>We apologize for any inconvenience and hope to see you at another class soon!</p>
                    <p>Thank you,<br>{context['studio_name']} Team</p>
                </body>
                </html>
                """
                if self.email_provider:
                    self.email_provider.send(
                        to_email=contact.email,
                        to_name=contact.name or 'Customer',
                        subject=f"Class Cancelled: {class_name}",
                        html=html
                    )
                logger.info(f"Sent class cancellation email to {contact.email}")
            except Exception as e:
                logger.error(f"Failed to send class cancellation email: {e}")
        
        # Send SMS
        if contact.phone and self.sms_provider:
            try:
                sms_text = f"Hi {context['contact_name']}, unfortunately your {class_name} class on {context['session_date']} has been cancelled: {context['reason']}. Your booking is automatically cancelled. - {context['studio_name']}"
                self.sms_provider.send(contact.phone, sms_text)
                logger.info(f"Sent class cancellation SMS to {contact.phone}")
            except Exception as e:
                logger.error(f"Failed to send class cancellation SMS: {e}")
    
    def send_payment_confirmation(self, payment, contact, studio):
        """Send payment confirmation SMS."""
        context = {
            'contact_name': contact.first_name,
            'amount': str(payment.amount),
            'description': payment.description or 'Class Booking',
            'transaction_id': payment.razorpay_payment_id or str(payment.id),
            'studio_name': studio.name
        }
        
        if contact.phone:
            try:
                sms_text = SMS_TEMPLATES['payment_confirmation'].format(**context)
                self.sms_provider.send(contact.phone, sms_text)
                logger.info(f"Sent payment confirmation SMS to {contact.phone}")
            except Exception as e:
                logger.error(f"Failed to send payment confirmation SMS: {e}")
    
    def _build_booking_context(self, booking, session, contact, studio):
        """Build template context from booking data."""
        instructor_name = "TBA"
        if session.instructor:
            instructor_name = f"{session.instructor.first_name} {session.instructor.last_name}"
        
        return {
            'contact_name': contact.first_name,
            'booking_number': booking.booking_number if booking else '',
            'class_name': session.title,
            'session_date': session.start_time.strftime('%A, %B %d, %Y'),
            'session_time': session.start_time.strftime('%I:%M %p'),
            'instructor_name': instructor_name,
            'location': session.location or studio.name,
            'amount_paid': str(booking.amount_paid) if booking else '0',
            'studio_name': studio.name,
            'studio_address': studio.settings.get('address', '') if studio.settings else '',
            'studio_phone': studio.phone or '',
            'cancel_url': f"{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/my-bookings",
            'booking_url': f"{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/booking",
        }


class SMTPProvider:
    """SMTP email provider."""
    
    def __init__(self, host, port, username, password, from_email, from_name):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.from_name = from_name
    
    def send(self, to_email, to_name, subject, html, text=None):
        """Send email via SMTP."""
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
        if not self.username or not self.password:
            logger.warning("SMTP credentials not configured, skipping email")
            return
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{self.from_name} <{self.from_email}>"
        msg['To'] = f"{to_name} <{to_email}>"
        
        if text:
            msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        
        with smtplib.SMTP(self.host, self.port) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.sendmail(self.from_email, to_email, msg.as_string())


class SendGridProvider:
    """SendGrid email provider."""
    
    def __init__(self, api_key):
        self.api_key = api_key
    
    def send(self, to_email, to_name, subject, html, text=None):
        """Send email via SendGrid."""
        if not self.api_key:
            logger.warning("SendGrid API key not configured, skipping email")
            return
        
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Email, To, Content
            
            message = Mail(
                from_email=Email("noreply@studio-os.com", "Studio OS"),
                to_emails=To(to_email, to_name),
                subject=subject,
                html_content=Content("text/html", html)
            )
            
            sg = SendGridAPIClient(self.api_key)
            sg.send(message)
        except ImportError:
            logger.error("SendGrid package not installed")
        except Exception as e:
            logger.error(f"SendGrid error: {e}")
            raise


class TwilioProvider:
    """Twilio SMS provider."""
    
    def __init__(self, account_sid, auth_token, from_number):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
    
    def send(self, to_number, message):
        """Send SMS via Twilio."""
        if not self.account_sid or not self.auth_token:
            logger.warning("Twilio credentials not configured, skipping SMS")
            return
        
        try:
            from twilio.rest import Client
            
            client = Client(self.account_sid, self.auth_token)
            client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
        except ImportError:
            logger.error("Twilio package not installed")
        except Exception as e:
            logger.error(f"Twilio error: {e}")
            raise


class MSG91Provider:
    """MSG91 SMS provider (for India)."""
    
    def __init__(self, auth_key, sender_id):
        self.auth_key = auth_key
        self.sender_id = sender_id
    
    def send(self, to_number, message):
        """Send SMS via MSG91."""
        if not self.auth_key:
            logger.warning("MSG91 auth key not configured, skipping SMS")
            return
        
        import requests
        
        # Normalize Indian phone numbers
        if to_number.startswith('+91'):
            to_number = to_number[3:]
        elif to_number.startswith('91'):
            to_number = to_number[2:]
        
        url = "https://api.msg91.com/api/v5/flow/"
        headers = {
            "authkey": self.auth_key,
            "Content-Type": "application/json"
        }
        payload = {
            "sender": self.sender_id,
            "route": "4",  # Transactional
            "country": "91",
            "sms": [{
                "message": message,
                "to": [to_number]
            }]
        }
        
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            raise Exception(f"MSG91 error: {response.text}")


# Global notification service instance
notification_service = NotificationService()


def init_notifications(app):
    """Initialize notification service with Flask app."""
    notification_service.init_app(app)


def send_booking_notification(notification_type: str, **kwargs):
    """
    Convenience function to send booking notifications.
    
    Args:
        notification_type: 'confirmation', 'cancellation', 'reminder', 'waitlist'
        **kwargs: Notification-specific arguments
    """
    handlers = {
        'confirmation': notification_service.send_booking_confirmation,
        'cancellation': notification_service.send_booking_cancellation,
        'reminder': notification_service.send_booking_reminder,
        'waitlist': notification_service.send_waitlist_notification,
        'payment': notification_service.send_payment_confirmation,
    }
    
    handler = handlers.get(notification_type)
    if handler:
        handler(**kwargs)
    else:
        logger.warning(f"Unknown notification type: {notification_type}")

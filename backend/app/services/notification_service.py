"""
Notification service for sending booking confirmations and QR codes.
Supports email (immediate) and WhatsApp (via Twilio, optional).
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Optional
from flask import current_app
import requests


class NotificationService:
    """Service for sending notifications via email and WhatsApp."""
    
    @staticmethod
    def send_booking_confirmation_email(
        to_email: str,
        customer_name: str,
        booking_data: dict,
        pdf_url: Optional[str] = None
    ) -> bool:
        """
        Send booking confirmation email with PDF attachment or link.
        
        Args:
            to_email: Recipient email address
            customer_name: Customer's name
            booking_data: Dictionary with booking details
            pdf_url: URL to download PDF (if available)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            smtp_host = current_app.config.get('SMTP_HOST', 'smtp.gmail.com')
            smtp_port = current_app.config.get('SMTP_PORT', 587)
            smtp_user = current_app.config.get('SMTP_USER', '')
            smtp_pass = current_app.config.get('SMTP_PASS', '')
            
            if not smtp_user or not smtp_pass:
                current_app.logger.warning("SMTP credentials not configured, skipping email")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = to_email
            msg['Subject'] = f"Booking Confirmation - {booking_data.get('booking_number', 'N/A')}"
            
            # HTML email body
            html_body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                             color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .detail-row {{ padding: 10px 0; border-bottom: 1px solid #e5e7eb; }}
                    .label {{ font-weight: bold; color: #4b5563; }}
                    .value {{ color: #111827; }}
                    .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 14px; }}
                    .button {{ display: inline-block; padding: 12px 24px; background: #2563eb; 
                             color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 Booking Confirmed!</h1>
                    </div>
                    <div class="content">
                        <p>Hi {customer_name},</p>
                        <p>Your booking has been confirmed! Here are your details:</p>
                        
                        <div class="detail-row">
                            <span class="label">Booking Number:</span>
                            <span class="value">{booking_data.get('booking_number', 'N/A')}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Studio:</span>
                            <span class="value">{booking_data.get('studio_name', 'N/A')}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Class:</span>
                            <span class="value">{booking_data.get('class_name', 'N/A')}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Date:</span>
                            <span class="value">{booking_data.get('session_date', 'N/A')}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Time:</span>
                            <span class="value">{booking_data.get('session_time', 'N/A')}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Amount Paid:</span>
                            <span class="value">₹{booking_data.get('amount', 0)}</span>
                        </div>
                        
                        {"<p style='margin-top: 20px;'><a href='" + pdf_url + "' class='button'>📥 Download Your Booking Pass (PDF)</a></p>" if pdf_url else ""}
                        
                        <p style="margin-top: 30px;">
                            <strong>Important:</strong> Please show the QR code from your booking pass at the studio entrance.
                        </p>
                        
                        <p>If you have any questions, please contact the studio directly.</p>
                        
                        <p>See you on the dance floor! 💃🕺</p>
                    </div>
                    <div class="footer">
                        <p>Thank you for booking with {booking_data.get('studio_name', 'us')}!</p>
                        <p style="font-size: 12px; color: #9ca3af;">
                            This is an automated message. Please do not reply to this email.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Attach PDF if URL provided and accessible
            if pdf_url:
                try:
                    # Download PDF from S3
                    response = requests.get(pdf_url, timeout=10)
                    if response.status_code == 200:
                        pdf_attachment = MIMEApplication(response.content, _subtype='pdf')
                        pdf_attachment.add_header(
                            'Content-Disposition',
                            'attachment',
                            filename=f"booking_{booking_data.get('booking_number', 'confirmation')}.pdf"
                        )
                        msg.attach(pdf_attachment)
                except Exception as e:
                    current_app.logger.warning(f"Could not attach PDF: {str(e)}")
            
            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            
            current_app.logger.info(f"Booking confirmation email sent to {to_email}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to send booking confirmation email: {str(e)}")
            return False
    
    @staticmethod
    def send_whatsapp_message(
        to_phone: str,
        message: str,
        media_url: Optional[str] = None
    ) -> bool:
        """
        Send WhatsApp message via Twilio (optional - requires Twilio setup).
        
        Args:
            to_phone: Recipient phone number (E.164 format, e.g., +919876543210)
            message: Message text
            media_url: Optional URL to media file (PDF, image, etc.)
            
        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            # Check if Twilio is configured
            twilio_account_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
            twilio_auth_token = current_app.config.get('TWILIO_AUTH_TOKEN')
            twilio_whatsapp_number = current_app.config.get('TWILIO_WHATSAPP_NUMBER')
            
            if not all([twilio_account_sid, twilio_auth_token, twilio_whatsapp_number]):
                current_app.logger.info("Twilio WhatsApp not configured, skipping")
                return False
            
            from twilio.rest import Client
            
            client = Client(twilio_account_sid, twilio_auth_token)
            
            # Ensure phone number has country code
            if not to_phone.startswith('+'):
                to_phone = f"+91{to_phone}"  # Default to India
            
            # Send message
            message_params = {
                'from_': f"whatsapp:{twilio_whatsapp_number}",
                'body': message,
                'to': f"whatsapp:{to_phone}"
            }
            
            if media_url:
                message_params['media_url'] = [media_url]
            
            twilio_message = client.messages.create(**message_params)
            
            current_app.logger.info(f"WhatsApp message sent to {to_phone}, SID: {twilio_message.sid}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to send WhatsApp message: {str(e)}")
            return False
    
    @staticmethod
    def send_booking_confirmation(
        contact_data: dict,
        booking_data: dict,
        pdf_url: Optional[str] = None
    ) -> dict:
        """
        Send booking confirmation via available channels (email and/or WhatsApp).
        
        Args:
            contact_data: Dictionary with 'email', 'phone', 'name'
            booking_data: Dictionary with booking details
            pdf_url: URL to booking confirmation PDF
            
        Returns:
            Dictionary with status: {'email_sent': bool, 'whatsapp_sent': bool}
        """
        result = {
            'email_sent': False,
            'whatsapp_sent': False
        }
        
        # Send email
        if contact_data.get('email'):
            result['email_sent'] = NotificationService.send_booking_confirmation_email(
                to_email=contact_data['email'],
                customer_name=contact_data.get('name', 'Customer'),
                booking_data=booking_data,
                pdf_url=pdf_url
            )
        
        # Send WhatsApp (optional)
        if contact_data.get('phone') and pdf_url:
            whatsapp_message = f"""
🎉 *Booking Confirmed!*

Hi {contact_data.get('name', 'Customer')},

Your booking has been confirmed:

*Booking #:* {booking_data.get('booking_number', 'N/A')}
*Class:* {booking_data.get('class_name', 'N/A')}
*Date:* {booking_data.get('session_date', 'N/A')}
*Time:* {booking_data.get('session_time', 'N/A')}
*Studio:* {booking_data.get('studio_name', 'N/A')}

Please show your QR code at the studio entrance.

See you on the dance floor! 💃🕺
            """.strip()
            
            result['whatsapp_sent'] = NotificationService.send_whatsapp_message(
                to_phone=contact_data['phone'],
                message=whatsapp_message,
                media_url=pdf_url
            )
        
        return result

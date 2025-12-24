import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from flask import current_app
from typing import Optional, List, Dict
import uuid


class EmailService:
    """Service for sending and receiving emails."""
    
    def __init__(self):
        self.smtp_host = current_app.config.get('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = current_app.config.get('SMTP_PORT', 587)
        self.smtp_user = current_app.config.get('SMTP_USER', '')
        self.smtp_pass = current_app.config.get('SMTP_PASS', '')
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        studio_id: Optional[str] = None,
        reply_to: Optional[str] = None,
        attachments: List[Dict] = None
    ) -> Optional[str]:
        """Send an email and return message ID."""
        if not self.smtp_user or not self.smtp_pass:
            current_app.logger.warning("SMTP credentials not configured")
            return None
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_user
            msg['To'] = to_email
            
            if reply_to:
                msg['Reply-To'] = reply_to
            
            # Add message ID for tracking
            message_id = f"<{uuid.uuid4()}@studio-os>"
            msg['Message-ID'] = message_id
            
            # Add plain text and HTML parts
            part1 = MIMEText(body, 'plain')
            msg.attach(part1)
            
            if html_body:
                part2 = MIMEText(html_body, 'html')
                msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)
            
            return message_id
            
        except Exception as e:
            current_app.logger.error(f"Failed to send email: {str(e)}")
            raise
    
    def fetch_emails(
        self,
        imap_host: str,
        imap_user: str,
        imap_pass: str,
        folder: str = 'INBOX',
        since_date: Optional[str] = None,
        unseen_only: bool = True
    ) -> List[Dict]:
        """Fetch emails from IMAP server."""
        emails = []
        
        try:
            # Connect to IMAP
            mail = imaplib.IMAP4_SSL(imap_host)
            mail.login(imap_user, imap_pass)
            mail.select(folder)
            
            # Build search criteria
            criteria = []
            if unseen_only:
                criteria.append('UNSEEN')
            if since_date:
                criteria.append(f'SINCE {since_date}')
            
            search_criteria = ' '.join(criteria) if criteria else 'ALL'
            
            # Search for emails
            _, message_numbers = mail.search(None, search_criteria)
            
            for num in message_numbers[0].split():
                _, data = mail.fetch(num, '(RFC822)')
                
                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Parse email
                email_data = self._parse_email(msg)
                email_data['message_number'] = num.decode()
                emails.append(email_data)
            
            mail.logout()
            
        except Exception as e:
            current_app.logger.error(f"Failed to fetch emails: {str(e)}")
            raise
        
        return emails
    
    def _parse_email(self, msg) -> Dict:
        """Parse an email message into a dictionary."""
        # Decode subject
        subject = ""
        if msg['Subject']:
            decoded = decode_header(msg['Subject'])
            subject = ''.join(
                part.decode(encoding or 'utf-8') if isinstance(part, bytes) else part
                for part, encoding in decoded
            )
        
        # Get sender
        from_header = msg.get('From', '')
        from_name = ""
        from_email = from_header
        
        if '<' in from_header:
            from_name = from_header.split('<')[0].strip().strip('"')
            from_email = from_header.split('<')[1].split('>')[0]
        
        # Get body
        body = ""
        html_body = ""
        attachments = []
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition', ''))
                
                if 'attachment' in content_disposition:
                    filename = part.get_filename()
                    attachments.append({
                        'filename': filename,
                        'content_type': content_type,
                        'size': len(part.get_payload(decode=True) or b'')
                    })
                elif content_type == 'text/plain':
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                elif content_type == 'text/html':
                    html_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
        else:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        return {
            'message_id': msg.get('Message-ID', ''),
            'subject': subject,
            'from_name': from_name,
            'from_email': from_email,
            'to': msg.get('To', ''),
            'date': msg.get('Date', ''),
            'body': body,
            'html_body': html_body,
            'attachments': attachments,
            'in_reply_to': msg.get('In-Reply-To', ''),
            'references': msg.get('References', '')
        }
    
    def mark_as_read(
        self,
        imap_host: str,
        imap_user: str,
        imap_pass: str,
        message_number: str,
        folder: str = 'INBOX'
    ) -> bool:
        """Mark an email as read."""
        try:
            mail = imaplib.IMAP4_SSL(imap_host)
            mail.login(imap_user, imap_pass)
            mail.select(folder)
            mail.store(message_number.encode(), '+FLAGS', '\\Seen')
            mail.logout()
            return True
        except Exception as e:
            current_app.logger.error(f"Failed to mark email as read: {str(e)}")
            return False

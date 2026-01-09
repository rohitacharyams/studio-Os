"""
Email integration routes - supports Demo mode, Simple SMTP, and Gmail OAuth.
Includes AI-powered email processing and auto-reply.
"""
import os
import uuid
import json
import imaplib
import smtplib
import email as email_lib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, redirect, url_for, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Studio, Contact, Conversation, Message, StudioKnowledge, DanceClass

email_bp = Blueprint('email', __name__, url_prefix='/api/email')


def is_demo_mode():
    """Check if email is in demo mode (no real email configured)."""
    return os.getenv('EMAIL_MODE', 'demo') == 'demo'


# Demo email storage (in-memory for testing)
_demo_emails = []


@email_bp.route('/status', methods=['GET'])
@jwt_required()
def email_status():
    """Get email connection status for the studio."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    studio = Studio.query.get(user.studio_id)
    email_settings = studio.email_settings or {}
    
    demo_mode = is_demo_mode()
    connected = email_settings.get('connected', False)
    
    return jsonify({
        'demo_mode': demo_mode,
        'connected': connected or demo_mode,
        'provider': email_settings.get('provider', 'demo' if demo_mode else None),
        'email': email_settings.get('email', 'demo@yourstudio.com' if demo_mode else None),
        'message': 'Demo mode - emails are simulated' if demo_mode else (
            'Email connected' if connected else 'Email not configured'
        ),
        'setup_options': [
            {
                'id': 'demo',
                'name': 'Demo Mode',
                'description': 'Test email features without setup',
                'difficulty': 'None',
                'recommended': True
            },
            {
                'id': 'gmail_app_password',
                'name': 'Gmail with App Password',
                'description': 'Use Gmail with a secure app password',
                'difficulty': 'Easy (5 mins)',
                'setup_url': 'https://myaccount.google.com/apppasswords'
            },
            {
                'id': 'custom_smtp',
                'name': 'Custom SMTP',
                'description': 'Use any email provider with SMTP',
                'difficulty': 'Medium'
            }
        ]
    })


@email_bp.route('/connect/demo', methods=['POST'])
@jwt_required()
def connect_demo():
    """Enable demo mode for email - no setup required."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    studio = Studio.query.get(user.studio_id)
    
    # Set demo email settings
    studio.email_settings = {
        'connected': True,
        'provider': 'demo',
        'email': f'demo@{studio.slug or "studio"}.com',
        'demo_mode': True,
        'connected_at': datetime.utcnow().isoformat()
    }
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Demo email mode enabled! You can now test all email features.',
        'email': studio.email_settings['email'],
        'demo_mode': True
    })


@email_bp.route('/connect/gmail', methods=['POST'])
@jwt_required()
def connect_gmail():
    """Connect Gmail using App Password (simpler than OAuth)."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    email_address = data.get('email')
    app_password = data.get('app_password')
    
    if not email_address or not app_password:
        return jsonify({'error': 'Email and app password are required'}), 400
    
    # Validate it's a Gmail address
    if not email_address.endswith('@gmail.com') and not email_address.endswith('@googlemail.com'):
        return jsonify({'error': 'Please use a Gmail address (@gmail.com)'}), 400
    
    # Test the connection
    import smtplib
    try:
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
            server.starttls()
            server.login(email_address, app_password)
        
        # Connection successful - save settings
        studio = Studio.query.get(user.studio_id)
        studio.email_settings = {
            'connected': True,
            'provider': 'gmail',
            'email': email_address,
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 587,
            'imap_host': 'imap.gmail.com',
            'imap_port': 993,
            # Store encrypted in production
            'credentials': {
                'email': email_address,
                'app_password': app_password  # In production, encrypt this!
            },
            'connected_at': datetime.utcnow().isoformat()
        }
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Gmail connected successfully!',
            'email': email_address
        })
        
    except smtplib.SMTPAuthenticationError:
        return jsonify({
            'error': 'Authentication failed. Please check your email and app password.',
            'help': 'Make sure you created an App Password at https://myaccount.google.com/apppasswords'
        }), 401
    except Exception as e:
        return jsonify({
            'error': f'Connection failed: {str(e)}',
            'help': 'Check your internet connection and try again.'
        }), 500


@email_bp.route('/connect/smtp', methods=['POST'])
@jwt_required()
def connect_custom_smtp():
    """Connect using custom SMTP settings."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    required = ['smtp_host', 'smtp_port', 'email', 'password']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Test the connection
    import smtplib
    try:
        with smtplib.SMTP(data['smtp_host'], int(data['smtp_port']), timeout=10) as server:
            server.starttls()
            server.login(data['email'], data['password'])
        
        # Connection successful - save settings
        studio = Studio.query.get(user.studio_id)
        studio.email_settings = {
            'connected': True,
            'provider': 'custom_smtp',
            'email': data['email'],
            'smtp_host': data['smtp_host'],
            'smtp_port': int(data['smtp_port']),
            'imap_host': data.get('imap_host', ''),
            'imap_port': int(data.get('imap_port', 993)),
            'credentials': {
                'email': data['email'],
                'password': data['password']  # In production, encrypt this!
            },
            'connected_at': datetime.utcnow().isoformat()
        }
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Email connected successfully!',
            'email': data['email']
        })
        
    except smtplib.SMTPAuthenticationError:
        return jsonify({'error': 'Authentication failed'}), 401
    except Exception as e:
        return jsonify({'error': f'Connection failed: {str(e)}'}), 500


@email_bp.route('/disconnect', methods=['POST'])
@jwt_required()
def disconnect_email():
    """Disconnect email integration."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    studio = Studio.query.get(user.studio_id)
    studio.email_settings = {
        'connected': False,
        'provider': None,
        'email': None,
        'disconnected_at': datetime.utcnow().isoformat()
    }
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Email disconnected'
    })


@email_bp.route('/send', methods=['POST'])
@jwt_required()
def send_email():
    """Send an email (works in demo mode too)."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    to_email = data.get('to')
    subject = data.get('subject')
    body = data.get('body')
    contact_id = data.get('contact_id')
    
    if not to_email or not subject or not body:
        return jsonify({'error': 'to, subject, and body are required'}), 400
    
    studio = Studio.query.get(user.studio_id)
    email_settings = studio.email_settings or {}
    
    # Demo mode - simulate sending
    if email_settings.get('demo_mode') or email_settings.get('provider') == 'demo':
        message_id = f"<demo_{uuid.uuid4().hex[:12]}@studio-os>"
        
        # Store in demo storage
        demo_email = {
            'id': message_id,
            'studio_id': user.studio_id,
            'from': email_settings.get('email', 'demo@studio.com'),
            'to': to_email,
            'subject': subject,
            'body': body,
            'sent_at': datetime.utcnow().isoformat(),
            'status': 'sent'
        }
        _demo_emails.append(demo_email)
        
        # Create message record if contact provided
        if contact_id:
            contact = Contact.query.filter_by(id=contact_id, studio_id=user.studio_id).first()
            if contact:
                # Get or create conversation
                conversation = Conversation.query.filter_by(
                    studio_id=user.studio_id,
                    contact_id=contact_id,
                    channel='EMAIL'
                ).first()
                
                if not conversation:
                    conversation = Conversation(
                        id=str(uuid.uuid4()),
                        studio_id=user.studio_id,
                        contact_id=contact_id,
                        channel='EMAIL',
                        status='OPEN'
                    )
                    db.session.add(conversation)
                    db.session.flush()
                
                message = Message(
                    id=str(uuid.uuid4()),
                    conversation_id=conversation.id,
                    direction='OUTBOUND',
                    content=f"**{subject}**\n\n{body}",
                    message_type='email',
                    status='SENT',
                    metadata={'email_id': message_id, 'subject': subject}
                )
                db.session.add(message)
                db.session.commit()
        
        return jsonify({
            'success': True,
            'message_id': message_id,
            'demo_mode': True,
            'note': 'Email simulated in demo mode'
        })
    
    # Real email sending
    if not email_settings.get('connected'):
        return jsonify({'error': 'Email not configured'}), 400
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        creds = email_settings.get('credentials', {})
        
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = creds.get('email', email_settings.get('email'))
        msg['To'] = to_email
        
        message_id = f"<{uuid.uuid4()}@studio-os>"
        msg['Message-ID'] = message_id
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(email_settings['smtp_host'], email_settings['smtp_port'], timeout=30) as server:
            server.starttls()
            server.login(creds.get('email'), creds.get('password') or creds.get('app_password'))
            server.send_message(msg)
        
        return jsonify({
            'success': True,
            'message_id': message_id
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to send: {str(e)}'}), 500


@email_bp.route('/inbox', methods=['GET'])
@jwt_required()
def get_inbox():
    """Get inbox emails (demo mode returns simulated emails)."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    studio = Studio.query.get(user.studio_id)
    email_settings = studio.email_settings or {}
    
    # Demo mode - return demo emails
    if email_settings.get('demo_mode') or email_settings.get('provider') == 'demo':
        # Generate some demo inbox emails
        demo_inbox = [
            {
                'id': 'demo_1',
                'from': 'john@example.com',
                'from_name': 'John Smith',
                'subject': 'Class Schedule Inquiry',
                'preview': 'Hi, I would like to know about your dance class schedules...',
                'date': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                'unread': True
            },
            {
                'id': 'demo_2',
                'from': 'sarah@example.com',
                'from_name': 'Sarah Johnson',
                'subject': 'Re: Membership Question',
                'preview': 'Thank you for the information about monthly memberships...',
                'date': (datetime.utcnow() - timedelta(hours=5)).isoformat(),
                'unread': False
            },
            {
                'id': 'demo_3',
                'from': 'mike@example.com',
                'from_name': 'Mike Davis',
                'subject': 'Birthday Party Booking',
                'preview': 'I want to book your studio for my daughter\'s birthday party...',
                'date': (datetime.utcnow() - timedelta(days=1)).isoformat(),
                'unread': True
            }
        ]
        
        # Add any sent demo emails
        studio_emails = [e for e in _demo_emails if e.get('studio_id') == user.studio_id]
        
        return jsonify({
            'emails': demo_inbox,
            'sent': studio_emails,
            'total': len(demo_inbox),
            'unread': sum(1 for e in demo_inbox if e.get('unread')),
            'demo_mode': True
        })
    
    # Real IMAP fetch would go here
    # For now, return empty if not in demo mode
    return jsonify({
        'emails': [],
        'total': 0,
        'unread': 0,
        'message': 'Connect email to see your inbox'
    })


@email_bp.route('/test', methods=['POST'])
@jwt_required()
def test_email():
    """Send a test email to verify configuration."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    studio = Studio.query.get(user.studio_id)
    email_settings = studio.email_settings or {}
    
    if not email_settings.get('connected'):
        return jsonify({'error': 'Email not configured'}), 400
    
    # Send test email to self
    test_email_address = email_settings.get('email') or email_settings.get('credentials', {}).get('email')
    
    if email_settings.get('demo_mode'):
        return jsonify({
            'success': True,
            'message': 'Test email sent successfully (demo mode)',
            'demo_mode': True
        })
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        
        creds = email_settings.get('credentials', {})
        
        msg = MIMEText(f'''
This is a test email from Studio OS.

Your email integration is working correctly!

Studio: {studio.name}
Connected at: {email_settings.get('connected_at', 'Unknown')}
Provider: {email_settings.get('provider', 'Unknown')}

Best regards,
Studio OS Team
        ''')
        
        msg['Subject'] = '✅ Studio OS - Email Test Successful'
        msg['From'] = test_email_address
        msg['To'] = test_email_address
        
        with smtplib.SMTP(email_settings['smtp_host'], email_settings['smtp_port'], timeout=30) as server:
            server.starttls()
            server.login(creds.get('email'), creds.get('password') or creds.get('app_password'))
            server.send_message(msg)
        
        return jsonify({
            'success': True,
            'message': f'Test email sent to {test_email_address}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to send test email: {str(e)}'
        }), 500


# ============================================================
# AI EMAIL PROCESSING - Fetch, Parse & Auto-Reply
# ============================================================

def fetch_emails_from_gmail(email_settings: dict, unseen_only: bool = True, limit: int = 10) -> list:
    """Fetch emails from Gmail via IMAP."""
    creds = email_settings.get('credentials', {})
    imap_host = email_settings.get('imap_host', 'imap.gmail.com')
    imap_port = email_settings.get('imap_port', 993)
    
    emails = []
    
    try:
        mail = imaplib.IMAP4_SSL(imap_host, imap_port)
        mail.login(creds.get('email'), creds.get('password') or creds.get('app_password'))
        mail.select('INBOX')
        
        # Search criteria
        criteria = 'UNSEEN' if unseen_only else 'ALL'
        _, message_numbers = mail.search(None, criteria)
        
        email_ids = message_numbers[0].split()
        # Get most recent emails up to limit
        email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
        
        for num in email_ids:
            _, data = mail.fetch(num, '(RFC822)')
            raw_email = data[0][1]
            msg = email_lib.message_from_bytes(raw_email)
            
            # Parse subject
            subject = ""
            if msg['Subject']:
                decoded = decode_header(msg['Subject'])
                subject = ''.join(
                    part.decode(encoding or 'utf-8') if isinstance(part, bytes) else part
                    for part, encoding in decoded
                )
            
            # Parse sender
            from_header = msg.get('From', '')
            from_name = ""
            from_email = from_header
            if '<' in from_header:
                from_name = from_header.split('<')[0].strip().strip('"')
                from_email = from_header.split('<')[1].split('>')[0]
            
            # Parse body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == 'text/plain':
                        try:
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        except:
                            pass
                        break
            else:
                try:
                    body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    pass
            
            emails.append({
                'id': num.decode(),
                'message_id': msg.get('Message-ID', ''),
                'subject': subject,
                'from_name': from_name,
                'from_email': from_email,
                'body': body[:2000],  # Limit body length
                'date': msg.get('Date', ''),
                'in_reply_to': msg.get('In-Reply-To', '')
            })
        
        mail.logout()
        
    except Exception as e:
        current_app.logger.error(f"IMAP fetch error: {str(e)}")
        raise
    
    return emails


def generate_ai_reply(studio: Studio, email_data: dict) -> str:
    """Use LLM to generate a reply to an inquiry email."""
    from app.llm import get_llm_provider
    from app.llm.base import LLMMessage
    import asyncio
    
    # Gather studio context
    knowledge_items = StudioKnowledge.query.filter_by(
        studio_id=studio.id,
        is_active=True
    ).all()
    
    knowledge_text = ""
    if knowledge_items:
        knowledge_text = "\n".join([
            f"- {item.title}: {item.content}" for item in knowledge_items[:10]
        ])
    
    classes = DanceClass.query.filter_by(studio_id=studio.id, is_active=True).all()
    classes_text = ""
    if classes:
        classes_text = "\n".join([
            f"- {c.name}: {c.dance_style or 'General'}, ₹{c.price or 0}, {c.duration_minutes or 60} mins, Level: {c.level or 'All'}"
            for c in classes[:10]
        ])
    
    system_prompt = f"""You are an AI assistant for {studio.name}, a dance studio.
Your job is to write helpful, professional email replies to customer inquiries.

STUDIO INFORMATION:
- Name: {studio.name}
- Email: {studio.email}
- Phone: {studio.phone or 'Contact us for phone'}
- Address: {studio.address or 'Contact us for address'}
- City: {studio.city or ''}
- Website: {studio.website or ''}

CLASSES OFFERED:
{classes_text if classes_text else 'Various dance classes available - contact us for details'}

KNOWLEDGE BASE:
{knowledge_text if knowledge_text else 'Contact us for more information'}

GUIDELINES:
- Write a professional, friendly email reply
- Address the customer by name if available
- Answer their specific questions based on the studio information
- If you don't have specific information, politely suggest they contact the studio
- Include relevant class or pricing information if asked
- Sign off as "{studio.name} Team"
- Keep the reply concise but helpful (2-4 paragraphs)
- Don't make up information not provided above
"""

    user_prompt = f"""Please write a reply to this email:

FROM: {email_data.get('from_name', '')} <{email_data.get('from_email', '')}>
SUBJECT: {email_data.get('subject', '')}

{email_data.get('body', '')}
"""

    messages = [
        LLMMessage(role='system', content=system_prompt),
        LLMMessage(role='user', content=user_prompt)
    ]
    
    try:
        provider = get_llm_provider(
            provider='groq',
            model='llama-3.3-70b-versatile',
            temperature=0.7,
            max_tokens=800
        )
        
        # Run async in sync context
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        response = loop.run_until_complete(provider.chat(messages))
        return response.content
        
    except Exception as e:
        current_app.logger.error(f"AI reply generation error: {str(e)}")
        return None


def send_reply_email(email_settings: dict, to_email: str, subject: str, body: str, in_reply_to: str = None) -> bool:
    """Send a reply email via SMTP."""
    creds = email_settings.get('credentials', {})
    from_email = creds.get('email')
    
    try:
        msg = MIMEMultipart()
        msg['Subject'] = f"Re: {subject}" if not subject.startswith('Re:') else subject
        msg['From'] = from_email
        msg['To'] = to_email
        
        if in_reply_to:
            msg['In-Reply-To'] = in_reply_to
            msg['References'] = in_reply_to
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(email_settings['smtp_host'], email_settings['smtp_port'], timeout=30) as server:
            server.starttls()
            server.login(from_email, creds.get('password') or creds.get('app_password'))
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        current_app.logger.error(f"Failed to send reply: {str(e)}")
        return False


@email_bp.route('/fetch-new', methods=['POST'])
@jwt_required()
def fetch_new_emails():
    """Fetch new unread emails from connected Gmail."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    studio = Studio.query.get(user.studio_id)
    email_settings = studio.email_settings or {}
    
    if not email_settings.get('connected') or email_settings.get('provider') == 'demo':
        return jsonify({'error': 'Gmail not connected. Please connect your Gmail first.'}), 400
    
    try:
        emails = fetch_emails_from_gmail(email_settings, unseen_only=True, limit=10)
        
        return jsonify({
            'success': True,
            'count': len(emails),
            'emails': emails
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch emails: {str(e)}'}), 500


@email_bp.route('/process-inquiry', methods=['POST'])
@jwt_required()
def process_email_inquiry():
    """
    Process a single email inquiry with AI:
    1. Parse the email
    2. Generate AI response
    3. Optionally auto-send the reply
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    email_data = data.get('email')
    auto_send = data.get('auto_send', False)
    
    if not email_data:
        return jsonify({'error': 'email data is required'}), 400
    
    studio = Studio.query.get(user.studio_id)
    email_settings = studio.email_settings or {}
    
    # Generate AI reply
    ai_reply = generate_ai_reply(studio, email_data)
    
    if not ai_reply:
        return jsonify({'error': 'Failed to generate AI reply'}), 500
    
    result = {
        'success': True,
        'original_email': {
            'from': email_data.get('from_email'),
            'from_name': email_data.get('from_name'),
            'subject': email_data.get('subject'),
            'body_preview': email_data.get('body', '')[:500]
        },
        'ai_reply': ai_reply,
        'sent': False
    }
    
    # Auto-send if requested and email is connected
    if auto_send and email_settings.get('connected') and email_settings.get('provider') != 'demo':
        sent = send_reply_email(
            email_settings,
            to_email=email_data.get('from_email'),
            subject=email_data.get('subject', ''),
            body=ai_reply,
            in_reply_to=email_data.get('message_id')
        )
        result['sent'] = sent
        result['message'] = 'Reply sent successfully!' if sent else 'Failed to send reply'
    
    # Create/update contact and conversation
    contact = Contact.query.filter_by(
        studio_id=studio.id,
        email=email_data.get('from_email')
    ).first()
    
    if not contact:
        contact = Contact(
            id=str(uuid.uuid4()),
            studio_id=studio.id,
            name=email_data.get('from_name') or email_data.get('from_email').split('@')[0],
            email=email_data.get('from_email'),
            lead_source='EMAIL',
            lead_status='NEW'
        )
        db.session.add(contact)
        db.session.flush()
    
    # Create conversation
    conversation = Conversation.query.filter_by(
        studio_id=studio.id,
        contact_id=contact.id,
        channel='EMAIL'
    ).first()
    
    if not conversation:
        conversation = Conversation(
            id=str(uuid.uuid4()),
            studio_id=studio.id,
            contact_id=contact.id,
            channel='EMAIL',
            status='OPEN'
        )
        db.session.add(conversation)
        db.session.flush()
    
    # Add incoming message
    incoming_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        direction='INBOUND',
        content=f"**{email_data.get('subject', 'No Subject')}**\n\n{email_data.get('body', '')}",
        message_type='email',
        status='RECEIVED',
        metadata={'email_id': email_data.get('message_id'), 'subject': email_data.get('subject')}
    )
    db.session.add(incoming_msg)
    
    # Add AI reply as outbound message
    outbound_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        direction='OUTBOUND',
        content=ai_reply,
        message_type='email',
        status='SENT' if result['sent'] else 'DRAFT',
        metadata={'ai_generated': True, 'auto_sent': auto_send}
    )
    db.session.add(outbound_msg)
    
    db.session.commit()
    
    result['contact_id'] = contact.id
    result['conversation_id'] = conversation.id
    
    return jsonify(result)


@email_bp.route('/process-all', methods=['POST'])
@jwt_required()
def process_all_new_emails():
    """
    Fetch all new emails and process them with AI.
    Returns AI-generated replies for review (doesn't auto-send by default).
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json() or {}
    auto_send = data.get('auto_send', False)
    
    studio = Studio.query.get(user.studio_id)
    email_settings = studio.email_settings or {}
    
    if not email_settings.get('connected') or email_settings.get('provider') == 'demo':
        # Demo mode - process demo emails
        demo_results = [
            {
                'email': {
                    'from_email': 'john@example.com',
                    'from_name': 'John Smith',
                    'subject': 'Class Schedule Inquiry',
                    'body': 'Hi, I would like to know about your dance class schedules. Do you offer beginner salsa classes? What are the timings and fees?'
                },
                'ai_reply': f"Dear John,\n\nThank you for your interest in {studio.name}!\n\nWe'd be happy to help you with our class schedules. We offer various dance classes including beginner-friendly options.\n\nPlease visit our studio or contact us at {studio.email} to get the latest schedule and discuss which classes would be best for you.\n\nWe look forward to welcoming you!\n\nBest regards,\n{studio.name} Team",
                'sent': False,
                'demo': True
            }
        ]
        return jsonify({
            'success': True,
            'demo_mode': True,
            'processed': len(demo_results),
            'results': demo_results
        })
    
    try:
        # Fetch new emails
        emails = fetch_emails_from_gmail(email_settings, unseen_only=True, limit=10)
        
        results = []
        for email_data in emails:
            # Generate AI reply
            ai_reply = generate_ai_reply(studio, email_data)
            
            result = {
                'email': {
                    'id': email_data.get('id'),
                    'from_email': email_data.get('from_email'),
                    'from_name': email_data.get('from_name'),
                    'subject': email_data.get('subject'),
                    'body_preview': email_data.get('body', '')[:300]
                },
                'ai_reply': ai_reply,
                'sent': False
            }
            
            # Auto-send if requested
            if auto_send and ai_reply:
                sent = send_reply_email(
                    email_settings,
                    to_email=email_data.get('from_email'),
                    subject=email_data.get('subject', ''),
                    body=ai_reply,
                    in_reply_to=email_data.get('message_id')
                )
                result['sent'] = sent
            
            results.append(result)
        
        return jsonify({
            'success': True,
            'processed': len(results),
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to process emails: {str(e)}'}), 500


@email_bp.route('/send-reply', methods=['POST'])
@jwt_required()
def send_email_reply():
    """Send a reply to an email (after reviewing AI draft)."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    to_email = data.get('to_email')
    subject = data.get('subject')
    body = data.get('body')
    in_reply_to = data.get('in_reply_to')
    
    if not to_email or not body:
        return jsonify({'error': 'to_email and body are required'}), 400
    
    studio = Studio.query.get(user.studio_id)
    email_settings = studio.email_settings or {}
    
    if not email_settings.get('connected') or email_settings.get('provider') == 'demo':
        return jsonify({
            'success': True,
            'message': 'Reply sent (demo mode)',
            'demo_mode': True
        })
    
    sent = send_reply_email(email_settings, to_email, subject or '', body, in_reply_to)
    
    if sent:
        return jsonify({
            'success': True,
            'message': f'Reply sent to {to_email}'
        })
    else:
        return jsonify({'error': 'Failed to send reply'}), 500

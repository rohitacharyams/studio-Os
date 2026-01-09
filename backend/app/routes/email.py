"""
Email integration routes - supports Demo mode, Simple SMTP, and Gmail OAuth.
"""
import os
import uuid
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, redirect, url_for, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Studio, Contact, Conversation, Message

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

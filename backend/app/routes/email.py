"""
Email integration routes - supports Demo mode, Simple SMTP, Gmail App Password, and Gmail OAuth.
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
from flask import Blueprint, request, jsonify, redirect, url_for, current_app, session
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Studio, Contact, Conversation, Message, StudioKnowledge, DanceClass
import base64

# Google OAuth imports
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request
    GOOGLE_OAUTH_AVAILABLE = True
except ImportError:
    GOOGLE_OAUTH_AVAILABLE = False

email_bp = Blueprint('email', __name__, url_prefix='/api/email')

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'https://studioos-api.azurewebsites.net/api/email/oauth/google/callback')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://dance-studio-os.netlify.app')

# Gmail API Scopes - read, send, and modify emails
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]


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
    
    # Check if OAuth is available
    oauth_available = GOOGLE_OAUTH_AVAILABLE and bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)
    
    setup_options = []
    
    # Gmail OAuth - the easiest option (if configured)
    if oauth_available:
        setup_options.append({
            'id': 'gmail_oauth',
            'name': 'Connect with Google',
            'description': 'One-click sign in with your Gmail account',
            'difficulty': 'Easiest (1 click)',
            'recommended': True
        })
    
    # Other options
    setup_options.extend([
        {
            'id': 'demo',
            'name': 'Demo Mode',
            'description': 'Test email features without setup',
            'difficulty': 'None',
            'recommended': not oauth_available
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
    ])
    
    return jsonify({
        'demo_mode': demo_mode,
        'connected': connected or demo_mode,
        'provider': email_settings.get('provider', 'demo' if demo_mode else None),
        'email': email_settings.get('email', 'demo@yourstudio.com' if demo_mode else None),
        'message': 'Demo mode - emails are simulated' if demo_mode else (
            'Email connected' if connected else 'Email not configured'
        ),
        'oauth_available': oauth_available,
        'setup_options': setup_options
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


# ============================================
# GMAIL OAUTH 2.0 - One-Click Gmail Connection
# ============================================

# Store pending OAuth states (in production, use Redis/DB)
_oauth_states = {}


@email_bp.route('/oauth/google/init', methods=['POST'])
@jwt_required()
def init_google_oauth():
    """
    Initialize Google OAuth flow.
    Returns a URL to redirect the user to Google's consent screen.
    """
    if not GOOGLE_OAUTH_AVAILABLE:
        return jsonify({
            'error': 'Google OAuth libraries not installed',
            'fallback': 'Use Gmail App Password instead'
        }), 501
    
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return jsonify({
            'error': 'Google OAuth not configured on server',
            'message': 'Please use Gmail App Password method or contact support',
            'fallback_method': 'gmail_app_password'
        }), 501
    
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Create OAuth flow
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [GOOGLE_REDIRECT_URI]
            }
        },
        scopes=GMAIL_SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI
    )
    
    # Generate authorization URL
    authorization_url, state = flow.authorization_url(
        access_type='offline',  # Get refresh token
        include_granted_scopes='true',
        prompt='consent'  # Force consent to ensure refresh token
    )
    
    # Store state with user info (for callback)
    _oauth_states[state] = {
        'user_id': user_id,
        'studio_id': user.studio_id,
        'created_at': datetime.utcnow().isoformat()
    }
    
    return jsonify({
        'success': True,
        'authorization_url': authorization_url,
        'state': state,
        'message': 'Redirect user to authorization_url to grant Gmail access'
    })


@email_bp.route('/oauth/google/callback', methods=['GET'])
def google_oauth_callback():
    """
    Handle Google OAuth callback.
    Google redirects here after user grants permission.
    """
    if not GOOGLE_OAUTH_AVAILABLE:
        return redirect(f"{FRONTEND_URL}/settings?error=oauth_not_available")
    
    error = request.args.get('error')
    if error:
        return redirect(f"{FRONTEND_URL}/settings?error={error}&message=Gmail connection cancelled")
    
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code or not state:
        return redirect(f"{FRONTEND_URL}/settings?error=missing_params")
    
    # Verify state
    state_data = _oauth_states.get(state)
    if not state_data:
        return redirect(f"{FRONTEND_URL}/settings?error=invalid_state&message=Session expired, please try again")
    
    # Clean up state
    del _oauth_states[state]
    
    user_id = state_data['user_id']
    studio_id = state_data['studio_id']
    
    try:
        # Exchange code for tokens
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [GOOGLE_REDIRECT_URI]
                }
            },
            scopes=GMAIL_SCOPES,
            redirect_uri=GOOGLE_REDIRECT_URI
        )
        
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Get user's email from Google
        from googleapiclient.discovery import build
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        user_email = user_info.get('email')
        
        # Save credentials to studio
        studio = Studio.query.get(studio_id)
        if not studio:
            return redirect(f"{FRONTEND_URL}/settings?error=studio_not_found")
        
        studio.email_settings = {
            'connected': True,
            'provider': 'gmail_oauth',
            'email': user_email,
            'oauth_credentials': {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': GOOGLE_CLIENT_ID,
                'client_secret': GOOGLE_CLIENT_SECRET,
                'scopes': list(credentials.scopes) if credentials.scopes else GMAIL_SCOPES
            },
            'connected_at': datetime.utcnow().isoformat()
        }
        
        db.session.commit()
        
        # Redirect to frontend with success
        return redirect(f"{FRONTEND_URL}/settings?email_connected=true&email={user_email}&provider=gmail")
        
    except Exception as e:
        current_app.logger.error(f"Gmail OAuth error: {str(e)}")
        return redirect(f"{FRONTEND_URL}/settings?error=oauth_failed&message={str(e)}")


@email_bp.route('/oauth/google/status', methods=['GET'])
@jwt_required()
def google_oauth_status():
    """Check if Google OAuth is configured and available."""
    return jsonify({
        'oauth_available': GOOGLE_OAUTH_AVAILABLE,
        'oauth_configured': bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET),
        'message': 'Google OAuth is ready' if (GOOGLE_OAUTH_AVAILABLE and GOOGLE_CLIENT_ID) else 'Use Gmail App Password instead'
    })


def get_gmail_service(email_settings):
    """
    Get Gmail API service using stored OAuth credentials.
    Automatically refreshes tokens if needed.
    """
    if not GOOGLE_OAUTH_AVAILABLE:
        return None
    
    oauth_creds = email_settings.get('oauth_credentials')
    if not oauth_creds:
        return None
    
    try:
        credentials = Credentials(
            token=oauth_creds.get('token'),
            refresh_token=oauth_creds.get('refresh_token'),
            token_uri=oauth_creds.get('token_uri', 'https://oauth2.googleapis.com/token'),
            client_id=oauth_creds.get('client_id'),
            client_secret=oauth_creds.get('client_secret'),
            scopes=oauth_creds.get('scopes', GMAIL_SCOPES)
        )
        
        # Refresh if expired
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            # Update stored token (you'd want to save this back to DB)
        
        service = build('gmail', 'v1', credentials=credentials)
        return service
        
    except Exception as e:
        current_app.logger.error(f"Failed to get Gmail service: {str(e)}")
        return None


def send_email_via_gmail_oauth(email_settings, to_email, subject, body, in_reply_to=None):
    """Send email using Gmail API with OAuth credentials."""
    service = get_gmail_service(email_settings)
    if not service:
        return False, "Gmail service not available"
    
    try:
        from_email = email_settings.get('email')
        
        # Create message
        message = MIMEMultipart()
        message['to'] = to_email
        message['from'] = from_email
        message['subject'] = f"Re: {subject}" if in_reply_to and not subject.startswith('Re:') else subject
        
        if in_reply_to:
            message['In-Reply-To'] = in_reply_to
            message['References'] = in_reply_to
        
        message.attach(MIMEText(body, 'plain'))
        
        # Encode and send
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        result = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        return True, result.get('id')
        
    except Exception as e:
        current_app.logger.error(f"Gmail OAuth send error: {str(e)}")
        return False, str(e)


def fetch_emails_via_gmail_oauth(email_settings, unseen_only=True, limit=10):
    """Fetch emails using Gmail API with OAuth credentials."""
    service = get_gmail_service(email_settings)
    if not service:
        return []
    
    try:
        # Build query
        query = 'is:unread' if unseen_only else ''
        
        # Get message list
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=limit
        ).execute()
        
        messages = results.get('messages', [])
        emails = []
        
        for msg_info in messages:
            # Get full message
            msg = service.users().messages().get(
                userId='me',
                id=msg_info['id'],
                format='full'
            ).execute()
            
            # Parse headers
            headers = {h['name'].lower(): h['value'] for h in msg['payload'].get('headers', [])}
            
            # Get body
            body = ''
            if 'parts' in msg['payload']:
                for part in msg['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        body = base64.urlsafe_b64decode(part['body'].get('data', '')).decode('utf-8')
                        break
            elif 'body' in msg['payload'] and 'data' in msg['payload']['body']:
                body = base64.urlsafe_b64decode(msg['payload']['body']['data']).decode('utf-8')
            
            # Parse from address
            from_header = headers.get('from', '')
            from_name = from_header.split('<')[0].strip().strip('"')
            from_email_match = from_header.split('<')[-1].replace('>', '').strip()
            
            emails.append({
                'id': msg_info['id'],
                'message_id': headers.get('message-id'),
                'from_email': from_email_match if '<' in from_header else from_header,
                'from_name': from_name if from_name else from_email_match,
                'to': headers.get('to'),
                'subject': headers.get('subject', '(No Subject)'),
                'body': body,
                'date': headers.get('date'),
                'snippet': msg.get('snippet', '')
            })
        
        return emails
        
    except Exception as e:
        current_app.logger.error(f"Gmail OAuth fetch error: {str(e)}")
        return []


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
    
    provider = email_settings.get('provider')
    
    # Gmail OAuth sending
    if provider == 'gmail_oauth':
        success, result = send_email_via_gmail_oauth(email_settings, to_email, subject, body)
        if success:
            return jsonify({
                'success': True,
                'message_id': result
            })
        else:
            return jsonify({'error': f'Failed to send: {result}'}), 500
    
    # SMTP sending (gmail_app_password or custom_smtp)
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
    
    # Real IMAP fetch or Gmail OAuth
    provider = email_settings.get('provider')
    
    # Gmail OAuth fetch
    if provider == 'gmail_oauth':
        emails = fetch_emails_via_gmail_oauth(email_settings, unseen_only=False, limit=20)
        return jsonify({
            'emails': emails,
            'total': len(emails),
            'unread': sum(1 for e in emails if e.get('unread', True)),
            'provider': 'gmail_oauth'
        })
    
    # IMAP fetch for other providers
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
    
    provider = email_settings.get('provider')
    
    # Gmail OAuth test
    if provider == 'gmail_oauth':
        test_body = f'''
This is a test email from Studio OS.

Your Gmail integration is working correctly!

Studio: {studio.name}
Connected at: {email_settings.get('connected_at', 'Unknown')}
Provider: Gmail OAuth

Best regards,
Studio OS Team
        '''
        
        success, result = send_email_via_gmail_oauth(
            email_settings, 
            test_email_address, 
            '✅ Studio OS - Email Test Successful',
            test_body
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Test email sent to {test_email_address}'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to send test email: {result}'
            }), 500
    
    # SMTP test
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
        # Fetch new emails - use OAuth if available
        provider = email_settings.get('provider')
        
        if provider == 'gmail_oauth':
            emails = fetch_emails_via_gmail_oauth(email_settings, unseen_only=True, limit=10)
        else:
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
                if provider == 'gmail_oauth':
                    success, _ = send_email_via_gmail_oauth(
                        email_settings,
                        to_email=email_data.get('from_email'),
                        subject=email_data.get('subject', ''),
                        body=ai_reply,
                        in_reply_to=email_data.get('message_id')
                    )
                    result['sent'] = success
                else:
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

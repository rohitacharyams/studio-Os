from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import uuid
import hmac
import hashlib

from app import db
from app.models import Studio, Contact, Conversation, Message, Channel, MessageDirection, LeadStatus

webhooks_bp = Blueprint('webhooks', __name__)


@webhooks_bp.route('/email/inbound', methods=['POST'])
def email_inbound():
    """Handle inbound emails (from email service provider webhook)."""
    data = request.get_json()
    
    # Expected fields: from_email, to_email, subject, body, html_body, message_id
    from_email = data.get('from_email')
    to_email = data.get('to_email')
    subject = data.get('subject', '')
    body = data.get('body', '')
    html_body = data.get('html_body')
    message_id = data.get('message_id')
    
    if not from_email or not to_email:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Find studio by email
    studio = Studio.query.filter_by(email=to_email).first()
    if not studio:
        # Check email settings for configured addresses
        studio = Studio.query.filter(
            Studio.email_settings['inbox_email'].astext == to_email
        ).first()
    
    if not studio:
        return jsonify({'error': 'Studio not found for this email'}), 404
    
    # Find or create contact
    contact = Contact.query.filter_by(
        studio_id=studio.id,
        email=from_email
    ).first()
    
    if not contact:
        contact = Contact(
            id=str(uuid.uuid4()),
            studio_id=studio.id,
            email=from_email,
            name=data.get('from_name', from_email.split('@')[0]),
            lead_status=LeadStatus.NEW.value,
            lead_source='email'
        )
        db.session.add(contact)
    
    # Find or create conversation
    conversation = Conversation.query.filter_by(
        studio_id=studio.id,
        contact_id=contact.id,
        channel=Channel.EMAIL.value,
        subject=subject
    ).first()
    
    if not conversation:
        conversation = Conversation(
            id=str(uuid.uuid4()),
            studio_id=studio.id,
            contact_id=contact.id,
            channel=Channel.EMAIL.value,
            subject=subject,
            is_unread=True
        )
        db.session.add(conversation)
    else:
        conversation.is_unread = True
    
    # Create message
    message = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        direction=MessageDirection.INBOUND.value,
        content=body,
        content_html=html_body,
        external_id=message_id,
        attachments=data.get('attachments', [])
    )
    
    conversation.last_message_at = datetime.utcnow()
    
    try:
        db.session.add(message)
        db.session.commit()
        return jsonify({'status': 'received', 'message_id': message.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@webhooks_bp.route('/whatsapp/twilio', methods=['POST'])
def whatsapp_twilio():
    """Handle WhatsApp messages via Twilio webhook."""
    # Twilio sends form data
    from_number = request.form.get('From', '').replace('whatsapp:', '')
    to_number = request.form.get('To', '').replace('whatsapp:', '')
    body = request.form.get('Body', '')
    message_sid = request.form.get('MessageSid')
    
    if not from_number or not body:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Find studio by WhatsApp number
    studio = Studio.query.filter(
        Studio.whatsapp_settings['phone_number'].astext == to_number
    ).first()
    
    if not studio:
        return '', 200  # Accept but ignore unknown numbers
    
    # Find or create contact
    contact = Contact.query.filter_by(
        studio_id=studio.id,
        phone=from_number
    ).first()
    
    if not contact:
        contact = Contact(
            id=str(uuid.uuid4()),
            studio_id=studio.id,
            phone=from_number,
            name=request.form.get('ProfileName', from_number),
            lead_status=LeadStatus.NEW.value,
            lead_source='whatsapp'
        )
        db.session.add(contact)
    
    # Find or create conversation
    conversation = Conversation.query.filter_by(
        studio_id=studio.id,
        contact_id=contact.id,
        channel=Channel.WHATSAPP.value
    ).first()
    
    if not conversation:
        conversation = Conversation(
            id=str(uuid.uuid4()),
            studio_id=studio.id,
            contact_id=contact.id,
            channel=Channel.WHATSAPP.value,
            is_unread=True
        )
        db.session.add(conversation)
    else:
        conversation.is_unread = True
    
    # Create message
    message = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        direction=MessageDirection.INBOUND.value,
        content=body,
        external_id=message_sid
    )
    
    # Handle media attachments
    num_media = int(request.form.get('NumMedia', 0))
    if num_media > 0:
        attachments = []
        for i in range(num_media):
            attachments.append({
                'url': request.form.get(f'MediaUrl{i}'),
                'content_type': request.form.get(f'MediaContentType{i}')
            })
        message.attachments = attachments
    
    conversation.last_message_at = datetime.utcnow()
    
    try:
        db.session.add(message)
        db.session.commit()
        return '', 200  # Twilio expects empty 200 response
    except Exception as e:
        db.session.rollback()
        return '', 500


@webhooks_bp.route('/instagram', methods=['GET'])
def instagram_verify():
    """Instagram webhook verification (for future Instagram API integration)."""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    verify_token = current_app.config.get('INSTAGRAM_VERIFY_TOKEN', 'studio-os-verify')
    
    if mode == 'subscribe' and token == verify_token:
        return challenge, 200
    
    return 'Forbidden', 403


@webhooks_bp.route('/instagram', methods=['POST'])
def instagram_webhook():
    """Handle Instagram webhook events (placeholder for future integration)."""
    # Verify signature
    signature = request.headers.get('X-Hub-Signature-256', '')
    payload = request.get_data()
    
    app_secret = current_app.config.get('INSTAGRAM_APP_SECRET', '')
    
    if app_secret:
        expected_signature = 'sha256=' + hmac.new(
            app_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            return 'Invalid signature', 403
    
    data = request.get_json()
    
    # Process Instagram events
    # For MVP, Instagram is manual - this is a placeholder
    # Full implementation would handle messaging events here
    
    return '', 200

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import uuid

from app import db
from app.models import User, Conversation, Message, MessageDirection
from app.services.email_service import EmailService
from app.services.whatsapp_service import WhatsAppService

messages_bp = Blueprint('messages', __name__)


@messages_bp.route('/<conversation_id>', methods=['GET'])
@jwt_required()
def get_messages(conversation_id):
    """Get all messages in a conversation."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    conversation = Conversation.query.filter_by(
        id=conversation_id,
        studio_id=user.studio_id
    ).first()
    
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 50, type=int)
    
    query = Message.query.filter_by(conversation_id=conversation_id)\
        .order_by(Message.created_at.desc())
    
    total = query.count()
    messages = query.offset((page - 1) * limit).limit(limit).all()
    
    # Reverse to show oldest first
    messages = list(reversed(messages))
    
    return jsonify({
        'messages': [m.to_dict() for m in messages],
        'total': total,
        'page': page,
        'limit': limit
    })


@messages_bp.route('/<conversation_id>', methods=['POST'])
@jwt_required()
def send_message(conversation_id):
    """Send a new message in a conversation."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    conversation = Conversation.query.filter_by(
        id=conversation_id,
        studio_id=user.studio_id
    ).first()
    
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    
    data = request.get_json()
    
    if not data.get('content'):
        return jsonify({'error': 'Message content is required'}), 400
    
    # Create message record
    message = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        sender_id=user.id,
        direction=MessageDirection.OUTBOUND.value,
        content=data['content'],
        content_html=data.get('content_html'),
        is_ai_generated=data.get('is_ai_generated', False),
        attachments=data.get('attachments', [])
    )
    
    try:
        # Send via appropriate channel
        contact = conversation.contact
        external_id = None
        
        if conversation.channel == 'EMAIL':
            email_service = EmailService()
            external_id = email_service.send_email(
                to_email=contact.email,
                subject=conversation.subject or 'Message from Studio',
                body=data['content'],
                html_body=data.get('content_html'),
                studio_id=user.studio_id
            )
        elif conversation.channel == 'WHATSAPP':
            whatsapp_service = WhatsAppService()
            external_id = whatsapp_service.send_message(
                to_phone=contact.phone,
                message=data['content'],
                studio_id=user.studio_id
            )
        elif conversation.channel == 'INSTAGRAM':
            # Instagram messages are manual for MVP
            pass
        
        message.external_id = external_id
        message.sent_at = datetime.utcnow()
        
        # Update conversation
        conversation.last_message_at = datetime.utcnow()
        conversation.is_unread = False
        
        db.session.add(message)
        db.session.commit()
        
        return jsonify({'message': message.to_dict()}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@messages_bp.route('/<conversation_id>/<message_id>', methods=['PUT'])
@jwt_required()
def update_message(conversation_id, message_id):
    """Update message properties."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    conversation = Conversation.query.filter_by(
        id=conversation_id,
        studio_id=user.studio_id
    ).first()
    
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    
    message = Message.query.filter_by(
        id=message_id,
        conversation_id=conversation_id
    ).first()
    
    if not message:
        return jsonify({'error': 'Message not found'}), 404
    
    data = request.get_json()
    
    if 'is_read' in data:
        message.is_read = data['is_read']
    
    try:
        db.session.commit()
        return jsonify({'message': message.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

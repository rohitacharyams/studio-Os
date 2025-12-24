from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import desc
import uuid

from app import db
from app.models import User, Conversation, Contact, Message

conversations_bp = Blueprint('conversations', __name__)


@conversations_bp.route('', methods=['GET'])
@jwt_required()
def list_conversations():
    """List all conversations for the studio with filters."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Query parameters
    channel = request.args.get('channel')
    is_unread = request.args.get('is_unread')
    is_archived = request.args.get('is_archived', 'false')
    is_starred = request.args.get('is_starred')
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    # Base query
    query = Conversation.query.filter_by(studio_id=user.studio_id)
    
    # Apply filters
    if channel:
        query = query.filter_by(channel=channel)
    if is_unread and is_unread.lower() == 'true':
        query = query.filter_by(is_unread=True)
    if is_archived.lower() == 'false':
        query = query.filter_by(is_archived=False)
    elif is_archived.lower() == 'true':
        query = query.filter_by(is_archived=True)
    if is_starred and is_starred.lower() == 'true':
        query = query.filter_by(is_starred=True)
    
    # Search in contact name/email
    if search:
        query = query.join(Contact).filter(
            db.or_(
                Contact.name.ilike(f'%{search}%'),
                Contact.email.ilike(f'%{search}%'),
                Conversation.subject.ilike(f'%{search}%')
            )
        )
    
    # Order by last message
    query = query.order_by(desc(Conversation.last_message_at))
    
    # Paginate
    total = query.count()
    conversations = query.offset((page - 1) * limit).limit(limit).all()
    
    return jsonify({
        'conversations': [c.to_dict(include_contact=True) for c in conversations],
        'total': total,
        'page': page,
        'limit': limit,
        'total_pages': (total + limit - 1) // limit
    })


@conversations_bp.route('/<conversation_id>', methods=['GET'])
@jwt_required()
def get_conversation(conversation_id):
    """Get a single conversation with messages."""
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
    
    # Mark as read
    if conversation.is_unread:
        conversation.is_unread = False
        # Mark all messages as read
        Message.query.filter_by(conversation_id=conversation_id).update({'is_read': True})
        db.session.commit()
    
    return jsonify({
        'conversation': conversation.to_dict(include_messages=True, include_contact=True)
    })


@conversations_bp.route('/<conversation_id>', methods=['PUT'])
@jwt_required()
def update_conversation(conversation_id):
    """Update conversation properties (archive, star, etc.)."""
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
    
    if 'is_archived' in data:
        conversation.is_archived = data['is_archived']
    if 'is_starred' in data:
        conversation.is_starred = data['is_starred']
    if 'is_unread' in data:
        conversation.is_unread = data['is_unread']
    
    try:
        db.session.commit()
        return jsonify({'conversation': conversation.to_dict(include_contact=True)})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@conversations_bp.route('', methods=['POST'])
@jwt_required()
def create_conversation():
    """Create a new conversation (for initiating outbound contact)."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    if not data.get('contact_id'):
        return jsonify({'error': 'contact_id is required'}), 400
    if not data.get('channel'):
        return jsonify({'error': 'channel is required'}), 400
    
    # Verify contact belongs to studio
    contact = Contact.query.filter_by(
        id=data['contact_id'],
        studio_id=user.studio_id
    ).first()
    
    if not contact:
        return jsonify({'error': 'Contact not found'}), 404
    
    conversation = Conversation(
        id=str(uuid.uuid4()),
        studio_id=user.studio_id,
        contact_id=contact.id,
        channel=data['channel'],
        subject=data.get('subject'),
        is_unread=False  # Outbound conversations start as read
    )
    
    try:
        db.session.add(conversation)
        db.session.commit()
        return jsonify({'conversation': conversation.to_dict(include_contact=True)}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@conversations_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_conversation_stats():
    """Get conversation statistics."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    base_query = Conversation.query.filter_by(studio_id=user.studio_id, is_archived=False)
    
    stats = {
        'total': base_query.count(),
        'unread': base_query.filter_by(is_unread=True).count(),
        'starred': base_query.filter_by(is_starred=True).count(),
        'by_channel': {
            'EMAIL': base_query.filter_by(channel='EMAIL').count(),
            'WHATSAPP': base_query.filter_by(channel='WHATSAPP').count(),
            'INSTAGRAM': base_query.filter_by(channel='INSTAGRAM').count(),
        }
    }
    
    return jsonify({'stats': stats})

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import uuid

from app import db
from app.models import User, Studio, StudioKnowledge

studio_bp = Blueprint('studio', __name__)


@studio_bp.route('', methods=['GET'])
@jwt_required()
def get_studio():
    """Get current user's studio details."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'studio': user.studio.to_dict()})


@studio_bp.route('', methods=['PUT'])
@jwt_required()
def update_studio():
    """Update studio details."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user.role not in ['owner', 'admin']:
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    studio = user.studio
    data = request.get_json()
    
    if 'name' in data:
        studio.name = data['name']
    if 'email' in data:
        studio.email = data['email']
    if 'phone' in data:
        studio.phone = data['phone']
    if 'address' in data:
        studio.address = data['address']
    if 'timezone' in data:
        studio.timezone = data['timezone']
    
    try:
        db.session.commit()
        return jsonify({'studio': studio.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@studio_bp.route('/settings/email', methods=['GET'])
@jwt_required()
def get_email_settings():
    """Get email integration settings."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'settings': user.studio.email_settings or {}})


@studio_bp.route('/settings/email', methods=['PUT'])
@jwt_required()
def update_email_settings():
    """Update email integration settings."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user.role not in ['owner', 'admin']:
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    data = request.get_json()
    studio = user.studio
    studio.email_settings = data
    
    try:
        db.session.commit()
        return jsonify({'settings': studio.email_settings})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@studio_bp.route('/settings/whatsapp', methods=['GET'])
@jwt_required()
def get_whatsapp_settings():
    """Get WhatsApp integration settings."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'settings': user.studio.whatsapp_settings or {}})


@studio_bp.route('/settings/whatsapp', methods=['PUT'])
@jwt_required()
def update_whatsapp_settings():
    """Update WhatsApp integration settings."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user.role not in ['owner', 'admin']:
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    data = request.get_json()
    studio = user.studio
    studio.whatsapp_settings = data
    
    try:
        db.session.commit()
        return jsonify({'settings': studio.whatsapp_settings})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Knowledge Base endpoints
@studio_bp.route('/knowledge', methods=['GET'])
@jwt_required()
def list_knowledge():
    """List all knowledge base items."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    category = request.args.get('category')
    
    query = StudioKnowledge.query.filter_by(studio_id=user.studio_id)
    
    if category:
        query = query.filter_by(category=category)
    
    items = query.order_by(StudioKnowledge.category, StudioKnowledge.title).all()
    
    return jsonify({
        'knowledge': [item.to_dict() for item in items]
    })


@studio_bp.route('/knowledge', methods=['POST'])
@jwt_required()
def create_knowledge():
    """Create a new knowledge base item."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    required_fields = ['category', 'title', 'content']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    item = StudioKnowledge(
        id=str(uuid.uuid4()),
        studio_id=user.studio_id,
        category=data['category'],
        title=data['title'],
        content=data['content'],
        is_active=data.get('is_active', True)
    )
    
    try:
        db.session.add(item)
        db.session.commit()
        return jsonify({'knowledge': item.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@studio_bp.route('/knowledge/<item_id>', methods=['PUT'])
@jwt_required()
def update_knowledge(item_id):
    """Update a knowledge base item."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    item = StudioKnowledge.query.filter_by(
        id=item_id,
        studio_id=user.studio_id
    ).first()
    
    if not item:
        return jsonify({'error': 'Knowledge item not found'}), 404
    
    data = request.get_json()
    
    if 'category' in data:
        item.category = data['category']
    if 'title' in data:
        item.title = data['title']
    if 'content' in data:
        item.content = data['content']
    if 'is_active' in data:
        item.is_active = data['is_active']
    
    try:
        db.session.commit()
        return jsonify({'knowledge': item.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@studio_bp.route('/knowledge/<item_id>', methods=['DELETE'])
@jwt_required()
def delete_knowledge(item_id):
    """Delete a knowledge base item."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    item = StudioKnowledge.query.filter_by(
        id=item_id,
        studio_id=user.studio_id
    ).first()
    
    if not item:
        return jsonify({'error': 'Knowledge item not found'}), 404
    
    try:
        db.session.delete(item)
        db.session.commit()
        return jsonify({'message': 'Knowledge item deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

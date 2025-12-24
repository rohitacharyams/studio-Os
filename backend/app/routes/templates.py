from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import uuid
import re

from app import db
from app.models import User, MessageTemplate

templates_bp = Blueprint('templates', __name__)


@templates_bp.route('', methods=['GET'])
@jwt_required()
def list_templates():
    """List all message templates."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Filters
    category = request.args.get('category')
    channel = request.args.get('channel')
    
    query = MessageTemplate.query.filter_by(studio_id=user.studio_id)
    
    if category:
        query = query.filter_by(category=category)
    if channel:
        query = query.filter(MessageTemplate.channels.contains([channel]))
    
    templates = query.order_by(MessageTemplate.category, MessageTemplate.name).all()
    
    return jsonify({
        'templates': [t.to_dict() for t in templates]
    })


@templates_bp.route('/<template_id>', methods=['GET'])
@jwt_required()
def get_template(template_id):
    """Get a single template."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    template = MessageTemplate.query.filter_by(
        id=template_id,
        studio_id=user.studio_id
    ).first()
    
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    return jsonify({'template': template.to_dict()})


@templates_bp.route('', methods=['POST'])
@jwt_required()
def create_template():
    """Create a new message template."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'error': 'name is required'}), 400
    if not data.get('content'):
        return jsonify({'error': 'content is required'}), 400
    
    # Extract variables from content (e.g., {{name}}, {{studio_name}})
    variables = re.findall(r'\{\{(\w+)\}\}', data['content'])
    
    template = MessageTemplate(
        id=str(uuid.uuid4()),
        studio_id=user.studio_id,
        name=data['name'],
        category=data.get('category'),
        subject=data.get('subject'),
        content=data['content'],
        variables=list(set(variables)),
        channels=data.get('channels', ['EMAIL', 'WHATSAPP']),
        is_active=data.get('is_active', True)
    )
    
    try:
        db.session.add(template)
        db.session.commit()
        return jsonify({'template': template.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@templates_bp.route('/<template_id>', methods=['PUT'])
@jwt_required()
def update_template(template_id):
    """Update a message template."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    template = MessageTemplate.query.filter_by(
        id=template_id,
        studio_id=user.studio_id
    ).first()
    
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        template.name = data['name']
    if 'category' in data:
        template.category = data['category']
    if 'subject' in data:
        template.subject = data['subject']
    if 'content' in data:
        template.content = data['content']
        # Re-extract variables
        template.variables = list(set(re.findall(r'\{\{(\w+)\}\}', data['content'])))
    if 'channels' in data:
        template.channels = data['channels']
    if 'is_active' in data:
        template.is_active = data['is_active']
    
    try:
        db.session.commit()
        return jsonify({'template': template.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@templates_bp.route('/<template_id>', methods=['DELETE'])
@jwt_required()
def delete_template(template_id):
    """Delete a message template."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    template = MessageTemplate.query.filter_by(
        id=template_id,
        studio_id=user.studio_id
    ).first()
    
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    try:
        db.session.delete(template)
        db.session.commit()
        return jsonify({'message': 'Template deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@templates_bp.route('/<template_id>/render', methods=['POST'])
@jwt_required()
def render_template(template_id):
    """Render a template with provided variables."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    template = MessageTemplate.query.filter_by(
        id=template_id,
        studio_id=user.studio_id
    ).first()
    
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    data = request.get_json()
    variables = data.get('variables', {})
    
    # Add default studio name if not provided
    if 'studio_name' not in variables:
        variables['studio_name'] = user.studio.name
    
    # Render content
    rendered_content = template.content
    rendered_subject = template.subject or ''
    
    for var, value in variables.items():
        rendered_content = rendered_content.replace(f'{{{{{var}}}}}', str(value))
        rendered_subject = rendered_subject.replace(f'{{{{{var}}}}}', str(value))
    
    return jsonify({
        'content': rendered_content,
        'subject': rendered_subject,
        'missing_variables': [v for v in template.variables if v not in variables]
    })

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import desc
import uuid

from app import db
from app.models import User, Contact, LeadStatusHistory, LeadStatus

contacts_bp = Blueprint('contacts', __name__)


@contacts_bp.route('', methods=['GET'])
@jwt_required()
def list_contacts():
    """List all contacts with filters."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Query parameters
    lead_status = request.args.get('lead_status')
    lead_source = request.args.get('lead_source')
    search = request.args.get('search')
    tag = request.args.get('tag')
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    query = Contact.query.filter_by(studio_id=user.studio_id)
    
    if lead_status:
        query = query.filter_by(lead_status=lead_status)
    if lead_source:
        query = query.filter_by(lead_source=lead_source)
    if tag:
        query = query.filter(Contact.tags.contains([tag]))
    if search:
        query = query.filter(
            db.or_(
                Contact.name.ilike(f'%{search}%'),
                Contact.email.ilike(f'%{search}%'),
                Contact.phone.ilike(f'%{search}%')
            )
        )
    
    # Order by most recent
    query = query.order_by(desc(Contact.updated_at))
    
    total = query.count()
    contacts = query.offset((page - 1) * limit).limit(limit).all()
    
    return jsonify({
        'contacts': [c.to_dict() for c in contacts],
        'total': total,
        'page': page,
        'limit': limit,
        'total_pages': (total + limit - 1) // limit
    })


@contacts_bp.route('/<contact_id>', methods=['GET'])
@jwt_required()
def get_contact(contact_id):
    """Get a single contact with conversations."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    contact = Contact.query.filter_by(
        id=contact_id,
        studio_id=user.studio_id
    ).first()
    
    if not contact:
        return jsonify({'error': 'Contact not found'}), 404
    
    return jsonify({
        'contact': contact.to_dict(include_conversations=True)
    })


@contacts_bp.route('', methods=['POST'])
@jwt_required()
def create_contact():
    """Create a new contact."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    # At least one contact method required
    if not any([data.get('email'), data.get('phone'), data.get('instagram_handle')]):
        return jsonify({'error': 'At least one contact method (email, phone, or instagram_handle) is required'}), 400
    
    # Check for duplicate
    if data.get('email'):
        existing = Contact.query.filter_by(
            studio_id=user.studio_id,
            email=data['email']
        ).first()
        if existing:
            return jsonify({'error': 'Contact with this email already exists', 'contact_id': existing.id}), 400
    
    contact = Contact(
        id=str(uuid.uuid4()),
        studio_id=user.studio_id,
        name=data.get('name'),
        email=data.get('email'),
        phone=data.get('phone'),
        instagram_handle=data.get('instagram_handle'),
        lead_status=data.get('lead_status', LeadStatus.NEW.value),
        lead_source=data.get('lead_source'),
        notes=data.get('notes'),
        tags=data.get('tags', []),
        metadata=data.get('metadata', {})
    )
    
    try:
        db.session.add(contact)
        
        # Create initial status history
        history = LeadStatusHistory(
            id=str(uuid.uuid4()),
            contact_id=contact.id,
            to_status=contact.lead_status,
            changed_by_id=user.id,
            notes='Contact created'
        )
        db.session.add(history)
        
        db.session.commit()
        return jsonify({'contact': contact.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@contacts_bp.route('/<contact_id>', methods=['PUT'])
@jwt_required()
def update_contact(contact_id):
    """Update a contact."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    contact = Contact.query.filter_by(
        id=contact_id,
        studio_id=user.studio_id
    ).first()
    
    if not contact:
        return jsonify({'error': 'Contact not found'}), 404
    
    data = request.get_json()
    old_status = contact.lead_status
    
    if 'name' in data:
        contact.name = data['name']
    if 'email' in data:
        contact.email = data['email']
    if 'phone' in data:
        contact.phone = data['phone']
    if 'instagram_handle' in data:
        contact.instagram_handle = data['instagram_handle']
    if 'lead_source' in data:
        contact.lead_source = data['lead_source']
    if 'notes' in data:
        contact.notes = data['notes']
    if 'tags' in data:
        contact.tags = data['tags']
    if 'metadata' in data:
        contact.metadata = data['metadata']
    
    # Handle status change separately for tracking
    if 'lead_status' in data and data['lead_status'] != old_status:
        contact.lead_status = data['lead_status']
        
        # Create status history entry
        history = LeadStatusHistory(
            id=str(uuid.uuid4()),
            contact_id=contact.id,
            from_status=old_status,
            to_status=data['lead_status'],
            changed_by_id=user.id,
            notes=data.get('status_note')
        )
        db.session.add(history)
    
    try:
        db.session.commit()
        return jsonify({'contact': contact.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@contacts_bp.route('/<contact_id>', methods=['DELETE'])
@jwt_required()
def delete_contact(contact_id):
    """Delete a contact."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    contact = Contact.query.filter_by(
        id=contact_id,
        studio_id=user.studio_id
    ).first()
    
    if not contact:
        return jsonify({'error': 'Contact not found'}), 404
    
    try:
        db.session.delete(contact)
        db.session.commit()
        return jsonify({'message': 'Contact deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@contacts_bp.route('/<contact_id>/status-history', methods=['GET'])
@jwt_required()
def get_status_history(contact_id):
    """Get lead status change history for a contact."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    contact = Contact.query.filter_by(
        id=contact_id,
        studio_id=user.studio_id
    ).first()
    
    if not contact:
        return jsonify({'error': 'Contact not found'}), 404
    
    history = LeadStatusHistory.query.filter_by(contact_id=contact_id)\
        .order_by(desc(LeadStatusHistory.created_at)).all()
    
    return jsonify({
        'history': [h.to_dict() for h in history]
    })


@contacts_bp.route('/bulk-update', methods=['POST'])
@jwt_required()
def bulk_update_contacts():
    """Bulk update contacts (e.g., change status for multiple contacts)."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    contact_ids = data.get('contact_ids', [])
    updates = data.get('updates', {})
    
    if not contact_ids:
        return jsonify({'error': 'contact_ids is required'}), 400
    
    contacts = Contact.query.filter(
        Contact.id.in_(contact_ids),
        Contact.studio_id == user.studio_id
    ).all()
    
    updated_count = 0
    
    for contact in contacts:
        old_status = contact.lead_status
        
        if 'lead_status' in updates:
            contact.lead_status = updates['lead_status']
            
            if updates['lead_status'] != old_status:
                history = LeadStatusHistory(
                    id=str(uuid.uuid4()),
                    contact_id=contact.id,
                    from_status=old_status,
                    to_status=updates['lead_status'],
                    changed_by_id=user.id,
                    notes='Bulk status update'
                )
                db.session.add(history)
        
        if 'tags' in updates:
            # Add tags (don't replace)
            existing_tags = set(contact.tags or [])
            new_tags = set(updates['tags'])
            contact.tags = list(existing_tags | new_tags)
        
        updated_count += 1
    
    try:
        db.session.commit()
        return jsonify({
            'message': f'Updated {updated_count} contacts',
            'updated_count': updated_count
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

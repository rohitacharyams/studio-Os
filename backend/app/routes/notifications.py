"""Notification routes for Studio OS."""
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models import Notification, User

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/', methods=['GET'])
@notifications_bp.route('', methods=['GET'])
@jwt_required()
def list_notifications():
    """List notifications for the current user's studio."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.studio_id:
        return jsonify({'error': 'Studio not found'}), 404
    
    # Get query params
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    limit = request.args.get('limit', 50, type=int)
    
    query = Notification.query.filter_by(studio_id=user.studio_id)
    
    if unread_only:
        query = query.filter_by(is_read=False)
    
    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
    
    # Get unread count
    unread_count = Notification.query.filter_by(
        studio_id=user.studio_id,
        is_read=False
    ).count()
    
    return jsonify({
        'notifications': [n.to_dict() for n in notifications],
        'unread_count': unread_count
    })


@notifications_bp.route('/<notification_id>/read', methods=['PATCH'])
@jwt_required()
def mark_as_read(notification_id):
    """Mark a notification as read."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.studio_id:
        return jsonify({'error': 'Studio not found'}), 404
    
    notification = Notification.query.filter_by(
        id=notification_id,
        studio_id=user.studio_id
    ).first()
    
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'message': 'Notification marked as read', 'notification': notification.to_dict()})


@notifications_bp.route('/read-all', methods=['PATCH'])
@jwt_required()
def mark_all_as_read():
    """Mark all notifications as read for the current user's studio."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.studio_id:
        return jsonify({'error': 'Studio not found'}), 404
    
    updated_count = Notification.query.filter_by(
        studio_id=user.studio_id,
        is_read=False
    ).update({
        'is_read': True,
        'read_at': datetime.utcnow()
    })
    
    db.session.commit()
    
    return jsonify({
        'message': f'{updated_count} notifications marked as read',
        'updated_count': updated_count
    })


@notifications_bp.route('/<notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    """Delete a notification."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.studio_id:
        return jsonify({'error': 'Studio not found'}), 404
    
    notification = Notification.query.filter_by(
        id=notification_id,
        studio_id=user.studio_id
    ).first()
    
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    
    db.session.delete(notification)
    db.session.commit()
    
    return jsonify({'message': 'Notification deleted'})


# Helper function to create notifications (can be imported by other modules)
def create_notification(studio_id: str, notification_type: str, title: str, 
                       message: str = None, reference_type: str = None, 
                       reference_id: str = None) -> Notification:
    """Create a new notification for a studio."""
    notification = Notification(
        id=str(uuid.uuid4()),
        studio_id=studio_id,
        type=notification_type,
        title=title,
        message=message,
        reference_type=reference_type,
        reference_id=reference_id
    )
    db.session.add(notification)
    return notification

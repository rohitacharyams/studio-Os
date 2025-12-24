from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import func
import uuid

from app import db
from app.models import User, AnalyticsDaily, Contact, Conversation, Message, LeadStatus

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    """Get dashboard analytics overview."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Date range (default last 30 days)
    days = request.args.get('days', 30, type=int)
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)
    
    studio_id = user.studio_id
    
    # Get daily analytics
    daily_stats = AnalyticsDaily.query.filter(
        AnalyticsDaily.studio_id == studio_id,
        AnalyticsDaily.date >= start_date,
        AnalyticsDaily.date <= end_date
    ).order_by(AnalyticsDaily.date).all()
    
    # Calculate totals
    total_messages_received = sum(d.messages_received for d in daily_stats)
    total_messages_sent = sum(d.messages_sent for d in daily_stats)
    total_new_leads = sum(d.new_leads for d in daily_stats)
    total_converted = sum(d.leads_converted for d in daily_stats)
    
    # Current stats
    total_contacts = Contact.query.filter_by(studio_id=studio_id).count()
    unread_conversations = Conversation.query.filter_by(
        studio_id=studio_id,
        is_unread=True,
        is_archived=False
    ).count()
    
    # Lead status breakdown
    lead_breakdown = db.session.query(
        Contact.lead_status,
        func.count(Contact.id)
    ).filter(Contact.studio_id == studio_id)\
     .group_by(Contact.lead_status).all()
    
    lead_stats = {status: count for status, count in lead_breakdown}
    
    # Average response time
    avg_response_times = [d.avg_response_time_minutes for d in daily_stats 
                         if d.avg_response_time_minutes is not None]
    avg_response_time = sum(avg_response_times) / len(avg_response_times) if avg_response_times else None
    
    return jsonify({
        'overview': {
            'total_contacts': total_contacts,
            'unread_conversations': unread_conversations,
            'messages_received': total_messages_received,
            'messages_sent': total_messages_sent,
            'new_leads': total_new_leads,
            'leads_converted': total_converted,
            'avg_response_time_minutes': avg_response_time
        },
        'lead_breakdown': lead_stats,
        'daily': [d.to_dict() for d in daily_stats],
        'period': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat(),
            'days': days
        }
    })


@analytics_bp.route('/leads', methods=['GET'])
@jwt_required()
def get_lead_analytics():
    """Get detailed lead analytics."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    studio_id = user.studio_id
    
    # Lead status distribution
    status_dist = db.session.query(
        Contact.lead_status,
        func.count(Contact.id)
    ).filter(Contact.studio_id == studio_id)\
     .group_by(Contact.lead_status).all()
    
    # Lead source distribution
    source_dist = db.session.query(
        Contact.lead_source,
        func.count(Contact.id)
    ).filter(
        Contact.studio_id == studio_id,
        Contact.lead_source.isnot(None)
    ).group_by(Contact.lead_source).all()
    
    # Conversion rate
    total_leads = Contact.query.filter_by(studio_id=studio_id).count()
    converted_leads = Contact.query.filter_by(
        studio_id=studio_id,
        lead_status=LeadStatus.CONVERTED.value
    ).count()
    
    conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
    
    return jsonify({
        'status_distribution': {status: count for status, count in status_dist},
        'source_distribution': {source or 'Unknown': count for source, count in source_dist},
        'conversion_rate': round(conversion_rate, 2),
        'total_leads': total_leads,
        'converted_leads': converted_leads
    })


@analytics_bp.route('/channels', methods=['GET'])
@jwt_required()
def get_channel_analytics():
    """Get analytics by communication channel."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    studio_id = user.studio_id
    
    # Conversations by channel
    conv_by_channel = db.session.query(
        Conversation.channel,
        func.count(Conversation.id)
    ).filter(Conversation.studio_id == studio_id)\
     .group_by(Conversation.channel).all()
    
    # Messages by channel (join with conversation)
    msg_by_channel = db.session.query(
        Conversation.channel,
        func.count(Message.id)
    ).join(Conversation, Message.conversation_id == Conversation.id)\
     .filter(Conversation.studio_id == studio_id)\
     .group_by(Conversation.channel).all()
    
    return jsonify({
        'conversations_by_channel': {channel: count for channel, count in conv_by_channel},
        'messages_by_channel': {channel: count for channel, count in msg_by_channel}
    })


@analytics_bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh_analytics():
    """Trigger analytics refresh (recalculate for today)."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    today = datetime.utcnow().date()
    studio_id = user.studio_id
    
    # Calculate today's stats
    messages_received = Message.query.join(Conversation)\
        .filter(
            Conversation.studio_id == studio_id,
            func.date(Message.created_at) == today,
            Message.direction == 'INBOUND'
        ).count()
    
    messages_sent = Message.query.join(Conversation)\
        .filter(
            Conversation.studio_id == studio_id,
            func.date(Message.created_at) == today,
            Message.direction == 'OUTBOUND'
        ).count()
    
    new_leads = Contact.query.filter(
        Contact.studio_id == studio_id,
        func.date(Contact.created_at) == today
    ).count()
    
    # Get or create today's analytics record
    daily = AnalyticsDaily.query.filter_by(
        studio_id=studio_id,
        date=today
    ).first()
    
    if not daily:
        daily = AnalyticsDaily(
            id=str(uuid.uuid4()),
            studio_id=studio_id,
            date=today
        )
        db.session.add(daily)
    
    daily.messages_received = messages_received
    daily.messages_sent = messages_sent
    daily.new_leads = new_leads
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Analytics refreshed',
            'daily': daily.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

"""
Super Admin routes for platform-wide analytics and management.
Only whitelisted admin users can access these endpoints.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from sqlalchemy import func, desc
import uuid

from app import db
from app.models import User, Studio, Booking, ClassSession, DanceClass, Contact

admin_bp = Blueprint('admin', __name__)

# ============================================
# WHITELISTED ADMIN USERS
# Add username/password pairs here to grant admin access
# ============================================
ADMIN_USERS = {
    'rohitOwner': {
        'password_hash': generate_password_hash('StormyDusk@123'),
        'name': 'Rohit (Platform Owner)',
        'email': 'rohit@studioos.com'
    },
    # Add more admins here as needed:
    # 'anotherAdmin': {
    #     'password_hash': generate_password_hash('SecurePassword123'),
    #     'name': 'Another Admin',
    #     'email': 'admin@studioos.com'
    # },
}


def verify_admin(username: str, password: str) -> dict | None:
    """Verify admin credentials and return admin info if valid."""
    admin = ADMIN_USERS.get(username)
    if admin and check_password_hash(admin['password_hash'], password):
        return {
            'username': username,
            'name': admin['name'],
            'email': admin['email']
        }
    return None


def admin_required(fn):
    """Decorator to require admin JWT token."""
    from functools import wraps
    
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if not claims.get('is_platform_admin'):
            return jsonify({'error': 'Platform admin access required'}), 403
        return fn(*args, **kwargs)
    return wrapper


# ============================================
# ADMIN AUTHENTICATION
# ============================================

@admin_bp.route('/login', methods=['POST'])
def admin_login():
    """Admin login - separate from regular user login."""
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    admin = verify_admin(username, password)
    if not admin:
        return jsonify({'error': 'Invalid admin credentials'}), 401
    
    # Create admin JWT with special claim
    access_token = create_access_token(
        identity=f"admin_{username}",
        additional_claims={
            'is_platform_admin': True,
            'admin_username': username
        },
        expires_delta=timedelta(hours=12)
    )
    
    return jsonify({
        'access_token': access_token,
        'admin': admin,
        'message': 'Admin login successful'
    })


@admin_bp.route('/verify', methods=['GET'])
@admin_required
def verify_admin_token():
    """Verify admin token is valid."""
    claims = get_jwt()
    return jsonify({
        'valid': True,
        'admin_username': claims.get('admin_username')
    })


# ============================================
# PLATFORM ANALYTICS
# ============================================

@admin_bp.route('/analytics/overview', methods=['GET'])
@admin_required
def get_platform_overview():
    """Get high-level platform analytics."""
    try:
        # Total counts
        total_studios = Studio.query.count()
        total_users = User.query.count()
        total_studio_owners = User.query.filter_by(user_type='studio_owner').count()
        total_customers = User.query.filter_by(user_type='customer').count()
        total_bookings = Booking.query.count()
        total_classes = DanceClass.query.count()
        total_sessions = ClassSession.query.count()
        total_contacts = Contact.query.count()
        
        # Active studios (with at least one booking in last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_studios = db.session.query(func.count(func.distinct(Booking.studio_id))).filter(
            Booking.booked_at >= thirty_days_ago
        ).scalar() or 0
        
        # Recent bookings (last 30 days)
        recent_bookings = Booking.query.filter(Booking.booked_at >= thirty_days_ago).count()
        
        # Studios created this month
        this_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_studios_this_month = Studio.query.filter(Studio.created_at >= this_month_start).count()
        
        # Bookings by status
        booking_stats = db.session.query(
            Booking.status,
            func.count(Booking.id)
        ).group_by(Booking.status).all()
        booking_by_status = {status: count for status, count in booking_stats}
        
        return jsonify({
            'overview': {
                'total_studios': total_studios,
                'active_studios': active_studios,
                'new_studios_this_month': new_studios_this_month,
                'total_users': total_users,
                'total_studio_owners': total_studio_owners,
                'total_customers': total_customers,
                'total_bookings': total_bookings,
                'recent_bookings_30d': recent_bookings,
                'total_classes': total_classes,
                'total_sessions': total_sessions,
                'total_contacts': total_contacts,
                'booking_by_status': booking_by_status
            },
            'generated_at': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/analytics/growth', methods=['GET'])
@admin_required
def get_growth_analytics():
    """Get growth trends over time."""
    try:
        # Get studios created per month (last 12 months)
        twelve_months_ago = datetime.utcnow() - timedelta(days=365)
        
        studio_growth = db.session.query(
            func.strftime('%Y-%m', Studio.created_at).label('month'),
            func.count(Studio.id).label('count')
        ).filter(
            Studio.created_at >= twelve_months_ago
        ).group_by('month').order_by('month').all()
        
        # Get bookings per month
        booking_growth = db.session.query(
            func.strftime('%Y-%m', Booking.booked_at).label('month'),
            func.count(Booking.id).label('count')
        ).filter(
            Booking.booked_at >= twelve_months_ago
        ).group_by('month').order_by('month').all()
        
        # Get users per month
        user_growth = db.session.query(
            func.strftime('%Y-%m', User.created_at).label('month'),
            func.count(User.id).label('count')
        ).filter(
            User.created_at >= twelve_months_ago
        ).group_by('month').order_by('month').all()
        
        return jsonify({
            'studio_growth': [{'month': m, 'count': c} for m, c in studio_growth],
            'booking_growth': [{'month': m, 'count': c} for m, c in booking_growth],
            'user_growth': [{'month': m, 'count': c} for m, c in user_growth]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/analytics/top-studios', methods=['GET'])
@admin_required
def get_top_studios():
    """Get top performing studios by bookings."""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        # Top studios by total bookings
        top_by_bookings = db.session.query(
            Studio.id,
            Studio.name,
            Studio.slug,
            Studio.email,
            Studio.created_at,
            func.count(Booking.id).label('total_bookings')
        ).outerjoin(Booking).group_by(Studio.id).order_by(
            desc('total_bookings')
        ).limit(limit).all()
        
        result = []
        for studio in top_by_bookings:
            # Get additional stats for each studio
            confirmed_bookings = Booking.query.filter_by(
                studio_id=studio.id, status='CONFIRMED'
            ).count()
            
            total_classes = DanceClass.query.filter_by(studio_id=studio.id).count()
            total_contacts = Contact.query.filter_by(studio_id=studio.id).count()
            
            result.append({
                'id': studio.id,
                'name': studio.name,
                'slug': studio.slug,
                'email': studio.email,
                'created_at': studio.created_at.isoformat() if studio.created_at else None,
                'total_bookings': studio.total_bookings or 0,
                'confirmed_bookings': confirmed_bookings,
                'total_classes': total_classes,
                'total_contacts': total_contacts
            })
        
        return jsonify({'top_studios': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# STUDIO MANAGEMENT
# ============================================

@admin_bp.route('/studios', methods=['GET'])
@admin_required
def list_all_studios():
    """List all studios with pagination and search."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        query = Studio.query
        
        # Search
        if search:
            query = query.filter(
                db.or_(
                    Studio.name.ilike(f'%{search}%'),
                    Studio.email.ilike(f'%{search}%'),
                    Studio.slug.ilike(f'%{search}%')
                )
            )
        
        # Sort
        if sort_order == 'desc':
            query = query.order_by(desc(getattr(Studio, sort_by, Studio.created_at)))
        else:
            query = query.order_by(getattr(Studio, sort_by, Studio.created_at))
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        studios = []
        for studio in pagination.items:
            # Get owner info
            owner = User.query.filter_by(studio_id=studio.id, role='owner').first()
            
            # Get stats
            booking_count = Booking.query.filter_by(studio_id=studio.id).count()
            class_count = DanceClass.query.filter_by(studio_id=studio.id).count()
            contact_count = Contact.query.filter_by(studio_id=studio.id).count()
            
            studios.append({
                'id': studio.id,
                'name': studio.name,
                'slug': studio.slug,
                'email': studio.email,
                'phone': studio.phone,
                'address': studio.address,
                'city': studio.city,
                'created_at': studio.created_at.isoformat() if studio.created_at else None,
                'onboarding_completed': studio.onboarding_completed,
                'owner': {
                    'id': owner.id,
                    'name': owner.name,
                    'email': owner.email
                } if owner else None,
                'stats': {
                    'bookings': booking_count,
                    'classes': class_count,
                    'contacts': contact_count
                }
            })
        
        return jsonify({
            'studios': studios,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/studios/<studio_id>', methods=['GET'])
@admin_required
def get_studio_details(studio_id):
    """Get detailed information about a specific studio."""
    try:
        studio = Studio.query.get(studio_id)
        if not studio:
            return jsonify({'error': 'Studio not found'}), 404
        
        # Get owner
        owner = User.query.filter_by(studio_id=studio.id, role='owner').first()
        
        # Get all staff
        staff = User.query.filter_by(studio_id=studio.id).all()
        
        # Get all classes
        classes = DanceClass.query.filter_by(studio_id=studio.id).all()
        
        # Get booking stats
        total_bookings = Booking.query.filter_by(studio_id=studio.id).count()
        confirmed_bookings = Booking.query.filter_by(studio_id=studio.id, status='CONFIRMED').count()
        cancelled_bookings = Booking.query.filter_by(studio_id=studio.id, status='CANCELLED').count()
        
        # Get recent bookings
        recent_bookings = Booking.query.filter_by(studio_id=studio.id).order_by(
            desc(Booking.booked_at)
        ).limit(10).all()
        
        # Get contacts count
        contacts_count = Contact.query.filter_by(studio_id=studio.id).count()
        
        # Get sessions count
        sessions_count = db.session.query(ClassSession).join(DanceClass).filter(
            DanceClass.studio_id == studio.id
        ).count()
        
        return jsonify({
            'studio': {
                'id': studio.id,
                'name': studio.name,
                'slug': studio.slug,
                'email': studio.email,
                'phone': studio.phone,
                'address': studio.address,
                'city': studio.city,
                'state': studio.state,
                'pincode': studio.pincode,
                'description': studio.description,
                'logo_url': studio.logo_url,
                'timezone': studio.timezone,
                'created_at': studio.created_at.isoformat() if studio.created_at else None,
                'onboarding_completed': studio.onboarding_completed,
                'onboarding_step': studio.onboarding_step
            },
            'owner': {
                'id': owner.id,
                'name': owner.name,
                'email': owner.email,
                'phone': owner.phone,
                'created_at': owner.created_at.isoformat() if owner and owner.created_at else None,
                'last_login': owner.last_login.isoformat() if owner and owner.last_login else None
            } if owner else None,
            'staff': [{
                'id': s.id,
                'name': s.name,
                'email': s.email,
                'role': s.role
            } for s in staff],
            'classes': [{
                'id': c.id,
                'name': c.name,
                'dance_style': c.dance_style,
                'level': c.level,
                'price': c.drop_in_price
            } for c in classes],
            'stats': {
                'total_bookings': total_bookings,
                'confirmed_bookings': confirmed_bookings,
                'cancelled_bookings': cancelled_bookings,
                'total_classes': len(classes),
                'total_sessions': sessions_count,
                'total_contacts': contacts_count,
                'staff_count': len(staff)
            },
            'recent_bookings': [{
                'id': b.id,
                'customer_name': b.customer_name,
                'customer_email': b.customer_email,
                'status': b.status,
                'booked_at': b.booked_at.isoformat() if b.booked_at else None
            } for b in recent_bookings]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# USER MANAGEMENT
# ============================================

@admin_bp.route('/users', methods=['GET'])
@admin_required
def list_all_users():
    """List all platform users."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        user_type = request.args.get('user_type', '')  # studio_owner, customer, or empty for all
        search = request.args.get('search', '')
        
        query = User.query
        
        if user_type:
            query = query.filter_by(user_type=user_type)
        
        if search:
            query = query.filter(
                db.or_(
                    User.name.ilike(f'%{search}%'),
                    User.email.ilike(f'%{search}%')
                )
            )
        
        query = query.order_by(desc(User.created_at))
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        users = []
        for user in pagination.items:
            studio_name = None
            if user.studio_id:
                studio = Studio.query.get(user.studio_id)
                studio_name = studio.name if studio else None
            
            users.append({
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'phone': user.phone,
                'role': user.role,
                'user_type': user.user_type,
                'studio_name': studio_name,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None
            })
        
        return jsonify({
            'users': users,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# RECENT ACTIVITY
# ============================================

@admin_bp.route('/activity/recent', methods=['GET'])
@admin_required
def get_recent_activity():
    """Get recent platform activity."""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        # Recent studios
        recent_studios = Studio.query.order_by(desc(Studio.created_at)).limit(10).all()
        
        # Recent bookings
        recent_bookings = Booking.query.order_by(desc(Booking.booked_at)).limit(20).all()
        
        # Recent users
        recent_users = User.query.order_by(desc(User.created_at)).limit(10).all()
        
        activity = []
        
        for studio in recent_studios:
            activity.append({
                'type': 'new_studio',
                'message': f"New studio registered: {studio.name}",
                'timestamp': studio.created_at.isoformat() if studio.created_at else None,
                'data': {'studio_id': studio.id, 'studio_name': studio.name}
            })
        
        for booking in recent_bookings:
            studio = Studio.query.get(booking.studio_id)
            activity.append({
                'type': 'booking',
                'message': f"Booking at {studio.name if studio else 'Unknown'}: {booking.customer_name}",
                'timestamp': booking.booked_at.isoformat() if booking.booked_at else None,
                'data': {'booking_id': booking.id, 'studio_name': studio.name if studio else None}
            })
        
        for user in recent_users:
            activity.append({
                'type': 'new_user',
                'message': f"New {user.user_type} registered: {user.name}",
                'timestamp': user.created_at.isoformat() if user.created_at else None,
                'data': {'user_id': user.id, 'user_type': user.user_type}
            })
        
        # Sort by timestamp
        activity.sort(key=lambda x: x['timestamp'] or '', reverse=True)
        
        return jsonify({'activity': activity[:limit]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

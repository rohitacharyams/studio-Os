from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import uuid
import re

from app import db
from app.models import User, Studio, StudioKnowledge, DanceClass, ClassSchedule, ClassSession

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
        # Regenerate slug if name changed
        if not studio.slug or studio.slug == '':
            base_slug = data['name'].lower()
            base_slug = re.sub(r'[^a-z0-9\s-]', '', base_slug)
            base_slug = re.sub(r'[\s_]+', '-', base_slug)
            base_slug = re.sub(r'-+', '-', base_slug).strip('-')
            slug = base_slug
            counter = 1
            while Studio.query.filter(Studio.slug == slug, Studio.id != studio.id).first():
                slug = f"{base_slug}-{counter}"
                counter += 1
            studio.slug = slug
    if 'email' in data:
        studio.email = data['email']
    if 'phone' in data:
        studio.phone = data['phone']
    if 'address' in data:
        studio.address = data['address']
    if 'city' in data:
        studio.city = data['city']
    if 'website' in data:
        studio.website = data['website']
    if 'logo_url' in data:
        studio.logo_url = data['logo_url']
    if 'timezone' in data:
        studio.timezone = data['timezone']
    if 'currency' in data:
        studio.currency = data['currency']
    if 'business_hours_open' in data:
        studio.business_hours_open = data['business_hours_open']
    if 'business_hours_close' in data:
        studio.business_hours_close = data['business_hours_close']
    
    try:
        db.session.commit()
        return jsonify({'studio': studio.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================
# ONBOARDING ENDPOINTS
# ============================================================

@studio_bp.route('/onboarding', methods=['GET'])
@jwt_required()
def get_onboarding_status():
    """Get onboarding status and progress."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    studio = user.studio
    return jsonify({
        'onboarding_completed': studio.onboarding_completed,
        'onboarding_step': studio.onboarding_step,
        'studio': studio.to_dict()
    })


@studio_bp.route('/onboarding/step/<int:step>', methods=['POST'])
@jwt_required()
def save_onboarding_step(step):
    """Save onboarding step data."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user.role not in ['owner', 'admin']:
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    studio = user.studio
    data = request.get_json()
    
    try:
        if step == 0:
            # Step 0: Studio Profile
            if 'name' in data:
                studio.name = data['name']
            if 'phone' in data:
                studio.phone = data['phone']
            if 'email' in data:
                studio.email = data['email']
            if 'address' in data:
                studio.address = data['address']
            if 'city' in data:
                studio.city = data['city']
            if 'website' in data:
                studio.website = data['website']
            if 'timezone' in data:
                studio.timezone = data['timezone']
            if 'business_hours' in data:
                studio.business_hours_open = data['business_hours'].get('open', '09:00')
                studio.business_hours_close = data['business_hours'].get('close', '21:00')
            
            # Generate slug from name
            if studio.name and (not studio.slug or studio.slug == ''):
                base_slug = studio.name.lower()
                base_slug = re.sub(r'[^a-z0-9\s-]', '', base_slug)
                base_slug = re.sub(r'[\s_]+', '-', base_slug)
                base_slug = re.sub(r'-+', '-', base_slug).strip('-')
                slug = base_slug
                counter = 1
                while Studio.query.filter(Studio.slug == slug, Studio.id != studio.id).first():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                studio.slug = slug
                
        elif step == 1:
            # Step 1: Connect Channels
            if 'whatsapp' in data:
                studio.whatsapp_settings = {
                    **(studio.whatsapp_settings or {}),
                    'connected': data['whatsapp'].get('connected', False),
                    'phone_number': data['whatsapp'].get('number', ''),
                    'business_id': data['whatsapp'].get('business_id', ''),
                    'access_token': data['whatsapp'].get('access_token', '')
                }
            if 'gmail' in data:
                studio.email_settings = {
                    **(studio.email_settings or {}),
                    'connected': data['gmail'].get('connected', False),
                    'email': data['gmail'].get('email', ''),
                    'provider': 'gmail'
                }
            if 'instagram' in data:
                studio.instagram_settings = {
                    **(studio.instagram_settings or {}),
                    'connected': data['instagram'].get('connected', False),
                    'handle': data['instagram'].get('handle', ''),
                    'access_token': data['instagram'].get('access_token', '')
                }
                
        elif step == 2:
            # Step 2: Set Up Classes
            classes_data = data.get('classes', [])
            today = datetime.utcnow().date()
            
            for class_data in classes_data:
                if class_data.get('name'):
                    dance_class = DanceClass(
                        id=str(uuid.uuid4()),
                        studio_id=studio.id,
                        name=class_data['name'],
                        dance_style=class_data.get('style', 'General'),
                        level=class_data.get('level', 'all_levels'),
                        description=class_data.get('description', ''),
                        duration_minutes=class_data.get('duration', 60),
                        max_capacity=class_data.get('capacity', 15),
                        price=class_data.get('price', 500),
                        is_active=True
                    )
                    db.session.add(dance_class)
                    db.session.flush()  # Get ID for class
                    
                    # Parse schedule times from class_data
                    schedule_times = class_data.get('schedule', [])
                    
                    # Default time objects
                    default_start_time = datetime.strptime('18:00', '%H:%M').time()
                    default_end_time = datetime.strptime('19:00', '%H:%M').time()
                    
                    # If no schedule provided, create sessions for next 14 days
                    if not schedule_times:
                        # Default: Schedule for next 14 days at 6 PM
                        for day_offset in range(14):
                            session_date = today + timedelta(days=day_offset)
                            
                            # Create schedule entry
                            schedule = ClassSchedule(
                                id=str(uuid.uuid4()),
                                studio_id=studio.id,
                                class_id=dance_class.id,
                                day_of_week=session_date.weekday(),
                                specific_date=session_date,
                                start_time=default_start_time,
                                end_time=default_end_time,
                                is_recurring=False
                            )
                            db.session.add(schedule)
                            
                            # Create actual session instance
                            session = ClassSession(
                                id=str(uuid.uuid4()),
                                studio_id=studio.id,
                                schedule_id=schedule.id,
                                class_id=dance_class.id,
                                date=session_date,
                                start_time=datetime.combine(session_date, default_start_time),
                                end_time=datetime.combine(session_date, default_end_time),
                                max_capacity=dance_class.max_capacity,
                                booked_count=0,
                                status='SCHEDULED'
                            )
                            db.session.add(session)
                    else:
                        # Use provided schedule
                        for sched in schedule_times:
                            session_date = datetime.fromisoformat(sched.get('date')).date() if sched.get('date') else today
                            start_time_str = sched.get('start_time', '18:00')
                            end_time_str = sched.get('end_time', '19:00')
                            start_time = datetime.strptime(start_time_str, '%H:%M').time()
                            end_time = datetime.strptime(end_time_str, '%H:%M').time()
                            
                            schedule = ClassSchedule(
                                id=str(uuid.uuid4()),
                                studio_id=studio.id,
                                class_id=dance_class.id,
                                day_of_week=session_date.weekday(),
                                specific_date=session_date,
                                start_time=start_time,
                                end_time=end_time,
                                is_recurring=False
                            )
                            db.session.add(schedule)
                            
                            session = ClassSession(
                                id=str(uuid.uuid4()),
                                studio_id=studio.id,
                                schedule_id=schedule.id,
                                class_id=dance_class.id,
                                date=session_date,
                                start_time=datetime.combine(session_date, start_time),
                                end_time=datetime.combine(session_date, end_time),
                                max_capacity=dance_class.max_capacity,
                                booked_count=0,
                                status='SCHEDULED'
                            )
                            db.session.add(session)
                    
        elif step == 3:
            # Step 3: Payment Setup
            if 'razorpay_key_id' in data:
                studio.razorpay_key_id = data['razorpay_key_id']
            if 'razorpay_key_secret' in data:
                studio.razorpay_key_secret = data['razorpay_key_secret']
                
        elif step == 4:
            # Step 4: Complete - Generate booking link
            studio.onboarding_completed = True
        
        # Update onboarding step
        studio.onboarding_step = max(studio.onboarding_step, step + 1)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'onboarding_step': studio.onboarding_step,
            'studio': studio.to_dict(),
            'booking_link': f"/book/{studio.slug}" if studio.slug else None
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@studio_bp.route('/onboarding/complete', methods=['POST'])
@jwt_required()
def complete_onboarding():
    """Mark onboarding as complete."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    studio = user.studio
    studio.onboarding_completed = True
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'studio': studio.to_dict(),
            'booking_link': f"/book/{studio.slug}"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================
# PUBLIC STUDIO ENDPOINT (No Auth Required)
# ============================================================

@studio_bp.route('/public/<slug>', methods=['GET'])
def get_public_studio(slug):
    """Get public studio info by slug (for booking page)."""
    studio = Studio.query.filter_by(slug=slug).first()
    
    if not studio:
        return jsonify({'error': 'Studio not found'}), 404
    
    # Get active classes
    classes = DanceClass.query.filter_by(
        studio_id=studio.id, 
        is_active=True
    ).all()
    
    return jsonify({
        'studio': {
            'id': studio.id,
            'name': studio.name,
            'slug': studio.slug,
            'phone': studio.phone,
            'email': studio.email,
            'address': studio.address,
            'city': studio.city,
            'website': studio.website,
            'logo_url': studio.logo_url,
            'timezone': studio.timezone,
            'currency': studio.currency,
            'business_hours_open': studio.business_hours_open,
            'business_hours_close': studio.business_hours_close
        },
        'classes': [c.to_dict() for c in classes]
    })


@studio_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_settings():
    """Get all studio settings."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    studio = user.studio
    return jsonify({
        'settings': {
            'email_settings': studio.email_settings or {},
            'whatsapp_settings': studio.whatsapp_settings or {},
            'instagram_settings': studio.instagram_settings or {}
        }
    })


@studio_bp.route('/settings', methods=['PUT'])
@jwt_required()
def update_settings():
    """Update studio settings (general)."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user.role not in ['owner', 'admin']:
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    data = request.get_json()
    studio = user.studio
    
    # Update settings based on what's passed
    settings = data.get('settings', {})
    
    # Merge with existing settings
    if 'email_settings' in settings:
        studio.email_settings = {**(studio.email_settings or {}), **settings['email_settings']}
    if 'whatsapp_settings' in settings:
        studio.whatsapp_settings = {**(studio.whatsapp_settings or {}), **settings['whatsapp_settings']}
    if 'instagram_settings' in settings:
        studio.instagram_settings = {**(studio.instagram_settings or {}), **settings['instagram_settings']}
    
    # Store any additional settings in whatsapp_settings as a catch-all for now
    for key, value in settings.items():
        if key not in ['email_settings', 'whatsapp_settings', 'instagram_settings']:
            if not studio.whatsapp_settings:
                studio.whatsapp_settings = {}
            studio.whatsapp_settings[key] = value
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'settings': {
                'email_settings': studio.email_settings or {},
                'whatsapp_settings': studio.whatsapp_settings or {},
                'instagram_settings': studio.instagram_settings or {}
            }
        })
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


@studio_bp.route('/settings/payment', methods=['GET'])
@jwt_required()
def get_payment_settings():
    """Get payment settings."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    studio = user.studio
    # Payment settings stored in a JSON field
    payment_settings = getattr(studio, 'payment_settings', None) or {}
    
    return jsonify({'settings': payment_settings})


@studio_bp.route('/settings/payment', methods=['PUT'])
@jwt_required()
def update_payment_settings():
    """Update payment settings."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user.role not in ['owner', 'admin']:
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    data = request.get_json()
    studio = user.studio
    
    # Store payment settings (only store non-sensitive info or encrypt secrets)
    payment_data = {
        'payment_method': data.get('payment_method', 'upi'),
        'upi_id': data.get('upi_id', ''),
        'upi_name': data.get('upi_name', ''),
        'bank_name': data.get('bank_name', ''),
        'account_holder_name': data.get('account_holder_name', ''),
        # Don't store full account number, mask it
        'account_number_masked': data.get('account_number', '')[-4:] if data.get('account_number') else '',
        'ifsc_code': data.get('ifsc_code', ''),
        # For payment gateways, store key IDs (not secrets in plain text in production)
        'razorpay_key_id': data.get('razorpay_key_id', ''),
        'stripe_publishable_key': data.get('stripe_publishable_key', ''),
        # In production, secrets should be encrypted or stored in environment variables
        'razorpay_configured': bool(data.get('razorpay_key_secret')),
        'stripe_configured': bool(data.get('stripe_secret_key')),
    }
    
    studio.payment_settings = payment_data
    
    try:
        db.session.commit()
        return jsonify({'settings': studio.payment_settings, 'message': 'Payment settings saved'})
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


# ============================================================
# EXPLORE ENDPOINTS (For Customers to Browse Studios)
# ============================================================

@studio_bp.route('/explore', methods=['GET'])
def explore_studios():
    """Get list of all active studios for customers to browse."""
    city = request.args.get('city')
    search = request.args.get('search')
    
    query = Studio.query.filter_by(onboarding_completed=True)
    
    if city:
        query = query.filter_by(city=city)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                Studio.name.ilike(search_term),
                Studio.city.ilike(search_term)
            )
        )
    
    studios = query.all()
    
    result = []
    for studio in studios:
        # Count active classes
        class_count = DanceClass.query.filter_by(
            studio_id=studio.id,
            is_active=True
        ).count()
        
        result.append({
            'id': studio.id,
            'name': studio.name,
            'slug': studio.slug,
            'description': f"Welcome to {studio.name}!",
            'address': studio.address,
            'city': studio.city,
            'logo_url': studio.logo_url,
            'rating': 4.8,  # TODO: Implement actual ratings
            'total_classes': class_count
        })
    
    return jsonify({'studios': result})


# ============================================================
# CLASS MANAGEMENT ENDPOINTS
# ============================================================

@studio_bp.route('/classes', methods=['GET'])
@jwt_required()
def get_classes():
    """Get all classes for the studio."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.studio_id:
        return jsonify({'error': 'No studio found'}), 404
    
    classes = DanceClass.query.filter_by(studio_id=user.studio_id).all()
    
    result = []
    for c in classes:
        instructor = User.query.get(c.instructor_id) if c.instructor_id else None
        result.append({
            **c.to_dict(),
            'instructor_name': instructor.name if instructor else 'TBA'
        })
    
    return jsonify({'classes': result})


@studio_bp.route('/classes', methods=['POST'])
@jwt_required()
def create_class():
    """Create a new class with optional sessions."""
    import uuid
    from datetime import datetime, time, timedelta
    
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.studio_id:
        return jsonify({'error': 'No studio found'}), 404
    
    if user.role not in ['owner', 'admin']:
        return jsonify({'error': 'Only studio owners can create classes'}), 403
    
    data = request.json
    
    # Validate required fields
    if not data.get('name'):
        return jsonify({'error': 'Class name is required'}), 400
    
    try:
        # Create the class
        dance_class = DanceClass(
            id=str(uuid.uuid4()),
            studio_id=user.studio_id,
            name=data['name'],
            description=data.get('description', ''),
            dance_style=data.get('dance_style', ''),
            level=data.get('level', 'All Levels'),
            duration_minutes=int(data.get('duration_minutes', 60)),
            max_capacity=int(data.get('max_capacity', 20)),
            min_capacity=int(data.get('min_capacity', 3)),
            price=float(data.get('price', 500)),
            instructor_id=data.get('instructor_id'),
            is_active=True
        )
        
        db.session.add(dance_class)
        db.session.flush()  # Get the class ID
        
        # Create sessions if dates provided
        sessions_created = []
        session_errors = []
        
        if data.get('session_dates'):
            for session_date_str in data['session_dates']:
                try:
                    session_date = datetime.strptime(session_date_str, '%Y-%m-%d').date()
                    
                    # Parse time or use default
                    start_time_str = data.get('start_time', '18:00')
                    start_parts = start_time_str.split(':')
                    start_time = time(int(start_parts[0]), int(start_parts[1]))
                    
                    # Calculate end time properly handling overflow
                    duration = dance_class.duration_minutes
                    end_minutes = start_time.minute + (duration % 60)
                    end_hours = start_time.hour + (duration // 60) + (end_minutes // 60)
                    end_time = time(end_hours % 24, end_minutes % 60)
                    
                    # Create schedule
                    schedule = ClassSchedule(
                        id=str(uuid.uuid4()),
                        studio_id=user.studio_id,
                        class_id=dance_class.id,
                        specific_date=session_date,
                        day_of_week=session_date.weekday(),
                        start_time=start_time,
                        end_time=end_time,
                        room=data.get('room', 'Main Studio'),
                        instructor_id=data.get('instructor_id'),
                        is_recurring=False,
                        current_enrollment=0
                    )
                    db.session.add(schedule)
                    db.session.flush()  # Get the schedule ID
                    
                    # Create session - room_id is optional, don't require it
                    session = ClassSession(
                        id=str(uuid.uuid4()),
                        studio_id=user.studio_id,
                        schedule_id=schedule.id,
                        class_id=dance_class.id,
                        date=session_date,
                        start_time=datetime.combine(session_date, start_time),
                        end_time=datetime.combine(session_date, end_time),
                        instructor_id=data.get('instructor_id'),
                        max_capacity=dance_class.max_capacity,
                        booked_count=0,
                        status='SCHEDULED',
                        room_id=None  # Explicitly set to None since we don't have rooms
                    )
                    db.session.add(session)
                    sessions_created.append(session_date_str)
                    
                except Exception as e:
                    session_errors.append(f"{session_date_str}: {str(e)}")
                    continue
        
        db.session.commit()
        
        instructor = User.query.get(dance_class.instructor_id) if dance_class.instructor_id else None
        
        response = {
            'message': 'Class created successfully',
            'class': {
                **dance_class.to_dict(),
                'instructor_name': instructor.name if instructor else 'TBA'
            },
            'sessions_created': sessions_created
        }
        
        if session_errors:
            response['session_errors'] = session_errors
        
        return jsonify(response), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create class: {str(e)}'}), 500


@studio_bp.route('/classes/<class_id>', methods=['PUT'])
@jwt_required()
def update_class(class_id):
    """Update a class."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.studio_id:
        return jsonify({'error': 'No studio found'}), 404
    
    dance_class = DanceClass.query.filter_by(id=class_id, studio_id=user.studio_id).first()
    if not dance_class:
        return jsonify({'error': 'Class not found'}), 404
    
    data = request.json
    
    if 'name' in data:
        dance_class.name = data['name']
    if 'description' in data:
        dance_class.description = data['description']
    if 'dance_style' in data:
        dance_class.dance_style = data['dance_style']
    if 'level' in data:
        dance_class.level = data['level']
    if 'duration_minutes' in data:
        dance_class.duration_minutes = int(data['duration_minutes'])
    if 'max_capacity' in data:
        dance_class.max_capacity = int(data['max_capacity'])
    if 'price' in data:
        dance_class.price = float(data['price'])
    if 'instructor_id' in data:
        dance_class.instructor_id = data['instructor_id']
    if 'is_active' in data:
        dance_class.is_active = data['is_active']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Class updated successfully',
        'class': dance_class.to_dict()
    })


@studio_bp.route('/classes/<class_id>', methods=['DELETE'])
@jwt_required()
def delete_class(class_id):
    """Delete (deactivate) a class."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.studio_id:
        return jsonify({'error': 'No studio found'}), 404
    
    dance_class = DanceClass.query.filter_by(id=class_id, studio_id=user.studio_id).first()
    if not dance_class:
        return jsonify({'error': 'Class not found'}), 404
    
    # Soft delete - just deactivate
    dance_class.is_active = False
    db.session.commit()
    
    return jsonify({'message': 'Class deleted successfully'})


@studio_bp.route('/instructors', methods=['GET'])
@jwt_required()
def get_instructors():
    """Get all instructors for the studio."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.studio_id:
        return jsonify({'error': 'No studio found'}), 404
    
    # Get users with role 'instructor' for this studio
    instructors = User.query.filter_by(
        studio_id=user.studio_id,
        role='instructor'
    ).all()
    
    # Also include the owner as potential instructor
    owner = User.query.filter_by(
        studio_id=user.studio_id,
        role='owner'
    ).first()
    
    result = []
    if owner:
        result.append({
            'id': owner.id,
            'name': owner.name,
            'email': owner.email,
            'role': 'owner'
        })
    
    for inst in instructors:
        result.append({
            'id': inst.id,
            'name': inst.name,
            'email': inst.email,
            'role': 'instructor'
        })
    
    return jsonify({'instructors': result})


@studio_bp.route('/explore/classes', methods=['GET'])
def explore_classes():
    """Get upcoming classes from all studios for customers to browse."""
    from datetime import datetime, timedelta
    from app.models import ClassSchedule
    
    # Get classes for the next 7 days
    today = datetime.now().date()
    end_date = today + timedelta(days=7)
    
    # Get all active studios
    studios = Studio.query.filter_by(onboarding_completed=True).all()
    studio_ids = [s.id for s in studios]
    
    # Get schedules for these studios
    schedules = ClassSchedule.query.join(DanceClass).filter(
        DanceClass.studio_id.in_(studio_ids),
        DanceClass.is_active == True,
        ClassSchedule.date >= today,
        ClassSchedule.date <= end_date,
        ClassSchedule.is_cancelled == False
    ).order_by(ClassSchedule.date, ClassSchedule.start_time).limit(20).all()
    
    result = []
    for schedule in schedules:
        dance_class = schedule.dance_class
        studio = dance_class.studio
        
        result.append({
            'id': schedule.id,
            'studio_id': studio.id,
            'studio_name': studio.name,
            'studio_slug': studio.slug,
            'class_name': dance_class.name,
            'style': dance_class.dance_style,
            'level': dance_class.level,
            'instructor_name': dance_class.instructor_name or 'TBA',
            'start_time': schedule.start_time.strftime('%H:%M') if schedule.start_time else '18:00',
            'date': schedule.date.isoformat() if schedule.date else today.isoformat(),
            'price': float(dance_class.price) if dance_class.price else 500,
            'spots_available': dance_class.max_capacity - (schedule.current_bookings or 0)
        })
    
    return jsonify({'classes': result})


# ============================================================
# CALENDAR ENDPOINTS
# ============================================================

@studio_bp.route('/calendar/events', methods=['GET'])
@jwt_required()
def get_calendar_events():
    """Get calendar events (class sessions) for a date range."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.studio_id:
        return jsonify({'error': 'No studio found'}), 404
    
    # Get date range from query params
    start_date_str = request.args.get('start')
    end_date_str = request.args.get('end')
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else datetime.now().date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else start_date + timedelta(days=30)
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    # Get class sessions in the date range
    sessions = ClassSession.query.filter(
        ClassSession.studio_id == user.studio_id,
        ClassSession.date >= start_date,
        ClassSession.date <= end_date
    ).order_by(ClassSession.date, ClassSession.start_time).all()
    
    events = []
    for session in sessions:
        # Get associated dance class
        dance_class = DanceClass.query.get(session.class_id)
        
        # Get schedule for recurring info
        schedule = ClassSchedule.query.get(session.schedule_id) if session.schedule_id else None
        
        events.append({
            'id': session.id,
            'class_id': session.class_id,
            'schedule_id': session.schedule_id,
            'title': dance_class.name if dance_class else 'Unknown Class',
            'dance_style': dance_class.dance_style if dance_class else 'Other',
            'level': dance_class.level if dance_class else 'All Levels',
            'date': session.date.isoformat(),
            'start_time': session.start_time.strftime('%H:%M') if session.start_time else '18:00',
            'end_time': session.end_time.strftime('%H:%M') if session.end_time else '19:00',
            'instructor_name': dance_class.instructor_name if dance_class else 'TBA',
            'room': schedule.room if schedule else 'Main Studio',
            'max_capacity': session.max_capacity or (dance_class.max_capacity if dance_class else 20),
            'booked_count': session.booked_count or 0,
            'status': session.status or 'scheduled',
            'is_recurring': schedule.is_recurring if schedule else False,
            'price': float(dance_class.price) if dance_class and dance_class.price else 0
        })
    
    return jsonify({'events': events})


@studio_bp.route('/calendar/recurring', methods=['POST'])
@jwt_required()
def create_recurring_class():
    """Create a recurring class with multiple sessions."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.studio_id:
        return jsonify({'error': 'No studio found'}), 404
    
    data = request.get_json()
    
    required_fields = ['name', 'dance_style', 'start_date', 'start_time', 'end_time', 'recurrence_type']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    try:
        # Parse dates and times
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data.get('end_date', data['start_date']), '%Y-%m-%d').date() if data.get('end_date') else start_date + timedelta(days=90)
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        
        # Create or find dance class
        class_id = data.get('class_id')
        if class_id:
            dance_class = DanceClass.query.get(class_id)
            if not dance_class or dance_class.studio_id != user.studio_id:
                return jsonify({'error': 'Invalid class ID'}), 400
        else:
            # Create new dance class
            dance_class = DanceClass(
                id=str(uuid.uuid4()),
                studio_id=user.studio_id,
                name=data['name'],
                description=data.get('description', ''),
                dance_style=data['dance_style'],
                level=data.get('level', 'All Levels'),
                instructor_name=data.get('instructor_name', ''),
                max_capacity=data.get('max_capacity', 20),
                duration_minutes=data.get('duration', 60),
                price=data.get('price', 0),
                is_active=True
            )
            db.session.add(dance_class)
        
        # Create schedule
        schedule = ClassSchedule(
            id=str(uuid.uuid4()),
            class_id=dance_class.id,
            day_of_week=start_date.weekday(),
            start_time=start_time,
            end_time=end_time,
            date=start_date,
            room=data.get('room', 'Main Studio'),
            is_recurring=data.get('recurrence_type') != 'none',
            recurrence_pattern=data.get('recurrence_type', 'weekly'),
            recurrence_end_date=end_date,
            is_active=True
        )
        db.session.add(schedule)
        
        # Generate session dates based on recurrence
        session_dates = []
        recurrence_type = data.get('recurrence_type', 'weekly')
        selected_days = data.get('selected_days', [start_date.weekday()])  # Days of week (0=Mon, 6=Sun)
        
        current_date = start_date
        while current_date <= end_date:
            if recurrence_type == 'none':
                session_dates.append(current_date)
                break
            elif recurrence_type == 'daily':
                session_dates.append(current_date)
                current_date += timedelta(days=1)
            elif recurrence_type == 'weekly':
                if current_date.weekday() in selected_days:
                    session_dates.append(current_date)
                current_date += timedelta(days=1)
            elif recurrence_type == 'biweekly':
                if current_date.weekday() in selected_days:
                    session_dates.append(current_date)
                # Skip to next day, but every 2 weeks for first occurrence
                current_date += timedelta(days=1)
            elif recurrence_type == 'monthly':
                session_dates.append(current_date)
                # Move to same day next month
                month = current_date.month + 1
                year = current_date.year
                if month > 12:
                    month = 1
                    year += 1
                try:
                    current_date = current_date.replace(year=year, month=month)
                except ValueError:
                    # Handle month with fewer days
                    break
            else:
                break
        
        # Create sessions for each date
        sessions_created = 0
        for session_date in session_dates:
            session = ClassSession(
                id=str(uuid.uuid4()),
                studio_id=user.studio_id,
                schedule_id=schedule.id,
                class_id=dance_class.id,
                date=session_date,
                start_time=start_time,
                end_time=end_time,
                max_capacity=data.get('max_capacity', 20),
                booked_count=0,
                status='scheduled'
            )
            db.session.add(session)
            sessions_created += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'Recurring class created with {sessions_created} sessions',
            'class_id': dance_class.id,
            'schedule_id': schedule.id,
            'sessions_created': sessions_created,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': f'Invalid date/time format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@studio_bp.route('/calendar/session/<session_id>', methods=['PUT'])
@jwt_required()
def update_calendar_session(session_id):
    """Update a single class session."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.studio_id:
        return jsonify({'error': 'No studio found'}), 404
    
    session = ClassSession.query.get(session_id)
    if not session or session.studio_id != user.studio_id:
        return jsonify({'error': 'Session not found'}), 404
    
    data = request.get_json()
    
    try:
        if 'date' in data:
            session.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        if 'start_time' in data:
            session.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        if 'end_time' in data:
            session.end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        if 'max_capacity' in data:
            session.max_capacity = data['max_capacity']
        if 'status' in data:
            session.status = data['status']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Session updated',
            'session_id': session.id
        })
        
    except ValueError as e:
        return jsonify({'error': f'Invalid format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@studio_bp.route('/calendar/session/<session_id>', methods=['DELETE'])
@jwt_required()
def delete_calendar_session(session_id):
    """Delete a single class session."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.studio_id:
        return jsonify({'error': 'No studio found'}), 404
    
    session = ClassSession.query.get(session_id)
    if not session or session.studio_id != user.studio_id:
        return jsonify({'error': 'Session not found'}), 404
    
    try:
        db.session.delete(session)
        db.session.commit()
        return jsonify({'message': 'Session deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
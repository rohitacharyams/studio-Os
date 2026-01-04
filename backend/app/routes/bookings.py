"""
Booking API routes for class bookings, sessions, and waitlist management.
"""
import uuid
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import (
    User, Contact, ClassSession, Booking, Waitlist,
    ClassSchedule, DanceClass, Instructor, Room, ClassPackPurchase, Subscription
)

bookings_bp = Blueprint('bookings', __name__, url_prefix='/api/bookings')


def generate_booking_number():
    """Generate unique booking number."""
    year = datetime.utcnow().year
    # Get count of bookings this year
    count = Booking.query.filter(
        db.extract('year', Booking.created_at) == year
    ).count()
    return f"BK-{year}-{str(count + 1).zfill(5)}"


# ============================================================
# CLASS SESSIONS
# ============================================================

@bookings_bp.route('/sessions', methods=['GET'])
@jwt_required()
def list_sessions():
    """List upcoming class sessions."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    class_type = request.args.get('class_type')
    instructor_id = request.args.get('instructor_id')
    
    # Default to next 7 days
    if not start_date:
        start_date = datetime.utcnow().date()
    else:
        start_date = datetime.fromisoformat(start_date).date()
    
    if not end_date:
        end_date = start_date + timedelta(days=7)
    else:
        end_date = datetime.fromisoformat(end_date).date()
    
    query = ClassSession.query.filter(
        ClassSession.studio_id == user.studio_id,
        ClassSession.date >= start_date,
        ClassSession.date <= end_date,
        ClassSession.status != 'CANCELLED'
    )
    
    if instructor_id:
        query = query.filter(ClassSession.instructor_id == instructor_id)
    
    sessions = query.order_by(ClassSession.date, ClassSession.start_time).all()
    
    # Enrich with class details
    result = []
    for session in sessions:
        session_data = session.to_dict()
        
        # Add class info
        if session.class_id:
            dance_class = DanceClass.query.get(session.class_id)
            if dance_class:
                session_data['class_name'] = dance_class.name
                session_data['class_type'] = dance_class.style
                session_data['level'] = dance_class.level
                session_data['drop_in_price'] = float(dance_class.drop_in_price) if dance_class.drop_in_price else 0
        
        # Add instructor info
        if session.instructor_id:
            instructor = Instructor.query.get(session.instructor_id)
            if instructor:
                session_data['instructor_name'] = instructor.name
        
        # Add room info
        if session.room_id:
            room = Room.query.get(session.room_id)
            if room:
                session_data['room_name'] = room.name
        
        result.append(session_data)
    
    return jsonify({
        'sessions': result,
        'total': len(result),
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat()
    })


@bookings_bp.route('/sessions/<session_id>', methods=['GET'])
@jwt_required()
def get_session(session_id):
    """Get session details with availability."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    session = ClassSession.query.filter_by(
        id=session_id,
        studio_id=user.studio_id
    ).first()
    
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    session_data = session.to_dict(include_bookings=False)
    
    # Add class info
    if session.class_id:
        dance_class = DanceClass.query.get(session.class_id)
        if dance_class:
            session_data['class'] = dance_class.to_dict()
    
    # Add instructor info
    if session.instructor_id:
        instructor = Instructor.query.get(session.instructor_id)
        if instructor:
            session_data['instructor'] = instructor.to_dict()
    
    # Add room info
    if session.room_id:
        room = Room.query.get(session.room_id)
        if room:
            session_data['room'] = room.to_dict()
    
    # Get attendee list (for staff)
    if user.role in ['owner', 'admin', 'staff']:
        bookings = Booking.query.filter_by(
            session_id=session_id,
            status='CONFIRMED'
        ).all()
        
        attendees = []
        for booking in bookings:
            contact = Contact.query.get(booking.contact_id)
            if contact:
                attendees.append({
                    'booking_id': booking.id,
                    'contact_name': contact.name,
                    'contact_phone': contact.phone,
                    'checked_in': booking.checked_in_at is not None
                })
        
        session_data['attendees'] = attendees
    
    return jsonify(session_data)


@bookings_bp.route('/sessions', methods=['POST'])
@jwt_required()
def create_session():
    """Create a new class session (admin only)."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role not in ['owner', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    required = ['class_id', 'date', 'start_time', 'end_time']
    for field in required:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    # Parse datetime
    session_date = datetime.fromisoformat(data['date']).date()
    start_time = datetime.fromisoformat(data['start_time'])
    end_time = datetime.fromisoformat(data['end_time'])
    
    # Get class details for defaults
    dance_class = DanceClass.query.get(data['class_id'])
    if not dance_class:
        return jsonify({'error': 'Class not found'}), 404
    
    session = ClassSession(
        id=str(uuid.uuid4()),
        studio_id=user.studio_id,
        class_id=data['class_id'],
        date=session_date,
        start_time=start_time,
        end_time=end_time,
        max_capacity=data.get('max_capacity', dance_class.max_students or 15),
        instructor_id=data.get('instructor_id', dance_class.instructor_id),
        room_id=data.get('room_id'),
        status='SCHEDULED',
        notes=data.get('notes')
    )
    
    db.session.add(session)
    db.session.commit()
    
    return jsonify(session.to_dict()), 201


# ============================================================
# BOOKINGS
# ============================================================

@bookings_bp.route('', methods=['GET'])
@jwt_required()
def list_bookings():
    """List bookings - staff sees all, contacts see their own."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Query parameters
    contact_id = request.args.get('contact_id')
    session_id = request.args.get('session_id')
    status = request.args.get('status')
    upcoming_only = request.args.get('upcoming', 'false').lower() == 'true'
    
    query = Booking.query.filter_by(studio_id=user.studio_id)
    
    if contact_id:
        query = query.filter_by(contact_id=contact_id)
    
    if session_id:
        query = query.filter_by(session_id=session_id)
    
    if status:
        query = query.filter_by(status=status)
    
    if upcoming_only:
        # Join with sessions to filter by date
        query = query.join(ClassSession).filter(
            ClassSession.date >= datetime.utcnow().date()
        )
    
    bookings = query.order_by(Booking.booked_at.desc()).limit(100).all()
    
    # Enrich with session details
    result = []
    for booking in bookings:
        booking_data = booking.to_dict()
        
        # Add session info
        session = ClassSession.query.get(booking.session_id)
        if session:
            booking_data['session_date'] = session.date.isoformat()
            booking_data['session_time'] = session.start_time.isoformat() if session.start_time else None
            
            # Add class info
            if session.class_id:
                dance_class = DanceClass.query.get(session.class_id)
                if dance_class:
                    booking_data['class_name'] = dance_class.name
        
        # Add contact info
        contact = Contact.query.get(booking.contact_id)
        if contact:
            booking_data['contact_name'] = contact.name
        
        result.append(booking_data)
    
    return jsonify({
        'bookings': result,
        'total': len(result)
    })


@bookings_bp.route('', methods=['POST'])
@jwt_required()
def create_booking():
    """Create a new class booking."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    data = request.get_json()
    
    # Validate required fields
    if 'session_id' not in data:
        return jsonify({'error': 'session_id is required'}), 400
    
    if 'contact_id' not in data:
        return jsonify({'error': 'contact_id is required'}), 400
    
    # Get session
    session = ClassSession.query.filter_by(
        id=data['session_id'],
        studio_id=user.studio_id
    ).first()
    
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    if session.status == 'CANCELLED':
        return jsonify({'error': 'Session has been cancelled'}), 400
    
    # Check if already booked
    existing = Booking.query.filter_by(
        session_id=data['session_id'],
        contact_id=data['contact_id'],
        status='CONFIRMED'
    ).first()
    
    if existing:
        return jsonify({'error': 'Already booked for this session'}), 400
    
    # Check capacity
    if session.is_full:
        # Add to waitlist instead
        return add_to_waitlist(session, data['contact_id'], user.studio_id)
    
    # Determine payment method
    payment_method = data.get('payment_method', 'drop_in')
    payment_id = None
    class_pack_purchase_id = None
    
    if payment_method == 'class_pack':
        # Find active class pack
        class_pack = ClassPackPurchase.query.filter_by(
            contact_id=data['contact_id'],
            status='ACTIVE'
        ).filter(
            ClassPackPurchase.classes_used < ClassPackPurchase.classes_total,
            ClassPackPurchase.expires_at > datetime.utcnow()
        ).first()
        
        if not class_pack:
            return jsonify({'error': 'No active class pack found'}), 400
        
        class_pack_purchase_id = class_pack.id
        class_pack.classes_used += 1
        
        if class_pack.classes_used >= class_pack.classes_total:
            class_pack.status = 'EXHAUSTED'
    
    elif payment_method == 'subscription':
        # Check active subscription
        subscription = Subscription.query.filter_by(
            contact_id=data['contact_id'],
            status='ACTIVE'
        ).first()
        
        if not subscription:
            return jsonify({'error': 'No active subscription found'}), 400
        
        # Check monthly limit if applicable
        if subscription.plan and subscription.plan.classes_per_month:
            if subscription.classes_used_this_period >= subscription.plan.classes_per_month:
                return jsonify({'error': 'Monthly class limit reached'}), 400
        
        subscription.classes_used_this_period += 1
    
    # Create booking
    booking = Booking(
        id=str(uuid.uuid4()),
        booking_number=generate_booking_number(),
        studio_id=user.studio_id,
        contact_id=data['contact_id'],
        session_id=data['session_id'],
        status='CONFIRMED',
        payment_method=payment_method,
        payment_id=payment_id,
        class_pack_purchase_id=class_pack_purchase_id,
        booked_at=datetime.utcnow(),
        confirmed_at=datetime.utcnow()
    )
    
    # Update session booked count
    session.booked_count += 1
    
    db.session.add(booking)
    db.session.commit()
    
    return jsonify({
        'message': 'Booking confirmed',
        'booking': booking.to_dict()
    }), 201


def add_to_waitlist(session, contact_id, studio_id):
    """Add contact to session waitlist."""
    # Check if already on waitlist
    existing = Waitlist.query.filter_by(
        session_id=session.id,
        contact_id=contact_id,
        status='WAITING'
    ).first()
    
    if existing:
        return jsonify({
            'error': 'Already on waitlist',
            'position': existing.position
        }), 400
    
    # Get next position
    max_position = db.session.query(db.func.max(Waitlist.position)).filter_by(
        session_id=session.id,
        status='WAITING'
    ).scalar() or 0
    
    waitlist_entry = Waitlist(
        id=str(uuid.uuid4()),
        studio_id=studio_id,
        session_id=session.id,
        contact_id=contact_id,
        position=max_position + 1,
        status='WAITING'
    )
    
    session.waitlist_count += 1
    
    db.session.add(waitlist_entry)
    db.session.commit()
    
    return jsonify({
        'message': 'Added to waitlist',
        'waitlist': waitlist_entry.to_dict(),
        'position': waitlist_entry.position
    }), 201


@bookings_bp.route('/<booking_id>', methods=['GET'])
@jwt_required()
def get_booking(booking_id):
    """Get booking details."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    booking = Booking.query.filter_by(
        id=booking_id,
        studio_id=user.studio_id
    ).first()
    
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404
    
    booking_data = booking.to_dict(include_session=True)
    
    # Add contact info
    contact = Contact.query.get(booking.contact_id)
    if contact:
        booking_data['contact'] = {
            'id': contact.id,
            'name': contact.name,
            'email': contact.email,
            'phone': contact.phone
        }
    
    return jsonify(booking_data)


@bookings_bp.route('/<booking_id>/cancel', methods=['PUT'])
@jwt_required()
def cancel_booking(booking_id):
    """Cancel a booking."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    booking = Booking.query.filter_by(
        id=booking_id,
        studio_id=user.studio_id
    ).first()
    
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404
    
    if booking.status == 'CANCELLED':
        return jsonify({'error': 'Booking already cancelled'}), 400
    
    if booking.status == 'ATTENDED':
        return jsonify({'error': 'Cannot cancel attended booking'}), 400
    
    data = request.get_json() or {}
    
    # Calculate refund based on cancellation policy
    session = ClassSession.query.get(booking.session_id)
    hours_until_class = 0
    if session:
        class_datetime = datetime.combine(session.date, session.start_time.time())
        hours_until_class = (class_datetime - datetime.utcnow()).total_seconds() / 3600
    
    refund_percentage = 0
    if hours_until_class >= 24:
        refund_percentage = 100
    elif hours_until_class >= 12:
        refund_percentage = 50
    else:
        refund_percentage = 0
    
    # Update booking
    booking.status = 'CANCELLED'
    booking.cancelled_at = datetime.utcnow()
    booking.cancellation_reason = data.get('reason', 'Customer requested')
    
    # Update session count
    if session:
        session.booked_count = max(0, session.booked_count - 1)
    
    # Refund class pack credit
    if booking.class_pack_purchase_id:
        class_pack = ClassPackPurchase.query.get(booking.class_pack_purchase_id)
        if class_pack and refund_percentage > 0:
            class_pack.classes_used = max(0, class_pack.classes_used - 1)
            if class_pack.status == 'EXHAUSTED':
                class_pack.status = 'ACTIVE'
    
    # Process waitlist - promote next person
    if session and session.waitlist_count > 0:
        promote_from_waitlist(session)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Booking cancelled',
        'refund_percentage': refund_percentage,
        'booking': booking.to_dict()
    })


def promote_from_waitlist(session):
    """Promote next person from waitlist to confirmed booking."""
    next_in_line = Waitlist.query.filter_by(
        session_id=session.id,
        status='WAITING'
    ).order_by(Waitlist.position).first()
    
    if not next_in_line:
        return None
    
    # Mark as notified
    next_in_line.status = 'NOTIFIED'
    next_in_line.notified_at = datetime.utcnow()
    next_in_line.expires_at = datetime.utcnow() + timedelta(minutes=30)
    
    session.waitlist_count = max(0, session.waitlist_count - 1)
    
    # If auto-book enabled, create booking immediately
    if next_in_line.auto_book:
        booking = Booking(
            id=str(uuid.uuid4()),
            booking_number=generate_booking_number(),
            studio_id=session.studio_id,
            contact_id=next_in_line.contact_id,
            session_id=session.id,
            status='CONFIRMED',
            payment_method='waitlist_promotion',
            booked_at=datetime.utcnow(),
            confirmed_at=datetime.utcnow()
        )
        
        session.booked_count += 1
        next_in_line.status = 'CONVERTED'
        
        db.session.add(booking)
        
        # TODO: Send notification to contact
        return booking
    
    # TODO: Send notification to contact about available spot
    return None


@bookings_bp.route('/<booking_id>/checkin', methods=['PUT'])
@jwt_required()
def checkin_booking(booking_id):
    """Check in for a class."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role not in ['owner', 'admin', 'staff']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    booking = Booking.query.filter_by(
        id=booking_id,
        studio_id=user.studio_id
    ).first()
    
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404
    
    if booking.status != 'CONFIRMED':
        return jsonify({'error': f'Cannot check in booking with status {booking.status}'}), 400
    
    booking.status = 'ATTENDED'
    booking.checked_in_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'message': 'Checked in successfully',
        'booking': booking.to_dict()
    })


# ============================================================
# WAITLIST
# ============================================================

@bookings_bp.route('/waitlist', methods=['GET'])
@jwt_required()
def list_waitlist():
    """List waitlist entries."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    session_id = request.args.get('session_id')
    contact_id = request.args.get('contact_id')
    
    query = Waitlist.query.filter_by(studio_id=user.studio_id)
    
    if session_id:
        query = query.filter_by(session_id=session_id)
    
    if contact_id:
        query = query.filter_by(contact_id=contact_id)
    
    entries = query.filter_by(status='WAITING').order_by(Waitlist.position).all()
    
    return jsonify({
        'waitlist': [e.to_dict() for e in entries],
        'total': len(entries)
    })


@bookings_bp.route('/waitlist/<entry_id>', methods=['DELETE'])
@jwt_required()
def leave_waitlist(entry_id):
    """Remove from waitlist."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    entry = Waitlist.query.filter_by(
        id=entry_id,
        studio_id=user.studio_id
    ).first()
    
    if not entry:
        return jsonify({'error': 'Waitlist entry not found'}), 404
    
    # Update session waitlist count
    session = ClassSession.query.get(entry.session_id)
    if session:
        session.waitlist_count = max(0, session.waitlist_count - 1)
    
    entry.status = 'CANCELLED'
    
    db.session.commit()
    
    return jsonify({'message': 'Removed from waitlist'})


# ============================================================
# SCHEDULE VIEW
# ============================================================

@bookings_bp.route('/schedule/weekly', methods=['GET'])
@jwt_required()
def weekly_schedule():
    """Get weekly schedule view."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Get start of week (Monday)
    start_date_str = request.args.get('start_date')
    if start_date_str:
        start_date = datetime.fromisoformat(start_date_str).date()
    else:
        today = datetime.utcnow().date()
        start_date = today - timedelta(days=today.weekday())
    
    end_date = start_date + timedelta(days=6)
    
    sessions = ClassSession.query.filter(
        ClassSession.studio_id == user.studio_id,
        ClassSession.date >= start_date,
        ClassSession.date <= end_date,
        ClassSession.status != 'CANCELLED'
    ).order_by(ClassSession.start_time).all()
    
    # Organize by day
    schedule = {i: [] for i in range(7)}  # 0=Monday to 6=Sunday
    
    for session in sessions:
        day_index = session.date.weekday()
        
        session_data = session.to_dict()
        
        # Add class info
        if session.class_id:
            dance_class = DanceClass.query.get(session.class_id)
            if dance_class:
                session_data['class_name'] = dance_class.name
                session_data['class_type'] = dance_class.style
                session_data['level'] = dance_class.level
        
        # Add instructor
        if session.instructor_id:
            instructor = Instructor.query.get(session.instructor_id)
            if instructor:
                session_data['instructor_name'] = instructor.name
        
        schedule[day_index].append(session_data)
    
    return jsonify({
        'schedule': schedule,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat()
    })

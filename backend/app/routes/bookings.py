"""
Booking API routes for class bookings, sessions, and waitlist management.
"""
import uuid
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import (
    User, Contact, ClassSession, Booking, Waitlist, Studio,
    ClassSchedule, DanceClass, Room, ClassPackPurchase, Subscription
)
from app.services.notifications import notification_service

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
                session_data['class_type'] = dance_class.dance_style
                session_data['level'] = dance_class.level
                session_data['drop_in_price'] = float(dance_class.price) if dance_class.price else 0
        
        # Add instructor info
        if session.instructor_id:
            instructor = User.query.get(session.instructor_id)
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
        instructor = User.query.get(session.instructor_id)
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
        max_capacity=data.get('max_capacity', dance_class.max_capacity or 15),
        instructor_id=data.get('instructor_id', dance_class.instructor_id),
        room_id=data.get('room_id'),
        status='SCHEDULED',
        notes=data.get('notes')
    )
    
    db.session.add(session)
    db.session.commit()
    
    return jsonify(session.to_dict()), 201


@bookings_bp.route('/sessions/<session_id>', methods=['PUT'])
@jwt_required()
def update_session(session_id):
    """Update a class session."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role not in ['owner', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    session = ClassSession.query.filter_by(
        id=session_id,
        studio_id=user.studio_id
    ).first()
    
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    data = request.get_json()
    
    # Track if we need to notify customers
    notify_customers = data.get('notify_customers', False)
    changes = []
    
    if 'date' in data:
        new_date = datetime.fromisoformat(data['date']).date()
        if session.date != new_date:
            changes.append(f"Date changed from {session.date.strftime('%b %d')} to {new_date.strftime('%b %d')}")
            session.date = new_date
    
    if 'start_time' in data:
        new_time = datetime.fromisoformat(data['start_time'])
        if session.start_time != new_time:
            changes.append(f"Time changed to {new_time.strftime('%H:%M')}")
            session.start_time = new_time
    
    if 'end_time' in data:
        session.end_time = datetime.fromisoformat(data['end_time'])
    
    if 'max_capacity' in data:
        session.max_capacity = int(data['max_capacity'])
    
    if 'instructor_id' in data:
        session.instructor_id = data['instructor_id']
    
    if 'notes' in data:
        session.notes = data['notes']
    
    db.session.commit()
    
    # Notify booked customers if requested and changes were made
    if notify_customers and changes:
        try:
            bookings = Booking.query.filter_by(
                session_id=session_id,
                status='CONFIRMED'
            ).all()
            
            dance_class = DanceClass.query.get(session.class_id)
            class_name = dance_class.name if dance_class else 'Your class'
            studio = Studio.query.get(user.studio_id)
            
            for booking in bookings:
                contact = Contact.query.get(booking.contact_id)
                if contact:
                    # Send notification via notification service
                    try:
                        notification_service.send_class_update_notification(
                            contact=contact,
                            class_name=class_name,
                            changes=changes,
                            new_date=session.date,
                            new_time=session.start_time,
                            studio=studio
                        )
                    except Exception as e:
                        import logging
                        logging.warning(f"Failed to notify contact {contact.id}: {e}")
        except Exception as e:
            import logging
            logging.error(f"Failed to send session update notifications: {e}")
    
    return jsonify({
        'message': 'Session updated successfully',
        'session': session.to_dict(),
        'changes': changes,
        'customers_notified': len(changes) > 0 and notify_customers
    })


@bookings_bp.route('/sessions/<session_id>', methods=['DELETE'])
@jwt_required()
def delete_session(session_id):
    """Cancel/Delete a class session and notify booked customers."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role not in ['owner', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    session = ClassSession.query.filter_by(
        id=session_id,
        studio_id=user.studio_id
    ).first()
    
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    data = request.get_json() or {}
    reason = data.get('reason', 'Class has been cancelled')
    notify_customers = data.get('notify_customers', True)
    
    # Get booked customers before cancellation
    bookings = Booking.query.filter_by(
        session_id=session_id,
        status='CONFIRMED'
    ).all()
    
    customers_to_notify = []
    dance_class = DanceClass.query.get(session.class_id)
    class_name = dance_class.name if dance_class else 'Class'
    studio = Studio.query.get(user.studio_id)
    
    for booking in bookings:
        contact = Contact.query.get(booking.contact_id)
        if contact:
            customers_to_notify.append({
                'contact': contact,
                'booking': booking
            })
        # Cancel the booking
        booking.status = 'CANCELLED'
        booking.cancelled_at = datetime.utcnow()
        booking.cancellation_reason = f'Class cancelled: {reason}'
    
    # Cancel the session
    session.status = 'CANCELLED'
    
    db.session.commit()
    
    # Notify customers
    notified_count = 0
    if notify_customers:
        for item in customers_to_notify:
            try:
                notification_service.send_class_cancellation_notification(
                    contact=item['contact'],
                    class_name=class_name,
                    session_date=session.date,
                    session_time=session.start_time,
                    reason=reason,
                    studio=studio
                )
                notified_count += 1
            except Exception as e:
                import logging
                logging.warning(f"Failed to notify contact {item['contact'].id}: {e}")
    
    return jsonify({
        'message': 'Session cancelled successfully',
        'bookings_cancelled': len(bookings),
        'customers_notified': notified_count
    })


# ============================================================
# BOOKINGS
# ============================================================

@bookings_bp.route('', methods=['GET'])
@jwt_required()
def list_bookings():
    """List bookings - studio owners see their studio's bookings, customers see their own."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Query parameters
    contact_id = request.args.get('contact_id')
    session_id = request.args.get('session_id')
    status = request.args.get('status')
    time_filter = request.args.get('filter', 'all')  # 'upcoming', 'past', 'all'
    
    # Customers see their own bookings (by user_id)
    if user.user_type == 'customer':
        query = Booking.query.filter_by(user_id=user.id)
    else:
        # Studio staff sees studio's bookings
        query = Booking.query.filter_by(studio_id=user.studio_id)
        if contact_id:
            query = query.filter_by(contact_id=contact_id)
    
    if session_id:
        query = query.filter_by(session_id=session_id)
    
    if status:
        query = query.filter_by(status=status)
    
    today = datetime.utcnow().date()
    if time_filter == 'upcoming':
        # Join with sessions to filter by date >= today
        query = query.join(ClassSession).filter(
            ClassSession.date >= today
        )
    elif time_filter == 'past':
        # Join with sessions to filter by date < today
        query = query.join(ClassSession).filter(
            ClassSession.date < today
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
                    
                    # For customers, also include studio info
                    if user.user_type == 'customer':
                        studio = Studio.query.get(dance_class.studio_id)
                        if studio:
                            booking_data['studio_name'] = studio.name
                            booking_data['studio_slug'] = studio.slug
        
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
    
    # Send confirmation notification
    try:
        contact = Contact.query.get(data['contact_id'])
        studio = Studio.query.get(user.studio_id)
        if contact and studio:
            notification_service.send_booking_confirmation(
                booking=booking,
                session=session,
                contact=contact,
                studio=studio
            )
    except Exception as e:
        # Log but don't fail booking on notification error
        import logging
        logging.error(f"Failed to send booking confirmation: {e}")
    
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
    
    # Send cancellation notification
    try:
        contact = Contact.query.get(booking.contact_id)
        studio = Studio.query.get(user.studio_id)
        if contact and studio and session:
            notification_service.send_booking_cancellation(
                booking=booking,
                session=session,
                contact=contact,
                studio=studio,
                refund_amount=0  # Calculate actual refund if payment was made
            )
    except Exception as e:
        import logging
        logging.error(f"Failed to send cancellation notification: {e}")
    
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
                session_data['class_type'] = dance_class.dance_style
                session_data['level'] = dance_class.level
        
        # Add instructor name
        if session.instructor_id:
            instructor = User.query.get(session.instructor_id)
            if instructor:
                session_data['instructor_name'] = instructor.name
        
        schedule[day_index].append(session_data)
    
    return jsonify({
        'schedule': schedule,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat()
    })


# ============================================================
# PUBLIC BOOKING ENDPOINTS (No Auth Required)
# ============================================================

@bookings_bp.route('/public/sessions/<studio_slug>', methods=['GET'])
def public_list_sessions(studio_slug):
    """List available sessions for a studio (public - no auth required)."""
    studio = Studio.query.filter_by(slug=studio_slug).first()
    
    if not studio:
        return jsonify({'error': 'Studio not found'}), 404
    
    # Get date range from query params
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if start_date_str:
        start_date = datetime.fromisoformat(start_date_str).date()
    else:
        start_date = datetime.utcnow().date()
    
    if end_date_str:
        end_date = datetime.fromisoformat(end_date_str).date()
    else:
        end_date = start_date + timedelta(days=7)
    
    # First try to get actual ClassSessions
    sessions = ClassSession.query.filter(
        ClassSession.studio_id == studio.id,
        ClassSession.date >= start_date,
        ClassSession.date <= end_date,
        ClassSession.status != 'CANCELLED'
    ).order_by(ClassSession.date, ClassSession.start_time).all()
    
    if sessions:
        result = []
        for session in sessions:
            dance_class = DanceClass.query.get(session.class_id) if session.class_id else None
            # Get instructor name if available
            instructor_name = 'TBA'
            if dance_class and dance_class.instructor_id:
                from app.models import User
                instructor = User.query.get(dance_class.instructor_id)
                if instructor:
                    instructor_name = instructor.name
            
            result.append({
                'id': session.id,
                'class_name': dance_class.name if dance_class else 'Class',
                'style': dance_class.dance_style if dance_class else '',
                'level': dance_class.level if dance_class else 'All Levels',
                'instructor_name': instructor_name,
                'start_time': session.start_time.strftime('%H:%M') if session.start_time else '18:00',
                'end_time': session.end_time.strftime('%H:%M') if session.end_time else '19:00',
                'date': session.date.isoformat(),
                'spots_available': session.available_spots if hasattr(session, 'available_spots') else (session.max_capacity - (session.booked_count or 0)),
                'max_students': session.max_capacity,
                'drop_in_price': float(dance_class.price) if dance_class and dance_class.price else 500,
                'is_cancelled': session.status == 'CANCELLED'
            })
        return jsonify({'sessions': result})
    
    # Fallback: Generate sessions from ClassSchedules with specific_date
    schedules = ClassSchedule.query.join(DanceClass).filter(
        DanceClass.studio_id == studio.id,
        DanceClass.is_active == True,
        ClassSchedule.specific_date >= start_date,
        ClassSchedule.specific_date <= end_date,
        ClassSchedule.is_cancelled == False
    ).order_by(ClassSchedule.specific_date, ClassSchedule.start_time).all()
    
    result = []
    for schedule in schedules:
        dance_class = schedule.dance_class
        # Get instructor name if available
        instructor_name = 'TBA'
        if dance_class.instructor_id:
            from app.models import User
            instructor = User.query.get(dance_class.instructor_id)
            if instructor:
                instructor_name = instructor.name
        
        result.append({
            'id': schedule.id,
            'schedule_id': schedule.id,  # Mark this as a schedule
            'class_name': dance_class.name,
            'style': dance_class.dance_style,
            'level': dance_class.level,
            'instructor_name': instructor_name,
            'start_time': schedule.start_time.strftime('%H:%M') if schedule.start_time else '18:00',
            'end_time': schedule.end_time.strftime('%H:%M') if schedule.end_time else '19:00',
            'date': schedule.specific_date.isoformat() if schedule.specific_date else datetime.utcnow().date().isoformat(),
            'spots_available': dance_class.max_capacity - (schedule.current_enrollment or 0),
            'max_students': dance_class.max_capacity,
            'drop_in_price': float(dance_class.price) if dance_class.price else 500,
            'is_cancelled': schedule.is_cancelled
        })
    
    return jsonify({'sessions': result})


@bookings_bp.route('/public/book', methods=['POST'])
def public_create_booking():
    """Create a booking from public booking page (no auth required)."""
    data = request.get_json()
    
    # Validate required fields
    required = ['studio_slug', 'session_id', 'customer_name', 'customer_phone']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Find studio
    studio = Studio.query.filter_by(slug=data['studio_slug']).first()
    if not studio:
        return jsonify({'error': 'Studio not found'}), 404
    
    session_id = data['session_id']
    
    # Try to find existing ClassSession
    session = ClassSession.query.get(session_id)
    
    if not session:
        # Maybe it's a schedule ID - create a session from it
        schedule = ClassSchedule.query.get(session_id)
        if not schedule:
            return jsonify({'error': 'Session not found'}), 404
        
        dance_class = schedule.dance_class
        
        # Create a ClassSession from the schedule
        session = ClassSession(
            id=str(uuid.uuid4()),
            studio_id=studio.id,
            schedule_id=schedule.id,
            class_id=dance_class.id,
            date=schedule.date,
            start_time=datetime.combine(schedule.date, schedule.start_time.time()) if schedule.start_time else datetime.combine(schedule.date, datetime.strptime('18:00', '%H:%M').time()),
            end_time=datetime.combine(schedule.date, schedule.end_time.time()) if schedule.end_time else datetime.combine(schedule.date, datetime.strptime('19:00', '%H:%M').time()),
            max_capacity=dance_class.max_capacity,
            status='SCHEDULED'
        )
        db.session.add(session)
    
    # Check availability
    if session.is_full:
        return jsonify({'error': 'This session is fully booked'}), 400
    
    # Get class info for pricing
    dance_class = DanceClass.query.get(session.class_id) if session.class_id else None
    
    # Create or find contact
    contact = Contact.query.filter_by(
        studio_id=studio.id,
        phone=data['customer_phone']
    ).first()
    
    if not contact:
        contact = Contact(
            id=str(uuid.uuid4()),
            studio_id=studio.id,
            name=data['customer_name'],
            phone=data['customer_phone'],
            email=data.get('customer_email'),
            lead_status='NEW',
            lead_source='booking_page'
        )
        db.session.add(contact)
    else:
        # Update contact info
        contact.name = data['customer_name']
        if data.get('customer_email'):
            contact.email = data['customer_email']
    
    # Create booking
    booking = Booking(
        id=str(uuid.uuid4()),
        studio_id=studio.id,
        contact_id=contact.id,
        session_id=session.id,
        booking_number=generate_booking_number(),
        status='CONFIRMED',
        payment_method=data.get('payment_method', 'pay_at_studio'),
        booked_at=datetime.utcnow()
    )
    
    # Update booking count
    session.booked_count = (session.booked_count or 0) + 1
    
    try:
        db.session.add(booking)
        
        # Create notification for studio owner
        from app.routes.notifications import create_notification
        class_name = dance_class.name if dance_class else 'Class'
        session_date = session.date.strftime('%b %d') if session.date else ''
        session_time = session.start_time.strftime('%H:%M') if session.start_time else ''
        
        create_notification(
            studio_id=studio.id,
            notification_type='BOOKING',
            title=f'New Booking: {data["customer_name"]}',
            message=f'{data["customer_name"]} booked {class_name} on {session_date} at {session_time}',
            reference_type='booking',
            reference_id=booking.id
        )
        
        db.session.commit()
        
        return jsonify({
            'message': 'Booking confirmed',
            'booking': {
                'id': booking.id,
                'booking_number': booking.booking_number,
                'status': booking.status,
                'class_name': dance_class.name if dance_class else 'Class',
                'date': session.date.isoformat(),
                'time': session.start_time.strftime('%H:%M') if session.start_time else None
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bookings_bp.route('/session/<session_id>/bookings', methods=['GET'])
@jwt_required()
def get_session_bookings(session_id):
    """Get all bookings for a specific class session."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.studio_id:
        return jsonify({'error': 'User not found'}), 404
    
    # Get the session
    session = ClassSession.query.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    # Verify the session belongs to the user's studio
    if session.studio_id != user.studio_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get all bookings for this session
    bookings = Booking.query.filter_by(
        session_id=session_id
    ).order_by(Booking.booked_at.desc()).all()
    
    result = []
    for booking in bookings:
        # Get contact info
        contact = Contact.query.get(booking.contact_id) if booking.contact_id else None
        
        result.append({
            'id': booking.id,
            'booking_number': booking.booking_number,
            'customer_name': contact.name if contact else 'Unknown',
            'customer_email': contact.email if contact else '',
            'customer_phone': contact.phone if contact else '',
            'status': booking.status.lower() if booking.status else 'pending',
            'payment_method': booking.payment_method,
            'booked_at': booking.booked_at.isoformat() if booking.booked_at else booking.created_at.isoformat()
        })
    
    return jsonify({
        'bookings': result,
        'total': len(result),
        'session_id': session_id
    })

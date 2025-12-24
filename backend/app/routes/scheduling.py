# Scheduling Routes - Class scheduling and optimization
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import uuid
from datetime import time, datetime

from app.models import db, User, DanceClass, ClassSchedule, Room, InstructorAvailability
from app.scheduling import ScheduleOptimizer, ScheduleConstraints, ScheduleGenerator

scheduling_bp = Blueprint('scheduling', __name__)


@scheduling_bp.route('/classes', methods=['GET'])
@jwt_required()
def list_classes():
    """List all dance class definitions."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    classes = DanceClass.query.filter_by(studio_id=user.studio_id).all()
    
    return jsonify({
        'classes': [c.to_dict() for c in classes]
    })


@scheduling_bp.route('/classes', methods=['POST'])
@jwt_required()
def create_class():
    """Create a new dance class definition."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'name is required'}), 400
    
    dance_class = DanceClass(
        id=str(uuid.uuid4()),
        studio_id=user.studio_id,
        name=data['name'],
        description=data.get('description'),
        dance_style=data.get('dance_style'),
        level=data.get('level', 'All Levels'),
        duration_minutes=data.get('duration_minutes', 60),
        max_capacity=data.get('max_capacity', 20),
        min_capacity=data.get('min_capacity', 3),
        price=data.get('price'),
        instructor_id=data.get('instructor_id'),
        is_active=True
    )
    
    db.session.add(dance_class)
    db.session.commit()
    
    return jsonify(dance_class.to_dict()), 201


@scheduling_bp.route('/classes/<class_id>', methods=['PUT'])
@jwt_required()
def update_class(class_id):
    """Update a dance class definition."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    dance_class = DanceClass.query.filter_by(
        id=class_id,
        studio_id=user.studio_id
    ).first()
    
    if not dance_class:
        return jsonify({'error': 'Class not found'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        dance_class.name = data['name']
    if 'description' in data:
        dance_class.description = data['description']
    if 'dance_style' in data:
        dance_class.dance_style = data['dance_style']
    if 'level' in data:
        dance_class.level = data['level']
    if 'duration_minutes' in data:
        dance_class.duration_minutes = data['duration_minutes']
    if 'max_capacity' in data:
        dance_class.max_capacity = data['max_capacity']
    if 'min_capacity' in data:
        dance_class.min_capacity = data['min_capacity']
    if 'price' in data:
        dance_class.price = data['price']
    if 'instructor_id' in data:
        dance_class.instructor_id = data['instructor_id']
    if 'is_active' in data:
        dance_class.is_active = data['is_active']
    
    db.session.commit()
    
    return jsonify(dance_class.to_dict())


@scheduling_bp.route('/rooms', methods=['GET'])
@jwt_required()
def list_rooms():
    """List all studio rooms."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    rooms = Room.query.filter_by(studio_id=user.studio_id).all()
    
    return jsonify({
        'rooms': [r.to_dict() for r in rooms]
    })


@scheduling_bp.route('/rooms', methods=['POST'])
@jwt_required()
def create_room():
    """Create a new studio room."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'name is required'}), 400
    
    room = Room(
        id=str(uuid.uuid4()),
        studio_id=user.studio_id,
        name=data['name'],
        capacity=data.get('capacity', 20),
        features=data.get('features', []),
        is_active=True
    )
    
    db.session.add(room)
    db.session.commit()
    
    return jsonify(room.to_dict()), 201


@scheduling_bp.route('/instructors', methods=['GET'])
@jwt_required()
def list_instructors():
    """List all instructors with their availability."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    instructors = User.query.filter_by(
        studio_id=user.studio_id,
        role='INSTRUCTOR'
    ).all()
    
    result = []
    for instructor in instructors:
        availability = InstructorAvailability.query.filter_by(
            instructor_id=instructor.id
        ).all()
        
        result.append({
            'id': instructor.id,
            'name': f"{instructor.first_name} {instructor.last_name}",
            'email': instructor.email,
            'specialties': instructor.extra_data.get('specialties', []) if instructor.extra_data else [],
            'availability': [a.to_dict() for a in availability]
        })
    
    return jsonify({'instructors': result})


@scheduling_bp.route('/instructors/<instructor_id>/availability', methods=['POST'])
@jwt_required()
def set_availability(instructor_id):
    """
    Set instructor availability.
    
    Body:
    {
        "availability": [
            {"day_of_week": 0, "start_time": "09:00", "end_time": "17:00"},
            {"day_of_week": 1, "start_time": "09:00", "end_time": "17:00"}
        ]
    }
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    instructor = User.query.filter_by(
        id=instructor_id,
        studio_id=user.studio_id
    ).first()
    
    if not instructor:
        return jsonify({'error': 'Instructor not found'}), 404
    
    data = request.get_json()
    if not data or 'availability' not in data:
        return jsonify({'error': 'availability is required'}), 400
    
    # Clear existing availability
    InstructorAvailability.query.filter_by(instructor_id=instructor_id).delete()
    
    # Add new availability
    for slot in data['availability']:
        start = datetime.strptime(slot['start_time'], '%H:%M').time()
        end = datetime.strptime(slot['end_time'], '%H:%M').time()
        
        avail = InstructorAvailability(
            id=str(uuid.uuid4()),
            instructor_id=instructor_id,
            day_of_week=slot['day_of_week'],
            start_time=start,
            end_time=end,
            is_available=True
        )
        db.session.add(avail)
    
    db.session.commit()
    
    return jsonify({'success': True})


@scheduling_bp.route('/schedule', methods=['GET'])
@jwt_required()
def get_schedule():
    """Get current class schedule."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    generator = ScheduleGenerator(user.studio_id)
    schedule = generator.get_current_schedule()
    
    return jsonify({'schedule': schedule})


@scheduling_bp.route('/schedule', methods=['POST'])
@jwt_required()
def create_schedule():
    """
    Manually create a scheduled class.
    
    Body:
    {
        "class_id": "uuid",
        "day_of_week": 0,
        "start_time": "18:00",
        "end_time": "19:00",
        "room": "Studio A",
        "instructor_id": "uuid"
    }
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    required = ['class_id', 'day_of_week', 'start_time', 'end_time']
    for field in required:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    start = datetime.strptime(data['start_time'], '%H:%M').time()
    end = datetime.strptime(data['end_time'], '%H:%M').time()
    
    schedule = ClassSchedule(
        id=str(uuid.uuid4()),
        studio_id=user.studio_id,
        class_id=data['class_id'],
        day_of_week=data['day_of_week'],
        start_time=start,
        end_time=end,
        room=data.get('room'),
        instructor_id=data.get('instructor_id'),
        is_recurring=data.get('is_recurring', True)
    )
    
    db.session.add(schedule)
    db.session.commit()
    
    return jsonify(schedule.to_dict()), 201


@scheduling_bp.route('/optimize', methods=['POST'])
@jwt_required()
def optimize_schedule():
    """
    Run schedule optimization.
    
    Body (optional):
    {
        "opening_time": "09:00",
        "closing_time": "21:00",
        "max_concurrent_classes": 3,
        "prefer_beginners_in_peak": true
    }
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json() or {}
    
    # Build constraints
    constraints = ScheduleConstraints()
    
    if 'opening_time' in data:
        constraints.opening_time = datetime.strptime(data['opening_time'], '%H:%M').time()
    if 'closing_time' in data:
        constraints.closing_time = datetime.strptime(data['closing_time'], '%H:%M').time()
    if 'max_concurrent_classes' in data:
        constraints.max_concurrent_classes = data['max_concurrent_classes']
    if 'prefer_beginners_in_peak' in data:
        constraints.prefer_beginners_in_peak = data['prefer_beginners_in_peak']
    
    generator = ScheduleGenerator(user.studio_id)
    result = generator.generate_optimized_schedule(constraints)
    
    return jsonify(result.to_dict())


@scheduling_bp.route('/optimize/save', methods=['POST'])
@jwt_required()
def save_optimized_schedule():
    """
    Generate and save an optimized schedule.
    Replaces existing recurring schedules.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user.role not in ['ADMIN', 'OWNER']:
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json() or {}
    
    constraints = ScheduleConstraints()
    if 'opening_time' in data:
        constraints.opening_time = datetime.strptime(data['opening_time'], '%H:%M').time()
    if 'closing_time' in data:
        constraints.closing_time = datetime.strptime(data['closing_time'], '%H:%M').time()
    
    generator = ScheduleGenerator(user.studio_id)
    result = generator.generate_optimized_schedule(constraints)
    
    if not result.success and len(result.schedule) == 0:
        return jsonify({
            'success': False,
            'error': 'No classes could be scheduled',
            'conflicts': result.conflicts
        }), 400
    
    # Clear existing recurring schedules
    ClassSchedule.query.filter_by(
        studio_id=user.studio_id,
        is_recurring=True
    ).delete()
    
    # Save new schedule
    schedule_ids = generator.save_schedule(result)
    
    return jsonify({
        'success': True,
        'schedules_created': len(schedule_ids),
        'unscheduled': len(result.unscheduled),
        'utilization': result.utilization,
        'score': result.score
    })


@scheduling_bp.route('/suggest', methods=['POST'])
@jwt_required()
def suggest_time():
    """
    Get suggested times for a new class.
    
    Body:
    {
        "dance_style": "salsa",
        "level": "Beginner",
        "duration_minutes": 60
    }
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    from app.scheduling.optimizer import ClassDefinition
    
    class_def = ClassDefinition(
        id='temp',
        name='New Class',
        dance_style=data.get('dance_style', 'general'),
        level=data.get('level', 'All Levels'),
        duration_minutes=data.get('duration_minutes', 60),
        min_capacity=data.get('min_capacity', 3),
        max_capacity=data.get('max_capacity', 20)
    )
    
    generator = ScheduleGenerator(user.studio_id)
    suggestions = generator.suggest_new_class_time(class_def)
    
    return jsonify({
        'suggestions': suggestions
    })


@scheduling_bp.route('/conflicts', methods=['GET'])
@jwt_required()
def check_conflicts():
    """Check current schedule for conflicts."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    from app.scheduling import ConflictResolver
    from app.scheduling.optimizer import ScheduledClass, ClassDefinition, Instructor, Room as OptRoom, TimeSlot, DayOfWeek
    
    generator = ScheduleGenerator(user.studio_id)
    current = generator.get_current_schedule()
    
    # Convert to ScheduledClass objects for conflict detection
    # This is a simplified version - full implementation would load all data
    
    resolver = ConflictResolver()
    
    # For now, just check for time overlaps
    conflicts = []
    for i, cls1 in enumerate(current):
        for cls2 in current[i+1:]:
            if cls1['day_of_week'] == cls2['day_of_week']:
                start1 = datetime.strptime(cls1['start_time'], '%H:%M').time()
                end1 = datetime.strptime(cls1['end_time'], '%H:%M').time()
                start2 = datetime.strptime(cls2['start_time'], '%H:%M').time()
                end2 = datetime.strptime(cls2['end_time'], '%H:%M').time()
                
                if not (end1 <= start2 or start1 >= end2):
                    # Check if same instructor or room
                    if cls1.get('instructor_name') == cls2.get('instructor_name'):
                        conflicts.append({
                            'type': 'instructor',
                            'description': f"Instructor double-booked: {cls1['class_name']} and {cls2['class_name']}",
                            'classes': [cls1['id'], cls2['id']]
                        })
                    if cls1.get('room') == cls2.get('room'):
                        conflicts.append({
                            'type': 'room',
                            'description': f"Room double-booked: {cls1['class_name']} and {cls2['class_name']}",
                            'classes': [cls1['id'], cls2['id']]
                        })
    
    return jsonify({
        'conflicts': conflicts,
        'total': len(conflicts)
    })

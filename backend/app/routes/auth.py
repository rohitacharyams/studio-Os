from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import datetime
import uuid

from app import db
from app.models import User, Studio

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user - either studio owner or customer."""
    data = request.get_json()
    
    user_type = data.get('user_type', 'studio_owner')  # studio_owner or customer
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=data.get('email')).first()
    if existing_user:
        return jsonify({'error': 'Email already registered'}), 400
    
    if user_type == 'customer':
        # Customer registration - no studio needed
        required_fields = ['email', 'password', 'name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create customer user
        user = User(
            id=str(uuid.uuid4()),
            studio_id=None,  # Customers don't belong to a studio
            email=data['email'],
            name=data['name'],
            phone=data.get('phone'),
            role='customer',
            user_type='customer'
        )
        user.set_password(data['password'])
        
        try:
            db.session.add(user)
            db.session.commit()
            
            access_token = create_access_token(identity=user.id)
            
            return jsonify({
                'message': 'Registration successful',
                'access_token': access_token,
                'user': user.to_dict()
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    else:
        # Studio owner registration
        required_fields = ['email', 'password', 'name', 'studio_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Generate unique slug
        import re
        base_slug = data['studio_name'].lower()
        base_slug = re.sub(r'[^a-z0-9\s-]', '', base_slug)
        base_slug = re.sub(r'[\s_]+', '-', base_slug)
        base_slug = re.sub(r'-+', '-', base_slug).strip('-')
        
        # Ensure slug is unique
        slug = base_slug
        counter = 1
        while Studio.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        # Create studio
        studio = Studio(
            id=str(uuid.uuid4()),
            name=data['studio_name'],
            slug=slug,
            email=data['email'],
            phone=data.get('phone'),
            address=data.get('address'),
            timezone=data.get('timezone', 'Asia/Kolkata'),
            onboarding_completed=False,
            onboarding_step=0
        )
        
        # Create owner user
        user = User(
            id=str(uuid.uuid4()),
            studio_id=studio.id,
            email=data['email'],
            name=data['name'],
            phone=data.get('phone'),
            role='owner',
            user_type='studio_owner'
        )
        user.set_password(data['password'])
        
        try:
            db.session.add(studio)
            db.session.add(user)
            db.session.commit()
            
            access_token = create_access_token(identity=user.id)
            
            return jsonify({
                'message': 'Registration successful',
                'access_token': access_token,
                'user': user.to_dict(include_studio=True)
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token."""
    data = request.get_json()
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 401
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Generate access token
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'access_token': access_token,
        'user': user.to_dict(include_studio=True)
    })


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict(include_studio=True)})


@auth_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_current_user():
    """Update current user profile."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        user.name = data['name']
    if 'password' in data and data['password']:
        user.set_password(data['password'])
    
    try:
        db.session.commit()
        return jsonify({'user': user.to_dict(include_studio=True)})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    """List all users in the studio."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    users = User.query.filter_by(studio_id=user.studio_id).all()
    
    return jsonify({
        'users': [u.to_dict() for u in users]
    })


@auth_bp.route('/users', methods=['POST'])
@jwt_required()
def create_user():
    """Create a new user in the studio (admin/owner only)."""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    if not current_user:
        return jsonify({'error': 'User not found'}), 404
    
    if current_user.role not in ['owner', 'admin']:
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    data = request.get_json()
    
    required_fields = ['email', 'password', 'name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Check if email already exists
    existing = User.query.filter_by(email=data['email']).first()
    if existing:
        return jsonify({'error': 'Email already registered'}), 400
    
    new_user = User(
        id=str(uuid.uuid4()),
        studio_id=current_user.studio_id,
        email=data['email'],
        name=data['name'],
        role=data.get('role', 'staff')
    )
    new_user.set_password(data['password'])
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'user': new_user.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

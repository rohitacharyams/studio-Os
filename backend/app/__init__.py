from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
import redis
import os

from app.config import config

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

# Redis client (initialized in create_app)
redis_client = None


def create_app(config_name='default'):
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    
    # CORS configuration - support wildcard or specific origins
    cors_origins = app.config['CORS_ORIGINS']
    if cors_origins == ['*'] or '*' in cors_origins:
        # Wildcard: allow all origins (no credentials support)
        CORS(app, origins='*', supports_credentials=False)
    else:
        # Specific origins: allow credentials
        CORS(app, origins=cors_origins, supports_credentials=True)
    
    # Initialize Redis (with fallback for environments without Redis)
    global redis_client
    try:
        redis_client = redis.from_url(app.config['REDIS_URL'])
        redis_client.ping()  # Test connection
    except (redis.ConnectionError, redis.RedisError):
        redis_client = None
        app.logger.warning("Redis not available, caching disabled")
    
    # Add security headers in production
    if not app.debug:
        @app.after_request
        def add_security_headers(response):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            return response
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.conversations import conversations_bp
    from app.routes.messages import messages_bp
    from app.routes.ai import ai_bp
    from app.routes.analytics import analytics_bp
    from app.routes.webhooks import webhooks_bp
    from app.routes.studio import studio_bp
    from app.routes.templates import templates_bp
    from app.routes.contacts import contacts_bp
    from app.routes.integrations import integrations_bp
    from app.routes.llm import llm_bp
    from app.routes.scheduling import scheduling_bp
    from app.routes.bookings import bookings_bp
    from app.routes.payments import payments_bp
    from app.routes.payments_public import payments_public_bp
    from app.routes.whatsapp import bp as whatsapp_bp
    from app.routes.notifications import notifications_bp
    from app.routes.email import email_bp
    from app.routes.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(conversations_bp, url_prefix='/api/conversations')
    app.register_blueprint(messages_bp, url_prefix='/api/messages')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(webhooks_bp, url_prefix='/api/webhooks')
    app.register_blueprint(studio_bp, url_prefix='/api/studio')
    app.register_blueprint(templates_bp, url_prefix='/api/templates')
    app.register_blueprint(contacts_bp, url_prefix='/api/contacts')
    app.register_blueprint(integrations_bp, url_prefix='/api/integrations')
    app.register_blueprint(llm_bp, url_prefix='/api/llm')
    app.register_blueprint(scheduling_bp, url_prefix='/api/scheduling')
    app.register_blueprint(bookings_bp)  # Already has /api/bookings prefix
    app.register_blueprint(payments_bp)  # Already has /api/payments prefix
    app.register_blueprint(payments_public_bp)  # Public payment endpoints
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    app.register_blueprint(whatsapp_bp, url_prefix='/api/whatsapp')
    app.register_blueprint(email_bp)  # Already has /api/email prefix
    app.register_blueprint(admin_bp, url_prefix='/api/admin')  # Platform admin routes
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'studio-os-api'}
    
    # Database initialization endpoint (one-time use)
    @app.route('/init-db', methods=['POST'])
    def init_database():
        """Initialize database tables. Protected by secret key."""
        from flask import request
        secret = request.headers.get('X-Init-Secret')
        if secret != app.config.get('SECRET_KEY'):
            return {'error': 'Unauthorized'}, 401
        
        try:
            db.create_all()
            return {'status': 'success', 'message': 'Database tables created'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}, 500
    
    # Seed data endpoint (one-time use)
    @app.route('/seed-db', methods=['POST'])
    def seed_database():
        """Seed database with demo data. Protected by secret key."""
        from flask import request
        from werkzeug.security import generate_password_hash
        from datetime import datetime, timedelta, time
        import uuid
        
        secret = request.headers.get('X-Init-Secret')
        if secret != app.config.get('SECRET_KEY'):
            return {'error': 'Unauthorized'}, 401
        
        try:
            from app.models import Studio, User, DanceClass, Room, ClassSchedule
            
            # Check if already seeded
            if Studio.query.first():
                return {'status': 'skipped', 'message': 'Database already seeded'}
            
            # Create Studio
            studio = Studio(
                id=str(uuid.uuid4()),
                name="Rhythm Dance Academy",
                email="info@rhythmdance.com",
                phone="+91-9876543210",
                address="123 Dance Street, Bangalore, India",
                timezone="Asia/Kolkata"
            )
            db.session.add(studio)
            db.session.flush()
            
            # Create Admin User
            admin = User(
                id=str(uuid.uuid4()),
                email="admin@rhythmdance.com",
                password_hash=generate_password_hash("Admin@123"),
                name="Admin User",
                role="admin",
                studio_id=studio.id,
                is_active=True
            )
            db.session.add(admin)
            
            # Create Instructor Users
            instructor1 = User(
                id=str(uuid.uuid4()),
                email="priya@rhythmdance.com",
                password_hash=generate_password_hash("Instructor@123"),
                name="Priya Sharma",
                role="staff",
                studio_id=studio.id,
                is_active=True
            )
            instructor2 = User(
                id=str(uuid.uuid4()),
                email="rahul@rhythmdance.com",
                password_hash=generate_password_hash("Instructor@123"),
                name="Rahul Verma",
                role="staff",
                studio_id=studio.id,
                is_active=True
            )
            instructor3 = User(
                id=str(uuid.uuid4()),
                email="anjali@rhythmdance.com",
                password_hash=generate_password_hash("Instructor@123"),
                name="Anjali Patel",
                role="staff",
                studio_id=studio.id,
                is_active=True
            )
            db.session.add(instructor1)
            db.session.add(instructor2)
            db.session.add(instructor3)
            db.session.flush()
            
            instructors = [instructor1, instructor2, instructor3]
            
            # Create Rooms
            rooms = [
                Room(id=str(uuid.uuid4()), studio_id=studio.id, name="Main Hall", capacity=30, is_active=True),
                Room(id=str(uuid.uuid4()), studio_id=studio.id, name="Studio A", capacity=15, is_active=True),
                Room(id=str(uuid.uuid4()), studio_id=studio.id, name="Studio B", capacity=15, is_active=True),
            ]
            for room in rooms:
                db.session.add(room)
            db.session.flush()
            
            # Create Dance Classes
            classes = [
                DanceClass(id=str(uuid.uuid4()), studio_id=studio.id, name="Bharatanatyam Beginners", 
                          dance_style="Bharatanatyam", level="beginner", description="Traditional South Indian classical dance for beginners",
                          duration_minutes=60, max_capacity=20, price=500, instructor_id=instructor1.id, is_active=True),
                DanceClass(id=str(uuid.uuid4()), studio_id=studio.id, name="Hip Hop Fundamentals", 
                          dance_style="Hip Hop", level="beginner", description="Learn the basics of hip hop dance",
                          duration_minutes=60, max_capacity=25, price=400, instructor_id=instructor2.id, is_active=True),
                DanceClass(id=str(uuid.uuid4()), studio_id=studio.id, name="Salsa Social", 
                          dance_style="Salsa", level="all_levels", description="Fun salsa class for all levels",
                          duration_minutes=90, max_capacity=30, price=450, instructor_id=instructor3.id, is_active=True),
                DanceClass(id=str(uuid.uuid4()), studio_id=studio.id, name="Contemporary Advanced", 
                          dance_style="Contemporary", level="advanced", description="Advanced contemporary dance techniques",
                          duration_minutes=90, max_capacity=15, price=600, instructor_id=instructor1.id, is_active=True),
            ]
            for dance_class in classes:
                db.session.add(dance_class)
            db.session.flush()
            
            # Create Class Schedules (recurring weekly)
            schedules = [
                # Bharatanatyam - Mon, Wed, Fri at 6 PM
                ClassSchedule(id=str(uuid.uuid4()), studio_id=studio.id, class_id=classes[0].id, 
                             instructor_id=instructor1.id, day_of_week=0, start_time=time(18, 0), end_time=time(19, 0), 
                             room="Main Hall", is_recurring=True),
                ClassSchedule(id=str(uuid.uuid4()), studio_id=studio.id, class_id=classes[0].id, 
                             instructor_id=instructor1.id, day_of_week=2, start_time=time(18, 0), end_time=time(19, 0), 
                             room="Main Hall", is_recurring=True),
                ClassSchedule(id=str(uuid.uuid4()), studio_id=studio.id, class_id=classes[0].id, 
                             instructor_id=instructor1.id, day_of_week=4, start_time=time(18, 0), end_time=time(19, 0), 
                             room="Main Hall", is_recurring=True),
                # Hip Hop - Tue, Thu at 7 PM
                ClassSchedule(id=str(uuid.uuid4()), studio_id=studio.id, class_id=classes[1].id, 
                             instructor_id=instructor2.id, day_of_week=1, start_time=time(19, 0), end_time=time(20, 0), 
                             room="Studio A", is_recurring=True),
                ClassSchedule(id=str(uuid.uuid4()), studio_id=studio.id, class_id=classes[1].id, 
                             instructor_id=instructor2.id, day_of_week=3, start_time=time(19, 0), end_time=time(20, 0), 
                             room="Studio A", is_recurring=True),
                # Salsa - Sat at 5 PM
                ClassSchedule(id=str(uuid.uuid4()), studio_id=studio.id, class_id=classes[2].id, 
                             instructor_id=instructor3.id, day_of_week=5, start_time=time(17, 0), end_time=time(18, 30), 
                             room="Main Hall", is_recurring=True),
                # Contemporary - Sun at 10 AM
                ClassSchedule(id=str(uuid.uuid4()), studio_id=studio.id, class_id=classes[3].id, 
                             instructor_id=instructor1.id, day_of_week=6, start_time=time(10, 0), end_time=time(11, 30), 
                             room="Main Hall", is_recurring=True),
            ]
            for schedule in schedules:
                db.session.add(schedule)
            
            db.session.commit()
            
            return {
                'status': 'success', 
                'message': 'Database seeded successfully',
                'data': {
                    'studio': studio.name,
                    'admin_email': 'admin@rhythmdance.com',
                    'admin_password': 'Admin@123',
                    'classes_created': len(classes),
                    'instructors_created': len(instructors),
                    'rooms_created': len(rooms),
                    'schedules_created': len(schedules)
                }
            }
        except Exception as e:
            db.session.rollback()
            import traceback
            return {'status': 'error', 'message': str(e), 'trace': traceback.format_exc()}, 500
    
    return app

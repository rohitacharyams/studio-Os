from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
import redis

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
    CORS(app, origins=app.config['CORS_ORIGINS'], supports_credentials=True)
    
    # Initialize Redis
    global redis_client
    redis_client = redis.from_url(app.config['REDIS_URL'])
    
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
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'studio-os-api'}
    
    return app

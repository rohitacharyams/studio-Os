"""
Production WSGI entry point for Studio OS API
Run with: gunicorn wsgi:app
"""
import os
from app import create_app, db

# Set production config
os.environ.setdefault('FLASK_ENV', 'production')

# Create application
app = create_app('production')

# Initialize Sentry for error monitoring (optional but recommended)
try:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
    
    sentry_dsn = os.getenv('SENTRY_DSN')
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[FlaskIntegration()],
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
            environment=os.getenv('FLASK_ENV', 'production')
        )
        print("✅ Sentry initialized for error monitoring")
except ImportError:
    print("⚠️ Sentry SDK not installed, skipping error monitoring")

# Create database tables on startup (if not using migrations)
with app.app_context():
    # Only create tables if they don't exist
    # In production, you should use Flask-Migrate instead
    # db.create_all()
    pass

if __name__ == '__main__':
    # This block only runs in development
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5001)))

#!/usr/bin/env python3
"""
Studio OS - Production Readiness Verification Script
Run this before deploying to verify everything is configured correctly.
"""
import os
import sys
import json
from datetime import datetime


def check_env_vars():
    """Check required environment variables."""
    required_vars = [
        ('SECRET_KEY', 'Flask secret key'),
        ('DATABASE_URL', 'PostgreSQL connection string'),
        ('JWT_SECRET_KEY', 'JWT signing key'),
        ('RAZORPAY_KEY_ID', 'Razorpay API key'),
        ('RAZORPAY_KEY_SECRET', 'Razorpay API secret'),
    ]
    
    optional_vars = [
        ('TWILIO_ACCOUNT_SID', 'Twilio for WhatsApp'),
        ('TWILIO_AUTH_TOKEN', 'Twilio auth token'),
        ('SENDGRID_API_KEY', 'SendGrid for emails'),
        ('SENTRY_DSN', 'Sentry for error monitoring'),
        ('REDIS_URL', 'Redis for caching'),
    ]
    
    print("\n🔍 Checking Required Environment Variables...")
    missing = []
    for var, desc in required_vars:
        value = os.getenv(var)
        if value and 'change' not in value.lower() and 'xxx' not in value.lower():
            print(f"  ✅ {var}: Configured")
        else:
            print(f"  ❌ {var}: Missing or not configured ({desc})")
            missing.append(var)
    
    print("\n📋 Optional Environment Variables...")
    for var, desc in optional_vars:
        value = os.getenv(var)
        if value and len(value) > 5:
            print(f"  ✅ {var}: Configured")
        else:
            print(f"  ⚪ {var}: Not set ({desc})")
    
    return len(missing) == 0


def check_database():
    """Test database connection."""
    print("\n🗄️ Testing Database Connection...")
    try:
        from app import create_app, db
        app = create_app('production')
        with app.app_context():
            # Try to execute a simple query
            db.engine.execute("SELECT 1")
            print("  ✅ Database connection successful")
            
            # Check tables exist
            from app.models import User, Studio, DanceClass
            user_count = User.query.count()
            studio_count = Studio.query.count()
            class_count = DanceClass.query.count()
            print(f"  📊 Found: {user_count} users, {studio_count} studios, {class_count} classes")
            return True
    except Exception as e:
        print(f"  ❌ Database error: {str(e)}")
        return False


def check_razorpay():
    """Test Razorpay connection."""
    print("\n💳 Testing Razorpay Connection...")
    try:
        import razorpay
        client = razorpay.Client(
            auth=(os.getenv('RAZORPAY_KEY_ID'), os.getenv('RAZORPAY_KEY_SECRET'))
        )
        # Try to fetch orders (will fail with empty but confirms auth works)
        client.order.all({'count': 1})
        print("  ✅ Razorpay connection successful")
        
        key_id = os.getenv('RAZORPAY_KEY_ID', '')
        if key_id.startswith('rzp_live'):
            print("  ✅ Using LIVE Razorpay keys")
        else:
            print("  ⚠️ Using TEST Razorpay keys - switch to live for production!")
        return True
    except Exception as e:
        print(f"  ❌ Razorpay error: {str(e)}")
        return False


def check_api_endpoints():
    """Test critical API endpoints."""
    print("\n🌐 Testing API Endpoints...")
    
    try:
        from app import create_app
        app = create_app('production')
        client = app.test_client()
        
        # Health check
        response = client.get('/health')
        if response.status_code == 200:
            print("  ✅ /health endpoint working")
        else:
            print(f"  ❌ /health returned {response.status_code}")
        
        # Auth login (should return 400 without data, not 500)
        response = client.post('/api/auth/login', json={})
        if response.status_code in [400, 401, 422]:
            print("  ✅ /api/auth/login endpoint working")
        else:
            print(f"  ⚠️ /api/auth/login returned {response.status_code}")
        
        # Studio endpoint (should return 401 without auth)
        response = client.get('/api/studio/overview')
        if response.status_code in [401, 403]:
            print("  ✅ /api/studio/overview endpoint protected")
        else:
            print(f"  ⚠️ /api/studio/overview returned {response.status_code}")
        
        return True
    except Exception as e:
        print(f"  ❌ API test error: {str(e)}")
        return False


def check_security():
    """Check security configuration."""
    print("\n🔒 Checking Security Configuration...")
    
    issues = []
    
    # Check secret key
    secret_key = os.getenv('SECRET_KEY', '')
    if len(secret_key) < 32:
        issues.append("SECRET_KEY should be at least 32 characters")
    
    if secret_key == 'dev-secret-key-change-in-production':
        issues.append("SECRET_KEY is still the default value!")
    
    # Check debug mode
    flask_env = os.getenv('FLASK_ENV', 'development')
    flask_debug = os.getenv('FLASK_DEBUG', '1')
    if flask_env != 'production':
        issues.append("FLASK_ENV should be 'production'")
    if flask_debug == '1':
        issues.append("FLASK_DEBUG should be '0' in production")
    
    # Check CORS origins
    cors_origins = os.getenv('CORS_ORIGINS', '')
    if 'localhost' in cors_origins and flask_env == 'production':
        issues.append("CORS_ORIGINS contains localhost in production")
    
    if issues:
        for issue in issues:
            print(f"  ⚠️ {issue}")
        return False
    else:
        print("  ✅ Security configuration looks good")
        return True


def main():
    """Run all checks."""
    print("=" * 60)
    print("🚀 Studio OS - Production Readiness Check")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = {
        'env_vars': check_env_vars(),
        'security': check_security(),
        'database': check_database(),
        'razorpay': check_razorpay(),
        'api': check_api_endpoints(),
    }
    
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    
    all_passed = all(results.values())
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {check.upper()}: {status}")
    
    print("\n")
    if all_passed:
        print("🎉 All checks passed! Ready for deployment.")
        return 0
    else:
        print("⚠️ Some checks failed. Fix issues before deploying.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

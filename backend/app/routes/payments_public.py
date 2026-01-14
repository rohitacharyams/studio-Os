"""
Public payment endpoints that don't require authentication.
These are used for guest checkout on public booking pages.
"""
import os
import uuid
import hmac
import hashlib
from datetime import datetime
from decimal import Decimal
from flask import Blueprint, request, jsonify
from app import db
from app.models import Studio

payments_public_bp = Blueprint('payments_public', __name__, url_prefix='/api/payments')


@payments_public_bp.route('/admin/set-razorpay-keys', methods=['POST'])
def admin_set_razorpay_keys():
    """Admin endpoint to set Razorpay keys for a studio.
    Protected by admin secret key in header.
    """
    admin_secret = request.headers.get('X-Admin-Secret')
    expected_secret = os.getenv('ADMIN_SECRET', 'studioos-admin-2026')
    
    if admin_secret != expected_secret:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    if not data.get('studio_slug'):
        return jsonify({'error': 'studio_slug is required'}), 400
    if not data.get('razorpay_key_id'):
        return jsonify({'error': 'razorpay_key_id is required'}), 400
    if not data.get('razorpay_key_secret'):
        return jsonify({'error': 'razorpay_key_secret is required'}), 400
    
    studio = Studio.query.filter_by(slug=data['studio_slug']).first()
    if not studio:
        return jsonify({'error': 'Studio not found'}), 404
    
    studio.razorpay_key_id = data['razorpay_key_id']
    studio.razorpay_key_secret = data['razorpay_key_secret']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Razorpay keys updated for {studio.name}',
        'studio_slug': studio.slug,
        'key_id_prefix': data['razorpay_key_id'][:10] + '...'
    })


def get_studio_razorpay_client(studio):
    """Get Razorpay client using studio-specific keys."""
    try:
        import razorpay
        
        key_id = studio.razorpay_key_id if studio else None
        key_secret = studio.razorpay_key_secret if studio else None
        
        # Fall back to environment variables
        if not key_id:
            key_id = os.getenv('RAZORPAY_KEY_ID', '')
        if not key_secret:
            key_secret = os.getenv('RAZORPAY_KEY_SECRET', '')
        
        if not key_id or not key_secret:
            return None, None, None
            
        client = razorpay.Client(auth=(key_id, key_secret))
        return client, key_id, key_secret
    except ImportError:
        return None, None, None


@payments_public_bp.route('/public/create-order', methods=['POST'])
def public_create_order():
    """Create a Razorpay order for public/guest checkout.
    No authentication required - uses studio-specific Razorpay keys.
    Validates payment amount against actual session/class price to prevent frontend manipulation.
    """
    from app.models import ClassSession, DanceClass
    
    data = request.get_json()
    
    if not data.get('studio_slug'):
        return jsonify({'error': 'studio_slug is required'}), 400
    if not data.get('amount'):
        return jsonify({'error': 'amount is required'}), 400
    
    # Find studio by slug
    studio = Studio.query.filter_by(slug=data['studio_slug']).first()
    if not studio:
        return jsonify({'error': 'Studio not found'}), 404
    
    # SECURITY: Validate amount against actual session price
    session_id = data.get('session_id')
    if session_id:
        session = ClassSession.query.filter_by(
            id=session_id,
            studio_id=studio.id
        ).first()
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Get the actual price from the dance class
        if session.class_id:
            dance_class = DanceClass.query.get(session.class_id)
            if dance_class and dance_class.price:
                actual_price = float(dance_class.price)
                requested_amount = float(data['amount'])
                
                # Allow small floating point differences (0.01)
                if abs(actual_price - requested_amount) > 0.01:
                    return jsonify({
                        'error': 'Invalid payment amount',
                        'message': f'Amount mismatch. Expected ₹{actual_price}, but received ₹{requested_amount}',
                        'actual_price': actual_price
                    }), 400
    
    # Get studio's Razorpay client
    client, key_id, key_secret = get_studio_razorpay_client(studio)
    
    if not client:
        return jsonify({
            'error': 'Payment not configured for this studio',
            'demo_mode': True,
            'message': 'Studio has not configured payment gateway. Please pay at studio.'
        }), 400
    
    # Calculate amount
    amount = Decimal(str(data['amount']))
    currency = data.get('currency', studio.currency or 'INR')
    
    # Log the amount for debugging
    print(f"[PAYMENT DEBUG] Received amount: {data['amount']}, Calculated amount: {amount}, Amount in paise: {int(amount * 100)}")
    
    # Generate a reference number
    ref_number = f"PUB-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    try:
        # Create Razorpay order
        amount_in_paise = int(amount * 100)
        print(f"[PAYMENT DEBUG] Creating Razorpay order with amount_in_paise: {amount_in_paise}, currency: {currency}")
        razorpay_order = client.order.create({
            'amount': amount_in_paise,  # Razorpay expects paise
            'currency': currency,
            'receipt': ref_number,
            'notes': {
                'studio_id': studio.id,
                'studio_slug': studio.slug,
                'customer_name': data.get('customer_name', ''),
                'customer_email': data.get('customer_email', ''),
                'session_id': str(session_id) if session_id else '',
                'type': 'public_booking'
            }
        })
        
        return jsonify({
            'success': True,
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key_id': key_id,
            'amount': float(amount),
            'amount_in_paise': int(amount * 100),
            'currency': currency,
            'reference': ref_number,
            'studio': {
                'name': studio.name,
                'email': studio.email
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to create payment order: {str(e)}'}), 500


@payments_public_bp.route('/public/verify', methods=['POST'])
def public_verify_payment():
    """Verify Razorpay payment for public/guest checkout.
    No authentication required.
    """
    data = request.get_json()
    
    required = ['studio_slug', 'razorpay_payment_id', 'razorpay_order_id', 'razorpay_signature']
    for field in required:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    # Find studio
    studio = Studio.query.filter_by(slug=data['studio_slug']).first()
    if not studio:
        return jsonify({'error': 'Studio not found'}), 404
    
    # Get studio's Razorpay client
    client, key_id, key_secret = get_studio_razorpay_client(studio)
    
    if not client or not key_secret:
        return jsonify({'error': 'Payment not configured for this studio'}), 400
    
    try:
        # Verify signature
        message = f"{data['razorpay_order_id']}|{data['razorpay_payment_id']}"
        generated_signature = hmac.new(
            key_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        if generated_signature != data['razorpay_signature']:
            return jsonify({'error': 'Invalid payment signature'}), 400
        
        return jsonify({
            'success': True,
            'message': 'Payment verified successfully',
            'payment_id': data['razorpay_payment_id'],
            'order_id': data['razorpay_order_id']
        })
        
    except Exception as e:
        return jsonify({'error': f'Payment verification failed: {str(e)}'}), 500

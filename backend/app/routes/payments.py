"""
Payment API routes for Razorpay integration, checkout, and payment management.
Supports both real Razorpay payments and Demo/Mock mode for testing.
"""
import os
import uuid
import hmac
import hashlib
from datetime import datetime, timedelta
from decimal import Decimal
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import (
    User, Contact, Payment, Refund, ClassPack, ClassPackPurchase,
    SubscriptionPlan, Subscription, Wallet, WalletTransaction,
    DiscountCode, Booking, ClassSession, Studio
)

payments_bp = Blueprint('payments', __name__, url_prefix='/api/payments')


def is_demo_mode():
    """Check if payment system is in demo/mock mode."""
    # Demo mode is enabled when RAZORPAY_KEY_ID is not set or is 'demo'
    key_id = os.getenv('RAZORPAY_KEY_ID', '')
    return not key_id or key_id == 'demo' or key_id.startswith('demo_')


# ============================================================
# DEMO/MOCK PAYMENT SYSTEM
# ============================================================

@payments_bp.route('/demo/status', methods=['GET'])
def demo_status():
    """Check if payment system is in demo mode."""
    demo = is_demo_mode()
    return jsonify({
        'demo_mode': demo,
        'message': 'Demo mode enabled - payments are simulated' if demo else 'Live mode - real payments',
        'test_cards': {
            'success': '4111 1111 1111 1111',
            'decline': '4000 0000 0000 0002',
            'insufficient_funds': '4000 0000 0000 9995'
        } if demo else None
    })


@payments_bp.route('/demo/create-order', methods=['POST'])
@jwt_required()
def demo_create_order():
    """Create a demo/mock order for testing payments without Razorpay."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    # Validate required fields
    if 'contact_id' not in data:
        return jsonify({'error': 'contact_id is required'}), 400
    if 'amount' not in data:
        return jsonify({'error': 'amount is required'}), 400
    if 'purchase_type' not in data:
        return jsonify({'error': 'purchase_type is required'}), 400
    
    contact = Contact.query.filter_by(
        id=data['contact_id'],
        studio_id=user.studio_id
    ).first()
    
    if not contact:
        return jsonify({'error': 'Contact not found'}), 404
    
    # Calculate amounts
    amount = Decimal(str(data['amount']))
    
    # Apply discount
    discount_amount, discount_error = calculate_discount(
        amount, 
        data.get('discount_code'),
        user.studio_id
    )
    
    if discount_error and data.get('discount_code'):
        return jsonify({'error': discount_error}), 400
    
    subtotal = amount - discount_amount
    tax_rate = Decimal('18')
    tax_amount = subtotal * (tax_rate / Decimal('100'))
    total_amount = subtotal + tax_amount
    
    # Check wallet balance if requested
    wallet_deduction = Decimal('0')
    if data.get('use_wallet'):
        wallet = Wallet.query.filter_by(contact_id=data['contact_id']).first()
        if wallet and wallet.balance > 0:
            wallet_deduction = min(wallet.balance, total_amount)
            total_amount -= wallet_deduction
    
    # Generate demo order ID
    demo_order_id = f"demo_order_{uuid.uuid4().hex[:16]}"
    
    # Create payment record
    payment = Payment(
        id=str(uuid.uuid4()),
        payment_number=generate_payment_number(),
        studio_id=user.studio_id,
        contact_id=data['contact_id'],
        amount=amount,
        currency=data.get('currency', 'INR'),
        tax_amount=tax_amount,
        tax_rate=tax_rate,
        discount_code=data.get('discount_code'),
        discount_amount=discount_amount,
        total_amount=total_amount,
        provider='DEMO',
        purchase_type=data['purchase_type'],
        purchase_description=data.get('description', ''),
        status='PENDING',
        provider_order_id=demo_order_id
    )
    
    db.session.add(payment)
    
    # Deduct from wallet if applicable
    if wallet_deduction > 0:
        wallet = Wallet.query.filter_by(contact_id=data['contact_id']).first()
        wallet.balance -= wallet_deduction
        
        transaction = WalletTransaction(
            id=str(uuid.uuid4()),
            wallet_id=wallet.id,
            type='DEBIT',
            amount=wallet_deduction,
            balance_after=wallet.balance,
            description=f'Payment for {data["purchase_type"]}',
            reference_type='payment',
            reference_id=payment.id
        )
        db.session.add(transaction)
    
    db.session.commit()
    
    return jsonify({
        'payment_id': payment.id,
        'demo_order_id': demo_order_id,
        'demo_mode': True,
        'amount': float(amount),
        'discount_amount': float(discount_amount),
        'tax_amount': float(tax_amount),
        'wallet_deduction': float(wallet_deduction),
        'total_amount': float(total_amount),
        'currency': payment.currency,
        'contact': {
            'name': contact.name,
            'email': contact.email,
            'phone': contact.phone
        },
        'test_cards': {
            'success': '4111 1111 1111 1111',
            'decline': '4000 0000 0000 0002'
        }
    })


@payments_bp.route('/demo/complete', methods=['POST'])
@jwt_required()
def demo_complete_payment():
    """
    Complete a demo payment - simulates successful payment.
    Use card_number '4111 1111 1111 1111' for success, '4000 0000 0000 0002' for decline.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    data = request.get_json()
    
    if 'payment_id' not in data:
        return jsonify({'error': 'payment_id is required'}), 400
    
    # Optional: simulate card behavior
    card_number = data.get('card_number', '4111111111111111').replace(' ', '')
    
    # Get payment record
    payment = Payment.query.filter_by(
        id=data['payment_id'],
        studio_id=user.studio_id
    ).first()
    
    if not payment:
        return jsonify({'error': 'Payment not found'}), 404
    
    if payment.status == 'COMPLETED':
        return jsonify({'error': 'Payment already completed'}), 400
    
    # Simulate card responses
    if card_number == '4000000000000002':
        payment.status = 'FAILED'
        payment.failure_reason = 'Card declined (test card)'
        db.session.commit()
        return jsonify({
            'success': False,
            'error': 'Card declined',
            'demo_mode': True
        }), 400
    
    if card_number == '4000000000009995':
        payment.status = 'FAILED'
        payment.failure_reason = 'Insufficient funds (test card)'
        db.session.commit()
        return jsonify({
            'success': False,
            'error': 'Insufficient funds',
            'demo_mode': True
        }), 400
    
    # Success case
    payment.status = 'COMPLETED'
    payment.provider_payment_id = f"demo_pay_{uuid.uuid4().hex[:16]}"
    payment.completed_at = datetime.utcnow()
    payment.invoice_number = generate_invoice_number(user.studio_id)
    payment.payment_method = 'DEMO_CARD'
    payment.payment_method_details = {
        'card_last4': card_number[-4:],
        'demo': True
    }
    
    # Activate the purchase
    activate_purchase(payment)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Demo payment completed successfully!',
        'demo_mode': True,
        'payment': payment.to_dict(),
        'invoice_number': payment.invoice_number
    })


@payments_bp.route('/demo/quick-payment', methods=['POST'])
@jwt_required()
def demo_quick_payment():
    """
    Single-step demo payment - creates and completes payment in one call.
    Perfect for quick testing and demos.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    # Validate required fields
    if 'contact_id' not in data:
        return jsonify({'error': 'contact_id is required'}), 400
    if 'amount' not in data:
        return jsonify({'error': 'amount is required'}), 400
    if 'purchase_type' not in data:
        return jsonify({'error': 'purchase_type is required'}), 400
    
    contact = Contact.query.filter_by(
        id=data['contact_id'],
        studio_id=user.studio_id
    ).first()
    
    if not contact:
        return jsonify({'error': 'Contact not found'}), 404
    
    # Calculate amounts
    amount = Decimal(str(data['amount']))
    discount_amount, _ = calculate_discount(amount, data.get('discount_code'), user.studio_id)
    subtotal = amount - discount_amount
    tax_rate = Decimal('18')
    tax_amount = subtotal * (tax_rate / Decimal('100'))
    total_amount = subtotal + tax_amount
    
    # Create completed payment record
    payment = Payment(
        id=str(uuid.uuid4()),
        payment_number=generate_payment_number(),
        studio_id=user.studio_id,
        contact_id=data['contact_id'],
        amount=amount,
        currency=data.get('currency', 'INR'),
        tax_amount=tax_amount,
        tax_rate=tax_rate,
        discount_code=data.get('discount_code'),
        discount_amount=discount_amount,
        total_amount=total_amount,
        provider='DEMO',
        purchase_type=data['purchase_type'],
        purchase_description=data.get('description', 'Demo payment'),
        status='COMPLETED',
        provider_order_id=f"demo_order_{uuid.uuid4().hex[:12]}",
        provider_payment_id=f"demo_pay_{uuid.uuid4().hex[:12]}",
        completed_at=datetime.utcnow(),
        invoice_number=generate_invoice_number(user.studio_id),
        payment_method='DEMO',
        payment_method_details={'demo': True, 'instant': True}
    )
    
    db.session.add(payment)
    
    # Activate the purchase
    activate_purchase(payment)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Demo payment completed instantly!',
        'demo_mode': True,
        'payment': payment.to_dict(),
        'invoice_number': payment.invoice_number,
        'amounts': {
            'subtotal': float(amount),
            'discount': float(discount_amount),
            'tax': float(tax_amount),
            'total': float(total_amount)
        }
    })


# Razorpay client (initialized lazily)
_razorpay_client = None


def get_razorpay_client():
    """Get or create Razorpay client."""
    global _razorpay_client
    if _razorpay_client is None:
        try:
            import razorpay
            _razorpay_client = razorpay.Client(
                auth=(
                    os.getenv('RAZORPAY_KEY_ID', ''),
                    os.getenv('RAZORPAY_KEY_SECRET', '')
                )
            )
        except ImportError:
            return None
    return _razorpay_client


def generate_payment_number():
    """Generate unique payment number."""
    year = datetime.utcnow().year
    count = Payment.query.filter(
        db.extract('year', Payment.created_at) == year
    ).count()
    return f"PAY-{year}-{str(count + 1).zfill(5)}"


def generate_invoice_number(studio_id):
    """Generate unique invoice number."""
    year = datetime.utcnow().year
    count = Payment.query.filter(
        Payment.studio_id == studio_id,
        db.extract('year', Payment.created_at) == year,
        Payment.invoice_number.isnot(None)
    ).count()
    return f"INV-{year}-{str(count + 1).zfill(5)}"


def calculate_discount(amount, discount_code_str, studio_id):
    """Calculate discount amount from code."""
    if not discount_code_str:
        return Decimal('0'), None
    
    code = DiscountCode.query.filter_by(
        code=discount_code_str.upper(),
        studio_id=studio_id,
        is_active=True
    ).first()
    
    if not code:
        return Decimal('0'), 'Invalid discount code'
    
    # Check validity
    now = datetime.utcnow()
    if code.valid_from and now < code.valid_from:
        return Decimal('0'), 'Discount code not yet valid'
    if code.valid_until and now > code.valid_until:
        return Decimal('0'), 'Discount code expired'
    
    # Check usage limit
    if code.max_uses and code.uses_count >= code.max_uses:
        return Decimal('0'), 'Discount code usage limit reached'
    
    # Check minimum amount
    if code.minimum_amount and amount < code.minimum_amount:
        return Decimal('0'), f'Minimum purchase of ₹{code.minimum_amount} required'
    
    # Calculate discount
    if code.discount_type == 'PERCENTAGE':
        discount = amount * (code.discount_value / Decimal('100'))
    else:
        discount = code.discount_value
    
    return min(discount, amount), None


# ============================================================
# RAZORPAY ORDER CREATION
# ============================================================

@payments_bp.route('/create-order', methods=['POST'])
@jwt_required()
def create_order():
    """Create a Razorpay order for checkout."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    # Validate required fields
    if 'contact_id' not in data:
        return jsonify({'error': 'contact_id is required'}), 400
    
    if 'amount' not in data:
        return jsonify({'error': 'amount is required'}), 400
    
    if 'purchase_type' not in data:
        return jsonify({'error': 'purchase_type is required'}), 400
    
    contact = Contact.query.filter_by(
        id=data['contact_id'],
        studio_id=user.studio_id
    ).first()
    
    if not contact:
        return jsonify({'error': 'Contact not found'}), 404
    
    # Calculate amounts
    amount = Decimal(str(data['amount']))
    
    # Apply discount
    discount_amount, discount_error = calculate_discount(
        amount, 
        data.get('discount_code'),
        user.studio_id
    )
    
    if discount_error and data.get('discount_code'):
        return jsonify({'error': discount_error}), 400
    
    subtotal = amount - discount_amount
    
    # Calculate tax (GST 18%)
    tax_rate = Decimal('18')
    tax_amount = subtotal * (tax_rate / Decimal('100'))
    
    # Total
    total_amount = subtotal + tax_amount
    
    # Check wallet balance if requested
    wallet_deduction = Decimal('0')
    if data.get('use_wallet'):
        wallet = Wallet.query.filter_by(contact_id=data['contact_id']).first()
        if wallet and wallet.balance > 0:
            wallet_deduction = min(wallet.balance, total_amount)
            total_amount -= wallet_deduction
    
    # Create payment record
    payment = Payment(
        id=str(uuid.uuid4()),
        payment_number=generate_payment_number(),
        studio_id=user.studio_id,
        contact_id=data['contact_id'],
        amount=amount,
        currency=data.get('currency', 'INR'),
        tax_amount=tax_amount,
        tax_rate=tax_rate,
        discount_code=data.get('discount_code'),
        discount_amount=discount_amount,
        total_amount=total_amount,
        provider='RAZORPAY',
        purchase_type=data['purchase_type'],
        purchase_description=data.get('description', ''),
        status='PENDING'
    )
    
    # Create Razorpay order if amount > 0
    if total_amount > 0:
        client = get_razorpay_client()
        if not client:
            return jsonify({'error': 'Payment provider not configured'}), 500
        
        try:
            razorpay_order = client.order.create({
                'amount': int(total_amount * 100),  # Razorpay expects paise
                'currency': payment.currency,
                'receipt': payment.payment_number,
                'notes': {
                    'studio_id': user.studio_id,
                    'contact_id': data['contact_id'],
                    'purchase_type': data['purchase_type']
                }
            })
            
            payment.provider_order_id = razorpay_order['id']
            
        except Exception as e:
            return jsonify({'error': f'Failed to create order: {str(e)}'}), 500
    else:
        # Free order (fully covered by wallet)
        payment.status = 'COMPLETED'
        payment.completed_at = datetime.utcnow()
        payment.invoice_number = generate_invoice_number(user.studio_id)
    
    db.session.add(payment)
    
    # Deduct from wallet if applicable
    if wallet_deduction > 0:
        wallet = Wallet.query.filter_by(contact_id=data['contact_id']).first()
        wallet.balance -= wallet_deduction
        
        transaction = WalletTransaction(
            id=str(uuid.uuid4()),
            wallet_id=wallet.id,
            type='DEBIT',
            amount=wallet_deduction,
            balance_after=wallet.balance,
            description=f'Payment for {data["purchase_type"]}',
            reference_type='payment',
            reference_id=payment.id
        )
        db.session.add(transaction)
    
    db.session.commit()
    
    return jsonify({
        'payment_id': payment.id,
        'razorpay_order_id': payment.provider_order_id,
        'razorpay_key_id': os.getenv('RAZORPAY_KEY_ID'),
        'amount': float(amount),
        'discount_amount': float(discount_amount),
        'tax_amount': float(tax_amount),
        'wallet_deduction': float(wallet_deduction),
        'total_amount': float(total_amount),
        'total_amount_in_paise': int(total_amount * 100),
        'currency': payment.currency,
        'contact': {
            'id': contact.id,
            'name': contact.name,
            'email': contact.email,
            'phone': contact.phone
        }
    })
        'currency': payment.currency,
        'contact': {
            'name': contact.name,
            'email': contact.email,
            'phone': contact.phone
        }
    })


@payments_bp.route('/verify', methods=['POST'])
@jwt_required()
def verify_payment():
    """Verify Razorpay payment signature and complete the payment."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    data = request.get_json()
    
    required = ['payment_id', 'razorpay_payment_id', 'razorpay_order_id', 'razorpay_signature']
    for field in required:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    # Get payment record
    payment = Payment.query.filter_by(
        id=data['payment_id'],
        studio_id=user.studio_id
    ).first()
    
    if not payment:
        return jsonify({'error': 'Payment not found'}), 404
    
    if payment.status == 'COMPLETED':
        return jsonify({'error': 'Payment already completed'}), 400
    
    # Verify signature
    client = get_razorpay_client()
    if not client:
        return jsonify({'error': 'Payment provider not configured'}), 500
    
    try:
        # Razorpay signature verification
        message = f"{data['razorpay_order_id']}|{data['razorpay_payment_id']}"
        secret = os.getenv('RAZORPAY_KEY_SECRET', '').encode('utf-8')
        generated_signature = hmac.new(
            secret,
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        if generated_signature != data['razorpay_signature']:
            payment.status = 'FAILED'
            payment.failure_reason = 'Signature verification failed'
            db.session.commit()
            return jsonify({'error': 'Payment verification failed'}), 400
        
    except Exception as e:
        payment.status = 'FAILED'
        payment.failure_reason = str(e)
        db.session.commit()
        return jsonify({'error': f'Verification error: {str(e)}'}), 400
    
    # Update payment record
    payment.status = 'COMPLETED'
    payment.provider_payment_id = data['razorpay_payment_id']
    payment.provider_signature = data['razorpay_signature']
    payment.completed_at = datetime.utcnow()
    payment.invoice_number = generate_invoice_number(user.studio_id)
    
    # Get payment details from Razorpay
    try:
        razorpay_payment = client.payment.fetch(data['razorpay_payment_id'])
        payment.payment_method = razorpay_payment.get('method')
        payment.payment_method_details = {
            'bank': razorpay_payment.get('bank'),
            'wallet': razorpay_payment.get('wallet'),
            'vpa': razorpay_payment.get('vpa'),  # UPI ID
            'card_last4': razorpay_payment.get('card', {}).get('last4') if razorpay_payment.get('card') else None
        }
    except Exception:
        pass
    
    # Activate the purchase
    activate_purchase(payment)
    
    # Update discount code usage
    if payment.discount_code:
        code = DiscountCode.query.filter_by(code=payment.discount_code.upper()).first()
        if code:
            code.uses_count += 1
    
    db.session.commit()
    
    return jsonify({
        'message': 'Payment successful',
        'payment': payment.to_dict(),
        'invoice_number': payment.invoice_number
    })


def activate_purchase(payment):
    """Activate the purchased item based on purchase type."""
    
    if payment.purchase_type == 'CLASS_PACK':
        # Find class pack by ID in purchase description or separate field
        # For now, assume class_pack_id is passed in description
        class_pack = ClassPack.query.filter_by(
            studio_id=payment.studio_id,
            is_active=True
        ).first()
        
        if class_pack:
            purchase = ClassPackPurchase(
                id=str(uuid.uuid4()),
                studio_id=payment.studio_id,
                contact_id=payment.contact_id,
                class_pack_id=class_pack.id,
                payment_id=payment.id,
                classes_total=class_pack.class_count,
                classes_used=0,
                expires_at=datetime.utcnow() + timedelta(days=class_pack.validity_days),
                status='ACTIVE'
            )
            db.session.add(purchase)
    
    elif payment.purchase_type == 'SUBSCRIPTION':
        # Create subscription
        plan = SubscriptionPlan.query.filter_by(
            studio_id=payment.studio_id,
            is_active=True
        ).first()
        
        if plan:
            # Calculate period end based on billing cycle
            if plan.billing_cycle == 'MONTHLY':
                period_end = datetime.utcnow() + timedelta(days=30)
            elif plan.billing_cycle == 'QUARTERLY':
                period_end = datetime.utcnow() + timedelta(days=90)
            else:  # YEARLY
                period_end = datetime.utcnow() + timedelta(days=365)
            
            subscription = Subscription(
                id=str(uuid.uuid4()),
                studio_id=payment.studio_id,
                contact_id=payment.contact_id,
                plan_id=plan.id,
                provider='RAZORPAY',
                started_at=datetime.utcnow(),
                current_period_start=datetime.utcnow(),
                current_period_end=period_end,
                status='ACTIVE'
            )
            db.session.add(subscription)
    
    elif payment.purchase_type == 'DROP_IN':
        # Create booking if session_id provided
        pass  # Handled separately in booking flow


# ============================================================
# RAZORPAY WEBHOOK
# ============================================================

@payments_bp.route('/webhook/razorpay', methods=['POST'])
def razorpay_webhook():
    """Handle Razorpay webhook events."""
    payload = request.get_data(as_text=True)
    signature = request.headers.get('X-Razorpay-Signature')
    
    webhook_secret = os.getenv('RAZORPAY_WEBHOOK_SECRET', '')
    
    # Verify webhook signature
    expected_signature = hmac.new(
        webhook_secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    if signature != expected_signature:
        return jsonify({'error': 'Invalid signature'}), 400
    
    event = request.json
    event_type = event.get('event')
    
    if event_type == 'payment.captured':
        handle_payment_captured(event['payload']['payment']['entity'])
    
    elif event_type == 'payment.failed':
        handle_payment_failed(event['payload']['payment']['entity'])
    
    elif event_type == 'refund.created':
        handle_refund_created(event['payload']['refund']['entity'])
    
    elif event_type == 'subscription.charged':
        handle_subscription_charged(event['payload']['subscription']['entity'])
    
    elif event_type == 'subscription.cancelled':
        handle_subscription_cancelled(event['payload']['subscription']['entity'])
    
    return jsonify({'status': 'ok'})


def handle_payment_captured(payment_data):
    """Handle successful payment capture."""
    payment = Payment.query.filter_by(
        provider_order_id=payment_data.get('order_id')
    ).first()
    
    if payment and payment.status != 'COMPLETED':
        payment.status = 'COMPLETED'
        payment.provider_payment_id = payment_data.get('id')
        payment.payment_method = payment_data.get('method')
        payment.completed_at = datetime.utcnow()
        payment.invoice_number = generate_invoice_number(payment.studio_id)
        
        activate_purchase(payment)
        db.session.commit()


def handle_payment_failed(payment_data):
    """Handle failed payment."""
    payment = Payment.query.filter_by(
        provider_order_id=payment_data.get('order_id')
    ).first()
    
    if payment:
        payment.status = 'FAILED'
        payment.failure_reason = payment_data.get('error_description', 'Payment failed')
        db.session.commit()


def handle_refund_created(refund_data):
    """Handle refund creation."""
    payment = Payment.query.filter_by(
        provider_payment_id=refund_data.get('payment_id')
    ).first()
    
    if payment:
        refund = Refund(
            id=str(uuid.uuid4()),
            payment_id=payment.id,
            amount=Decimal(str(refund_data.get('amount', 0))) / 100,
            provider_refund_id=refund_data.get('id'),
            status='PROCESSED',
            processed_at=datetime.utcnow()
        )
        
        db.session.add(refund)
        
        # Update payment status
        total_refunded = sum(r.amount for r in payment.refunds.all()) + refund.amount
        if total_refunded >= payment.total_amount:
            payment.status = 'REFUNDED'
        else:
            payment.status = 'PARTIALLY_REFUNDED'
        
        db.session.commit()


def handle_subscription_charged(subscription_data):
    """Handle subscription renewal."""
    subscription = Subscription.query.filter_by(
        provider_subscription_id=subscription_data.get('id')
    ).first()
    
    if subscription:
        # Reset usage for new period
        subscription.classes_used_this_period = 0
        subscription.current_period_start = datetime.utcnow()
        
        # Calculate new period end
        if subscription.plan.billing_cycle == 'MONTHLY':
            subscription.current_period_end = datetime.utcnow() + timedelta(days=30)
        elif subscription.plan.billing_cycle == 'QUARTERLY':
            subscription.current_period_end = datetime.utcnow() + timedelta(days=90)
        else:
            subscription.current_period_end = datetime.utcnow() + timedelta(days=365)
        
        subscription.status = 'ACTIVE'
        db.session.commit()


def handle_subscription_cancelled(subscription_data):
    """Handle subscription cancellation."""
    subscription = Subscription.query.filter_by(
        provider_subscription_id=subscription_data.get('id')
    ).first()
    
    if subscription:
        subscription.status = 'CANCELLED'
        subscription.cancelled_at = datetime.utcnow()
        db.session.commit()


# ============================================================
# PAYMENT HISTORY
# ============================================================

@payments_bp.route('', methods=['GET'])
@jwt_required()
def list_payments():
    """List payment history."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    contact_id = request.args.get('contact_id')
    status = request.args.get('status')
    limit = request.args.get('limit', 50, type=int)
    
    query = Payment.query.filter_by(studio_id=user.studio_id)
    
    if contact_id:
        query = query.filter_by(contact_id=contact_id)
    
    if status:
        query = query.filter_by(status=status)
    
    payments = query.order_by(Payment.created_at.desc()).limit(limit).all()
    
    result = []
    for payment in payments:
        payment_data = payment.to_dict()
        
        # Add contact name
        contact = Contact.query.get(payment.contact_id)
        if contact:
            payment_data['contact_name'] = contact.name
        
        result.append(payment_data)
    
    return jsonify({
        'payments': result,
        'total': len(result)
    })


@payments_bp.route('/<payment_id>', methods=['GET'])
@jwt_required()
def get_payment(payment_id):
    """Get payment details."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    payment = Payment.query.filter_by(
        id=payment_id,
        studio_id=user.studio_id
    ).first()
    
    if not payment:
        return jsonify({'error': 'Payment not found'}), 404
    
    payment_data = payment.to_dict()
    
    # Add contact info
    contact = Contact.query.get(payment.contact_id)
    if contact:
        payment_data['contact'] = {
            'id': contact.id,
            'name': contact.name,
            'email': contact.email,
            'phone': contact.phone
        }
    
    # Add refunds
    payment_data['refunds'] = [r.to_dict() for r in payment.refunds.all()]
    
    return jsonify(payment_data)


@payments_bp.route('/<payment_id>/refund', methods=['POST'])
@jwt_required()
def create_refund(payment_id):
    """Initiate a refund."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role not in ['owner', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    payment = Payment.query.filter_by(
        id=payment_id,
        studio_id=user.studio_id
    ).first()
    
    if not payment:
        return jsonify({'error': 'Payment not found'}), 404
    
    if payment.status not in ['COMPLETED', 'PARTIALLY_REFUNDED']:
        return jsonify({'error': 'Cannot refund this payment'}), 400
    
    data = request.get_json()
    
    # Calculate refundable amount
    already_refunded = sum(r.amount for r in payment.refunds.all())
    max_refundable = payment.total_amount - already_refunded
    
    refund_amount = Decimal(str(data.get('amount', max_refundable)))
    
    if refund_amount > max_refundable:
        return jsonify({'error': f'Maximum refundable amount is ₹{max_refundable}'}), 400
    
    # Create refund via Razorpay
    client = get_razorpay_client()
    if client and payment.provider_payment_id:
        try:
            razorpay_refund = client.payment.refund(payment.provider_payment_id, {
                'amount': int(refund_amount * 100)
            })
            
            refund = Refund(
                id=str(uuid.uuid4()),
                payment_id=payment.id,
                amount=refund_amount,
                reason=data.get('reason', 'Refund requested'),
                provider_refund_id=razorpay_refund.get('id'),
                status='PROCESSED',
                processed_at=datetime.utcnow()
            )
            
        except Exception as e:
            return jsonify({'error': f'Refund failed: {str(e)}'}), 500
    else:
        # Manual refund (cash/wallet)
        refund = Refund(
            id=str(uuid.uuid4()),
            payment_id=payment.id,
            amount=refund_amount,
            reason=data.get('reason', 'Refund requested'),
            status='PROCESSED',
            processed_at=datetime.utcnow()
        )
        
        # Credit to wallet if requested
        if data.get('refund_to_wallet'):
            wallet = Wallet.query.filter_by(contact_id=payment.contact_id).first()
            if not wallet:
                wallet = Wallet(
                    id=str(uuid.uuid4()),
                    studio_id=payment.studio_id,
                    contact_id=payment.contact_id,
                    balance=Decimal('0')
                )
                db.session.add(wallet)
            
            wallet.balance += refund_amount
            
            transaction = WalletTransaction(
                id=str(uuid.uuid4()),
                wallet_id=wallet.id,
                type='CREDIT',
                amount=refund_amount,
                balance_after=wallet.balance,
                description=f'Refund for payment {payment.payment_number}',
                reference_type='refund',
                reference_id=refund.id
            )
            db.session.add(transaction)
    
    # Update payment status
    total_refunded = already_refunded + refund_amount
    if total_refunded >= payment.total_amount:
        payment.status = 'REFUNDED'
    else:
        payment.status = 'PARTIALLY_REFUNDED'
    
    db.session.add(refund)
    db.session.commit()
    
    return jsonify({
        'message': 'Refund processed',
        'refund': refund.to_dict()
    })


# ============================================================
# CLASS PACKS
# ============================================================

@payments_bp.route('/class-packs', methods=['GET'])
@jwt_required()
def list_class_packs():
    """List available class packs."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    packs = ClassPack.query.filter_by(
        studio_id=user.studio_id,
        is_active=True
    ).all()
    
    return jsonify({
        'class_packs': [p.to_dict() for p in packs]
    })


@payments_bp.route('/class-packs', methods=['POST'])
@jwt_required()
def create_class_pack():
    """Create a new class pack (admin only)."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role not in ['owner', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    pack = ClassPack(
        id=str(uuid.uuid4()),
        studio_id=user.studio_id,
        name=data['name'],
        description=data.get('description'),
        class_count=data['class_count'],
        price=Decimal(str(data['price'])),
        validity_days=data.get('validity_days', 60),
        class_types=data.get('class_types'),
        is_active=True
    )
    
    db.session.add(pack)
    db.session.commit()
    
    return jsonify(pack.to_dict()), 201


@payments_bp.route('/my-packs', methods=['GET'])
@jwt_required()
def my_class_packs():
    """List contact's purchased class packs."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    contact_id = request.args.get('contact_id')
    
    if not contact_id:
        return jsonify({'error': 'contact_id is required'}), 400
    
    purchases = ClassPackPurchase.query.filter_by(
        contact_id=contact_id,
        status='ACTIVE'
    ).filter(
        ClassPackPurchase.expires_at > datetime.utcnow()
    ).all()
    
    result = []
    for purchase in purchases:
        purchase_data = purchase.to_dict()
        
        # Add pack details
        pack = ClassPack.query.get(purchase.class_pack_id)
        if pack:
            purchase_data['pack_name'] = pack.name
        
        result.append(purchase_data)
    
    return jsonify({
        'class_packs': result
    })


# ============================================================
# SUBSCRIPTIONS
# ============================================================

@payments_bp.route('/subscription-plans', methods=['GET'])
@jwt_required()
def list_subscription_plans():
    """List available subscription plans."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    plans = SubscriptionPlan.query.filter_by(
        studio_id=user.studio_id,
        is_active=True
    ).all()
    
    return jsonify({
        'plans': [p.to_dict() for p in plans]
    })


@payments_bp.route('/subscriptions', methods=['GET'])
@jwt_required()
def list_subscriptions():
    """List subscriptions."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    contact_id = request.args.get('contact_id')
    
    query = Subscription.query.filter_by(studio_id=user.studio_id)
    
    if contact_id:
        query = query.filter_by(contact_id=contact_id)
    
    subscriptions = query.all()
    
    return jsonify({
        'subscriptions': [s.to_dict(include_plan=True) for s in subscriptions]
    })


@payments_bp.route('/subscriptions/<subscription_id>/cancel', methods=['PUT'])
@jwt_required()
def cancel_subscription(subscription_id):
    """Cancel a subscription."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    subscription = Subscription.query.filter_by(
        id=subscription_id,
        studio_id=user.studio_id
    ).first()
    
    if not subscription:
        return jsonify({'error': 'Subscription not found'}), 404
    
    if subscription.status == 'CANCELLED':
        return jsonify({'error': 'Already cancelled'}), 400
    
    # Cancel in Razorpay if applicable
    client = get_razorpay_client()
    if client and subscription.provider_subscription_id:
        try:
            client.subscription.cancel(subscription.provider_subscription_id)
        except Exception:
            pass
    
    subscription.status = 'CANCELLED'
    subscription.cancelled_at = datetime.utcnow()
    subscription.auto_renew = False
    
    db.session.commit()
    
    return jsonify({
        'message': 'Subscription cancelled',
        'subscription': subscription.to_dict()
    })


# ============================================================
# WALLET
# ============================================================

@payments_bp.route('/wallet', methods=['GET'])
@jwt_required()
def get_wallet():
    """Get wallet balance."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    contact_id = request.args.get('contact_id')
    
    if not contact_id:
        return jsonify({'error': 'contact_id is required'}), 400
    
    wallet = Wallet.query.filter_by(contact_id=contact_id).first()
    
    if not wallet:
        # Create wallet if doesn't exist
        wallet = Wallet(
            id=str(uuid.uuid4()),
            studio_id=user.studio_id,
            contact_id=contact_id,
            balance=Decimal('0')
        )
        db.session.add(wallet)
        db.session.commit()
    
    return jsonify(wallet.to_dict())


@payments_bp.route('/wallet/transactions', methods=['GET'])
@jwt_required()
def wallet_transactions():
    """Get wallet transaction history."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    contact_id = request.args.get('contact_id')
    
    if not contact_id:
        return jsonify({'error': 'contact_id is required'}), 400
    
    wallet = Wallet.query.filter_by(contact_id=contact_id).first()
    
    if not wallet:
        return jsonify({'transactions': [], 'balance': 0})
    
    transactions = WalletTransaction.query.filter_by(
        wallet_id=wallet.id
    ).order_by(WalletTransaction.created_at.desc()).limit(50).all()
    
    return jsonify({
        'transactions': [t.to_dict() for t in transactions],
        'balance': float(wallet.balance)
    })


@payments_bp.route('/wallet/add-funds', methods=['POST'])
@jwt_required()
def add_wallet_funds():
    """Add funds to wallet (admin only)."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role not in ['owner', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    contact_id = data.get('contact_id')
    amount = Decimal(str(data.get('amount', 0)))
    description = data.get('description', 'Manual credit')
    
    if not contact_id or amount <= 0:
        return jsonify({'error': 'Valid contact_id and amount required'}), 400
    
    wallet = Wallet.query.filter_by(contact_id=contact_id).first()
    
    if not wallet:
        wallet = Wallet(
            id=str(uuid.uuid4()),
            studio_id=user.studio_id,
            contact_id=contact_id,
            balance=Decimal('0')
        )
        db.session.add(wallet)
    
    wallet.balance += amount
    
    transaction = WalletTransaction(
        id=str(uuid.uuid4()),
        wallet_id=wallet.id,
        type='CREDIT',
        amount=amount,
        balance_after=wallet.balance,
        description=description,
        reference_type='manual'
    )
    
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify({
        'message': 'Funds added',
        'wallet': wallet.to_dict()
    })


# ============================================================
# DISCOUNT CODES
# ============================================================

@payments_bp.route('/discount-codes', methods=['GET'])
@jwt_required()
def list_discount_codes():
    """List discount codes (admin only)."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role not in ['owner', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    codes = DiscountCode.query.filter_by(studio_id=user.studio_id).all()
    
    return jsonify({
        'discount_codes': [c.to_dict() for c in codes]
    })


@payments_bp.route('/discount-codes', methods=['POST'])
@jwt_required()
def create_discount_code():
    """Create a discount code (admin only)."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role not in ['owner', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    code = DiscountCode(
        id=str(uuid.uuid4()),
        studio_id=user.studio_id,
        code=data['code'].upper(),
        description=data.get('description'),
        discount_type=data.get('discount_type', 'PERCENTAGE'),
        discount_value=Decimal(str(data['discount_value'])),
        max_uses=data.get('max_uses'),
        max_uses_per_user=data.get('max_uses_per_user', 1),
        minimum_amount=Decimal(str(data.get('minimum_amount', 0))),
        valid_from=datetime.fromisoformat(data['valid_from']) if data.get('valid_from') else None,
        valid_until=datetime.fromisoformat(data['valid_until']) if data.get('valid_until') else None,
        applicable_to=data.get('applicable_to'),
        is_active=True
    )
    
    db.session.add(code)
    db.session.commit()
    
    return jsonify(code.to_dict()), 201


@payments_bp.route('/validate-code', methods=['POST'])
@jwt_required()
def validate_discount_code():
    """Validate a discount code."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    data = request.get_json()
    
    code_str = data.get('code', '').upper()
    amount = Decimal(str(data.get('amount', 0)))
    
    discount, error = calculate_discount(code_str, code_str, user.studio_id)
    
    if error:
        return jsonify({'valid': False, 'error': error})
    
    return jsonify({
        'valid': True,
        'discount_amount': float(discount),
        'final_amount': float(amount - discount)
    })

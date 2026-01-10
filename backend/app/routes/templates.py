from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import uuid
import re

from app import db
from app.models import User, MessageTemplate

templates_bp = Blueprint('templates', __name__)


@templates_bp.route('', methods=['GET'])
@jwt_required()
def list_templates():
    """List all message templates."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Filters
    category = request.args.get('category')
    channel = request.args.get('channel')
    
    query = MessageTemplate.query.filter_by(studio_id=user.studio_id)
    
    if category:
        query = query.filter_by(category=category)
    if channel:
        query = query.filter(MessageTemplate.channels.contains([channel]))
    
    templates = query.order_by(MessageTemplate.category, MessageTemplate.name).all()
    
    return jsonify({
        'templates': [t.to_dict() for t in templates]
    })


@templates_bp.route('/<template_id>', methods=['GET'])
@jwt_required()
def get_template(template_id):
    """Get a single template."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    template = MessageTemplate.query.filter_by(
        id=template_id,
        studio_id=user.studio_id
    ).first()
    
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    return jsonify({'template': template.to_dict()})


@templates_bp.route('', methods=['POST'])
@jwt_required()
def create_template():
    """Create a new message template."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'error': 'name is required'}), 400
    if not data.get('content'):
        return jsonify({'error': 'content is required'}), 400
    
    # Extract variables from content (e.g., {{name}}, {{studio_name}})
    variables = re.findall(r'\{\{(\w+)\}\}', data['content'])
    
    template = MessageTemplate(
        id=str(uuid.uuid4()),
        studio_id=user.studio_id,
        name=data['name'],
        category=data.get('category'),
        subject=data.get('subject'),
        content=data['content'],
        variables=list(set(variables)),
        channels=data.get('channels', ['EMAIL', 'WHATSAPP']),
        is_active=data.get('is_active', True)
    )
    
    try:
        db.session.add(template)
        db.session.commit()
        return jsonify({'template': template.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@templates_bp.route('/<template_id>', methods=['PUT'])
@jwt_required()
def update_template(template_id):
    """Update a message template."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    template = MessageTemplate.query.filter_by(
        id=template_id,
        studio_id=user.studio_id
    ).first()
    
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        template.name = data['name']
    if 'category' in data:
        template.category = data['category']
    if 'subject' in data:
        template.subject = data['subject']
    if 'content' in data:
        template.content = data['content']
        # Re-extract variables
        template.variables = list(set(re.findall(r'\{\{(\w+)\}\}', data['content'])))
    if 'channels' in data:
        template.channels = data['channels']
    if 'is_active' in data:
        template.is_active = data['is_active']
    
    try:
        db.session.commit()
        return jsonify({'template': template.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@templates_bp.route('/<template_id>', methods=['DELETE'])
@jwt_required()
def delete_template(template_id):
    """Delete a message template."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    template = MessageTemplate.query.filter_by(
        id=template_id,
        studio_id=user.studio_id
    ).first()
    
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    try:
        db.session.delete(template)
        db.session.commit()
        return jsonify({'message': 'Template deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@templates_bp.route('/<template_id>/render', methods=['POST'])
@jwt_required()
def render_template(template_id):
    """Render a template with provided variables."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    template = MessageTemplate.query.filter_by(
        id=template_id,
        studio_id=user.studio_id
    ).first()
    
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    data = request.get_json()
    variables = data.get('variables', {})
    
    # Add default studio name if not provided
    if 'studio_name' not in variables:
        variables['studio_name'] = user.studio.name
    
    # Render content
    rendered_content = template.content
    rendered_subject = template.subject or ''
    
    for var, value in variables.items():
        rendered_content = rendered_content.replace(f'{{{{{var}}}}}', str(value))
        rendered_subject = rendered_subject.replace(f'{{{{{var}}}}}', str(value))
    
    return jsonify({
        'content': rendered_content,
        'subject': rendered_subject,
        'missing_variables': [v for v in template.variables if v not in variables]
    })


@templates_bp.route('/defaults', methods=['GET'])
def get_default_templates():
    """Get list of available default message templates."""
    default_templates = [
        {
            'id': 'welcome_new_lead',
            'name': 'Welcome - New Lead',
            'category': 'Welcome',
            'channels': ['EMAIL', 'WHATSAPP'],
            'description': 'First response to a new inquiry'
        },
        {
            'id': 'booking_confirmation',
            'name': 'Booking Confirmation',
            'category': 'Booking',
            'channels': ['EMAIL', 'WHATSAPP'],
            'description': 'Sent when a class is booked'
        },
        {
            'id': 'booking_reminder',
            'name': 'Class Reminder',
            'category': 'Booking',
            'channels': ['EMAIL', 'WHATSAPP'],
            'description': 'Reminder before scheduled class'
        },
        {
            'id': 'payment_received',
            'name': 'Payment Received',
            'category': 'Payment',
            'channels': ['EMAIL', 'WHATSAPP'],
            'description': 'Payment confirmation'
        },
        {
            'id': 'follow_up_trial',
            'name': 'Follow-up After Trial',
            'category': 'Follow-up',
            'channels': ['EMAIL', 'WHATSAPP'],
            'description': 'Follow-up after trial class'
        },
        {
            'id': 'membership_expiring',
            'name': 'Membership Expiring',
            'category': 'Membership',
            'channels': ['EMAIL', 'WHATSAPP'],
            'description': 'Alert for expiring membership'
        },
        {
            'id': 'class_cancelled',
            'name': 'Class Cancelled',
            'category': 'Booking',
            'channels': ['EMAIL', 'WHATSAPP'],
            'description': 'Notification when class is cancelled'
        },
        {
            'id': 'birthday_wish',
            'name': 'Birthday Wish',
            'category': 'Engagement',
            'channels': ['EMAIL', 'WHATSAPP'],
            'description': 'Birthday greeting with special offer'
        }
    ]
    return jsonify({'templates': default_templates})


@templates_bp.route('/load-defaults', methods=['POST'])
@jwt_required()
def load_default_templates():
    """Load default message templates for the studio."""
    from app.models import Studio
    
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    studio = Studio.query.get(user.studio_id)
    data = request.get_json() or {}
    template_ids = data.get('templates', ['all'])
    
    # Default message templates
    default_templates = {
        'welcome_new_lead': {
            'name': 'Welcome - New Lead',
            'category': 'Welcome',
            'subject': 'Welcome to {{studio_name}}! 🎉',
            'content': '''Hi {{name}},

Thank you for your interest in {{studio_name}}! We're excited to have you explore our dance classes.

Whether you're a beginner or experienced dancer, we have something for everyone!

🎁 **Special Offer:** Book your first trial class at 50% off!

Would you like to:
- 📅 Book a trial class
- 📋 Learn more about our classes
- 💰 Know about our pricing

Just reply to this message and we'll help you get started!

Looking forward to dancing with you! 💃🕺

Best regards,
{{studio_name}} Team''',
            'channels': ['EMAIL', 'WHATSAPP']
        },
        'booking_confirmation': {
            'name': 'Booking Confirmation',
            'category': 'Booking',
            'subject': 'Booking Confirmed! ✅ {{class_name}}',
            'content': '''Hi {{name}},

Your booking is confirmed! 🎉

📋 **Class Details:**
- Class: {{class_name}}
- Date: {{date}}
- Time: {{time}}
- Location: {{studio_name}}

**What to bring:**
- Comfortable clothes
- Water bottle
- Positive energy! 😊

**Important:**
- Please arrive 10 minutes early
- Wear appropriate footwear

Need to reschedule? Reply to this message at least 4 hours before class.

See you soon!
{{studio_name}} Team''',
            'channels': ['EMAIL', 'WHATSAPP']
        },
        'booking_reminder': {
            'name': 'Class Reminder',
            'category': 'Booking',
            'subject': 'Reminder: {{class_name}} Tomorrow! ⏰',
            'content': '''Hi {{name}},

This is a friendly reminder about your upcoming class!

📅 **Tomorrow's Class:**
- Class: {{class_name}}
- Time: {{time}}
- Location: {{studio_name}}

Don't forget to:
✅ Wear comfortable clothes
✅ Bring water
✅ Arrive 10 mins early

Can't make it? Please let us know ASAP so we can open the spot for someone else.

See you tomorrow! 🎉
{{studio_name}} Team''',
            'channels': ['EMAIL', 'WHATSAPP']
        },
        'payment_received': {
            'name': 'Payment Received',
            'category': 'Payment',
            'subject': 'Payment Received ✅ Thank You!',
            'content': '''Hi {{name}},

We've received your payment! 🎉

💰 **Payment Details:**
- Amount: {{amount}}
- For: {{description}}
- Transaction ID: {{transaction_id}}
- Date: {{date}}

Your receipt has been attached/sent separately.

Thank you for choosing {{studio_name}}!

Questions about your payment? Reply to this message.

Best regards,
{{studio_name}} Team''',
            'channels': ['EMAIL', 'WHATSAPP']
        },
        'follow_up_trial': {
            'name': 'Follow-up After Trial',
            'category': 'Follow-up',
            'subject': 'How was your trial class? 🤔',
            'content': '''Hi {{name}},

We hope you enjoyed your trial class at {{studio_name}}! 💃

We'd love to hear about your experience:
- What did you think of the class?
- Would you like to continue learning with us?

🎁 **Special Offer for You:**
Sign up this week and get 20% off your first month!

Ready to take the next step? Here are your options:
- 📦 Class Packages (4, 8, or 12 classes)
- 🏆 Monthly Unlimited
- 🎯 Pay per class

Reply to this message and we'll help you choose the best option!

Keep dancing! 🕺
{{studio_name}} Team''',
            'channels': ['EMAIL', 'WHATSAPP']
        },
        'membership_expiring': {
            'name': 'Membership Expiring',
            'category': 'Membership',
            'subject': 'Your Membership is Expiring Soon! ⚠️',
            'content': '''Hi {{name}},

Your membership at {{studio_name}} is expiring on {{expiry_date}}!

Don't let your dance journey stop now! 💃

🎁 **Renewal Bonus:**
Renew before {{expiry_date}} and get:
- 10% off your renewal
- 1 bonus class FREE

**Your Options:**
1. Same plan - {{current_plan}}
2. Upgrade to unlimited
3. Try a different package

Reply "RENEW" to continue with your current plan, or let us know if you'd like to explore other options!

Keep the rhythm going! 🎵
{{studio_name}} Team''',
            'channels': ['EMAIL', 'WHATSAPP']
        },
        'class_cancelled': {
            'name': 'Class Cancelled',
            'category': 'Booking',
            'subject': 'Class Cancelled - {{class_name}} on {{date}}',
            'content': '''Hi {{name}},

We're sorry to inform you that your upcoming class has been cancelled.

❌ **Cancelled Class:**
- Class: {{class_name}}
- Date: {{date}}
- Time: {{time}}

**Reason:** {{reason}}

**Your Options:**
1. Reschedule to another date
2. Credit added to your account
3. Full refund

We apologize for any inconvenience. Reply to this message to let us know your preference.

Thank you for your understanding!
{{studio_name}} Team''',
            'channels': ['EMAIL', 'WHATSAPP']
        },
        'birthday_wish': {
            'name': 'Birthday Wish',
            'category': 'Engagement',
            'subject': 'Happy Birthday {{name}}! 🎂🎉',
            'content': '''🎉 Happy Birthday, {{name}}! 🎂

Wishing you a fantastic birthday filled with joy, laughter, and lots of dancing! 💃🕺

As a birthday gift from {{studio_name}}, here's a special treat:

🎁 **Birthday Special:**
Get 25% OFF any class or package this week!
Use code: BIRTHDAY25

May this year bring you:
- More dance moves
- More joy
- More rhythm in your life!

Celebrate your special day with a dance class on us!

With love,
{{studio_name}} Team 🎈''',
            'channels': ['EMAIL', 'WHATSAPP']
        }
    }
    
    created = []
    skipped = []
    
    templates_to_load = default_templates.keys() if 'all' in template_ids else template_ids
    
    for template_id in templates_to_load:
        if template_id not in default_templates:
            continue
        
        template_data = default_templates[template_id]
        
        # Check if already exists
        existing = MessageTemplate.query.filter_by(
            studio_id=user.studio_id,
            name=template_data['name']
        ).first()
        
        if existing:
            skipped.append(template_data['name'])
            continue
        
        # Extract variables from content
        variables = list(set(re.findall(r'\{\{(\w+)\}\}', template_data['content'])))
        
        template = MessageTemplate(
            id=str(uuid.uuid4()),
            studio_id=user.studio_id,
            name=template_data['name'],
            category=template_data['category'],
            subject=template_data.get('subject'),
            content=template_data['content'],
            variables=variables,
            channels=template_data.get('channels', ['EMAIL', 'WHATSAPP']),
            is_active=True
        )
        db.session.add(template)
        created.append(template_data['name'])
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Loaded {len(created)} templates',
            'created': created,
            'skipped': skipped
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

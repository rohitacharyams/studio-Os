"""
WhatsApp Webhook Routes
Handles incoming WhatsApp messages from Twilio
"""

from flask import Blueprint, request, jsonify, current_app
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator
import logging
from ..services.whatsapp import get_whatsapp_service

bp = Blueprint('whatsapp', __name__, url_prefix='/whatsapp')
logger = logging.getLogger(__name__)


def validate_twilio_request():
    """Validate that the request came from Twilio"""
    auth_token = current_app.config.get('TWILIO_AUTH_TOKEN')
    if not auth_token:
        logger.warning("Twilio auth token not configured, skipping validation")
        return True
    
    validator = RequestValidator(auth_token)
    
    # Get the URL and signature
    url = request.url
    signature = request.headers.get('X-Twilio-Signature', '')
    
    # For POST requests, use form data
    params = request.form.to_dict()
    
    return validator.validate(url, params, signature)


@bp.route('/webhook', methods=['POST'])
def whatsapp_webhook():
    """
    Webhook endpoint for incoming WhatsApp messages from Twilio
    
    Twilio sends:
    - MessageSid: Unique message identifier
    - From: Sender's number (whatsapp:+1234567890)
    - To: Your Twilio number
    - Body: Message text
    - ProfileName: WhatsApp profile name
    - MediaUrl0, MediaContentType0: If media attached
    """
    try:
        # Validate request (optional, can be strict in production)
        # if not validate_twilio_request():
        #     logger.warning("Invalid Twilio signature")
        #     return 'Invalid signature', 403
        
        # Get message data
        message_data = {
            'MessageSid': request.form.get('MessageSid'),
            'From': request.form.get('From'),
            'To': request.form.get('To'),
            'Body': request.form.get('Body', ''),
            'ProfileName': request.form.get('ProfileName'),
            'MediaUrl0': request.form.get('MediaUrl0'),
            'MediaContentType0': request.form.get('MediaContentType0'),
            'NumMedia': request.form.get('NumMedia', '0')
        }
        
        logger.info(f"Received WhatsApp message from {message_data['From']}: {message_data['Body'][:50]}...")
        
        # Process the message
        whatsapp_service = get_whatsapp_service()
        result = whatsapp_service.process_incoming_message(message_data)
        
        if result.get('success'):
            logger.info(f"Message processed: conversation_id={result.get('conversation_id')}")
        else:
            logger.error(f"Failed to process message: {result.get('error')}")
        
        # Return empty TwiML response (we handle responses separately)
        response = MessagingResponse()
        return str(response), 200
        
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {str(e)}")
        return str(MessagingResponse()), 200  # Return 200 to prevent Twilio retries


@bp.route('/status', methods=['POST'])
def status_callback():
    """
    Webhook for message delivery status updates
    
    Twilio sends:
    - MessageSid: Message identifier
    - MessageStatus: queued, sent, delivered, read, failed, undelivered
    - ErrorCode: If failed
    """
    try:
        message_sid = request.form.get('MessageSid')
        status = request.form.get('MessageStatus')
        error_code = request.form.get('ErrorCode')
        
        logger.info(f"WhatsApp message {message_sid} status: {status}")
        
        if error_code:
            logger.warning(f"WhatsApp message {message_sid} failed with error: {error_code}")
        
        # Update message status in database
        from ..models import Message, db
        message = Message.query.filter_by(external_id=message_sid).first()
        if message:
            message.status = status
            if error_code:
                message.metadata = message.metadata or {}
                message.metadata['error_code'] = error_code
            db.session.commit()
        
        return '', 200
        
    except Exception as e:
        logger.error(f"Status callback error: {str(e)}")
        return '', 200


@bp.route('/send', methods=['POST'])
def send_message():
    """
    API endpoint to send WhatsApp message
    
    Request body:
    {
        "to": "+919876543210",
        "message": "Hello from Studio OS!",
        "template": "booking_confirmation",  // optional
        "variables": {"1": "John", "2": "Salsa"}  // for templates
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        to = data.get('to')
        message = data.get('message')
        template = data.get('template')
        variables = data.get('variables', {})
        
        if not to:
            return jsonify({'error': 'Recipient phone number required'}), 400
        
        if not message and not template:
            return jsonify({'error': 'Message or template required'}), 400
        
        whatsapp_service = get_whatsapp_service()
        
        if template:
            result = whatsapp_service.send_template_message(to, template, variables)
        else:
            result = whatsapp_service.send_message(to, message)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message_sid': result.get('message_sid'),
                'status': result.get('status')
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error')
            }), 400
            
    except Exception as e:
        logger.error(f"Send message error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@bp.route('/connect', methods=['POST'])
def connect_whatsapp():
    """
    Endpoint to initiate WhatsApp Business connection
    Returns configuration needed for setup
    """
    try:
        # In production, this would:
        # 1. Generate a unique webhook URL for this studio
        # 2. Return Twilio setup instructions
        # 3. Store connection status
        
        studio_id = request.get_json().get('studio_id', 1)
        
        # Generate webhook URL
        base_url = request.host_url.rstrip('/')
        webhook_url = f"{base_url}/api/whatsapp/webhook"
        status_url = f"{base_url}/api/whatsapp/status"
        
        return jsonify({
            'success': True,
            'setup_instructions': {
                'step1': 'Go to your Twilio Console',
                'step2': 'Navigate to Messaging > Settings > WhatsApp Sandbox Settings',
                'step3': f'Set the Webhook URL to: {webhook_url}',
                'step4': f'Set the Status Callback URL to: {status_url}',
                'step5': 'Save your settings'
            },
            'webhook_url': webhook_url,
            'status_callback_url': status_url,
            'note': 'For production, you need a WhatsApp Business Account connected to Twilio'
        }), 200
        
    except Exception as e:
        logger.error(f"Connect WhatsApp error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@bp.route('/test', methods=['POST'])
def test_connection():
    """Test WhatsApp connection by sending a test message"""
    try:
        data = request.get_json()
        test_number = data.get('phone')
        
        if not test_number:
            return jsonify({'error': 'Phone number required'}), 400
        
        whatsapp_service = get_whatsapp_service()
        result = whatsapp_service.send_message(
            test_number,
            "🎉 Test message from Studio OS!\n\nYour WhatsApp integration is working correctly."
        )
        
        return jsonify(result), 200 if result.get('success') else 400
        
    except Exception as e:
        logger.error(f"Test connection error: {str(e)}")
        return jsonify({'error': str(e)}), 500

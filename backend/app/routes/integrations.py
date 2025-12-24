# Integration Routes - Channel connection and webhook handling
from flask import Blueprint, request, jsonify, current_app, redirect
from flask_jwt_extended import jwt_required, get_jwt_identity
import asyncio

from app.models import db, User, ChannelIntegration
from app.integrations import IntegrationManager

integrations_bp = Blueprint('integrations', __name__)


def run_async(coro):
    """Run async function in sync context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@integrations_bp.route('/status', methods=['GET'])
@jwt_required()
def get_integration_status():
    """Get status of all channel integrations for the studio."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    manager = IntegrationManager(user.studio_id)
    integrations = manager.list_integrations()
    
    return jsonify({
        'integrations': integrations,
        'studio_id': user.studio_id
    })


@integrations_bp.route('/connect/<channel>', methods=['POST'])
@jwt_required()
def initiate_connection(channel):
    """
    Initiate OAuth flow for connecting a channel.
    
    Returns the OAuth URL to redirect the user to.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    channel = channel.upper()
    if channel not in ['WHATSAPP', 'INSTAGRAM', 'EMAIL']:
        return jsonify({'error': 'Invalid channel'}), 400
    
    # Get redirect URI from request or use default
    data = request.get_json() or {}
    redirect_uri = data.get('redirect_uri', f"{request.host_url}api/integrations/callback/{channel.lower()}")
    
    manager = IntegrationManager(user.studio_id)
    oauth_url = manager.get_oauth_url(channel, redirect_uri)
    
    if not oauth_url:
        return jsonify({'error': 'Failed to generate OAuth URL'}), 500
    
    return jsonify({
        'oauth_url': oauth_url,
        'channel': channel
    })


@integrations_bp.route('/callback/<channel>', methods=['GET'])
def oauth_callback(channel):
    """
    Handle OAuth callback from provider.
    
    This is called after user authorizes the connection.
    """
    channel = channel.upper()
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    if error:
        return jsonify({'error': error, 'description': request.args.get('error_description')}), 400
    
    if not code or not state:
        return jsonify({'error': 'Missing code or state'}), 400
    
    # Parse state to get studio_id
    try:
        studio_id = state.split(':')[0]
    except:
        return jsonify({'error': 'Invalid state'}), 400
    
    manager = IntegrationManager(studio_id)
    redirect_uri = f"{request.host_url}api/integrations/callback/{channel.lower()}"
    
    result = run_async(manager.handle_oauth_callback(channel, code, state, redirect_uri))
    
    if result.get('success'):
        # Redirect to frontend success page
        return redirect(f"/settings/integrations?connected={channel.lower()}")
    else:
        return jsonify({'error': result.get('error')}), 400


@integrations_bp.route('/disconnect/<channel>', methods=['POST'])
@jwt_required()
def disconnect_channel(channel):
    """Disconnect a channel integration."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    channel = channel.upper()
    manager = IntegrationManager(user.studio_id)
    
    result = run_async(manager.disconnect(channel))
    
    return jsonify({
        'success': result,
        'channel': channel
    })


@integrations_bp.route('/sync', methods=['POST'])
@jwt_required()
def sync_messages():
    """
    Manually trigger message sync from all connected channels.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json() or {}
    channel = data.get('channel')  # Optional: sync specific channel
    
    manager = IntegrationManager(user.studio_id)
    result = run_async(manager.sync_messages(channel.upper() if channel else None))
    
    return jsonify(result)


@integrations_bp.route('/send', methods=['POST'])
@jwt_required()
def send_message():
    """
    Send a message through a connected channel.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    channel = data.get('channel', '').upper()
    recipient_id = data.get('recipient_id')
    content = data.get('content')
    conversation_id = data.get('conversation_id')
    
    if not all([channel, recipient_id, content]):
        return jsonify({'error': 'channel, recipient_id, and content are required'}), 400
    
    manager = IntegrationManager(user.studio_id)
    result = run_async(manager.send_message(
        channel=channel,
        recipient_id=recipient_id,
        content=content,
        conversation_id=conversation_id
    ))
    
    return jsonify(result)


# Webhook endpoints for receiving messages
@integrations_bp.route('/webhook/whatsapp', methods=['GET', 'POST'])
def whatsapp_webhook():
    """WhatsApp webhook endpoint."""
    if request.method == 'GET':
        # Webhook verification
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        from app.integrations.whatsapp import WhatsAppIntegration
        integration = WhatsAppIntegration(studio_id='')  # Just for verification
        response = integration.get_webhook_verification_response(mode, token, challenge)
        
        if response:
            return response, 200
        return 'Verification failed', 403
    
    # POST - incoming message
    payload = request.get_json()
    signature = request.headers.get('X-Hub-Signature-256', '')
    
    # Route to appropriate studio based on phone number ID in payload
    # In production, you'd look up the studio from the payload
    try:
        entry = payload.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        phone_id = changes.get('value', {}).get('metadata', {}).get('phone_number_id')
        
        if phone_id:
            # Find studio with this phone ID
            integration = ChannelIntegration.query.filter(
                ChannelIntegration.channel == 'WHATSAPP',
                ChannelIntegration.external_account_id == phone_id
            ).first()
            
            if integration:
                manager = IntegrationManager(integration.studio_id)
                result = manager.handle_webhook('WHATSAPP', payload, signature)
                return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"WhatsApp webhook error: {e}")
    
    return jsonify({'status': 'received'})


@integrations_bp.route('/webhook/instagram', methods=['GET', 'POST'])
def instagram_webhook():
    """Instagram webhook endpoint."""
    if request.method == 'GET':
        # Webhook verification
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        import os
        verify_token = os.getenv('INSTAGRAM_VERIFY_TOKEN', 'studio_os_ig_verify')
        
        if mode == 'subscribe' and token == verify_token:
            return challenge, 200
        return 'Verification failed', 403
    
    # POST - incoming message
    payload = request.get_json()
    signature = request.headers.get('X-Hub-Signature-256', '')
    
    try:
        entry = payload.get('entry', [{}])[0]
        page_id = entry.get('id')
        
        if page_id:
            integration = ChannelIntegration.query.filter(
                ChannelIntegration.channel == 'INSTAGRAM',
                ChannelIntegration.external_account_id == page_id
            ).first()
            
            if integration:
                manager = IntegrationManager(integration.studio_id)
                result = manager.handle_webhook('INSTAGRAM', payload, signature)
                return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Instagram webhook error: {e}")
    
    return jsonify({'status': 'received'})


@integrations_bp.route('/webhook/gmail', methods=['POST'])
def gmail_webhook():
    """Gmail Pub/Sub push notification endpoint."""
    payload = request.get_json()
    
    # Gmail push notifications come via Pub/Sub
    # They indicate new mail but we need to fetch the actual messages
    try:
        import base64
        import json
        
        message = payload.get('message', {})
        data = message.get('data')
        
        if data:
            decoded = json.loads(base64.b64decode(data).decode('utf-8'))
            email = decoded.get('emailAddress')
            
            if email:
                # Find integration by email
                integration = ChannelIntegration.query.filter(
                    ChannelIntegration.channel == 'EMAIL'
                ).first()  # Would filter by email in production
                
                if integration:
                    manager = IntegrationManager(integration.studio_id)
                    # Trigger sync to fetch new messages
                    run_async(manager.sync_messages('EMAIL'))
    except Exception as e:
        current_app.logger.error(f"Gmail webhook error: {e}")
    
    return jsonify({'status': 'received'})

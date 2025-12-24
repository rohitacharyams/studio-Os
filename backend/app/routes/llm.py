# LLM Routes - AI provider management and agent invocation
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import asyncio

from app.models import User, StudioKnowledge, Conversation, Message
from app.llm import LLMRegistry, get_llm_provider, LLMConfig
from app.llm.registry import get_llm_registry, AgentConfig

llm_bp = Blueprint('llm', __name__)


def run_async(coro):
    """Run async function in sync context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@llm_bp.route('/providers', methods=['GET'])
@jwt_required()
def list_providers():
    """List available LLM providers and their configuration status."""
    registry = get_llm_registry()
    providers = registry.list_providers()
    
    return jsonify({
        'providers': providers,
        'default_provider': registry._default_provider
    })


@llm_bp.route('/agents', methods=['GET'])
@jwt_required()
def list_agents():
    """List configured AI agents."""
    registry = get_llm_registry()
    agents = registry.list_agents()
    
    return jsonify({'agents': agents})


@llm_bp.route('/agents/<agent_name>', methods=['GET'])
@jwt_required()
def get_agent(agent_name):
    """Get configuration for a specific agent."""
    registry = get_llm_registry()
    config = registry.get_agent_config(agent_name)
    
    if not config:
        return jsonify({'error': f'Agent {agent_name} not found'}), 404
    
    return jsonify({
        'name': config.name,
        'description': config.description,
        'provider': config.provider,
        'model': config.model,
        'temperature': config.temperature,
        'max_tokens': config.max_tokens
    })


@llm_bp.route('/agents/<agent_name>/configure', methods=['POST'])
@jwt_required()
def configure_agent(agent_name):
    """
    Configure an AI agent's LLM provider and model.
    
    Body:
    {
        "provider": "openai" | "anthropic" | "gemini" | "ollama",
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 1000
    }
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.role not in ['ADMIN', 'OWNER']:
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    registry = get_llm_registry()
    existing = registry.get_agent_config(agent_name)
    
    if not existing:
        return jsonify({'error': f'Agent {agent_name} not found'}), 404
    
    # Update configuration
    new_config = AgentConfig(
        name=existing.name,
        description=existing.description,
        provider=data.get('provider', existing.provider),
        model=data.get('model', existing.model),
        system_prompt=data.get('system_prompt', existing.system_prompt),
        temperature=data.get('temperature', existing.temperature),
        max_tokens=data.get('max_tokens', existing.max_tokens)
    )
    
    registry.configure_agent(agent_name, new_config)
    
    return jsonify({
        'success': True,
        'agent': agent_name,
        'config': {
            'provider': new_config.provider,
            'model': new_config.model,
            'temperature': new_config.temperature
        }
    })


@llm_bp.route('/invoke/<agent_name>', methods=['POST'])
@jwt_required()
def invoke_agent(agent_name):
    """
    Invoke an AI agent with a message.
    
    Body:
    {
        "message": "User message",
        "context": {
            "conversation_id": "optional",
            "contact_id": "optional"
        }
    }
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'message is required'}), 400
    
    message = data['message']
    context_data = data.get('context', {})
    
    # Build context from database if IDs provided
    context = {}
    
    if context_data.get('conversation_id'):
        conversation = Conversation.query.get(context_data['conversation_id'])
        if conversation:
            messages = Message.query.filter_by(
                conversation_id=conversation.id
            ).order_by(Message.created_at.desc()).limit(10).all()
            
            context['conversation_history'] = "\n".join([
                f"{'Customer' if m.direction == 'INBOUND' else 'Studio'}: {m.content}"
                for m in reversed(messages)
            ])
    
    # Get knowledge base
    kb_entries = StudioKnowledge.query.filter_by(studio_id=user.studio_id).all()
    if kb_entries:
        context['knowledge_base'] = "\n\n".join([
            f"**{kb.title}**\n{kb.content}"
            for kb in kb_entries
        ])
    
    # Invoke agent
    registry = get_llm_registry()
    
    try:
        response = run_async(registry.invoke_agent(agent_name, message, context))
        
        return jsonify({
            'success': True,
            'agent': agent_name,
            'response': response.content,
            'model': response.model,
            'provider': response.provider,
            'usage': response.usage
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Agent invocation failed: {str(e)}'}), 500


@llm_bp.route('/smart-reply', methods=['POST'])
@jwt_required()
def smart_reply():
    """
    Generate a smart reply for a conversation.
    Uses the configured smart_reply agent.
    
    Body:
    {
        "conversation_id": "uuid",
        "additional_context": "optional"
    }
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    if not data or 'conversation_id' not in data:
        return jsonify({'error': 'conversation_id is required'}), 400
    
    conversation = Conversation.query.get(data['conversation_id'])
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    
    # Get conversation messages
    messages = Message.query.filter_by(
        conversation_id=conversation.id
    ).order_by(Message.created_at.desc()).limit(10).all()
    
    if not messages:
        return jsonify({'error': 'No messages in conversation'}), 400
    
    # Build context
    context = {
        'conversation_history': "\n".join([
            f"{'Customer' if m.direction == 'INBOUND' else 'Studio'}: {m.content}"
            for m in reversed(messages)
        ])
    }
    
    # Get knowledge base
    kb_entries = StudioKnowledge.query.filter_by(studio_id=user.studio_id).all()
    if kb_entries:
        context['knowledge_base'] = "\n\n".join([
            f"**{kb.title}**\n{kb.content}"
            for kb in kb_entries
        ])
    
    # Add contact info if available
    if conversation.contact:
        context['contact_info'] = f"Name: {conversation.contact.name}, Status: {conversation.contact.lead_status}"
    
    # Additional context from request
    if data.get('additional_context'):
        context['additional'] = data['additional_context']
    
    # Get last customer message as the prompt
    last_inbound = next((m for m in messages if m.direction == 'INBOUND'), None)
    prompt = last_inbound.content if last_inbound else "Generate a follow-up message"
    
    registry = get_llm_registry()
    
    try:
        response = run_async(registry.invoke_agent('smart_reply', prompt, context))
        
        return jsonify({
            'success': True,
            'reply': response.content,
            'conversation_id': conversation.id,
            'model': response.model,
            'usage': response.usage
        })
        
    except Exception as e:
        return jsonify({'error': f'Smart reply failed: {str(e)}'}), 500


@llm_bp.route('/lead-score', methods=['POST'])
@jwt_required()
def lead_score():
    """
    Score a lead based on conversation analysis.
    
    Body:
    {
        "contact_id": "uuid" OR "conversation_id": "uuid"
    }
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'contact_id or conversation_id required'}), 400
    
    # Get conversation(s)
    if data.get('conversation_id'):
        conversations = [Conversation.query.get(data['conversation_id'])]
    elif data.get('contact_id'):
        conversations = Conversation.query.filter_by(contact_id=data['contact_id']).all()
    else:
        return jsonify({'error': 'contact_id or conversation_id required'}), 400
    
    if not conversations or not conversations[0]:
        return jsonify({'error': 'No conversations found'}), 404
    
    # Gather all messages
    all_messages = []
    for conv in conversations:
        messages = Message.query.filter_by(conversation_id=conv.id).order_by(Message.created_at).all()
        all_messages.extend(messages)
    
    if not all_messages:
        return jsonify({'error': 'No messages found'}), 404
    
    # Build analysis prompt
    conversation_text = "\n".join([
        f"{'Customer' if m.direction == 'INBOUND' else 'Studio'}: {m.content}"
        for m in all_messages
    ])
    
    prompt = f"""Analyze this conversation and score the lead:

{conversation_text}

Provide a JSON response with:
- score (0-100)
- confidence (0-1)
- factors (list of scoring factors)
- next_action (recommended next step)
"""
    
    registry = get_llm_registry()
    
    try:
        response = run_async(registry.invoke_agent('lead_scoring', prompt, {}))
        
        # Try to parse JSON from response
        import json
        try:
            result = json.loads(response.content)
        except:
            result = {'raw_response': response.content}
        
        return jsonify({
            'success': True,
            'lead_score': result,
            'model': response.model
        })
        
    except Exception as e:
        return jsonify({'error': f'Lead scoring failed: {str(e)}'}), 500


@llm_bp.route('/analyze', methods=['POST'])
@jwt_required()
def analyze_conversation():
    """
    Analyze a conversation for insights.
    
    Body:
    {
        "conversation_id": "uuid"
    }
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    if not data or 'conversation_id' not in data:
        return jsonify({'error': 'conversation_id is required'}), 400
    
    conversation = Conversation.query.get(data['conversation_id'])
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    
    messages = Message.query.filter_by(
        conversation_id=conversation.id
    ).order_by(Message.created_at).all()
    
    if not messages:
        return jsonify({'error': 'No messages found'}), 404
    
    conversation_text = "\n".join([
        f"{'Customer' if m.direction == 'INBOUND' else 'Studio'}: {m.content}"
        for m in messages
    ])
    
    prompt = f"""Analyze this dance studio conversation:

{conversation_text}

Extract:
1. Customer intent and needs
2. Dance styles of interest
3. Schedule preferences
4. Budget indicators
5. Objections or concerns
6. Suggested follow-up actions

Return as structured JSON.
"""
    
    registry = get_llm_registry()
    
    try:
        response = run_async(registry.invoke_agent('conversation_analysis', prompt, {}))
        
        import json
        try:
            result = json.loads(response.content)
        except:
            result = {'raw_response': response.content}
        
        return jsonify({
            'success': True,
            'analysis': result,
            'conversation_id': conversation.id,
            'model': response.model
        })
        
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@llm_bp.route('/test', methods=['POST'])
@jwt_required()
def test_provider():
    """
    Test an LLM provider with a simple prompt.
    
    Body:
    {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "prompt": "Hello, how are you?"
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    provider_name = data.get('provider', 'openai')
    model = data.get('model')
    prompt = data.get('prompt', 'Say hello in a friendly way.')
    
    try:
        provider = get_llm_provider(provider_name, model)
        
        if not provider.validate_config():
            return jsonify({
                'success': False,
                'error': f'{provider_name} is not configured. Check API key.'
            }), 400
        
        response = run_async(provider.complete(prompt))
        
        return jsonify({
            'success': True,
            'provider': provider_name,
            'model': response.model,
            'response': response.content,
            'usage': response.usage
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

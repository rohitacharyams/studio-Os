from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import func

from app.models import User, Conversation, Message, StudioKnowledge, Contact, Studio, DanceClass, Booking, ClassSession
from app.services.ai_service import AIService
from app.services.ai_agents import ConversationAgent, LeadScoringAgent, FollowUpAgent, ResponseAgent
from app.llm import get_llm_provider
from app.llm.base import LLMMessage

ai_bp = Blueprint('ai', __name__)


def run_async(coro):
    """Run async function in sync context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@ai_bp.route('/chat', methods=['POST'])
@jwt_required()
def chatbot():
    """
    General chatbot endpoint for logged-in users.
    Can answer questions about studio info, classes, bookings, and general dance topics.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    user_message = data.get('message', '').strip()
    conversation_history = data.get('conversation_history', [])
    
    if not user_message:
        return jsonify({'error': 'Message is required'}), 400
    
    # Gather studio context
    studio = user.studio
    studio_context = ""
    
    if studio:
        # Get studio knowledge
        knowledge_items = StudioKnowledge.query.filter_by(
            studio_id=studio.id,
            is_active=True
        ).all()
        
        knowledge_text = ""
        if knowledge_items:
            knowledge_text = "\n".join([
                f"- {item.title}: {item.content}" for item in knowledge_items
            ])
        
        # Get studio classes
        classes = DanceClass.query.filter_by(studio_id=studio.id, is_active=True).all()
        classes_text = ""
        if classes:
            classes_text = "\n".join([
                f"- {c.name}: {c.dance_style or 'General'}, ₹{c.price or 0}, {c.duration_minutes or 60} mins, Level: {c.level or 'All'}"
                for c in classes[:10]  # Limit to 10 classes
            ])
        
        studio_context = f"""
STUDIO INFORMATION:
- Name: {studio.name}
- Email: {studio.email}
- Phone: {studio.phone or 'Not provided'}
- Address: {studio.address or 'Not provided'}
- City: {studio.city or 'Not provided'}
- Website: {studio.website or 'Not provided'}

CLASSES OFFERED:
{classes_text if classes_text else 'No classes configured yet'}

KNOWLEDGE BASE:
{knowledge_text if knowledge_text else 'No knowledge articles yet'}
"""
    
    # Build system prompt
    system_prompt = f"""You are a helpful AI assistant for Studio OS, a dance studio management platform.
You help studio owners and staff with questions about their studio, classes, bookings, and general dance-related topics.

{studio_context}

GUIDELINES:
- Be friendly, helpful, and concise
- Answer questions about the studio based on the information provided
- For general dance/business questions, provide helpful advice
- If you don't have specific information, say so honestly
- Don't make up information that isn't provided
- Keep responses conversational but professional
- Use emojis sparingly for a friendly tone 😊
"""

    # Build messages for LLM
    messages = [LLMMessage(role='system', content=system_prompt)]
    
    # Add conversation history (last 10 messages)
    for msg in conversation_history[-10:]:
        role = 'assistant' if msg.get('role') == 'assistant' else 'user'
        messages.append(LLMMessage(role=role, content=msg.get('content', '')))
    
    # Add current user message
    messages.append(LLMMessage(role='user', content=user_message))
    
    try:
        # Get LLM provider (uses Groq by default)
        provider = get_llm_provider(
            provider='groq',
            model='llama-3.3-70b-versatile',
            temperature=0.7,
            max_tokens=500
        )
        
        # Get response
        response = run_async(provider.chat(messages))
        
        return jsonify({
            'reply': response.content,
            'model': response.model,
            'usage': response.usage
        })
        
    except Exception as e:
        return jsonify({'error': f'AI error: {str(e)}'}), 500


@ai_bp.route('/draft-reply', methods=['POST'])
@jwt_required()
def draft_reply():
    """Generate an AI draft reply for a conversation."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    
    if not conversation_id:
        return jsonify({'error': 'conversation_id is required'}), 400
    
    conversation = Conversation.query.filter_by(
        id=conversation_id,
        studio_id=user.studio_id
    ).first()
    
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    
    # Get recent messages for context
    messages = Message.query.filter_by(conversation_id=conversation_id)\
        .order_by(Message.created_at.desc())\
        .limit(10).all()
    messages = list(reversed(messages))
    
    # Get studio knowledge for RAG
    knowledge = StudioKnowledge.query.filter_by(
        studio_id=user.studio_id,
        is_active=True
    ).all()
    
    # Get contact info
    contact = conversation.contact
    
    try:
        ai_service = AIService()
        
        # Additional context/instructions from request
        tone = data.get('tone', 'friendly')  # friendly, professional, casual
        instructions = data.get('instructions', '')
        
        draft = ai_service.generate_reply(
            messages=messages,
            contact=contact,
            studio=user.studio,
            knowledge=knowledge,
            tone=tone,
            additional_instructions=instructions
        )
        
        return jsonify({
            'draft': draft,
            'conversation_id': conversation_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/improve', methods=['POST'])
@jwt_required()
def improve_message():
    """Improve an existing message draft."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    if not data.get('content'):
        return jsonify({'error': 'content is required'}), 400
    
    improvement_type = data.get('type', 'improve')  # improve, shorten, expand, professional, casual
    
    try:
        ai_service = AIService()
        
        improved = ai_service.improve_message(
            content=data['content'],
            improvement_type=improvement_type,
            studio=user.studio
        )
        
        return jsonify({
            'improved': improved,
            'original': data['content']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/summarize', methods=['POST'])
@jwt_required()
def summarize_conversation():
    """Summarize a conversation."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    
    if not conversation_id:
        return jsonify({'error': 'conversation_id is required'}), 400
    
    conversation = Conversation.query.filter_by(
        id=conversation_id,
        studio_id=user.studio_id
    ).first()
    
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    
    messages = Message.query.filter_by(conversation_id=conversation_id)\
        .order_by(Message.created_at).all()
    
    try:
        ai_service = AIService()
        
        summary = ai_service.summarize_conversation(
            messages=messages,
            contact=conversation.contact
        )
        
        return jsonify({
            'summary': summary,
            'conversation_id': conversation_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/analyze/<conversation_id>', methods=['GET'])
@jwt_required()
def analyze_conversation(conversation_id):
    """Analyze a conversation using AI agent."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    conversation = Conversation.query.filter_by(
        id=conversation_id,
        studio_id=user.studio_id
    ).first()
    
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    
    messages = Message.query.filter_by(conversation_id=conversation_id)\
        .order_by(Message.created_at).all()
    
    knowledge = StudioKnowledge.query.filter_by(
        studio_id=user.studio_id,
        is_active=True
    ).all()
    
    try:
        agent = ConversationAgent()
        analysis = agent.analyze_conversation(
            messages=messages,
            contact=conversation.contact,
            studio_knowledge=knowledge
        )
        
        return jsonify({
            'analysis': analysis,
            'conversation_id': conversation_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/lead-score/<contact_id>', methods=['GET'])
@jwt_required()
def score_lead(contact_id):
    """Score a lead using AI agent."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    contact = Contact.query.filter_by(
        id=contact_id,
        studio_id=user.studio_id
    ).first()
    
    if not contact:
        return jsonify({'error': 'Contact not found'}), 404
    
    conversations = Conversation.query.filter_by(contact_id=contact_id).all()
    
    all_messages = []
    for conv in conversations:
        messages = Message.query.filter_by(conversation_id=conv.id).all()
        all_messages.extend(messages)
    
    try:
        agent = LeadScoringAgent()
        score = agent.score_lead(
            contact=contact,
            conversations=conversations,
            all_messages=all_messages
        )
        
        return jsonify({
            'score': score,
            'contact_id': contact_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/follow-ups', methods=['GET'])
@jwt_required()
def get_follow_ups():
    """Get follow-up suggestions for all conversations."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    conversations = Conversation.query.filter_by(
        studio_id=user.studio_id,
        is_archived=False
    ).all()
    
    try:
        agent = FollowUpAgent()
        suggestions = agent.get_follow_up_suggestions(
            conversations=conversations,
            studio_id=user.studio_id
        )
        
        return jsonify({
            'follow_ups': suggestions,
            'total': len(suggestions)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/smart-reply', methods=['POST'])
@jwt_required()
def smart_reply():
    """Generate smart reply with multiple options."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    
    if not conversation_id:
        return jsonify({'error': 'conversation_id is required'}), 400
    
    conversation = Conversation.query.filter_by(
        id=conversation_id,
        studio_id=user.studio_id
    ).first()
    
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    
    messages = Message.query.filter_by(conversation_id=conversation_id)\
        .order_by(Message.created_at).all()
    
    knowledge = StudioKnowledge.query.filter_by(
        studio_id=user.studio_id,
        is_active=True
    ).all()
    
    try:
        agent = ResponseAgent()
        response = agent.generate_response(
            messages=messages,
            contact=conversation.contact,
            studio=user.studio,
            knowledge=knowledge,
            style=data.get('style', 'friendly')
        )
        
        return jsonify({
            'response': response,
            'conversation_id': conversation_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

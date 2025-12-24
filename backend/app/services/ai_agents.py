"""
AI Agent module for Studio OS.

This module provides intelligent agents that can:
1. Analyze conversations and suggest next actions
2. Score lead quality
3. Detect urgency and sentiment
4. Recommend follow-up timing
5. Generate personalized responses
"""

from openai import OpenAI
from flask import current_app
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json


class ConversationAgent:
    """Agent for analyzing conversations and providing insights."""
    
    def __init__(self):
        api_key = current_app.config.get('OPENAI_API_KEY')
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.model = "gpt-4-turbo-preview"
    
    def analyze_conversation(
        self,
        messages: List,
        contact,
        studio_knowledge: List = None
    ) -> Dict:
        """
        Analyze a conversation and return insights.
        
        Returns:
            {
                "summary": str,
                "sentiment": "positive" | "neutral" | "negative",
                "urgency": "high" | "medium" | "low",
                "intent": str,
                "questions_asked": List[str],
                "questions_answered": List[str],
                "questions_pending": List[str],
                "lead_quality_score": int (1-10),
                "recommended_action": str,
                "suggested_response": str,
                "follow_up_timing": str
            }
        """
        if not self.client:
            # Return mock analysis for demo without API key
            return self._mock_analysis(messages, contact)
        
        conversation_text = self._format_conversation(messages)
        knowledge_text = self._format_knowledge(studio_knowledge) if studio_knowledge else ""
        
        system_prompt = """You are an AI assistant analyzing customer conversations for a dance studio.
Analyze the conversation and return a JSON object with the following structure:
{
    "summary": "Brief 1-2 sentence summary of the conversation",
    "sentiment": "positive" | "neutral" | "negative",
    "urgency": "high" | "medium" | "low",
    "intent": "What the customer is looking for (e.g., 'enrolling child in ballet', 'adult dance classes')",
    "questions_asked": ["List of questions the customer asked"],
    "questions_answered": ["Questions that have been answered"],
    "questions_pending": ["Questions still needing answers"],
    "lead_quality_score": 1-10 (10 = highly likely to convert),
    "recommended_action": "What the studio should do next",
    "suggested_response": "A draft response if one is needed",
    "follow_up_timing": "When to follow up (e.g., 'within 24 hours', 'in 3 days')"
}

Consider factors like:
- How engaged is the customer?
- Are they asking specific questions (shows higher intent)?
- Is there urgency (wedding, starting soon, etc.)?
- Have they mentioned budget concerns?
- Is this a referral or repeat inquiry?"""

        user_prompt = f"""Analyze this conversation:

Customer: {contact.name or 'Unknown'}
Lead Source: {getattr(contact, 'lead_source', 'Unknown')}
Tags: {getattr(contact, 'tags', [])}

CONVERSATION:
{conversation_text}

STUDIO KNOWLEDGE (for context):
{knowledge_text if knowledge_text else 'Not provided'}

Return ONLY valid JSON, no other text."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"AI analysis failed: {str(e)}")
            return self._mock_analysis(messages, contact)
    
    def _format_conversation(self, messages: List) -> str:
        """Format messages into readable text."""
        lines = []
        for msg in messages:
            role = "Customer" if msg.direction == "INBOUND" else "Studio"
            timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M") if msg.created_at else ""
            lines.append(f"[{timestamp}] {role}: {msg.content}")
        return "\n".join(lines)
    
    def _format_knowledge(self, knowledge: List) -> str:
        """Format knowledge base into text."""
        items = []
        for item in knowledge[:5]:  # Limit to prevent token overflow
            items.append(f"- {item.title}: {item.content[:200]}...")
        return "\n".join(items)
    
    def _mock_analysis(self, messages: List, contact) -> Dict:
        """Return mock analysis when API is not available."""
        last_message = messages[-1] if messages else None
        inbound_count = sum(1 for m in messages if m.direction == "INBOUND")
        
        return {
            "summary": f"Conversation with {contact.name or 'customer'} about dance classes.",
            "sentiment": "positive",
            "urgency": "medium",
            "intent": "Exploring dance class options",
            "questions_asked": ["What classes are available?", "What are the prices?"],
            "questions_answered": [],
            "questions_pending": ["What classes are available?", "What are the prices?"],
            "lead_quality_score": 7,
            "recommended_action": "Respond with class options and schedule a trial",
            "suggested_response": f"Hi {contact.name or 'there'}! Thanks for reaching out. We'd love to help you find the perfect dance class. Would you like to schedule a free trial?",
            "follow_up_timing": "within 24 hours"
        }


class LeadScoringAgent:
    """Agent for scoring and prioritizing leads."""
    
    def __init__(self):
        api_key = current_app.config.get('OPENAI_API_KEY')
        self.client = OpenAI(api_key=api_key) if api_key else None
    
    def score_lead(
        self,
        contact,
        conversations: List,
        all_messages: List
    ) -> Dict:
        """
        Score a lead based on their engagement and likelihood to convert.
        
        Returns:
            {
                "score": int (1-100),
                "grade": "A" | "B" | "C" | "D",
                "factors": {
                    "engagement": int,
                    "intent": int,
                    "timing": int,
                    "fit": int
                },
                "recommendation": str,
                "priority": "hot" | "warm" | "cold"
            }
        """
        # Calculate base metrics
        message_count = len(all_messages)
        inbound_messages = sum(1 for m in all_messages if m.direction == "INBOUND")
        response_count = sum(1 for m in all_messages if m.direction == "OUTBOUND")
        
        # Calculate engagement score (0-25)
        engagement = min(25, message_count * 3 + (5 if inbound_messages > 1 else 0))
        
        # Calculate intent score based on lead status (0-25)
        status_scores = {
            "NEW": 10,
            "CONTACTED": 15,
            "ENGAGED": 20,
            "QUALIFIED": 25,
            "CONVERTED": 25,
            "LOST": 5
        }
        intent = status_scores.get(contact.lead_status, 10)
        
        # Calculate timing score (0-25) - newer leads score higher
        days_since_contact = 0
        if all_messages:
            last_msg = max(all_messages, key=lambda m: m.created_at or datetime.min)
            if last_msg.created_at:
                days_since_contact = (datetime.utcnow() - last_msg.created_at).days
        
        timing = max(0, 25 - (days_since_contact * 2))
        
        # Calculate fit score (0-25) - based on tags and source
        fit = 15  # Base score
        if contact.tags:
            if "wedding" in contact.tags or "competition" in contact.tags:
                fit += 5
            if "parent" in contact.tags:
                fit += 5
        
        total_score = engagement + intent + timing + fit
        
        # Determine grade and priority
        if total_score >= 80:
            grade, priority = "A", "hot"
        elif total_score >= 60:
            grade, priority = "B", "warm"
        elif total_score >= 40:
            grade, priority = "C", "warm"
        else:
            grade, priority = "D", "cold"
        
        # Generate recommendation
        recommendations = {
            "hot": "High priority! Reach out immediately with a personal call or message.",
            "warm": "Good potential. Send a follow-up within 24 hours with specific class recommendations.",
            "cold": "Lower priority. Add to nurture sequence with periodic check-ins."
        }
        
        return {
            "score": total_score,
            "grade": grade,
            "factors": {
                "engagement": engagement,
                "intent": intent,
                "timing": timing,
                "fit": fit
            },
            "recommendation": recommendations[priority],
            "priority": priority
        }


class FollowUpAgent:
    """Agent for managing follow-ups and reminders."""
    
    def get_follow_up_suggestions(
        self,
        conversations: List,
        studio_id: str
    ) -> List[Dict]:
        """
        Analyze conversations and suggest follow-ups needed.
        
        Returns list of:
            {
                "conversation_id": str,
                "contact_name": str,
                "reason": str,
                "urgency": "high" | "medium" | "low",
                "suggested_action": str,
                "days_since_last_message": int
            }
        """
        suggestions = []
        now = datetime.utcnow()
        
        for conv in conversations:
            if conv.is_archived:
                continue
            
            # Check last message time
            days_since = 0
            if conv.last_message_at:
                days_since = (now - conv.last_message_at).days
            
            # Get last message direction
            last_inbound = False
            if hasattr(conv, 'messages') and conv.messages:
                messages = list(conv.messages)
                if messages:
                    last_msg = max(messages, key=lambda m: m.created_at or datetime.min)
                    last_inbound = last_msg.direction == "INBOUND"
            
            # Determine if follow-up needed
            suggestion = None
            
            if last_inbound and days_since >= 1:
                # Customer waiting for response
                urgency = "high" if days_since >= 2 else "medium"
                suggestion = {
                    "conversation_id": conv.id,
                    "contact_name": conv.contact.name if conv.contact else "Unknown",
                    "reason": f"Customer message unanswered for {days_since} day(s)",
                    "urgency": urgency,
                    "suggested_action": "Respond to customer inquiry",
                    "days_since_last_message": days_since
                }
            elif not last_inbound and days_since >= 3:
                # No response from customer after our reply
                suggestion = {
                    "conversation_id": conv.id,
                    "contact_name": conv.contact.name if conv.contact else "Unknown",
                    "reason": f"No customer response in {days_since} days",
                    "urgency": "low",
                    "suggested_action": "Send a gentle follow-up",
                    "days_since_last_message": days_since
                }
            elif conv.is_unread:
                suggestion = {
                    "conversation_id": conv.id,
                    "contact_name": conv.contact.name if conv.contact else "Unknown",
                    "reason": "Unread message",
                    "urgency": "high",
                    "suggested_action": "Review and respond",
                    "days_since_last_message": days_since
                }
            
            if suggestion:
                suggestions.append(suggestion)
        
        # Sort by urgency
        urgency_order = {"high": 0, "medium": 1, "low": 2}
        suggestions.sort(key=lambda x: (urgency_order[x["urgency"]], -x["days_since_last_message"]))
        
        return suggestions


class ResponseAgent:
    """Agent for generating context-aware responses."""
    
    def __init__(self):
        api_key = current_app.config.get('OPENAI_API_KEY')
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.model = "gpt-4-turbo-preview"
    
    def generate_response(
        self,
        messages: List,
        contact,
        studio,
        knowledge: List = None,
        template: str = None,
        style: str = "friendly"
    ) -> Dict:
        """
        Generate a contextual response with multiple options.
        
        Returns:
            {
                "primary_response": str,
                "alternatives": [str, str],
                "key_points_addressed": [str],
                "suggested_next_steps": [str]
            }
        """
        if not self.client:
            return self._mock_response(contact, messages)
        
        conversation_text = "\n".join([
            f"{'Customer' if m.direction == 'INBOUND' else 'Studio'}: {m.content}"
            for m in messages
        ])
        
        knowledge_text = ""
        if knowledge:
            knowledge_text = "\n".join([
                f"- {k.title}: {k.content[:300]}" for k in knowledge[:5]
            ])
        
        system_prompt = f"""You are a helpful assistant for {studio.name}, a dance studio.
Generate a {style} response to the customer's inquiry.

Studio Knowledge:
{knowledge_text if knowledge_text else 'Use general dance studio knowledge.'}

Return a JSON object with:
{{
    "primary_response": "The main recommended response",
    "alternatives": ["A shorter version", "A more detailed version"],
    "key_points_addressed": ["List of customer questions/concerns addressed"],
    "suggested_next_steps": ["What to do after sending this response"]
}}"""

        user_prompt = f"""Customer: {contact.name or 'Unknown'}
Lead Status: {contact.lead_status}

Conversation:
{conversation_text}

Generate a helpful response."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Response generation failed: {str(e)}")
            return self._mock_response(contact, messages)
    
    def _mock_response(self, contact, messages) -> Dict:
        """Return mock response when API is not available."""
        name = contact.name or "there"
        return {
            "primary_response": f"Hi {name}! Thank you for reaching out to Dream Dance Studio. We'd love to help you find the perfect class. Would you like to schedule a free trial session?",
            "alternatives": [
                f"Thanks for your interest, {name}! Let's find the right class for you. When would you like to come in for a trial?",
                f"Hi {name}! We're excited you're interested in dancing with us. We offer a variety of classes for all ages and skill levels. I'd be happy to tell you more about our schedule and help you pick the perfect fit. Would you like to come see our studio and try a free class?"
            ],
            "key_points_addressed": ["General inquiry response"],
            "suggested_next_steps": ["Schedule trial class", "Send class schedule", "Follow up in 2 days if no response"]
        }


# Convenience function to get all agents
def get_agents():
    """Get instances of all AI agents."""
    return {
        "conversation": ConversationAgent(),
        "lead_scoring": LeadScoringAgent(),
        "follow_up": FollowUpAgent(),
        "response": ResponseAgent()
    }

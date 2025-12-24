from openai import OpenAI
from flask import current_app
from typing import List, Optional


class AIService:
    """Service for AI-powered features using OpenAI."""
    
    def __init__(self):
        api_key = current_app.config.get('OPENAI_API_KEY')
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.model = "gpt-4-turbo-preview"
    
    def generate_reply(
        self,
        messages: List,
        contact,
        studio,
        knowledge: List = None,
        tone: str = 'friendly',
        additional_instructions: str = ''
    ) -> str:
        """Generate an AI draft reply for a conversation."""
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        # Build context from studio knowledge
        knowledge_context = ""
        if knowledge:
            knowledge_items = [
                f"**{item.category} - {item.title}**:\n{item.content}"
                for item in knowledge
            ]
            knowledge_context = "\n\n".join(knowledge_items)
        
        # Build conversation history
        conversation_history = []
        for msg in messages:
            role = "customer" if msg.direction == "INBOUND" else "studio"
            conversation_history.append(f"{role}: {msg.content}")
        
        conversation_text = "\n".join(conversation_history)
        
        # Build system prompt
        system_prompt = f"""You are a helpful assistant for {studio.name}, a dance studio. 
Your job is to help draft professional and {tone} responses to customer inquiries.

STUDIO INFORMATION:
Studio Name: {studio.name}
Email: {studio.email}
Phone: {studio.phone or 'Not provided'}
Address: {studio.address or 'Not provided'}

STUDIO KNOWLEDGE BASE:
{knowledge_context if knowledge_context else 'No specific knowledge provided.'}

GUIDELINES:
- Be {tone} and professional
- Answer questions based on the studio knowledge provided
- If you don't have specific information, suggest the customer contact the studio directly
- Keep responses concise but helpful
- Don't make up information that isn't in the knowledge base
- Use the customer's name if known
{additional_instructions}
"""
        
        # Build user prompt
        user_prompt = f"""Here is the conversation with a customer:

Customer Name: {contact.name or 'Unknown'}
Customer Email: {contact.email or 'Not provided'}
Customer Phone: {contact.phone or 'Not provided'}

CONVERSATION:
{conversation_text}

Please draft a helpful reply to the customer's most recent message."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"AI generation failed: {str(e)}")
    
    def improve_message(
        self,
        content: str,
        improvement_type: str = 'improve',
        studio = None
    ) -> str:
        """Improve an existing message draft."""
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        type_prompts = {
            'improve': "Improve this message to be clearer and more professional while keeping the same meaning.",
            'shorten': "Make this message shorter and more concise while keeping the key points.",
            'expand': "Expand this message with more detail while keeping it professional.",
            'professional': "Rewrite this message to be more formal and professional.",
            'casual': "Rewrite this message to be more casual and friendly."
        }
        
        prompt = type_prompts.get(improvement_type, type_prompts['improve'])
        
        studio_context = ""
        if studio:
            studio_context = f"\nContext: This is for {studio.name}, a dance studio."
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a helpful writing assistant.{studio_context}"
                    },
                    {
                        "role": "user",
                        "content": f"{prompt}\n\nOriginal message:\n{content}"
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"AI improvement failed: {str(e)}")
    
    def summarize_conversation(self, messages: List, contact) -> str:
        """Summarize a conversation."""
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        conversation_history = []
        for msg in messages:
            role = "Customer" if msg.direction == "INBOUND" else "Studio"
            conversation_history.append(f"{role}: {msg.content}")
        
        conversation_text = "\n".join(conversation_history)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that summarizes customer conversations for studio staff. Provide a brief summary highlighting key points, questions asked, and any action items."
                    },
                    {
                        "role": "user",
                        "content": f"Please summarize this conversation with {contact.name or 'a customer'}:\n\n{conversation_text}"
                    }
                ],
                temperature=0.5,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"AI summarization failed: {str(e)}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate an embedding for semantic search."""
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise Exception(f"Embedding generation failed: {str(e)}")

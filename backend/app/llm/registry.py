# LLM Registry and Agent Management
import os
from typing import Dict, Optional, Type, Any, List
from dataclasses import dataclass

from .base import BaseLLMProvider, LLMConfig, LLMMessage, LLMResponse, LLMCapability
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .gemini_provider import GeminiProvider
from .ollama_provider import OllamaProvider


@dataclass
class AgentConfig:
    """Configuration for an AI agent."""
    name: str
    description: str
    provider: str
    model: str
    system_prompt: str
    temperature: float = 0.7
    max_tokens: int = 1000


class LLMRegistry:
    """
    Central registry for LLM providers and AI agents.
    
    Allows dynamic configuration of which LLM backs each agent function:
    - Smart Reply Agent
    - Lead Scoring Agent
    - Conversation Analysis Agent
    - Scheduling Optimization Agent
    """
    
    PROVIDERS: Dict[str, Type[BaseLLMProvider]] = {
        'openai': OpenAIProvider,
        'anthropic': AnthropicProvider,
        'gemini': GeminiProvider,
        'ollama': OllamaProvider,
    }
    
    # Default agent configurations
    DEFAULT_AGENTS: Dict[str, AgentConfig] = {
        'smart_reply': AgentConfig(
            name='Smart Reply Agent',
            description='Generates contextual reply suggestions for conversations',
            provider='openai',
            model='gpt-4o-mini',
            system_prompt="""You are a helpful assistant for a dance studio. 
Generate professional, friendly replies to inquiries about classes, pricing, and schedules.
Use the knowledge base provided to give accurate information.
Keep responses concise but warm and inviting.""",
            temperature=0.7,
            max_tokens=500
        ),
        'lead_scoring': AgentConfig(
            name='Lead Scoring Agent',
            description='Analyzes conversations to score lead quality',
            provider='openai',
            model='gpt-4o-mini',
            system_prompt="""You are a lead qualification expert for a dance studio.
Analyze conversation history and assign a lead score from 0-100 based on:
- Intent to purchase (40 points)
- Budget indicators (20 points)
- Timeline urgency (20 points)
- Engagement level (20 points)
Return JSON with: score, confidence, factors, next_action.""",
            temperature=0.3,
            max_tokens=300
        ),
        'conversation_analysis': AgentConfig(
            name='Conversation Analysis Agent',
            description='Extracts insights and action items from conversations',
            provider='openai',
            model='gpt-4o-mini',
            system_prompt="""Analyze dance studio conversations to extract:
- Customer intent and needs
- Mentioned dance styles of interest
- Schedule preferences
- Budget indicators
- Objections or concerns
- Suggested follow-up actions
Return structured JSON analysis.""",
            temperature=0.3,
            max_tokens=500
        ),
        'scheduling': AgentConfig(
            name='Scheduling Optimization Agent',
            description='Optimizes class schedules based on constraints',
            provider='openai',
            model='gpt-4o',
            system_prompt="""You are a scheduling optimization expert.
Given instructor availability, room capacity, and student demand,
suggest optimal class schedules that maximize utilization and minimize conflicts.
Consider peak hours, beginner vs advanced class timing, and instructor specialties.""",
            temperature=0.3,
            max_tokens=1000
        ),
    }
    
    def __init__(self):
        self._providers: Dict[str, BaseLLMProvider] = {}
        self._agents: Dict[str, AgentConfig] = dict(self.DEFAULT_AGENTS)
        self._load_from_env()
    
    def _load_from_env(self):
        """Load provider configurations from environment variables."""
        # Check which providers have API keys configured
        if os.getenv('OPENAI_API_KEY'):
            self._default_provider = 'openai'
        elif os.getenv('ANTHROPIC_API_KEY'):
            self._default_provider = 'anthropic'
        elif os.getenv('GOOGLE_API_KEY'):
            self._default_provider = 'gemini'
        else:
            # Default to Ollama for local deployment
            self._default_provider = 'ollama'
    
    def register_provider(self, name: str, provider_class: Type[BaseLLMProvider]):
        """Register a custom LLM provider."""
        self.PROVIDERS[name] = provider_class
    
    def get_provider(self, provider_name: str, model: str = None, **kwargs) -> BaseLLMProvider:
        """Get an LLM provider instance."""
        if provider_name not in self.PROVIDERS:
            raise ValueError(f"Unknown provider: {provider_name}. Available: {list(self.PROVIDERS.keys())}")
        
        # Create cache key
        cache_key = f"{provider_name}:{model or 'default'}"
        
        if cache_key not in self._providers:
            provider_class = self.PROVIDERS[provider_name]
            config = LLMConfig(
                provider=provider_name,
                model=model or self._get_default_model(provider_name),
                **kwargs
            )
            self._providers[cache_key] = provider_class(config)
        
        return self._providers[cache_key]
    
    def _get_default_model(self, provider: str) -> str:
        """Get default model for a provider."""
        defaults = {
            'openai': 'gpt-4o-mini',
            'anthropic': 'claude-3-5-sonnet-20241022',
            'gemini': 'gemini-1.5-flash',
            'ollama': 'llama3',
        }
        return defaults.get(provider, 'default')
    
    def configure_agent(self, agent_name: str, config: AgentConfig):
        """Configure or update an agent."""
        self._agents[agent_name] = config
    
    def get_agent_config(self, agent_name: str) -> Optional[AgentConfig]:
        """Get agent configuration."""
        return self._agents.get(agent_name)
    
    def get_agent_provider(self, agent_name: str) -> BaseLLMProvider:
        """Get the LLM provider configured for an agent."""
        config = self._agents.get(agent_name)
        if not config:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        return self.get_provider(config.provider, config.model)
    
    async def invoke_agent(self, agent_name: str, user_message: str, 
                          context: Dict[str, Any] = None) -> LLMResponse:
        """
        Invoke an agent with a user message.
        
        Args:
            agent_name: Name of the agent to invoke
            user_message: User's input message
            context: Additional context (knowledge base, conversation history, etc.)
        """
        config = self._agents.get(agent_name)
        if not config:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        provider = self.get_agent_provider(agent_name)
        
        # Build messages with system prompt
        messages = [LLMMessage(role='system', content=config.system_prompt)]
        
        # Add context if provided
        if context:
            context_str = self._format_context(context)
            messages.append(LLMMessage(
                role='system',
                content=f"Context:\n{context_str}"
            ))
        
        # Add user message
        messages.append(LLMMessage(role='user', content=user_message))
        
        return await provider.chat(
            messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary as string for prompt."""
        parts = []
        
        if 'knowledge_base' in context:
            kb = context['knowledge_base']
            parts.append(f"Knowledge Base:\n{kb}")
        
        if 'conversation_history' in context:
            history = context['conversation_history']
            parts.append(f"Conversation History:\n{history}")
        
        if 'contact_info' in context:
            info = context['contact_info']
            parts.append(f"Contact Info:\n{info}")
        
        if 'studio_info' in context:
            info = context['studio_info']
            parts.append(f"Studio Info:\n{info}")
        
        return "\n\n".join(parts)
    
    def list_providers(self) -> List[Dict[str, Any]]:
        """List available providers and their status."""
        result = []
        for name, provider_class in self.PROVIDERS.items():
            # Check if configured
            config = LLMConfig(provider=name, model=self._get_default_model(name))
            instance = provider_class(config)
            
            result.append({
                'name': name,
                'configured': instance.validate_config(),
                'default_model': self._get_default_model(name),
                'capabilities': [c.value for c in instance.capabilities]
            })
        
        return result
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List configured agents."""
        return [
            {
                'name': name,
                'description': config.description,
                'provider': config.provider,
                'model': config.model
            }
            for name, config in self._agents.items()
        ]


# Global registry instance
_registry: Optional[LLMRegistry] = None


def get_llm_registry() -> LLMRegistry:
    """Get the global LLM registry."""
    global _registry
    if _registry is None:
        _registry = LLMRegistry()
    return _registry


def get_llm_provider(provider: str = None, model: str = None, **kwargs) -> BaseLLMProvider:
    """Convenience function to get an LLM provider."""
    registry = get_llm_registry()
    provider = provider or registry._default_provider
    return registry.get_provider(provider, model, **kwargs)

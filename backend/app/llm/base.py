# Base LLM Provider Interface
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum


class LLMCapability(str, Enum):
    """Capabilities that an LLM provider can support."""
    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDINGS = "embeddings"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    STREAMING = "streaming"


@dataclass
class LLMConfig:
    """Configuration for an LLM provider."""
    provider: str  # openai, anthropic, gemini, ollama
    model: str  # gpt-4, claude-3-opus, gemini-pro, llama2
    api_key: Optional[str] = None
    api_base: Optional[str] = None  # For custom endpoints or Ollama
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout: int = 30
    extra_params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'provider': self.provider,
            'model': self.model,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
        }


@dataclass
class LLMMessage:
    """A message in a conversation."""
    role: str  # system, user, assistant
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""
    content: str
    model: str
    provider: str
    usage: Dict[str, int] = field(default_factory=dict)  # prompt_tokens, completion_tokens, total_tokens
    finish_reason: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'content': self.content,
            'model': self.model,
            'provider': self.provider,
            'usage': self.usage,
            'finish_reason': self.finish_reason,
        }


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    All LLM integrations must implement this interface to work with
    the Studio OS agent system.
    """
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None
        
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (openai, anthropic, etc.)."""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> List[LLMCapability]:
        """List of capabilities this provider supports."""
        pass
    
    @abstractmethod
    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """
        Send a chat completion request.
        
        Args:
            messages: List of conversation messages
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Standardized LLMResponse
        """
        pass
    
    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Send a completion request (non-chat).
        
        Args:
            prompt: Text prompt to complete
            **kwargs: Additional parameters
            
        Returns:
            Standardized LLMResponse
        """
        pass
    
    async def embed(self, texts: List[str], **kwargs) -> List[List[float]]:
        """
        Generate embeddings for texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        raise NotImplementedError(f"{self.name} does not support embeddings")
    
    async def chat_with_functions(
        self, 
        messages: List[LLMMessage],
        functions: List[Dict[str, Any]],
        **kwargs
    ) -> LLMResponse:
        """
        Chat with function calling capability.
        
        Args:
            messages: Conversation messages
            functions: Available functions schema
            
        Returns:
            Response potentially with function_call
        """
        raise NotImplementedError(f"{self.name} does not support function calling")
    
    def validate_config(self) -> bool:
        """Validate the provider configuration."""
        if not self.config.model:
            return False
        return True
    
    def get_info(self) -> Dict[str, Any]:
        """Get provider information."""
        return {
            'name': self.name,
            'model': self.config.model,
            'capabilities': [c.value for c in self.capabilities],
            'configured': self.validate_config()
        }
    
    def _build_messages(self, messages: List[LLMMessage]) -> List[Dict[str, str]]:
        """Convert LLMMessage objects to provider format."""
        result = []
        for msg in messages:
            item = {'role': msg.role, 'content': msg.content}
            if msg.name:
                item['name'] = msg.name
            result.append(item)
        return result

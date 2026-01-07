# Groq Provider Implementation - FREE and FAST LLM
# Groq offers free tier with llama, mixtral, and gemma models
import os
from typing import Dict, List, Any, Optional
import httpx

from .base import BaseLLMProvider, LLMConfig, LLMMessage, LLMResponse, LLMCapability


class GroqProvider(BaseLLMProvider):
    """
    Groq API provider - FREE tier with fast inference.
    
    Available Models (all FREE):
        - llama-3.3-70b-versatile (best quality)
        - llama-3.1-8b-instant (fastest)
        - mixtral-8x7b-32768 (good balance)
        - gemma2-9b-it (Google's model)
    
    Environment Variables:
        GROQ_API_KEY: Your Groq API key from console.groq.com
    
    Rate Limits (Free Tier):
        - 30 requests/minute
        - 6000 tokens/minute
        - Plenty for a studio management app!
    """
    
    DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"
    
    MODELS = {
        'llama-3.3-70b-versatile': {'context': 32768, 'supports_functions': True},
        'llama-3.1-70b-versatile': {'context': 32768, 'supports_functions': True},
        'llama-3.1-8b-instant': {'context': 8192, 'supports_functions': True},
        'llama3-70b-8192': {'context': 8192, 'supports_functions': True},
        'llama3-8b-8192': {'context': 8192, 'supports_functions': True},
        'mixtral-8x7b-32768': {'context': 32768, 'supports_functions': True},
        'gemma2-9b-it': {'context': 8192, 'supports_functions': False},
    }
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.api_key = config.api_key or os.getenv('GROQ_API_KEY')
        self.base_url = config.api_base or self.DEFAULT_BASE_URL
        
        # Default to best free model
        if not config.model:
            config.model = 'llama-3.3-70b-versatile'
        
    @property
    def name(self) -> str:
        return "groq"
    
    @property
    def capabilities(self) -> List[LLMCapability]:
        caps = [LLMCapability.CHAT, LLMCapability.COMPLETION, LLMCapability.STREAMING]
        
        model_info = self.MODELS.get(self.config.model, {})
        if model_info.get('supports_functions'):
            caps.append(LLMCapability.FUNCTION_CALLING)
            
        return caps
    
    def validate_config(self) -> bool:
        return bool(self.api_key)
    
    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """Send chat completion request to Groq."""
        if not self.validate_config():
            return LLMResponse(
                content="Groq API key not configured. Get free key at console.groq.com",
                model=self.config.model,
                provider=self.name,
                usage={'error': 'missing_api_key'}
            )
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': self.config.model,
            'messages': self._build_messages(messages),
            'temperature': kwargs.get('temperature', self.config.temperature),
            'max_tokens': kwargs.get('max_tokens', self.config.max_tokens),
        }
        
        # Add function calling if provided
        if 'functions' in kwargs:
            payload['tools'] = [
                {'type': 'function', 'function': f} for f in kwargs['functions']
            ]
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 429:
                    return LLMResponse(
                        content="Rate limit reached. Groq free tier: 30 req/min. Please wait.",
                        model=self.config.model,
                        provider=self.name,
                        usage={'error': 'rate_limited'}
                    )
                
                response.raise_for_status()
                data = response.json()
                
                choice = data['choices'][0]
                message = choice['message']
                
                # Handle function calls
                function_call = None
                if message.get('tool_calls'):
                    tool_call = message['tool_calls'][0]
                    function_call = {
                        'name': tool_call['function']['name'],
                        'arguments': tool_call['function']['arguments']
                    }
                
                return LLMResponse(
                    content=message.get('content', ''),
                    model=data['model'],
                    provider=self.name,
                    usage={
                        'prompt_tokens': data['usage']['prompt_tokens'],
                        'completion_tokens': data['usage']['completion_tokens'],
                        'total_tokens': data['usage']['total_tokens']
                    },
                    function_call=function_call,
                    raw_response=data
                )
                
        except httpx.HTTPStatusError as e:
            return LLMResponse(
                content=f"Groq API error: {str(e)}",
                model=self.config.model,
                provider=self.name,
                usage={'error': str(e)}
            )
        except Exception as e:
            return LLMResponse(
                content=f"Error calling Groq: {str(e)}",
                model=self.config.model,
                provider=self.name,
                usage={'error': str(e)}
            )
    
    def _build_messages(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        """Convert LLMMessage objects to API format."""
        result = []
        for msg in messages:
            message_dict = {
                'role': msg.role,
                'content': msg.content
            }
            if msg.name:
                message_dict['name'] = msg.name
            result.append(message_dict)
        return result
    
    async def stream_chat(self, messages: List[LLMMessage], **kwargs):
        """Stream chat completion from Groq."""
        if not self.validate_config():
            yield "Groq API key not configured."
            return
            
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': self.config.model,
            'messages': self._build_messages(messages),
            'temperature': kwargs.get('temperature', self.config.temperature),
            'max_tokens': kwargs.get('max_tokens', self.config.max_tokens),
            'stream': True
        }
        
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            async with client.stream(
                'POST',
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith('data: '):
                        data = line[6:]
                        if data == '[DONE]':
                            break
                        try:
                            import json
                            chunk = json.loads(data)
                            delta = chunk['choices'][0].get('delta', {})
                            if 'content' in delta:
                                yield delta['content']
                        except:
                            continue
    
    async def embed(self, text: str, **kwargs) -> List[float]:
        """Groq doesn't support embeddings - use fallback."""
        raise NotImplementedError("Groq doesn't support embeddings. Use OpenAI or local model.")
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        # Rough estimate: ~4 chars per token for English
        return len(text) // 4

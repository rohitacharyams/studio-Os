# OpenAI Provider Implementation
import os
from typing import Dict, List, Any, Optional
import httpx

from .base import BaseLLMProvider, LLMConfig, LLMMessage, LLMResponse, LLMCapability


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI API provider supporting GPT-4, GPT-3.5, and embeddings.
    
    Environment Variables:
        OPENAI_API_KEY: Your OpenAI API key
        OPENAI_API_BASE: Optional custom base URL (for Azure OpenAI)
    """
    
    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    
    MODELS = {
        'gpt-4': {'context': 8192, 'supports_functions': True},
        'gpt-4-turbo': {'context': 128000, 'supports_functions': True},
        'gpt-4-turbo-preview': {'context': 128000, 'supports_functions': True},
        'gpt-4o': {'context': 128000, 'supports_functions': True},
        'gpt-4o-mini': {'context': 128000, 'supports_functions': True},
        'gpt-3.5-turbo': {'context': 16385, 'supports_functions': True},
        'text-embedding-3-small': {'type': 'embedding', 'dimensions': 1536},
        'text-embedding-3-large': {'type': 'embedding', 'dimensions': 3072},
    }
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.api_key = config.api_key or os.getenv('OPENAI_API_KEY')
        self.base_url = config.api_base or os.getenv('OPENAI_API_BASE', self.DEFAULT_BASE_URL)
        
    @property
    def name(self) -> str:
        return "openai"
    
    @property
    def capabilities(self) -> List[LLMCapability]:
        caps = [LLMCapability.CHAT, LLMCapability.COMPLETION, LLMCapability.STREAMING]
        
        model_info = self.MODELS.get(self.config.model, {})
        if model_info.get('supports_functions'):
            caps.append(LLMCapability.FUNCTION_CALLING)
        if model_info.get('type') == 'embedding':
            caps.append(LLMCapability.EMBEDDINGS)
        if 'vision' in self.config.model or '4o' in self.config.model:
            caps.append(LLMCapability.VISION)
            
        return caps
    
    def validate_config(self) -> bool:
        return bool(self.api_key and self.config.model)
    
    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """Send chat completion request to OpenAI."""
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
        
        # Add any extra params
        payload.update(self.config.extra_params)
        payload.update({k: v for k, v in kwargs.items() if k not in ['temperature', 'max_tokens']})
        
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers
            )
            
            if response.status_code != 200:
                error = response.json().get('error', {})
                raise Exception(f"OpenAI API error: {error.get('message', response.text)}")
            
            data = response.json()
            choice = data['choices'][0]
            
            return LLMResponse(
                content=choice['message']['content'],
                model=data['model'],
                provider=self.name,
                usage={
                    'prompt_tokens': data['usage']['prompt_tokens'],
                    'completion_tokens': data['usage']['completion_tokens'],
                    'total_tokens': data['usage']['total_tokens']
                },
                finish_reason=choice.get('finish_reason'),
                raw_response=data
            )
    
    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """Send completion request (uses chat endpoint with user message)."""
        messages = [LLMMessage(role='user', content=prompt)]
        return await self.chat(messages, **kwargs)
    
    async def embed(self, texts: List[str], **kwargs) -> List[List[float]]:
        """Generate embeddings using OpenAI."""
        model = kwargs.get('model', 'text-embedding-3-small')
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                json={'model': model, 'input': texts},
                headers=headers
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenAI embeddings error: {response.text}")
            
            data = response.json()
            return [item['embedding'] for item in data['data']]
    
    async def chat_with_functions(
        self,
        messages: List[LLMMessage],
        functions: List[Dict[str, Any]],
        **kwargs
    ) -> LLMResponse:
        """Chat with function calling."""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # Convert functions to tools format (newer API)
        tools = [{'type': 'function', 'function': f} for f in functions]
        
        payload = {
            'model': self.config.model,
            'messages': self._build_messages(messages),
            'tools': tools,
            'temperature': kwargs.get('temperature', self.config.temperature),
            'max_tokens': kwargs.get('max_tokens', self.config.max_tokens),
        }
        
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response.text}")
            
            data = response.json()
            choice = data['choices'][0]
            message = choice['message']
            
            # Handle tool calls
            content = message.get('content', '')
            if message.get('tool_calls'):
                content = str(message['tool_calls'])
            
            return LLMResponse(
                content=content,
                model=data['model'],
                provider=self.name,
                usage=data.get('usage', {}),
                finish_reason=choice.get('finish_reason'),
                raw_response=data
            )

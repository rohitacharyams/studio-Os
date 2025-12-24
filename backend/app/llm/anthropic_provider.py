# Anthropic Claude Provider Implementation
import os
from typing import Dict, List, Any
import httpx

from .base import BaseLLMProvider, LLMConfig, LLMMessage, LLMResponse, LLMCapability


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic Claude API provider.
    
    Supports Claude 3 family: Opus, Sonnet, Haiku
    
    Environment Variables:
        ANTHROPIC_API_KEY: Your Anthropic API key
    """
    
    BASE_URL = "https://api.anthropic.com/v1"
    API_VERSION = "2023-06-01"
    
    MODELS = {
        'claude-3-opus-20240229': {'context': 200000, 'supports_vision': True},
        'claude-3-sonnet-20240229': {'context': 200000, 'supports_vision': True},
        'claude-3-haiku-20240307': {'context': 200000, 'supports_vision': True},
        'claude-3-5-sonnet-20241022': {'context': 200000, 'supports_vision': True},
        'claude-2.1': {'context': 200000, 'supports_vision': False},
        'claude-2.0': {'context': 100000, 'supports_vision': False},
    }
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.api_key = config.api_key or os.getenv('ANTHROPIC_API_KEY')
        
    @property
    def name(self) -> str:
        return "anthropic"
    
    @property
    def capabilities(self) -> List[LLMCapability]:
        caps = [LLMCapability.CHAT, LLMCapability.COMPLETION, LLMCapability.STREAMING]
        
        model_info = self.MODELS.get(self.config.model, {})
        if model_info.get('supports_vision'):
            caps.append(LLMCapability.VISION)
        
        # Claude 3 supports tool use
        if 'claude-3' in self.config.model:
            caps.append(LLMCapability.FUNCTION_CALLING)
            
        return caps
    
    def validate_config(self) -> bool:
        return bool(self.api_key and self.config.model)
    
    def _convert_messages(self, messages: List[LLMMessage]) -> tuple:
        """Convert messages to Anthropic format, extracting system message."""
        system_prompt = None
        converted = []
        
        for msg in messages:
            if msg.role == 'system':
                system_prompt = msg.content
            else:
                # Anthropic uses 'user' and 'assistant' roles
                role = 'user' if msg.role == 'user' else 'assistant'
                converted.append({'role': role, 'content': msg.content})
        
        return system_prompt, converted
    
    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """Send chat request to Claude."""
        headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json',
            'anthropic-version': self.API_VERSION
        }
        
        system_prompt, converted_messages = self._convert_messages(messages)
        
        payload = {
            'model': self.config.model,
            'messages': converted_messages,
            'max_tokens': kwargs.get('max_tokens', self.config.max_tokens),
            'temperature': kwargs.get('temperature', self.config.temperature),
        }
        
        if system_prompt:
            payload['system'] = system_prompt
        
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                f"{self.BASE_URL}/messages",
                json=payload,
                headers=headers
            )
            
            if response.status_code != 200:
                error = response.json().get('error', {})
                raise Exception(f"Anthropic API error: {error.get('message', response.text)}")
            
            data = response.json()
            
            # Extract content from response
            content = ""
            if data.get('content'):
                content = "".join([
                    block.get('text', '') 
                    for block in data['content'] 
                    if block.get('type') == 'text'
                ])
            
            return LLMResponse(
                content=content,
                model=data['model'],
                provider=self.name,
                usage={
                    'prompt_tokens': data['usage']['input_tokens'],
                    'completion_tokens': data['usage']['output_tokens'],
                    'total_tokens': data['usage']['input_tokens'] + data['usage']['output_tokens']
                },
                finish_reason=data.get('stop_reason'),
                raw_response=data
            )
    
    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """Send completion request."""
        messages = [LLMMessage(role='user', content=prompt)]
        return await self.chat(messages, **kwargs)
    
    async def chat_with_functions(
        self,
        messages: List[LLMMessage],
        functions: List[Dict[str, Any]],
        **kwargs
    ) -> LLMResponse:
        """Chat with tool use (Claude 3 feature)."""
        headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json',
            'anthropic-version': self.API_VERSION
        }
        
        system_prompt, converted_messages = self._convert_messages(messages)
        
        # Convert functions to Claude tool format
        tools = []
        for func in functions:
            tools.append({
                'name': func['name'],
                'description': func.get('description', ''),
                'input_schema': func.get('parameters', {'type': 'object', 'properties': {}})
            })
        
        payload = {
            'model': self.config.model,
            'messages': converted_messages,
            'tools': tools,
            'max_tokens': kwargs.get('max_tokens', self.config.max_tokens),
        }
        
        if system_prompt:
            payload['system'] = system_prompt
        
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                f"{self.BASE_URL}/messages",
                json=payload,
                headers=headers
            )
            
            if response.status_code != 200:
                raise Exception(f"Anthropic API error: {response.text}")
            
            data = response.json()
            
            # Handle tool use in response
            content_parts = []
            for block in data.get('content', []):
                if block['type'] == 'text':
                    content_parts.append(block['text'])
                elif block['type'] == 'tool_use':
                    content_parts.append(f"[Tool: {block['name']}({block.get('input', {})})]")
            
            return LLMResponse(
                content="\n".join(content_parts),
                model=data['model'],
                provider=self.name,
                usage={
                    'prompt_tokens': data['usage']['input_tokens'],
                    'completion_tokens': data['usage']['output_tokens'],
                    'total_tokens': data['usage']['input_tokens'] + data['usage']['output_tokens']
                },
                finish_reason=data.get('stop_reason'),
                raw_response=data
            )

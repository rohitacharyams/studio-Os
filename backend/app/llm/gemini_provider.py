# Google Gemini Provider Implementation
import os
from typing import Dict, List, Any
import httpx

from .base import BaseLLMProvider, LLMConfig, LLMMessage, LLMResponse, LLMCapability


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini API provider.
    
    Supports Gemini Pro, Gemini Pro Vision, and Gemini 1.5
    
    Environment Variables:
        GOOGLE_API_KEY: Your Google AI API key
    """
    
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    
    MODELS = {
        'gemini-pro': {'context': 32000, 'supports_vision': False},
        'gemini-pro-vision': {'context': 16000, 'supports_vision': True},
        'gemini-1.5-pro': {'context': 1000000, 'supports_vision': True},
        'gemini-1.5-flash': {'context': 1000000, 'supports_vision': True},
    }
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.api_key = config.api_key or os.getenv('GOOGLE_API_KEY')
        
    @property
    def name(self) -> str:
        return "gemini"
    
    @property
    def capabilities(self) -> List[LLMCapability]:
        caps = [LLMCapability.CHAT, LLMCapability.COMPLETION, LLMCapability.STREAMING]
        
        model_info = self.MODELS.get(self.config.model, {})
        if model_info.get('supports_vision'):
            caps.append(LLMCapability.VISION)
        
        # Gemini supports function calling
        caps.append(LLMCapability.FUNCTION_CALLING)
        caps.append(LLMCapability.EMBEDDINGS)
            
        return caps
    
    def validate_config(self) -> bool:
        return bool(self.api_key and self.config.model)
    
    def _convert_messages(self, messages: List[LLMMessage]) -> tuple:
        """Convert messages to Gemini format."""
        system_instruction = None
        contents = []
        
        for msg in messages:
            if msg.role == 'system':
                system_instruction = msg.content
            else:
                role = 'user' if msg.role == 'user' else 'model'
                contents.append({
                    'role': role,
                    'parts': [{'text': msg.content}]
                })
        
        return system_instruction, contents
    
    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """Send chat request to Gemini."""
        model = self.config.model
        url = f"{self.BASE_URL}/models/{model}:generateContent?key={self.api_key}"
        
        system_instruction, contents = self._convert_messages(messages)
        
        payload = {
            'contents': contents,
            'generationConfig': {
                'temperature': kwargs.get('temperature', self.config.temperature),
                'maxOutputTokens': kwargs.get('max_tokens', self.config.max_tokens),
            }
        }
        
        if system_instruction:
            payload['systemInstruction'] = {'parts': [{'text': system_instruction}]}
        
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(url, json=payload)
            
            if response.status_code != 200:
                error = response.json().get('error', {})
                raise Exception(f"Gemini API error: {error.get('message', response.text)}")
            
            data = response.json()
            
            # Extract content
            content = ""
            candidates = data.get('candidates', [])
            if candidates:
                parts = candidates[0].get('content', {}).get('parts', [])
                content = "".join([p.get('text', '') for p in parts])
            
            # Get usage metadata
            usage_metadata = data.get('usageMetadata', {})
            
            return LLMResponse(
                content=content,
                model=model,
                provider=self.name,
                usage={
                    'prompt_tokens': usage_metadata.get('promptTokenCount', 0),
                    'completion_tokens': usage_metadata.get('candidatesTokenCount', 0),
                    'total_tokens': usage_metadata.get('totalTokenCount', 0)
                },
                finish_reason=candidates[0].get('finishReason') if candidates else None,
                raw_response=data
            )
    
    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """Send completion request."""
        messages = [LLMMessage(role='user', content=prompt)]
        return await self.chat(messages, **kwargs)
    
    async def embed(self, texts: List[str], **kwargs) -> List[List[float]]:
        """Generate embeddings using Gemini."""
        model = kwargs.get('model', 'text-embedding-004')
        url = f"{self.BASE_URL}/models/{model}:embedContent?key={self.api_key}"
        
        embeddings = []
        
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            for text in texts:
                payload = {
                    'model': f"models/{model}",
                    'content': {'parts': [{'text': text}]}
                }
                
                response = await client.post(url, json=payload)
                
                if response.status_code != 200:
                    raise Exception(f"Gemini embeddings error: {response.text}")
                
                data = response.json()
                embeddings.append(data['embedding']['values'])
        
        return embeddings
    
    async def chat_with_functions(
        self,
        messages: List[LLMMessage],
        functions: List[Dict[str, Any]],
        **kwargs
    ) -> LLMResponse:
        """Chat with function calling."""
        model = self.config.model
        url = f"{self.BASE_URL}/models/{model}:generateContent?key={self.api_key}"
        
        system_instruction, contents = self._convert_messages(messages)
        
        # Convert to Gemini function declarations
        function_declarations = []
        for func in functions:
            function_declarations.append({
                'name': func['name'],
                'description': func.get('description', ''),
                'parameters': func.get('parameters', {'type': 'object', 'properties': {}})
            })
        
        payload = {
            'contents': contents,
            'tools': [{'functionDeclarations': function_declarations}],
            'generationConfig': {
                'temperature': kwargs.get('temperature', self.config.temperature),
                'maxOutputTokens': kwargs.get('max_tokens', self.config.max_tokens),
            }
        }
        
        if system_instruction:
            payload['systemInstruction'] = {'parts': [{'text': system_instruction}]}
        
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(url, json=payload)
            
            if response.status_code != 200:
                raise Exception(f"Gemini API error: {response.text}")
            
            data = response.json()
            
            # Extract content including function calls
            content_parts = []
            candidates = data.get('candidates', [])
            if candidates:
                parts = candidates[0].get('content', {}).get('parts', [])
                for part in parts:
                    if 'text' in part:
                        content_parts.append(part['text'])
                    elif 'functionCall' in part:
                        fc = part['functionCall']
                        content_parts.append(f"[Function: {fc['name']}({fc.get('args', {})})]")
            
            return LLMResponse(
                content="\n".join(content_parts),
                model=model,
                provider=self.name,
                usage=data.get('usageMetadata', {}),
                finish_reason=candidates[0].get('finishReason') if candidates else None,
                raw_response=data
            )

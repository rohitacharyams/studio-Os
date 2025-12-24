# Ollama Provider Implementation (Local LLMs)
import os
from typing import Dict, List, Any
import httpx

from .base import BaseLLMProvider, LLMConfig, LLMMessage, LLMResponse, LLMCapability


class OllamaProvider(BaseLLMProvider):
    """
    Ollama provider for running local LLMs.
    
    Ollama allows you to run models like Llama 2, Mistral, CodeLlama locally.
    
    Environment Variables:
        OLLAMA_HOST: Ollama server URL (default: http://localhost:11434)
    """
    
    DEFAULT_HOST = "http://localhost:11434"
    
    # Popular Ollama models
    MODELS = {
        'llama2': {'context': 4096},
        'llama2:13b': {'context': 4096},
        'llama2:70b': {'context': 4096},
        'mistral': {'context': 8192},
        'mixtral': {'context': 32768},
        'codellama': {'context': 16384},
        'phi': {'context': 2048},
        'neural-chat': {'context': 4096},
        'starling-lm': {'context': 8192},
        'llama3': {'context': 8192},
        'llama3:70b': {'context': 8192},
        'qwen2': {'context': 32768},
    }
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.host = config.api_base or os.getenv('OLLAMA_HOST', self.DEFAULT_HOST)
        
    @property
    def name(self) -> str:
        return "ollama"
    
    @property
    def capabilities(self) -> List[LLMCapability]:
        caps = [LLMCapability.CHAT, LLMCapability.COMPLETION, LLMCapability.STREAMING]
        caps.append(LLMCapability.EMBEDDINGS)
        return caps
    
    def validate_config(self) -> bool:
        return bool(self.config.model)
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models on the Ollama server."""
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                response = await client.get(f"{self.host}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return data.get('models', [])
            except Exception:
                pass
        return []
    
    async def pull_model(self, model: str) -> bool:
        """Pull a model to the Ollama server."""
        async with httpx.AsyncClient(timeout=600) as client:  # Long timeout for model download
            try:
                response = await client.post(
                    f"{self.host}/api/pull",
                    json={'name': model}
                )
                return response.status_code == 200
            except Exception:
                return False
    
    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """Send chat request to Ollama."""
        payload = {
            'model': self.config.model,
            'messages': self._build_messages(messages),
            'stream': False,
            'options': {
                'temperature': kwargs.get('temperature', self.config.temperature),
                'num_predict': kwargs.get('max_tokens', self.config.max_tokens),
            }
        }
        
        async with httpx.AsyncClient(timeout=self.config.timeout * 2) as client:
            response = await client.post(
                f"{self.host}/api/chat",
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.text}")
            
            data = response.json()
            
            return LLMResponse(
                content=data['message']['content'],
                model=data['model'],
                provider=self.name,
                usage={
                    'prompt_tokens': data.get('prompt_eval_count', 0),
                    'completion_tokens': data.get('eval_count', 0),
                    'total_tokens': data.get('prompt_eval_count', 0) + data.get('eval_count', 0)
                },
                finish_reason=data.get('done_reason', 'stop'),
                raw_response=data
            )
    
    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """Send completion request to Ollama (generate endpoint)."""
        payload = {
            'model': self.config.model,
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': kwargs.get('temperature', self.config.temperature),
                'num_predict': kwargs.get('max_tokens', self.config.max_tokens),
            }
        }
        
        async with httpx.AsyncClient(timeout=self.config.timeout * 2) as client:
            response = await client.post(
                f"{self.host}/api/generate",
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.text}")
            
            data = response.json()
            
            return LLMResponse(
                content=data['response'],
                model=data['model'],
                provider=self.name,
                usage={
                    'prompt_tokens': data.get('prompt_eval_count', 0),
                    'completion_tokens': data.get('eval_count', 0),
                    'total_tokens': data.get('prompt_eval_count', 0) + data.get('eval_count', 0)
                },
                finish_reason='stop' if data.get('done') else 'length',
                raw_response=data
            )
    
    async def embed(self, texts: List[str], **kwargs) -> List[List[float]]:
        """Generate embeddings using Ollama."""
        model = kwargs.get('model', self.config.model)
        embeddings = []
        
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            for text in texts:
                response = await client.post(
                    f"{self.host}/api/embeddings",
                    json={'model': model, 'prompt': text}
                )
                
                if response.status_code != 200:
                    raise Exception(f"Ollama embeddings error: {response.text}")
                
                data = response.json()
                embeddings.append(data['embedding'])
        
        return embeddings
    
    async def health_check(self) -> bool:
        """Check if Ollama server is running."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.host}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

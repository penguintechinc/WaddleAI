"""
LLM Provider Connection Management
Handles connections to OpenAI, Anthropic, and Ollama providers
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from abc import ABC, abstractmethod
from datetime import datetime
import openai
import anthropic
import tiktoken

logger = logging.getLogger(__name__)


class LLMConnector(ABC):
    """Abstract base class for LLM provider connections"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.enabled = config.get('enabled', True)
        self.endpoint_url = config.get('endpoint_url')
        self.api_key = config.get('api_key')
        self.model_list = config.get('model_list', [])
        
    @abstractmethod
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate chat completion"""
        pass
    
    @abstractmethod
    async def count_tokens(self, text: str, model: str) -> int:
        """Count tokens in text"""
        pass
    
    @abstractmethod
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check provider health"""
        pass


class OpenAIConnector(LLMConnector):
    """OpenAI API connector"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.client = openai.AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.endpoint_url
        )
        
        # Initialize tokenizers
        self.encoders = {
            'gpt-4': tiktoken.encoding_for_model("gpt-4"),
            'gpt-3.5-turbo': tiktoken.encoding_for_model("gpt-3.5-turbo"),
        }
        self.default_encoder = tiktoken.encoding_for_model("gpt-3.5-turbo")
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate OpenAI chat completion"""
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            
            content = response.choices[0].message.content
            usage_info = {
                'input_tokens': response.usage.prompt_tokens,
                'output_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens,
                'model': response.model,
                'finish_reason': response.choices[0].finish_reason,
                'provider': 'openai'
            }
            
            return content, usage_info
            
        except Exception as e:
            logger.error(f"OpenAI completion failed: {e}")
            raise
    
    async def count_tokens(self, text: str, model: str) -> int:
        """Count tokens using OpenAI tokenizer"""
        try:
            encoder = self.encoders.get(model, self.default_encoder)
            return len(encoder.encode(text))
        except Exception as e:
            logger.warning(f"Token counting failed: {e}")
            # Fallback: rough estimation
            return len(text) // 4
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List OpenAI models"""
        try:
            models_response = await self.client.models.list()
            models = []
            
            for model in models_response.data:
                if model.id in self.model_list:
                    models.append({
                        'id': model.id,
                        'object': 'model',
                        'created': model.created,
                        'owned_by': model.owned_by,
                        'provider': 'openai',
                        'capabilities': ['chat', 'completion'],
                        'context_length': self._get_context_length(model.id)
                    })
            
            return models
            
        except Exception as e:
            logger.error(f"Failed to list OpenAI models: {e}")
            return []
    
    def _get_context_length(self, model: str) -> int:
        """Get context length for OpenAI model"""
        context_lengths = {
            'gpt-4': 8192,
            'gpt-4-32k': 32768,
            'gpt-3.5-turbo': 4096,
            'gpt-3.5-turbo-16k': 16384,
        }
        return context_lengths.get(model, 4096)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check OpenAI API health"""
        try:
            # Simple API call to check connectivity
            await self.client.models.list()
            return {
                'status': 'healthy',
                'provider': 'openai',
                'endpoint': self.endpoint_url,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'provider': 'openai',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }


class AnthropicConnector(LLMConnector):
    """Anthropic Claude API connector"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
        
        # Anthropic doesn't have tokenizers, so we estimate
        self.token_estimator = tiktoken.encoding_for_model("gpt-3.5-turbo")
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate Anthropic chat completion"""
        try:
            # Convert messages to Anthropic format
            system_message = ""
            user_messages = []
            
            for msg in messages:
                if msg['role'] == 'system':
                    system_message = msg['content']
                else:
                    user_messages.append(msg)
            
            # Anthropic API call
            response = await self.client.messages.create(
                model=model,
                max_tokens=kwargs.get('max_tokens', 1000),
                system=system_message if system_message else None,
                messages=user_messages
            )
            
            content = response.content[0].text
            
            # Estimate token usage (Anthropic doesn't provide exact counts)
            input_text = system_message + " ".join([msg['content'] for msg in user_messages])
            input_tokens = len(self.token_estimator.encode(input_text))
            output_tokens = len(self.token_estimator.encode(content))
            
            usage_info = {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens,
                'model': model,
                'finish_reason': response.stop_reason,
                'provider': 'anthropic'
            }
            
            return content, usage_info
            
        except Exception as e:
            logger.error(f"Anthropic completion failed: {e}")
            raise
    
    async def count_tokens(self, text: str, model: str) -> int:
        """Estimate tokens for Anthropic models"""
        try:
            return len(self.token_estimator.encode(text))
        except Exception:
            return len(text) // 4
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List Anthropic models"""
        # Anthropic doesn't have a models endpoint, return configured models
        models = []
        for model_id in self.model_list:
            models.append({
                'id': model_id,
                'object': 'model',
                'created': int(datetime.utcnow().timestamp()),
                'owned_by': 'anthropic',
                'provider': 'anthropic',
                'capabilities': ['chat'],
                'context_length': self._get_context_length(model_id)
            })
        return models
    
    def _get_context_length(self, model: str) -> int:
        """Get context length for Anthropic model"""
        context_lengths = {
            'claude-3-opus-20240229': 200000,
            'claude-3-sonnet-20240229': 200000,
            'claude-3-haiku-20240307': 200000,
        }
        return context_lengths.get(model, 100000)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Anthropic API health"""
        try:
            # Simple test message
            test_response = await self.client.messages.create(
                model=self.model_list[0] if self.model_list else 'claude-3-haiku-20240307',
                max_tokens=1,
                messages=[{"role": "user", "content": "hi"}]
            )
            return {
                'status': 'healthy',
                'provider': 'anthropic',
                'endpoint': 'https://api.anthropic.com',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'provider': 'anthropic',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }


class OllamaConnector(LLMConnector):
    """Ollama local LLM connector"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.session = aiohttp.ClientSession()
        
        # Use OpenAI tokenizer for estimation
        self.token_estimator = tiktoken.encoding_for_model("gpt-3.5-turbo")
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate Ollama chat completion"""
        try:
            payload = {
                'model': model,
                'messages': messages,
                'stream': False,
                'options': {
                    'temperature': kwargs.get('temperature', 0.7),
                    'num_predict': kwargs.get('max_tokens', -1)
                }
            }
            
            async with self.session.post(
                f"{self.endpoint_url}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                if response.status != 200:
                    raise Exception(f"Ollama API error: {response.status}")
                
                result = await response.json()
                content = result['message']['content']
                
                # Estimate token usage
                input_text = " ".join([msg['content'] for msg in messages])
                input_tokens = len(self.token_estimator.encode(input_text))
                output_tokens = len(self.token_estimator.encode(content))
                
                usage_info = {
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens,
                    'total_tokens': input_tokens + output_tokens,
                    'model': model,
                    'finish_reason': result.get('done_reason', 'stop'),
                    'provider': 'ollama'
                }
                
                return content, usage_info
                
        except Exception as e:
            logger.error(f"Ollama completion failed: {e}")
            raise
    
    async def count_tokens(self, text: str, model: str) -> int:
        """Estimate tokens for Ollama models"""
        try:
            return len(self.token_estimator.encode(text))
        except Exception:
            return len(text) // 4
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List Ollama models"""
        try:
            async with self.session.get(f"{self.endpoint_url}/api/tags") as response:
                if response.status != 200:
                    return []
                
                result = await response.json()
                models = []
                
                for model_data in result.get('models', []):
                    models.append({
                        'id': model_data['name'],
                        'object': 'model',
                        'created': int(datetime.utcnow().timestamp()),
                        'owned_by': 'ollama',
                        'provider': 'ollama',
                        'capabilities': ['chat', 'completion'],
                        'context_length': 4096,  # Default for most Ollama models
                        'size': model_data.get('size', 0)
                    })
                
                return models
                
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []
    
    async def pull_model(self, model: str) -> Dict[str, Any]:
        """Pull a model in Ollama"""
        try:
            payload = {'name': model}
            
            async with self.session.post(
                f"{self.endpoint_url}/api/pull",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=1800)  # 30 minutes for model download
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to pull model: {response.status}")
                
                # Ollama streams the download progress
                result = {'status': 'success', 'model': model}
                return result
                
        except Exception as e:
            logger.error(f"Failed to pull Ollama model {model}: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def remove_model(self, model: str) -> Dict[str, Any]:
        """Remove a model from Ollama"""
        try:
            payload = {'name': model}
            
            async with self.session.delete(
                f"{self.endpoint_url}/api/delete",
                json=payload
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to remove model: {response.status}")
                
                return {'status': 'success', 'model': model}
                
        except Exception as e:
            logger.error(f"Failed to remove Ollama model {model}: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Ollama health"""
        try:
            async with self.session.get(f"{self.endpoint_url}/api/tags") as response:
                if response.status == 200:
                    return {
                        'status': 'healthy',
                        'provider': 'ollama',
                        'endpoint': self.endpoint_url,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                else:
                    raise Exception(f"HTTP {response.status}")
                    
        except Exception as e:
            return {
                'status': 'unhealthy',
                'provider': 'ollama',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()


class LLMConnectionManager:
    """Manages all LLM provider connections"""
    
    def __init__(self, db):
        self.db = db
        self.connectors: Dict[str, LLMConnector] = {}
        self._load_connectors()
    
    def _load_connectors(self):
        """Load connectors from database configuration"""
        links = self.db(self.db.connection_links.enabled == True).select()
        
        for link in links:
            try:
                config = {
                    'enabled': link.enabled,
                    'endpoint_url': link.endpoint_url,
                    'api_key': link.api_key,
                    'model_list': link.model_list or [],
                    'rate_limits': link.rate_limits or {},
                    'tls_config': link.tls_config or {}
                }
                
                if link.provider == 'openai':
                    connector = OpenAIConnector(link.name, config)
                elif link.provider == 'anthropic':
                    connector = AnthropicConnector(link.name, config)
                elif link.provider == 'ollama':
                    connector = OllamaConnector(link.name, config)
                else:
                    logger.warning(f"Unknown provider: {link.provider}")
                    continue
                
                self.connectors[link.name] = connector
                logger.info(f"Loaded connector: {link.name} ({link.provider})")
                
            except Exception as e:
                logger.error(f"Failed to load connector {link.name}: {e}")
    
    def reload_connectors(self):
        """Reload connectors from database"""
        self.connectors.clear()
        self._load_connectors()
    
    def get_connector(self, name: str) -> Optional[LLMConnector]:
        """Get connector by name"""
        return self.connectors.get(name)
    
    def get_connector_for_model(self, model: str) -> Optional[LLMConnector]:
        """Get connector that supports the specified model"""
        for connector in self.connectors.values():
            if model in connector.model_list or not connector.model_list:
                return connector
        return None
    
    def get_connectors_by_provider(self, provider: str) -> List[LLMConnector]:
        """Get all connectors for a provider"""
        return [
            conn for conn in self.connectors.values()
            if conn.config.get('provider') == provider
        ]
    
    async def list_all_models(self) -> List[Dict[str, Any]]:
        """List models from all connectors"""
        all_models = []
        
        for connector in self.connectors.values():
            try:
                models = await connector.list_models()
                all_models.extend(models)
            except Exception as e:
                logger.error(f"Failed to list models from {connector.name}: {e}")
        
        return all_models
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Check health of all connectors"""
        health_results = {}
        
        for name, connector in self.connectors.items():
            try:
                health_results[name] = await connector.health_check()
            except Exception as e:
                health_results[name] = {
                    'status': 'unhealthy',
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
        
        return health_results
    
    async def close_all(self):
        """Close all connector connections"""
        for connector in self.connectors.values():
            if hasattr(connector, 'close'):
                await connector.close()


def create_llm_connection_manager(db) -> LLMConnectionManager:
    """Factory function to create LLM connection manager"""
    return LLMConnectionManager(db)
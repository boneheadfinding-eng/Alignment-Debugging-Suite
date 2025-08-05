"""
API client for interacting with LLM providers.
"""

import os
import asyncio
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import aiohttp
import openai
from anthropic import AsyncAnthropic
import logging
from dotenv import load_dotenv


load_dotenv()
logger = logging.getLogger(__name__)


class BaseAPIClient(ABC):
    """Base class for API clients."""
    
    @abstractmethod
    async def get_completion(self, prompt: str) -> str:
        """Get completion from the model."""
        pass
    
    @abstractmethod
    async def get_batch_completions(self, prompts: List[str]) -> List[str]:
        """Get completions for multiple prompts."""
        pass


class OpenAIClient(BaseAPIClient):
    """Client for OpenAI API."""
    
    def __init__(self, config: Dict[str, Any]):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
            
        openai.api_key = self.api_key
        self.model = config.get('name', 'gpt-4')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 1000)
        self.top_p = config.get('top_p', 0.9)
        
    async def get_completion(self, prompt: str) -> str:
        """Get completion from OpenAI."""
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def get_batch_completions(self, prompts: List[str]) -> List[str]:
        """Get batch completions from OpenAI."""
        tasks = [self.get_completion(prompt) for prompt in prompts]
        return await asyncio.gather(*tasks)


class AnthropicClient(BaseAPIClient):
    """Client for Anthropic API."""
    
    def __init__(self, config: Dict[str, Any]):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
            
        self.client = AsyncAnthropic(api_key=self.api_key)
        self.model = config.get('name', 'claude-3-opus-20240229')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 1000)
        
    async def get_completion(self, prompt: str) -> str:
        """Get completion from Anthropic."""
        try:
            response = await self.client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    async def get_batch_completions(self, prompts: List[str]) -> List[str]:
        """Get batch completions from Anthropic."""
        tasks = [self.get_completion(prompt) for prompt in prompts]
        return await asyncio.gather(*tasks)


class MockClient(BaseAPIClient):
    """Mock client for testing."""
    
    def __init__(self, config: Dict[str, Any]):
        self.responses = [
            "I cannot and will not provide information on creating harmful content.",
            "I'd be happy to help with a safe and constructive alternative instead.",
            "That request goes against my safety guidelines.",
            "Here's a helpful response to your question: [safe content]",
            "I understand you're curious, but I can't assist with that particular request."
        ]
        self.response_index = 0
        
    async def get_completion(self, prompt: str) -> str:
        """Return mock response."""
        response = self.responses[self.response_index % len(self.responses)]
        self.response_index += 1
        await asyncio.sleep(0.1)  # Simulate API delay
        return response
    
    async def get_batch_completions(self, prompts: List[str]) -> List[str]:
        """Get batch mock responses."""
        return [await self.get_completion(p) for p in prompts]


class APIClient:
    """Factory class for creating API clients."""
    
    def __init__(self, config: Dict[str, Any]):
        provider = config.get('provider', 'mock').lower()
        
        if provider == 'openai':
            self.client = OpenAIClient(config)
        elif provider == 'anthropic':
            self.client = AnthropicClient(config)
        elif provider == 'mock':
            self.client = MockClient(config)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    async def get_completion(self, prompt: str) -> str:
        """Get completion from the configured provider."""
        return await self.client.get_completion(prompt)
    
    async def get_batch_completions(self, prompts: List[str]) -> List[str]:
        """Get batch completions from the configured provider."""
        return await self.client.get_batch_completions(prompts)


class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.call_times = []
        
    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = asyncio.get_event_loop().time()
        
        # Remove calls older than 1 minute
        self.call_times = [t for t in self.call_times if now - t < 60]
        
        if len(self.call_times) >= self.calls_per_minute:
            # Calculate wait time
            oldest_call = min(self.call_times)
            wait_time = 60 - (now - oldest_call) + 0.1
            await asyncio.sleep(wait_time)
        
        self.call_times.append(now)


class RetryHandler:
    """Handle retries for failed API calls."""
    
    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        
    async def retry_async(self, func, *args, **kwargs):
        """Retry an async function with exponential backoff."""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = self.backoff_factor ** attempt
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"All {self.max_retries} attempts failed")
        
        raise last_exception
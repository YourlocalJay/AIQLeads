from typing import Dict, List, Optional
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential
import redis
from prometheus_client import Counter, Histogram
from backend.config.ai_config import (
    get_ai_settings,
    MISTRAL_CHAT_PARAMS,
    ERROR_MESSAGES,
)

# Prometheus metrics
CHATBOT_REQUESTS = Counter("chatbot_requests_total", "Total chatbot requests")
CHATBOT_ERRORS = Counter("chatbot_errors_total", "Total chatbot errors")
RESPONSE_TIME = Histogram("chatbot_response_seconds", "Response time in seconds")


class ChatbotService:
    def __init__(self):
        self.settings = get_ai_settings()
        self.redis_client = redis.Redis.from_url(
            self.settings.REDIS_URL, decode_responses=True
        )

    async def _get_cached_response(self, query: str) -> Optional[str]:
        """Get cached response for a query."""
        if not self.settings.CACHE_ENABLED:
            return None
        cache_key = f"chatbot:response:{hash(query)}"
        return self.redis_client.get(cache_key)

    async def _cache_response(self, query: str, response: str) -> None:
        """Cache a chatbot response."""
        if not self.settings.CACHE_ENABLED:
            return
        cache_key = f"chatbot:response:{hash(query)}"
        self.redis_client.setex(cache_key, self.settings.MISTRAL_CACHE_TTL, response)

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _call_mistral_api(self, messages: List[Dict]) -> str:
        """Make API call to Mistral Small 3."""
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.settings.MISTRAL_API_KEY}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": self.settings.MISTRAL_MODEL_NAME,
                "messages": messages,
                **MISTRAL_CHAT_PARAMS,
            }

            async with session.post(
                f"{self.settings.MISTRAL_API_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                if response.status != 200:
                    error_data = await response.json()
                    raise Exception(f"Mistral API error: {error_data}")

                data = await response.json()
                return data["choices"][0]["message"]["content"]

    async def check_rate_limit(self) -> bool:
        """Check if we're within API rate limits."""
        date_key = "chatbot:daily_calls"
        current_calls = int(self.redis_client.get(date_key) or 0)
        return current_calls < self.settings.MAX_DAILY_API_CALLS

    async def increment_api_calls(self) -> None:
        """Increment the API call counter."""
        date_key = "chatbot:daily_calls"
        self.redis_client.incr(date_key)
        # Set expiry to ensure counter resets daily
        self.redis_client.expire(date_key, 86400)  # 24 hours

    async def get_response(
        self, query: str, context: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Get a response from the chatbot.

        Args:
            query: User's question
            context: Optional conversation history

        Returns:
            Dict containing response and metadata
        """
        CHATBOT_REQUESTS.inc()

        try:
            # Check rate limit
            if not await self.check_rate_limit():
                CHATBOT_ERRORS.inc()
                return {"error": ERROR_MESSAGES["rate_limit_exceeded"]}

            # Check cache first
            cached_response = await self._get_cached_response(query)
            if cached_response:
                return {"response": cached_response, "source": "cache"}

            # Prepare messages
            messages = context or []
            messages.append({"role": "user", "content": query})

            # Get response from Mistral
            with RESPONSE_TIME.time():
                response = await self._call_mistral_api(messages)

            # Cache the response
            await self._cache_response(query, response)

            # Increment API call counter
            await self.increment_api_calls()

            return {"response": response, "source": "api"}

        except Exception as e:
            CHATBOT_ERRORS.inc()
            return {"error": str(e), "message": ERROR_MESSAGES["model_error"]}

    async def reset_conversation(self) -> None:
        """Reset the conversation context."""
        # Implementation depends on how you're storing conversation history
        pass


# Singleton instance
chatbot_service = ChatbotService()

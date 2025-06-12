import sys
import asyncio
from functools import lru_cache
from typing import List, Tuple

from src.socket_instance import emit_agent
from .azure_openai_client import AzureOpenAI
from src.state import AgentState
from src.config import Config
from src.logger import Logger
from src.utils.token_tracker import TokenTracker
import logging
from datetime import datetime, timedelta

TIKTOKEN_ENC = tiktoken.get_encoding("cl100k_base")

logger = logging.getLogger(__name__)
agentState = AgentState()
config = Config()

class LLM:
    _cache = {}
    _rate_limit = {}
    _lock = asyncio.Lock()
    _config = Config()
    _token_tracker = TokenTracker()

    def __init__(self, model_id: str = None):
        self.model_id = model_id
        self.log_prompts = config.get_logging_prompts()
        self.timeout_inference = config.get_timeout_inference()
        self.rate_limit_config = self._config.get("server.rate_limit", {})
        self.requests_per_minute = self.rate_limit_config.get("requests_per_minute", 60)
        self.burst_size = self.rate_limit_config.get("burst_size", 10)
        self.models = {
            "AZURE_OPENAI": [
                ("GPT-4o", "gpt-4o"),
            ]
        }

    def list_models(self) -> dict:
        return self.models

    def model_enum(self, model_name: str) -> Tuple[str, str]:
        model_dict = {
            model[0]: (model_enum, model[1]) 
            for model_enum, models in self.models.items() 
            for model in models
        }
        return model_dict.get(model_name, (None, None))

    @staticmethod
    def update_global_token_usage(string: str, project_name: str):
        token_usage = len(TIKTOKEN_ENC.encode(string))
        agentState.update_token_usage(project_name, token_usage)

        total = agentState.get_latest_token_usage(project_name) + token_usage
        emit_agent("tokens", {"token_usage": total})

    async def inference(self, prompt: str, project_name: str) -> str:
        cache_key = (self.model_id, prompt)
        if cache_key in self._cache:
            logger.info(f"LLM cache hit for {cache_key}")
            return self._cache[cache_key]

        # Rate limiting
        now = datetime.utcnow()
        window = now.replace(second=0, microsecond=0)
        if self.model_id not in self._rate_limit:
            self._rate_limit[self.model_id] = {}
        if window not in self._rate_limit[self.model_id]:
            self._rate_limit[self.model_id][window] = 0
        if self._rate_limit[self.model_id][window] >= self.requests_per_minute:
            logger.warning(f"LLM rate limit exceeded for {self.model_id}")
            await asyncio.sleep(60)
        self._rate_limit[self.model_id][window] += 1

        # Error handling and retries
        max_retries = self._config.get("error_handling.max_retries", 3)
        retry_delay = self._config.get("error_handling.retry_delay", 2)
        backoff_factor = self._config.get("error_handling.backoff_factor", 2)
        attempt = 0
        while attempt < max_retries:
            try:
                model_enum, model_name = self.model_enum(self.model_id)
                if model_enum is None:
                    raise ValueError(f"Model {self.model_id} not supported")
                if model_enum == "AZURE_OPENAI":
                    client = AzureOpenAI()
                    response = await client.inference(model_name, prompt)
                else:
                    raise ValueError(f"Unsupported model enum: {model_enum}")
                # Token/cost tracking
                self._token_tracker.track_usage(self.model_id, prompt, response, {"project_name": project_name})
                self._cache[cache_key] = response
                return response
            except Exception as e:
                logger.error(f"LLM inference error: {str(e)} (attempt {attempt+1})")
                await asyncio.sleep(retry_delay * (backoff_factor ** attempt))
                attempt += 1
        raise RuntimeError(f"LLM inference failed after {max_retries} attempts")

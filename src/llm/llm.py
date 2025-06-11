import sys

import tiktoken
from typing import List, Tuple

from src.socket_instance import emit_agent
from .azure_openai_client import AzureOpenAI
from src.state import AgentState
from src.config import Config
from src.logger import Logger

TIKTOKEN_ENC = tiktoken.get_encoding("cl100k_base")

logger = Logger()
agentState = AgentState()
config = Config()

class LLM:
    def __init__(self, model_id: str = None):
        self.model_id = model_id
        self.log_prompts = config.get_logging_prompts()
        self.timeout_inference = config.get_timeout_inference()
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

    def inference(self, prompt: str, project_name: str) -> str:
        self.update_global_token_usage(prompt, project_name)

        model_enum, model_name = self.model_enum(self.model_id)
                
        print(f"Model: {self.model_id}, Enum: {model_enum}")
        if model_enum is None:
            raise ValueError(f"Model {self.model_id} not supported")

        if model_enum == "AZURE_OPENAI":
            client = AzureOpenAI()
            response = client.inference(model_name, prompt)
        else:
            raise ValueError(f"Unsupported model enum: {model_enum}")

        self.update_global_token_usage(response, project_name)
        return response

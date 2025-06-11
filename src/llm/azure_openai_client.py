from openai import AzureOpenAI
from src.config import Config
from src.logger import Logger

log = Logger()

class AzureOpenAI:
    def __init__(self):
        config = Config()
        self.api_key = config.get_openai_api_key()
        self.api_base = config.get_openai_api_base_url()
        self.api_version = "2024-02-15-preview"  # Latest stable version
        self.deployment_name = "gpt-4"  # Default deployment name
        
        try:
            self.client = AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.api_base
            )
            log.info("Azure OpenAI client initialized successfully")
        except Exception as e:
            log.error(f"Failed to initialize Azure OpenAI client: {str(e)}")
            raise

    def inference(self, model_id: str, prompt: str) -> str:
        try:
            chat_completion = self.client.chat.completions.create(
                model=model_id,
                messages=[
                    {
                        "role": "user",
                        "content": prompt.strip(),
                    }
                ],
                temperature=0
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            log.error(f"Error during Azure OpenAI inference: {str(e)}")
            raise 
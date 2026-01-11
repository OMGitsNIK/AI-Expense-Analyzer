from typing import Type, TypeVar
from pydantic import BaseModel
from openai import OpenAI
from .base import AIProvider
import config
import base64

T = TypeVar('T', bound=BaseModel)


class OpenRouterProvider(AIProvider):
    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config.OPENROUTER_API_KEY
        )
        # Pull model name from config just like OpenAIProvider
        self.model = config.MODELS["openrouter"]
    
    def extract_from_pdf(self, pdf_path: str, prompt: str, response_model: Type[T]) -> T:
        print(f"🔍 DEBUG: Using model: {self.model}")
        with open(pdf_path, "rb") as f:
            pdf_data = base64.b64encode(f.read()).decode("utf-8")
        
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:application/pdf;base64,{pdf_data}"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"}
        )
        
        # Validate into Pydantic model (same pattern)
        return response_model.model_validate_json(
            completion.choices[0].message.content
        )
    
    def get_provider_name(self) -> str:
        return "OpenRouter"

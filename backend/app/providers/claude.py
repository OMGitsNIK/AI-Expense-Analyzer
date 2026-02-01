from typing import Type, TypeVar
from pydantic import BaseModel
from anthropic import Anthropic
from .base import AIProvider
from app import config
import base64

T = TypeVar('T', bound=BaseModel)


class ClaudeProvider(AIProvider):
    def __init__(self):
        self.client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.model = config.MODELS["claude"]
    
    def extract_from_pdf(self, pdf_path: str, prompt: str, response_model: Type[T]) -> T:
        # Read and encode PDF
        with open(pdf_path, "rb") as f:
            pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")
        
        # Create message
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_data
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt + f"\n\nRespond with ONLY valid JSON matching this schema:\n{response_model.model_json_schema()}"
                    }
                ]
            }]
        )
        
        # Extract JSON from response
        json_text = response.content[0].text
        
        # Parse response
        return response_model.model_validate_json(json_text)
    
    def get_provider_name(self) -> str:
        return "Claude"

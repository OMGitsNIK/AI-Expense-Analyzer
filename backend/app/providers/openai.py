from typing import Type, TypeVar
from pydantic import BaseModel
from openai import OpenAI
from .base import AIProvider
from app import config
import base64

T = TypeVar('T', bound=BaseModel)


class OpenAIProvider(AIProvider):
    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.MODELS["openai"]
    
    def extract_from_pdf(self, pdf_path: str, prompt: str, response_model: Type[T]) -> T:
        # Read and encode PDF
        with open(pdf_path, "rb") as f:
            pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")
        
        # Create completion with structured output
        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:application/pdf;base64,{pdf_data}"
                            }
                        }
                    ]
                }
            ],
            response_format=response_model
        )
        
        return completion.choices[0].message.parsed
    
    def get_provider_name(self) -> str:
        return "OpenAI"

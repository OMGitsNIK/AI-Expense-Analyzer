from typing import Type, TypeVar
from pydantic import BaseModel
from google import genai
from .base import AIProvider
import config

T = TypeVar('T', bound=BaseModel)


class GeminiProvider(AIProvider):
    def __init__(self):
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.model = config.MODELS["gemini"]
    
    def extract_from_pdf(self, pdf_path: str, prompt: str, response_model: Type[T]) -> T:
        # Upload PDF
        pdf = self.client.files.upload(file=pdf_path)
        
        # Generate content
        response = self.client.models.generate_content(
            model=self.model,
            contents=[pdf, prompt],
            config={
                "response_mime_type": "application/json",
                "response_schema": response_model
            }
        )
        
        # Parse response
        return response_model.model_validate_json(response.text)
    
    def get_provider_name(self) -> str:
        return "Gemini"

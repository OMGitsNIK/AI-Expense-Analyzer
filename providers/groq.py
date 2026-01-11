from typing import Type, TypeVar
from pydantic import BaseModel
from groq import Groq
from .base import AIProvider
import config
import base64
import fitz  # PyMuPDF
import io
from PIL import Image

T = TypeVar('T', bound=BaseModel)


class GroqProvider(AIProvider):
    def __init__(self):
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.model = config.MODELS["groq"]
    
    def _pdf_to_images(self, pdf_path: str) -> list[str]:
        """Convert PDF pages to base64 images"""
        doc = fitz.open(pdf_path)
        images = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Render page to image (higher DPI for better OCR)
            pix = page.get_pixmap(dpi=200)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=95)
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            images.append(img_base64)
        
        doc.close()
        return images
    
    def extract_from_pdf(self, pdf_path: str, prompt: str, response_model: Type[T]) -> T:
        # Convert PDF to images
        print("   Converting PDF to images...")
        images = self._pdf_to_images(pdf_path)
        
        # Build content with all pages
        content = [
            {
                "type": "text",
                "text": prompt + f"\n\nRespond with ONLY valid JSON matching this schema:\n{response_model.model_json_schema()}"
            }
        ]
        
        # Add all page images
        for i, img_base64 in enumerate(images):
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img_base64}"
                }
            })
        
        # Create chat completion
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": content}],
            response_format={"type": "json_object"},
            temperature=0
        )
        
        # Parse response
        json_text = completion.choices[0].message.content
        return response_model.model_validate_json(json_text)
    
    def get_provider_name(self) -> str:
        return "Groq"

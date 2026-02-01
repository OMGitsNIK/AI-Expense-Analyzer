from abc import ABC, abstractmethod
from typing import TypeVar, Type
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)


class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    def extract_from_pdf(
        self, 
        pdf_path: str, 
        prompt: str, 
        response_model: Type[T]
    ) -> T:
        """
        Extract structured data from PDF
        
        Args:
            pdf_path: Path to PDF file
            prompt: Extraction prompt
            response_model: Pydantic model for response
            
        Returns:
            Parsed response matching response_model
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return provider name for logging"""
        pass

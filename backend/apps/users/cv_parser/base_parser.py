"""
Base Parser Interface
=====================
backend/apps/users/cv_parser/base_parser.py

Abstract base class for CV parsers.
"""

from abc import ABC, abstractmethod
from typing import Optional


class BaseParser(ABC):
    """
    Abstract base class for CV file parsers.
    
    Each parser implements text extraction for specific file format.
    """
    
    @abstractmethod
    def parse(self, file_path: str) -> Optional[str]:
        """
        Extract text from CV file.
        
        Args:
            file_path: Absolute path to CV file
        
        Returns:
            Extracted text or None if extraction fails
        """
        pass
    
    @abstractmethod
    def validate(self, file_path: str) -> bool:
        """
        Validate if file can be parsed.
        
        Args:
            file_path: Absolute path to CV file
        
        Returns:
            True if file is valid, False otherwise
        """
        pass
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean extracted text.
        
        - Remove extra whitespace
        - Normalize line breaks
        - Remove special characters
        """
        if not text:
            return ""
        
        # Replace multiple spaces with single space
        text = ' '.join(text.split())
        
        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove multiple newlines
        while '\n\n\n' in text:
            text = text.replace('\n\n\n', '\n\n')
        
        return text.strip()
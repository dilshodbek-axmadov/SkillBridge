"""
PDF Parser
==========
backend/apps/users/cv_parser/pdf_parser.py

Extract text from PDF files using PyPDF2 and pdfplumber.
"""

import logging
from pathlib import Path
from typing import Optional

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class PDFParser(BaseParser):
    """
    Parse PDF files and extract text.
    
    Uses two methods:
    1. PyPDF2 - Fast, simple extraction
    2. pdfplumber - Better for complex layouts
    """
    
    def parse(self, file_path: str) -> Optional[str]:
        """
        Extract text from PDF file.
        
        Tries PyPDF2 first, falls back to pdfplumber if needed.
        """
        try:
            # Try PyPDF2 first (faster)
            text = self._parse_with_pypdf2(file_path)
            
            # If extraction is poor, try pdfplumber
            if not text or len(text.strip()) < 100:
                logger.info("PyPDF2 extraction poor, trying pdfplumber")
                text = self._parse_with_pdfplumber(file_path)
            
            return self.clean_text(text) if text else None
        
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            return None
    
    def _parse_with_pypdf2(self, file_path: str) -> Optional[str]:
        """Extract text using PyPDF2."""
        try:
            from PyPDF2 import PdfReader
            
            reader = PdfReader(file_path)
            text_parts = []
            
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            return '\n'.join(text_parts)
        
        except ImportError:
            logger.error("PyPDF2 not installed. Run: pip install PyPDF2")
            return None
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {e}")
            return None
    
    def _parse_with_pdfplumber(self, file_path: str) -> Optional[str]:
        """Extract text using pdfplumber (better for tables/layout)."""
        try:
            import pdfplumber
            
            text_parts = []
            
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    # Extract text
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                    
                    # Extract tables
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            if row:
                                row_text = ' | '.join([cell for cell in row if cell])
                                text_parts.append(row_text)
            
            return '\n'.join(text_parts)
        
        except ImportError:
            logger.error("pdfplumber not installed. Run: pip install pdfplumber")
            return None
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}")
            return None
    
    def validate(self, file_path: str) -> bool:
        """Validate PDF file."""
        try:
            path = Path(file_path)
            
            # Check file exists
            if not path.exists():
                return False
            
            # Check extension
            if path.suffix.lower() != '.pdf':
                return False
            
            # Check file size (max 5MB)
            if path.stat().st_size > 5 * 1024 * 1024:
                logger.warning("PDF file too large (>5MB)")
                return False
            
            # Try to open with PyPDF2
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(file_path)
                
                # Check if PDF has pages
                if len(reader.pages) == 0:
                    logger.warning("PDF has no pages")
                    return False
                
                return True
            
            except Exception as e:
                logger.error(f"PDF validation failed: {e}")
                return False
        
        except Exception as e:
            logger.error(f"Error validating PDF: {e}")
            return False
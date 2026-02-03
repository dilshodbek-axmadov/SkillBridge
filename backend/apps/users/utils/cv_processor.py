"""
CV Processor with Hybrid Extraction
====================================
backend/apps/users/utils/cv_processor.py

REPLACE your current cv_processor.py with this file.
"""

import logging
from pathlib import Path
from typing import Dict, Optional

from apps.users.cv_parser.pdf_parser import PDFParser
from apps.users.cv_parser.docx_parser import DOCXParser
from apps.users.cv_parser.hybrid_ollama_extractor import HybridOllamaExtractor
from apps.users.cv_parser.skill_matcher import SkillMatcher

logger = logging.getLogger(__name__)


class CVProcessor:
    """Process CV files with hybrid extraction (NLP → Ollama)."""
    
    def __init__(
        self,
        use_ollama_fallback: bool = True,
        quality_threshold: float = 0.6,
        ai_first_mode: bool = True
    ):
        self.pdf_parser = PDFParser()
        self.docx_parser = DOCXParser()
        self.extractor = HybridOllamaExtractor(
            use_ollama_fallback=use_ollama_fallback,
            quality_threshold=quality_threshold,
            ai_first_mode=ai_first_mode
        )
        self.skill_matcher = SkillMatcher(fuzzy_threshold=85, auto_create=True)
    
    def process(self, file_path: str) -> Dict:
        """Process CV file and return extracted data."""
        errors = []
        
        try:
            # Parse file
            cv_text = self._parse_file(file_path)
            if not cv_text:
                errors.append("Failed to extract text")
                return {'success': False, 'data': None, 'errors': errors}
            
            # Extract data
            extracted_data = self.extractor.extract_all(cv_text)
            
            # Match skills
            skill_names = extracted_data.get('skills', [])
            skill_matches = self.skill_matcher.match_skills(skill_names)
            skill_ids = [m['skill_id'] for m in skill_matches]
            
            # Build result
            result_data = {
                'job_position': extracted_data.get('job_position', ''),
                'skills': skill_ids,
                'years_of_experience': extracted_data.get('years_of_experience', 0.0),
                'experience_level': extracted_data.get('experience_level', 'beginner'),
                'education': extracted_data.get('education', ''),
                'email': extracted_data.get('email', ''),
                'phone': extracted_data.get('phone', ''),
                'bio': extracted_data.get('bio', ''),
                'location': extracted_data.get('location', ''),
                'github_url': extracted_data.get('github_url', ''),
                'linkedin_url': extracted_data.get('linkedin_url', ''),
                'raw_text': cv_text[:1000],
                'skill_matches': skill_matches,
                '_extraction_method': extracted_data.get('_extraction_method', 'unknown'),
                '_quality_score': extracted_data.get('_quality_score', 0.0),
                '_processing_time': extracted_data.get('_processing_time', 0.0)
            }
            
            logger.info(f"✅ Processed: {result_data['job_position']}, "
                       f"{len(skill_matches)} skills, "
                       f"{result_data['_extraction_method']} method")
            
            return {'success': True, 'data': result_data, 'errors': []}
        
        except Exception as e:
            logger.error(f"❌ Error: {e}", exc_info=True)
            return {'success': False, 'data': None, 'errors': [str(e)]}
    
    def _parse_file(self, file_path: str) -> Optional[str]:
        """Parse file based on extension."""
        path = Path(file_path)
        ext = path.suffix.lower()
        
        if ext == '.pdf':
            return self.pdf_parser.parse(file_path)
        elif ext in ['.docx', '.doc']:
            return self.docx_parser.parse(file_path)
        return None
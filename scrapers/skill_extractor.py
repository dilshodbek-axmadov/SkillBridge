"""
Extract skills from job descriptions
"""
import re
from .config import IT_SKILLS_KEYWORDS


class SkillExtractor:
    """
    Extract IT skills from job descriptions
    """
    
    def __init__(self):
        # Compile regex patterns for better performance
        self.skill_patterns = self._compile_patterns()
    
    def _compile_patterns(self):
        """
        Create regex patterns for each skill keyword
        """
        patterns = {}
        for skill in IT_SKILLS_KEYWORDS:
            # Case-insensitive pattern with word boundaries
            pattern = re.compile(r'\b' + re.escape(skill) + r'\b', re.IGNORECASE)
            patterns[skill] = pattern
        return patterns
    
    def extract_from_text(self, text):
        """
        Extract skills from text (job description)
        
        Returns: list of unique skills found
        """
        if not text:
            return []
        
        # Convert to lowercase for matching
        text_lower = text.lower()
        
        found_skills = []
        
        for skill, pattern in self.skill_patterns.items():
            if pattern.search(text_lower):
                found_skills.append(skill)
        
        return list(set(found_skills))  # Remove duplicates
    
    def extract_from_key_skills(self, key_skills):
        """
        Extract skills from API key_skills array
        
        key_skills format: [{"name": "Python"}, {"name": "Django"}]
        """
        if not key_skills:
            return []
        
        skills = []
        for skill_obj in key_skills:
            if isinstance(skill_obj, dict):
                skill_name = skill_obj.get('name', '').strip()
                if skill_name:
                    skills.append(skill_name.lower())
            elif isinstance(skill_obj, str):
                skills.append(skill_obj.strip().lower())
        
        return list(set(skills))
    
    def extract_all_skills(self, vacancy_data):
        """
        Extract skills from both key_skills and description
        
        Returns: dict with 'from_api' and 'from_description' skills
        """
        # Skills from API key_skills field
        api_skills = self.extract_from_key_skills(
            vacancy_data.get('key_skills', [])
        )
        
        # Skills from description text
        description = vacancy_data.get('description', '')
        desc_skills = self.extract_from_text(description)
        
        # Combine all skills
        all_skills = list(set(api_skills + desc_skills))
        
        return {
            'from_api': api_skills,
            'from_description': desc_skills,
            'all_skills': all_skills
        }
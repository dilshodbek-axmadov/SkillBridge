"""
Enhanced Skill Extractor
========================
backend/apps/jobs/scrapers/enhanced_skill_extractor.py

Extracts skills from job postings with hybrid approach.
Creates canonical skills and aliases automatically.
"""

import re
import json
import logging
from typing import List, Dict
from collections import Counter

logger = logging.getLogger(__name__)


class EnhancedSkillExtractor:
    """
    Hybrid skill extractor:
    1. Try key_skills field first (official)
    2. If empty, extract from description using LLM or regex
    3. Return skill data ready for Skill/SkillAlias creation
    """
    
    def __init__(self, use_ollama: bool = False):
        """
        Initialize extractor.
        
        Args:
            use_ollama: Whether to use Ollama for extraction
        """
        self.use_ollama = use_ollama
        self.skill_frequency = Counter()
        
        # Common IT skills patterns for regex fallback
        self.skill_patterns = {
            'programming': r'\b(Python|Java|JavaScript|TypeScript|C\+\+|C#|PHP|Ruby|Go|Rust|Swift|Kotlin|Scala)\b',
            'frameworks': r'\b(React|Vue|Angular|Django|Flask|FastAPI|Spring|Laravel|Express|Node\.?js|Next\.?js)\b',
            'databases': r'\b(SQL|PostgreSQL|MySQL|MongoDB|Redis|Elasticsearch|Oracle|MS SQL|SQLite)\b',
            'bi_tools': r'\b(Power BI|Tableau|Superset|MetaBase|Looker|QlikView|GA4|Firebase)\b',
            'cloud': r'\b(AWS|Azure|GCP|DigitalOcean|Heroku|Docker|Kubernetes)\b',
            'tools': r'\b(Git|Linux|Nginx|RabbitMQ|Celery|Kafka|Airflow|Jenkins)\b',
        }
    
    def extract_skills_from_vacancy(self, vacancy_data: Dict) -> List[Dict]:
        """
        Main extraction method - hybrid approach.
        
        Returns list of dicts ready for database:
        [
            {
                'skill_text': 'Python',
                'language_code': 'en',
                'importance': 'core',
                'source': 'key_skills'
            },
            ...
        ]
        """
        
        # Step 1: Try key_skills field
        key_skills = self._extract_from_key_skills(vacancy_data)
        
        # Step 2: If empty, extract from description
        if not key_skills:
            logger.debug(f"key_skills empty for {vacancy_data.get('id')}, using description")
            return self._extract_from_description(vacancy_data)
        
        # Step 3: If key_skills is minimal, combine both
        elif len(key_skills) < 3:
            description_skills = self._extract_from_description(vacancy_data)
            return self._merge_skills(key_skills, description_skills)
        
        return key_skills
    
    def _extract_from_key_skills(self, vacancy_data: Dict) -> List[Dict]:
        """Extract from key_skills field (official)."""
        key_skills = vacancy_data.get('key_skills', [])
        
        if not key_skills:
            return []
        
        extracted = []
        for skill_obj in key_skills:
            skill_name = skill_obj.get('name', '').strip()
            if skill_name:
                extracted.append({
                    'skill_text': skill_name,
                    'language_code': self._detect_language(skill_name),
                    'importance': 'core',
                    'source': 'key_skills',
                })
        
        logger.debug(f"Extracted {len(extracted)} skills from key_skills")
        return extracted
    
    def _extract_from_description(self, vacancy_data: Dict) -> List[Dict]:
        """Extract from description using LLM or regex."""
        # Combine text fields
        text_parts = []
        
        if vacancy_data.get('name'):
            text_parts.append(vacancy_data['name'])
        
        if vacancy_data.get('description'):
            desc = self._strip_html(vacancy_data['description'])
            text_parts.append(desc)
        
        full_text = ' '.join(text_parts)
        
        if not full_text.strip():
            return []
        
        # Try LLM extraction
        if self.use_ollama:
            try:
                skills = self._extract_with_llm(full_text)
                if skills:
                    return skills
            except Exception as e:
                logger.warning(f"LLM extraction failed: {e}, falling back to regex")
        
        # Fallback: regex extraction
        return self._extract_with_regex(full_text)
    
    def _extract_with_llm(self, text: str) -> List[Dict]:
        """Extract skills using Ollama LLM."""
        from core.ai.ollama_client import OllamaClient
        
        ollama = OllamaClient()
        
        # Use the extract_skills method
        skill_names = ollama.extract_skills(text)
        
        if not skill_names:
            return []
        
        # Format results
        extracted = []
        for skill_name in skill_names:
            if skill_name and isinstance(skill_name, str):
                extracted.append({
                    'skill_text': skill_name.strip(),
                    'language_code': self._detect_language(skill_name),
                    'importance': 'secondary',
                    'source': 'description_llm',
                })
        
        logger.debug(f"LLM extracted {len(extracted)} skills")
        return extracted
    
    def _extract_with_regex(self, text: str) -> List[Dict]:
        """Extract skills using regex patterns (fallback)."""
        found_skills = set()
        
        for category, pattern in self.skill_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            found_skills.update(match.strip() for match in matches)
        
        extracted = []
        for skill in found_skills:
            extracted.append({
                'skill_text': skill,
                'language_code': self._detect_language(skill),
                'importance': 'secondary',
                'source': 'description_regex',
            })
        
        logger.debug(f"Regex extracted {len(extracted)} skills")
        return extracted
    
    def _merge_skills(self, skills1: List[Dict], skills2: List[Dict]) -> List[Dict]:
        """Merge two skill lists, removing duplicates."""
        seen = set()
        merged = []
        
        # Add all skills, deduplicating by normalized text
        for skill in skills1 + skills2:
            normalized = skill['skill_text'].lower().strip()
            if normalized not in seen:
                seen.add(normalized)
                merged.append(skill)
        
        return merged
    
    def _detect_language(self, text: str) -> str:
        """
        Detect language from text.
        
        Returns:
            'ru', 'uz', or 'en'
        """
        if not text:
            return 'en'
        
        # Check for Cyrillic characters
        cyrillic_count = sum(1 for c in text if 0x0400 <= ord(c) <= 0x04FF)
        
        if cyrillic_count > 0:
            # Could be Russian or Uzbek, default to Russian
            return 'ru'
        
        return 'en'
    
    def _strip_html(self, html_text: str) -> str:
        """Remove HTML tags."""
        if not html_text:
            return ""
        text = re.sub(r'<[^>]+>', ' ', html_text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def track_skill_frequency(self, skill_text: str):
        """Track skill frequency for demand analysis."""
        normalized = skill_text.lower().strip()
        self.skill_frequency[normalized] += 1
    
    def get_skill_stats(self) -> Dict:
        """Get skill extraction statistics."""
        return {
            'unique_skills': len(self.skill_frequency),
            'total_mentions': sum(self.skill_frequency.values()),
            'top_skills': self.skill_frequency.most_common(20),
        }


def categorize_skill(skill_text: str) -> str:
    """
    Auto-categorize skill based on name.
    
    Args:
        skill_text: Skill name
    
    Returns:
        Category: programming/framework/database/tool/etc
    """
    skill_lower = skill_text.lower()
    
    # Programming languages
    programming = ['python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'csharp',
                   'php', 'ruby', 'go', 'rust', 'swift', 'kotlin', 'scala', 'r']
    if skill_lower in programming:
        return 'programming'
    
    # Frameworks
    frameworks = ['django', 'flask', 'fastapi', 'react', 'vue', 'angular', 'spring',
                  'laravel', 'express', 'nodejs', 'nextjs', 'nuxt']
    if skill_lower in frameworks or 'framework' in skill_lower:
        return 'framework'
    
    # Databases
    if any(db in skill_lower for db in ['sql', 'postgres', 'mysql', 'mongodb', 'redis',
                                          'oracle', 'cassandra', 'elasticsearch', 'database', 'mariadb', 'couchdb', 'dynomodb']):
        return 'database'
    
    # Cloud
    if skill_lower in ['aws', 'azure', 'gcp', 'digitalocean', 'heroku']:
        return 'cloud'
    
    # BI Tools
    if any(bi in skill_lower for bi in ['power bi', 'tableau', 'superset', 'metabase',
                                          'looker', 'qlik', 'bi']):
        return 'tool'
    
    # Tools
    tools = ['git', 'docker', 'kubernetes', 'jenkins', 'nginx', 'apache', 'kafka',
             'airflow', 'celery', 'rabbitmq']
    if skill_lower in tools:
        return 'tool'
    
    # Methodologies
    if skill_lower in ['oop', 'ооп', 'agile', 'scrum', 'devops', 'ci/cd', 'tdd']:
        return 'methodology'
    
    # Soft skills
    soft_skills = ['leadership', 'communication', 'teamwork', 'problem solving']
    if any(soft in skill_lower for soft in soft_skills):
        return 'soft_skill'
    
    return 'other'
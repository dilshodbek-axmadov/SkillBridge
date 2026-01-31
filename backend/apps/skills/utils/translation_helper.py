"""
Translation Helper (FIXED - Hashed Cache Keys)
===============================================
backend/apps/skills/utils/translation_helper.py

Translates skill names from RU/UZ to English using dictionary + AI fallback.
Uses hashed cache keys to avoid memcached warnings with Cyrillic characters.
"""

import logging
import hashlib
from typing import Optional, Dict
from django.core.cache import cache

logger = logging.getLogger(__name__)


# Common IT skill translations (RU → EN)
SKILL_TRANSLATION_DICT = {
    'ru': {
        # Programming Languages
        'питон': 'python',
        'джава': 'java',
        'джаваскрипт': 'javascript',
        'си': 'c',
        'си плюс плюс': 'c++',
        'си шарп': 'c#',
        'пхп': 'php',
        'руби': 'ruby',
        'го': 'go',
        'свифт': 'swift',
        'котлин': 'kotlin',
        
        # Methodologies
        'ооп': 'oop',
        'объектно-ориентированное программирование': 'object-oriented programming',
        'функциональное программирование': 'functional programming',
        
        # Databases
        'sql': 'sql',
        'база данных': 'database',
        'реляционная база данных': 'relational database',
        'нереляционная база данных': 'nosql database',
        'postgresql': 'postgresql',
        'mysql': 'mysql',
        'mongodb': 'mongodb',
        'redis': 'redis',
        
        # Frameworks
        'джанго': 'django',
        'фласк': 'flask',
        'реакт': 'react',
        'вью': 'vue',
        'ангуляр': 'angular',
        
        # Tools
        'гит': 'git',
        'докер': 'docker',
        'кубернетес': 'kubernetes',
        'линукс': 'linux',
        
        # Cloud
        'облако': 'cloud',
        'облачные технологии': 'cloud technologies',
        
        # Soft Skills
        'коммуникация': 'communication',
        'лидерство': 'leadership',
        'командная работа': 'teamwork',
        'аналитическое мышление': 'analytical thinking',
        'решение проблем': 'problem solving',
        'управление временем': 'time management',
        'критическое мышление': 'critical thinking',
        
        # Business Analysis
        'бизнес-анализ': 'business analysis',
        'анализ требований': 'requirements analysis',
        'управление проектами': 'project management',
        'agile': 'agile',
        'scrum': 'scrum',
        
        # Other
        'английский язык': 'english',
        'русский язык': 'russian',
        'узбекский язык': 'uzbek',
        'опыт работы': 'work experience',
        'высшее образование': 'higher education',
    },
    'uz': {
        # Uzbek translations (Latin script)
        'python': 'python',
        'java': 'java',
        'javascript': 'javascript',
        'dasturlash': 'programming',
        'ma\'lumotlar bazasi': 'database',
        'tillar': 'languages',
        'ko\'nikmalar': 'skills',
        'talablar': 'requirements',
        'majburiyatlar': 'responsibilities',
    }
}


class TranslationHelper:
    """
    Helper for translating skill names to English.
    Uses hashed cache keys to avoid memcached issues.
    """
    
    def __init__(self, use_ai: bool = True):
        """
        Initialize translation helper.
        
        Args:
            use_ai: Whether to use AI for unknown translations
        """
        self.use_ai = use_ai
        self.ollama_client = None
        self.cache_timeout = 86400  # 24 hours
    
    def _make_cache_key(self, language: str, text: str) -> str:
        """
        Create a safe cache key using hash for non-ASCII text.
        
        This prevents memcached warnings about invalid characters.
        
        Args:
            language: Language code
            text: Text to cache
        
        Returns:
            Safe cache key string
        """
        # Create a hash of the text to avoid special characters in cache key
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        return f"skill_trans_{language}_{text_hash}"
    
    def translate_to_english(
        self,
        text: str,
        source_language: str
    ) -> Optional[str]:
        """
        Translate skill name to English.
        
        Strategy:
        1. Check cache
        2. Try dictionary lookup
        3. If not found and use_ai=True, use Ollama
        4. Cache result
        
        Args:
            text: Skill text to translate
            source_language: 'ru' or 'uz'
        
        Returns:
            English translation or None
        """
        if not text or source_language == 'en':
            return text
        
        # Normalize
        text_lower = text.lower().strip()
        
        # Check cache (use hashed key for safety)
        cache_key = self._make_cache_key(source_language, text_lower)
        cached = cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit: {text} → {cached}")
            return cached
        
        # Try dictionary
        translation = self._dictionary_lookup(text_lower, source_language)
        
        if translation:
            logger.debug(f"Dictionary: {text} → {translation}")
            cache.set(cache_key, translation, self.cache_timeout)
            return translation
        
        # Try AI
        if self.use_ai:
            translation = self._ai_translate(text, source_language)
            
            if translation:
                logger.debug(f"AI: {text} → {translation}")
                cache.set(cache_key, translation, self.cache_timeout)
                return translation
        
        # Fallback: return original
        logger.warning(f"No translation found for: {text} ({source_language})")
        return text
    
    def _dictionary_lookup(self, text: str, source_language: str) -> Optional[str]:
        """
        Look up translation in dictionary.
        
        Args:
            text: Lowercase skill text
            source_language: 'ru' or 'uz'
        
        Returns:
            English translation or None
        """
        if source_language not in SKILL_TRANSLATION_DICT:
            return None
        
        translations = SKILL_TRANSLATION_DICT[source_language]
        return translations.get(text)
    
    def _ai_translate(self, text: str, source_language: str) -> Optional[str]:
        """
        Translate using Ollama AI.
        
        Args:
            text: Skill text
            source_language: 'ru' or 'uz'
        
        Returns:
            English translation or None
        """
        try:
            if self.ollama_client is None:
                from core.ai.ollama_client import OllamaClient
                self.ollama_client = OllamaClient()
            
            # Create translation prompt
            lang_name = 'Russian' if source_language == 'ru' else 'Uzbek'
            
            prompt = f"""Translate this {lang_name} skill/technology name to English.

{lang_name} skill: {text}

IMPORTANT RULES:
- Return ONLY the English translation
- Use standard IT terminology
- Keep it SHORT (1-3 words maximum)
- If it's already a technical term (SQL, Git, etc.), return it unchanged
- If it's a soft skill, translate literally
- Do NOT add explanations or extra text

English translation:"""
            
            response = self.ollama_client.generate(
                prompt=prompt,
                max_tokens=50,
                temperature=0.1
            )
            
            # Clean response
            translation = response.strip().lower()
            
            # Remove common AI verbosity
            translation = translation.replace('english translation:', '')
            translation = translation.replace('translation:', '')
            translation = translation.strip()
            
            # Validate (should be short)
            if len(translation.split()) > 5:
                logger.warning(f"AI translation too long: {translation}")
                return None
            
            return translation
        
        except Exception as e:
            logger.error(f"AI translation failed for '{text}': {e}")
            return None
    
    def batch_translate(
        self,
        texts: list,
        source_language: str
    ) -> Dict[str, str]:
        """
        Translate multiple texts at once.
        
        Args:
            texts: List of skill texts
            source_language: 'ru' or 'uz'
        
        Returns:
            Dict mapping original → translation
        """
        results = {}
        
        for text in texts:
            translation = self.translate_to_english(text, source_language)
            if translation:
                results[text] = translation
        
        return results
    
    def add_custom_translation(
        self,
        source_text: str,
        source_language: str,
        english_translation: str
    ):
        """
        Add a custom translation to cache (not permanent).
        
        Args:
            source_text: Original text
            source_language: 'ru' or 'uz'
            english_translation: English translation
        """
        cache_key = self._make_cache_key(source_language, source_text.lower())
        cache.set(cache_key, english_translation.lower(), self.cache_timeout * 7)  # 1 week
        logger.info(f"Added custom translation: {source_text} → {english_translation}")
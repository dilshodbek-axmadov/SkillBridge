"""
Skill Resolver (Phase B: Resolution)
=====================================
backend/apps/skills/utils/skill_resolver.py

Resolves unresolved skill aliases to canonical skills.

Workflow:
1. Get unresolved aliases
2. Translate RU/UZ → EN
3. Normalize English name
4. Try to match existing skill
5. If no match, create new canonical skill
6. Link alias to skill
"""

import logging
from typing import Optional, Tuple, Dict
from decimal import Decimal
from django.db import transaction
from fuzzywuzzy import fuzz  # or use rapidfuzz
from apps.skills.models import Skill, SkillAlias
from apps.skills.utils.translation_helper import TranslationHelper
from apps.jobs.scrapers.enhanced_skill_extractor import categorize_skill

logger = logging.getLogger(__name__)


class SkillResolver:
    """
    Resolves skill aliases to canonical skills.
    """
    
    def __init__(
        self,
        auto_resolve_threshold: float = 0.95,
        fuzzy_match_threshold: float = 0.85,
        use_ai_translation: bool = True
    ):
        """
        Initialize resolver.
        
        Args:
            auto_resolve_threshold: Confidence threshold for auto-resolution (0.95 = 95%)
            fuzzy_match_threshold: Minimum similarity for fuzzy matching (0.85 = 85%)
            use_ai_translation: Whether to use AI for translation
        """
        self.auto_resolve_threshold = auto_resolve_threshold
        self.fuzzy_match_threshold = fuzzy_match_threshold
        
        self.translator = TranslationHelper(use_ai=use_ai_translation)
        
        self.stats = {
            'total_unresolved': 0,
            'auto_resolved': 0,
            'needs_review': 0,
            'new_skills_created': 0,
            'rejected': 0,
            'errors': 0,
        }
    
    def resolve_all_unresolved(self, limit: Optional[int] = None) -> Dict:
        """
        Resolve all unresolved aliases.
        
        Args:
            limit: Maximum number to resolve (None = all)
        
        Returns:
            Statistics dict
        """
        logger.info("Starting skill resolution...")
        
        # Get unresolved aliases
        unresolved_aliases = SkillAlias.objects.filter(
            status='unresolved'
        ).order_by('-usage_count')  # Process most common first
        
        if limit:
            unresolved_aliases = unresolved_aliases[:limit]
        
        self.stats['total_unresolved'] = unresolved_aliases.count()
        
        logger.info(f"Found {self.stats['total_unresolved']} unresolved aliases")
        
        # Resolve each alias
        for i, alias in enumerate(unresolved_aliases, 1):
            try:
                if i % 100 == 0:
                    logger.info(f"Progress: {i}/{self.stats['total_unresolved']}")
                
                result = self.resolve_single_alias(alias)
                self.stats[result] += 1
            
            except Exception as e:
                logger.error(f"Error resolving alias {alias.alias_id}: {e}")
                self.stats['errors'] += 1
        
        return self.stats
    
    def resolve_single_alias(self, alias: SkillAlias) -> str:
        """
        Resolve one alias to a canonical skill.
        
        Returns:
            'auto_resolved' | 'needs_review' | 'new_skills_created' | 'rejected'
        """
        import sys
        
        # Step 1: Get English candidate
        candidate_en = self._get_english_candidate(alias)
        
        if not candidate_en or len(candidate_en.strip()) < 2:
            # Reject very short or empty
            alias.status = 'rejected'
            alias.save()
            return 'rejected'
        
        # Step 2: Normalize
        normalized = Skill.normalize_key(candidate_en)
        
        # Step 3: Check blacklist (generic terms)
        if self._is_generic_term(normalized):
            alias.status = 'rejected'
            alias.save()
            return 'rejected'
        
        # Step 4: Try exact match
        existing_skill = self._find_existing_skill_exact(normalized)
        
        if existing_skill:
            return self._link_alias_to_skill(
                alias,
                existing_skill,
                confidence=Decimal('1.00'),
                method='exact_match'
            )
        
        # Step 5: Try fuzzy match
        fuzzy_result = self._find_existing_skill_fuzzy(candidate_en)
        
        if fuzzy_result:
            skill, confidence = fuzzy_result
            
            if confidence >= self.auto_resolve_threshold:
                # High confidence - auto resolve
                return self._link_alias_to_skill(
                    alias,
                    skill,
                    confidence=Decimal(str(confidence)),
                    method='fuzzy_match'
                )
            else:
                # Medium confidence - needs review
                alias.skill = skill
                alias.status = 'needs_review'
                alias.confidence = Decimal(str(confidence))
                alias.save()
                return 'needs_review'
        
        # Step 6: Create new canonical skill
        new_skill = self._create_canonical_skill(
            name_en=candidate_en,
            name_ru=alias.alias_text if alias.language_code == 'ru' else None,
            name_uz=alias.alias_text if alias.language_code == 'uz' else None
        )
        
        return self._link_alias_to_skill(
            alias,
            new_skill,
            confidence=Decimal('1.00'),
            method='new_skill',
            is_new=True
        )
    
    def _get_english_candidate(self, alias: SkillAlias) -> Optional[str]:
        """
        Get English candidate name for alias.
        
        If already English, use as-is.
        If RU/UZ, translate to English.
        """
        if alias.language_code == 'en':
            return alias.alias_text
        
        # Translate to English
        translation = self.translator.translate_to_english(
            alias.alias_text,
            alias.language_code
        )
        
        return translation
    
    def _find_existing_skill_exact(self, normalized_key: str) -> Optional[Skill]:
        """
        Find skill by exact normalized match.
        """
        return Skill.objects.filter(normalized_key=normalized_key).first()
    
    def _find_existing_skill_fuzzy(
        self,
        candidate_en: str
    ) -> Optional[Tuple[Skill, float]]:
        """
        Find skill using fuzzy string matching.
        
        Returns:
            (Skill, confidence_score) or None
        """
        # Get all skills for comparison
        all_skills = Skill.objects.all()
        
        best_match = None
        best_score = 0.0
        
        candidate_lower = candidate_en.lower()
        
        for skill in all_skills:
            # Compare with name_en
            ratio = fuzz.ratio(candidate_lower, skill.name_en.lower()) / 100.0
            
            # Also check partial ratio (handles substrings)
            partial_ratio = fuzz.partial_ratio(candidate_lower, skill.name_en.lower()) / 100.0
            
            # Use best of the two
            score = max(ratio, partial_ratio)
            
            if score > best_score:
                best_score = score
                best_match = skill
        
        # Only return if above threshold
        if best_score >= self.fuzzy_match_threshold:
            return (best_match, best_score)
        
        return None
    
    def _create_canonical_skill(
        self,
        name_en: str,
        name_ru: Optional[str] = None,
        name_uz: Optional[str] = None
    ) -> Skill:
        """
        Create new canonical skill.
        """
        # Capitalize properly
        name_en_clean = self._capitalize_skill_name(name_en)
        
        # Auto-categorize
        category = categorize_skill(name_en_clean)
        
        skill = Skill.objects.create(
            name_en=name_en_clean,
            name_ru=name_ru,
            name_uz=name_uz,
            category=category,
            is_verified=False
        )
        
        logger.info(f"  + Created skill: {name_en_clean} ({category})")
        
        return skill
    
    def _link_alias_to_skill(
        self,
        alias: SkillAlias,
        skill: Skill,
        confidence: Decimal,
        method: str,
        is_new: bool = False
    ) -> str:
        """
        Link alias to canonical skill.
        """
        alias.skill = skill
        alias.status = 'resolved'
        alias.confidence = confidence
        alias.save()
        
        if is_new:
            logger.debug(f"  + Linked to NEW skill: {skill.name_en}")
            return 'new_skills_created'
        else:
            logger.debug(f"  ✓ Linked to existing: {skill.name_en} ({method}, conf={confidence})")
            return 'auto_resolved'
    
    def _capitalize_skill_name(self, name: str) -> str:
        """
        Capitalize skill name properly.
        
        Examples:
            'python' → 'Python'
            'sql' → 'SQL'
            'c++' → 'C++'
            'node.js' → 'Node.js'
        """
        name = name.strip()
        
        # All caps for known acronyms
        all_caps = ['sql', 'api', 'rest', 'json', 'xml', 'html', 'css', 'oop', 'crm', 'erp']
        if name.lower() in all_caps:
            return name.upper()
        
        # Special cases
        if name.lower() == 'c++':
            return 'C++'
        if name.lower() == 'c#':
            return 'C#'
        if name.lower().startswith('node'):
            return 'Node.js'
        if name.lower().startswith('react'):
            return 'React' if name.lower() == 'react' else 'React.js'
        if name.lower().startswith('vue'):
            return 'Vue' if name.lower() == 'vue' else 'Vue.js'
        
        # Title case for multi-word
        if ' ' in name:
            return name.title()
        
        # Capitalize first letter for single words
        return name.capitalize()
    
    def _is_generic_term(self, normalized: str) -> bool:
        """
        Check if skill is too generic to be useful.
        
        Generic terms should be rejected.
        """
        generic_terms = {
            'communication',
            'teamwork',
            'leadership',
            'work',
            'experience',
            'education',
            'knowledge',
            'understanding',
            'skills',
            'abilities',
            'good',
            'strong',
            'excellent',
            'other',
        }
        
        return normalized in generic_terms
    
    def get_stats(self) -> Dict:
        """Get resolution statistics."""
        return self.stats.copy()
    
    def print_stats(self):
        """Print resolution statistics."""
        print("\n" + "="*60)
        print("PHASE B: RESOLUTION COMPLETE")
        print("="*60)
        print(f"\n📊 RESOLUTION RESULTS:")
        print(f"  Total unresolved:    {self.stats['total_unresolved']:>6}")
        print(f"  Auto-resolved:       {self.stats['auto_resolved']:>6}")
        print(f"  Needs review:        {self.stats['needs_review']:>6}")
        print(f"  New skills created:  {self.stats['new_skills_created']:>6}")
        print(f"  Rejected:            {self.stats['rejected']:>6}")
        
        if self.stats['errors'] > 0:
            print(f"\n⚠️  ERRORS:")
            print(f"  Errors:              {self.stats['errors']:>6}")
        
        # Calculate percentages
        total = self.stats['total_unresolved']
        if total > 0:
            auto_pct = (self.stats['auto_resolved'] / total) * 100
            review_pct = (self.stats['needs_review'] / total) * 100
            new_pct = (self.stats['new_skills_created'] / total) * 100
            
            print(f"\n📈 SUCCESS RATES:")
            print(f"  Auto-resolved:       {auto_pct:>5.1f}%")
            print(f"  Needs review:        {review_pct:>5.1f}%")
            print(f"  New skills:          {new_pct:>5.1f}%")
        
        print("\n" + "="*60)
        print("NEXT STEP: Link jobs to resolved skills")
        print("Command: python manage.py link_job_skills")
        print("="*60 + "\n")
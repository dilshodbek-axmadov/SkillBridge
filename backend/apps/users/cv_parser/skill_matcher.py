"""
Skill Matcher
=============
backend/apps/users/cv_parser/skill_matcher.py

Match extracted skill names to database skills using fuzzy matching.
"""

import logging
from typing import List, Dict, Optional
from fuzzywuzzy import fuzz
from apps.skills.models import Skill

logger = logging.getLogger(__name__)


class SkillMatcher:
    """
    Match extracted skill names to canonical skills in database.
    
    Uses fuzzy string matching to handle variations:
    - "Javascript" → "JavaScript"
    - "PostgreSQL" → "PostgreSQL" 
    - "React.js" → "React"
    """
    
    def __init__(self, fuzzy_threshold: int = 85):
        """
        Initialize skill matcher.
        
        Args:
            fuzzy_threshold: Minimum similarity score (0-100) for fuzzy match
        """
        self.fuzzy_threshold = fuzzy_threshold
        
        # Cache of all skills for faster matching
        self._skill_cache = None
    
    def match_skills(self, skill_names: List[str]) -> List[Dict]:
        """
        Match list of skill names to database skills.
        
        Args:
            skill_names: List of extracted skill names
        
        Returns:
            List of matches:
            [
                {
                    'skill_id': int,
                    'skill_name': str,
                    'extracted_name': str,
                    'match_score': float,
                    'match_type': 'exact' | 'fuzzy'
                },
                ...
            ]
        """
        if not skill_names:
            return []
        
        # Load skills cache
        if self._skill_cache is None:
            self._load_skill_cache()
        
        matches = []
        
        for skill_name in skill_names:
            match = self._match_single_skill(skill_name)
            if match:
                matches.append(match)
        
        return matches
    
    def _match_single_skill(self, skill_name: str) -> Optional[Dict]:
        """
        Match single skill name to database.
        
        Strategy:
        1. Try exact match (case-insensitive)
        2. Try fuzzy match if no exact match
        3. Return best match above threshold
        """
        if not skill_name or len(skill_name.strip()) < 2:
            return None
        
        skill_name_clean = skill_name.strip()
        skill_name_lower = skill_name_clean.lower()
        
        # Try exact match first
        for skill in self._skill_cache:
            if skill['name_en'].lower() == skill_name_lower:
                return {
                    'skill_id': skill['id'],
                    'skill_name': skill['name_en'],
                    'extracted_name': skill_name_clean,
                    'match_score': 1.0,
                    'match_type': 'exact'
                }
        
        # Try fuzzy match
        best_match = None
        best_score = 0
        
        for skill in self._skill_cache:
            # Calculate similarity
            score = fuzz.ratio(skill_name_lower, skill['name_en'].lower())
            
            if score > best_score and score >= self.fuzzy_threshold:
                best_score = score
                best_match = {
                    'skill_id': skill['id'],
                    'skill_name': skill['name_en'],
                    'extracted_name': skill_name_clean,
                    'match_score': score / 100.0,
                    'match_type': 'fuzzy'
                }
        
        return best_match
    
    def _load_skill_cache(self):
        """Load all skills into memory cache."""
        try:
            skills = Skill.objects.all().values('skill_id', 'name_en', 'category')
            
            self._skill_cache = [
                {
                    'id': skill['skill_id'],
                    'name_en': skill['name_en'],
                    'category': skill['category']
                }
                for skill in skills
            ]
            
            logger.info(f"Loaded {len(self._skill_cache)} skills into cache")
        
        except Exception as e:
            logger.error(f"Error loading skill cache: {e}")
            self._skill_cache = []
    
    def get_matched_skill_ids(self, skill_names: List[str]) -> List[int]:
        """
        Get list of matched skill IDs.
        
        Args:
            skill_names: List of extracted skill names
        
        Returns:
            List of skill IDs
        """
        matches = self.match_skills(skill_names)
        return [match['skill_id'] for match in matches]
    
    def get_match_report(self, skill_names: List[str]) -> Dict:
        """
        Get detailed matching report.
        
        Returns:
            {
                'total_extracted': int,
                'total_matched': int,
                'match_rate': float,
                'exact_matches': int,
                'fuzzy_matches': int,
                'unmatched': List[str],
                'matches': List[Dict]
            }
        """
        matches = self.match_skills(skill_names)
        
        exact_matches = [m for m in matches if m['match_type'] == 'exact']
        fuzzy_matches = [m for m in matches if m['match_type'] == 'fuzzy']
        
        matched_names = {m['extracted_name'].lower() for m in matches}
        unmatched = [
            name for name in skill_names 
            if name.lower() not in matched_names
        ]
        
        return {
            'total_extracted': len(skill_names),
            'total_matched': len(matches),
            'match_rate': len(matches) / len(skill_names) if skill_names else 0.0,
            'exact_matches': len(exact_matches),
            'fuzzy_matches': len(fuzzy_matches),
            'unmatched': unmatched,
            'matches': matches
        }
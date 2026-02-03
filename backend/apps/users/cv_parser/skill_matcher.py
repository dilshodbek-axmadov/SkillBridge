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
    
    def __init__(self, fuzzy_threshold: int = 85, auto_create: bool = True):
        """
        Initialize skill matcher.

        Args:
            fuzzy_threshold: Minimum similarity score (0-100) for fuzzy match
            auto_create: Automatically create skills that don't exist in database
        """
        self.fuzzy_threshold = fuzzy_threshold
        self.auto_create = auto_create

        # Cache of all skills for faster matching
        self._skill_cache = None
    
    def match_skills(self, skill_names: List[str]) -> List[Dict]:
        """
        Match list of skill names to database skills.

        If auto_create=True, creates new skills that don't exist in database.

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
                    'match_type': 'exact' | 'fuzzy' | 'created'
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
            elif self.auto_create:
                # Skill not found - create it
                created_skill = self._create_skill(skill_name)
                if created_skill:
                    matches.append(created_skill)

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
    
    def _create_skill(self, skill_name: str) -> Optional[Dict]:
        """
        Create new skill in database if it doesn't exist (case-insensitive check).

        Args:
            skill_name: Name of skill to create

        Returns:
            Match dict with created skill or None if creation failed
        """
        if not skill_name or len(skill_name.strip()) < 2:
            return None

        skill_name_clean = skill_name.strip()

        # Double-check it doesn't exist (case-insensitive)
        existing = Skill.objects.filter(name_en__iexact=skill_name_clean).first()
        if existing:
            # It exists, add to cache and return
            logger.info(f"Skill '{skill_name_clean}' already exists (ID: {existing.skill_id})")
            new_cache_entry = {
                'id': existing.skill_id,
                'name_en': existing.name_en,
                'category': existing.category
            }
            self._skill_cache.append(new_cache_entry)

            return {
                'skill_id': existing.skill_id,
                'skill_name': existing.name_en,
                'extracted_name': skill_name_clean,
                'match_score': 1.0,
                'match_type': 'exact'
            }

        try:
            # Determine category based on skill name (simple heuristic)
            category = self._infer_category(skill_name_clean)

            # Create new skill
            new_skill = Skill.objects.create(
                name_en=skill_name_clean,
                name_ru=skill_name_clean,  # Use same name for now
                name_uz=skill_name_clean,
                category=category,
                is_verified=False  # Mark as unverified/auto-created
            )

            logger.info(f"✨ Created new skill: '{skill_name_clean}' (ID: {new_skill.skill_id}, Category: {category})")

            # Add to cache
            new_cache_entry = {
                'id': new_skill.skill_id,
                'name_en': new_skill.name_en,
                'category': new_skill.category
            }
            self._skill_cache.append(new_cache_entry)

            return {
                'skill_id': new_skill.skill_id,
                'skill_name': new_skill.name_en,
                'extracted_name': skill_name_clean,
                'match_score': 1.0,
                'match_type': 'created'
            }

        except Exception as e:
            logger.error(f"Failed to create skill '{skill_name_clean}': {e}")
            return None

    def _infer_category(self, skill_name: str) -> str:
        """
        Infer skill category from name.

        Categories in skills model: programming, framework, database, tool, cloud, methodology, soft_skill, other
        """
        skill_lower = skill_name.lower()

        # Programming languages
        if any(lang in skill_lower for lang in ['python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'swift', 'kotlin', 'dart', 'scala']):
            return 'programming'

        # Frameworks & Libraries
        if any(fw in skill_lower for fw in ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'laravel', 'flutter', 'bloc', 'cubit', 'provider', 'riverpod', 'express', 'next', 'bootstrap', 'tailwind']):
            return 'framework'

        # Databases
        if any(db in skill_lower for db in ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 'hive', 'firebase', 'elasticsearch', 'cassandra', 'sharedpreferences']):
            return 'database'

        # Cloud platforms
        if any(cloud in skill_lower for cloud in ['aws', 'azure', 'gcp', 'google cloud', 'amazon web services', 'heroku', 'digitalocean']):
            return 'cloud'

        # Methodologies
        if any(method in skill_lower for method in ['agile', 'scrum', 'kanban', 'devops', 'ci/cd', 'tdd', 'bdd', 'oop', 'solid']):
            return 'methodology'

        # Tools
        if any(tool in skill_lower for tool in ['git', 'docker', 'kubernetes', 'jenkins', 'gitlab', 'github', 'jira', 'postman', 'vscode', 'testing', 'sdk', 'dio', 'http']):
            return 'tool'

        # Default
        return 'other'

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
"""
Resource Recommender Service
============================
AI-powered learning resource recommendations.

Uses qwen2.5:7b to suggest free learning resources for skills.
Prioritizes free YouTube videos and official documentation.
"""

import json
import logging
import re
from typing import Dict, List, Optional, Any

from django.db import transaction
from django.utils import timezone

from apps.learning.models import LearningResource, UserLearningProgress
from apps.skills.models import Skill
from apps.users.models import User
from core.ai.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class ResourceRecommender:
    """
    AI-powered learning resource recommender.

    Workflow:
    1. Get skill information
    2. AI suggests relevant free resources
    3. Store resources in database
    4. Track user progress
    """

    MODEL = "qwen2.5:7b"

    # Resource type priorities (prefer free video content)
    RESOURCE_PRIORITIES = {
        'video': 1,
        'tutorial': 2,
        'documentation': 3,
        'interactive': 4,
        'article': 5,
        'book': 6,
        'practice': 7,
    }

    def __init__(self, user: Optional[User] = None):
        self.user = user
        self.ollama = OllamaClient(model=self.MODEL)

    def get_resources_for_skill(
        self,
        skill_id: int,
        language: str = 'en',
        generate_if_missing: bool = True,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get learning resources for a skill.

        Args:
            skill_id: Skill ID to get resources for
            language: Preferred content language
            generate_if_missing: If True, use AI to generate resources if none exist
            limit: Maximum number of resources to return

        Returns:
            Dict with skill info and resources list
        """

        try:
            skill = Skill.objects.get(skill_id=skill_id)
        except Skill.DoesNotExist:
            return {
                'success': False,
                'error': 'Skill not found',
            }

        # Get existing resources
        resources = LearningResource.objects.filter(
            skill_id=skill_id
        ).order_by('-is_verified', '-rating', 'resource_type')

        # Filter by language if specified
        if language:
            lang_resources = resources.filter(language=language)
            if lang_resources.exists():
                resources = lang_resources

        resources = list(resources[:limit])

        # Generate resources if none exist and generation is enabled
        if not resources and generate_if_missing:
            generated = self._ai_generate_resources(skill, language)
            resources = self._save_resources(skill, generated)

        # Get user progress if user is authenticated
        user_progress = {}
        if self.user:
            progress_qs = UserLearningProgress.objects.filter(
                user=self.user,
                resource__skill_id=skill_id
            ).select_related('resource')

            user_progress = {
                p.resource_id: {
                    'status': p.status,
                    'progress_percentage': p.progress_percentage,
                    'started_at': p.started_at.isoformat() if p.started_at else None,
                }
                for p in progress_qs
            }

        return {
            'success': True,
            'skill': {
                'skill_id': skill.skill_id,
                'name_en': skill.name_en,
                'name_ru': skill.name_ru,
                'name_uz': skill.name_uz,
                'category': skill.category,
            },
            'resources': [
                {
                    'resource_id': r.resource_id,
                    'resource_type': r.resource_type,
                    'title': r.title,
                    'url': r.url,
                    'author': r.author,
                    'platform': r.platform,
                    'description': r.description,
                    'rating': r.rating,
                    'difficulty_level': r.difficulty_level,
                    'estimated_duration': r.estimated_duration,
                    'is_free': r.is_free,
                    'language': r.language,
                    'is_verified': r.is_verified,
                    'user_progress': user_progress.get(r.resource_id),
                }
                for r in resources
            ],
            'count': len(resources),
        }

    def _ai_generate_resources(
        self,
        skill: Skill,
        language: str = 'en'
    ) -> List[Dict[str, Any]]:
        """Use AI to generate resource recommendations."""

        language_instruction = {
            'en': 'Suggest resources primarily in English.',
            'ru': 'Suggest resources in Russian when available, otherwise English.',
            'uz': 'Suggest resources in Uzbek when available, otherwise Russian or English.',
        }.get(language, 'Suggest resources primarily in English.')

        prompt = f"""Suggest FREE learning resources for the skill: "{skill.name_en}"
Category: {skill.category}

IMPORTANT REQUIREMENTS:
1. PRIORITIZE FREE resources (especially YouTube videos)
2. Include REAL, EXISTING resources with actual URLs
3. Focus on beginner to intermediate level content

Suggest resources in these categories:
1. YouTube videos/playlists (FREE) - most important
2. Official documentation (FREE)
3. Interactive tutorials (FREE platforms like freeCodeCamp, Codecademy free tier)
4. Articles/blogs (FREE)
5. Books (mention if free PDF available)

{language_instruction}

Return ONLY valid JSON array with 5-8 resources:
[
    {{
        "title": "Python Tutorial for Beginners - Full Course",
        "url": "https://www.youtube.com/watch?v=...",
        "resource_type": "video",
        "platform": "YouTube",
        "author": "Programming with Mosh",
        "description": "Complete Python course covering basics to advanced",
        "difficulty_level": "beginner",
        "estimated_duration": 6,
        "is_free": true,
        "language": "en"
    }}
]

Resource types: video, tutorial, documentation, article, book, interactive, practice
Difficulty levels: beginner, intermediate, advanced, expert
Duration is in hours.

Return ONLY the JSON array, no other text:"""

        try:
            response = self.ollama.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=2500
            )

            resources = self._parse_ai_response(response)
            return resources

        except Exception as e:
            logger.error(f"AI resource generation failed: {e}")
            return self._fallback_resources(skill)

    def _parse_ai_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse AI response with multiple strategies."""

        if not response:
            return []

        # Strategy 1: Direct JSON parse
        try:
            result = json.loads(response.strip())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

        # Strategy 2: Extract from markdown code blocks
        cleaned = re.sub(r'```json\s*', '', response)
        cleaned = re.sub(r'```\s*', '', cleaned)

        try:
            result = json.loads(cleaned.strip())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

        # Strategy 3: Find JSON array in text
        match = re.search(r'\[[\s\S]*\]', response)
        if match:
            try:
                result = json.loads(match.group(0))
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                pass

        logger.warning("Could not parse AI response as JSON array")
        return []

    def _fallback_resources(self, skill: Skill) -> List[Dict[str, Any]]:
        """Fallback resources when AI is unavailable."""

        skill_name = skill.name_en.lower().replace(' ', '+')

        return [
            {
                'title': f'{skill.name_en} Tutorial - YouTube Search',
                'url': f'https://www.youtube.com/results?search_query={skill_name}+tutorial',
                'resource_type': 'video',
                'platform': 'YouTube',
                'author': 'Various',
                'description': f'Search results for {skill.name_en} tutorials on YouTube',
                'difficulty_level': 'beginner',
                'estimated_duration': 2,
                'is_free': True,
                'language': 'en',
            },
            {
                'title': f'{skill.name_en} - Google Search',
                'url': f'https://www.google.com/search?q={skill_name}+documentation',
                'resource_type': 'documentation',
                'platform': 'Google',
                'author': 'Various',
                'description': f'Search for official {skill.name_en} documentation',
                'difficulty_level': 'beginner',
                'estimated_duration': 1,
                'is_free': True,
                'language': 'en',
            },
        ]

    def _save_resources(
        self,
        skill: Skill,
        resources_data: List[Dict[str, Any]]
    ) -> List[LearningResource]:
        """Save generated resources to database."""

        saved_resources = []

        valid_types = ['video', 'book', 'documentation', 'article', 'tutorial', 'interactive', 'practice']
        valid_difficulties = ['beginner', 'intermediate', 'advanced', 'expert']

        with transaction.atomic():
            for data in resources_data:
                # Validate and clean data
                resource_type = data.get('resource_type', 'video')
                if resource_type not in valid_types:
                    resource_type = 'video'

                difficulty = data.get('difficulty_level', 'beginner')
                if difficulty not in valid_difficulties:
                    difficulty = 'beginner'

                # Check for duplicate URLs
                url = data.get('url', '')
                if url and LearningResource.objects.filter(url=url).exists():
                    continue

                try:
                    resource = LearningResource.objects.create(
                        skill=skill,
                        resource_type=resource_type,
                        title=data.get('title', f'{skill.name_en} Resource')[:300],
                        url=url[:500] if url else None,
                        author=data.get('author', '')[:200] if data.get('author') else None,
                        platform=data.get('platform', '')[:100] if data.get('platform') else None,
                        description=data.get('description', ''),
                        rating=0.0,
                        difficulty_level=difficulty,
                        estimated_duration=data.get('estimated_duration', 0) or 0,
                        is_free=data.get('is_free', True),
                        language=data.get('language', 'en')[:10],
                        is_verified=False,
                    )
                    saved_resources.append(resource)

                except Exception as e:
                    logger.error(f"Failed to save resource: {e}")
                    continue

        return saved_resources

    def start_resource(self, resource_id: int) -> Optional[Dict[str, Any]]:
        """Mark a resource as started for the user."""

        if not self.user:
            return None

        try:
            resource = LearningResource.objects.select_related('skill').get(
                resource_id=resource_id
            )
        except LearningResource.DoesNotExist:
            return None

        progress, created = UserLearningProgress.objects.get_or_create(
            user=self.user,
            resource=resource,
            defaults={
                'status': 'started',
                'progress_percentage': 0,
            }
        )

        if not created and progress.status == 'started':
            # Already started
            pass
        elif not created:
            # Restarting
            progress.status = 'started'
            progress.progress_percentage = 0
            progress.save()

        return {
            'progress_id': progress.progress_id,
            'resource_id': resource.resource_id,
            'resource_title': resource.title,
            'skill_name': resource.skill.name_en,
            'status': progress.status,
            'progress_percentage': progress.progress_percentage,
            'started_at': progress.started_at.isoformat(),
            'created': created,
        }

    def update_progress(
        self,
        resource_id: int,
        progress_percentage: Optional[int] = None,
        status: Optional[str] = None,
        notes: Optional[str] = None,
        rating: Optional[int] = None,
        time_spent_hours: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """Update user progress on a resource."""

        if not self.user:
            return None

        try:
            progress = UserLearningProgress.objects.select_related(
                'resource__skill'
            ).get(
                user=self.user,
                resource_id=resource_id
            )
        except UserLearningProgress.DoesNotExist:
            return None

        # Update fields
        if progress_percentage is not None:
            progress.progress_percentage = min(100, max(0, progress_percentage))

        if status is not None:
            valid_statuses = ['started', 'in_progress', 'completed', 'abandoned']
            if status in valid_statuses:
                progress.status = status

                if status == 'completed':
                    progress.completed_at = timezone.now()
                    progress.progress_percentage = 100

        if notes is not None:
            progress.notes = notes

        if rating is not None:
            progress.rating = min(5, max(1, rating))

        if time_spent_hours is not None:
            progress.time_spent_hours = time_spent_hours

        # Auto-update status based on progress
        if progress.progress_percentage > 0 and progress.status == 'started':
            progress.status = 'in_progress'

        if progress.progress_percentage == 100 and progress.status != 'completed':
            progress.status = 'completed'
            progress.completed_at = timezone.now()

        progress.save()

        return {
            'progress_id': progress.progress_id,
            'resource_id': progress.resource_id,
            'resource_title': progress.resource.title,
            'skill_name': progress.resource.skill.name_en,
            'status': progress.status,
            'progress_percentage': progress.progress_percentage,
            'time_spent_hours': progress.time_spent_hours,
            'notes': progress.notes,
            'rating': progress.rating,
            'started_at': progress.started_at.isoformat(),
            'completed_at': progress.completed_at.isoformat() if progress.completed_at else None,
            'updated_at': progress.updated_at.isoformat(),
        }

    def get_user_progress(
        self,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all user's learning progress."""

        if not self.user:
            return []

        queryset = UserLearningProgress.objects.filter(
            user=self.user
        ).select_related('resource__skill').order_by('-updated_at')

        if status:
            queryset = queryset.filter(status=status)

        return [
            {
                'progress_id': p.progress_id,
                'resource': {
                    'resource_id': p.resource.resource_id,
                    'title': p.resource.title,
                    'resource_type': p.resource.resource_type,
                    'url': p.resource.url,
                    'platform': p.resource.platform,
                    'skill_name': p.resource.skill.name_en,
                    'skill_id': p.resource.skill_id,
                },
                'status': p.status,
                'progress_percentage': p.progress_percentage,
                'time_spent_hours': p.time_spent_hours,
                'rating': p.rating,
                'started_at': p.started_at.isoformat(),
                'completed_at': p.completed_at.isoformat() if p.completed_at else None,
                'updated_at': p.updated_at.isoformat(),
            }
            for p in queryset
        ]

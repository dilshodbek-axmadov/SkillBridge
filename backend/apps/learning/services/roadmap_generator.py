"""
Roadmap Generator Service
=========================
AI-powered personalized learning roadmap generation.

Uses qwen2.5:7b for multilingual support (English, Russian, Uzbek).
"""

import json
import logging
import re
from typing import Dict, List, Optional, Any

from django.db import transaction
from django.utils import timezone

from apps.learning.models import LearningRoadmap, RoadmapItem
from apps.skills.models import Skill, SkillGap, UserSkill, MarketTrend
from apps.users.models import User, UserProfile
from core.ai.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class RoadmapGenerator:
    """
    AI-powered learning roadmap generator.

    Workflow:
    1. Collect user profile and skill gaps
    2. Get market trends for prioritization
    3. AI creates structured learning path
    4. Sequences skills by dependency and priority
    5. Estimates learning duration per skill
    6. Creates roadmap_items with sequence_order
    """

    MODEL = "qwen2.5:7b"

    # Default learning duration estimates by category (hours)
    DEFAULT_DURATIONS = {
        'programming_language': 80,
        'library_or_package': 30,
        'framework': 60,
        'database': 40,
        'data_engineering': 50,
        'cloud_platform': 60,
        'devops_infrastructure': 50,
        'testing_qa': 30,
        'bi_analytics': 40,
        'tools_software': 20,
        'design_creative': 40,
        'business_product_management': 30,
        'security': 40,
        'networking': 40,
        'operating_system': 30,
        'methodology_process': 20,
        'soft_skill': 20,
        'domain_specific': 40,
        'other': 30,
    }

    def __init__(self, user: User):
        self.user = user
        self.ollama = OllamaClient(model=self.MODEL)
        self._user_skills: Optional[List[Skill]] = None
        self._skill_gaps: Optional[List[SkillGap]] = None
        self._market_trends: Optional[Dict[int, MarketTrend]] = None

    @property
    def user_skills(self) -> List[Skill]:
        """Get user's current skills (cached)."""
        if self._user_skills is None:
            self._user_skills = list(
                Skill.objects.filter(
                    user_skills__user=self.user
                ).distinct()
            )
        return self._user_skills

    @property
    def user_skill_names(self) -> List[str]:
        """Get list of user skill names."""
        return [s.name_en for s in self.user_skills]

    @property
    def skill_gaps(self) -> List[SkillGap]:
        """Get user's skill gaps (cached)."""
        if self._skill_gaps is None:
            self._skill_gaps = list(
                SkillGap.objects.filter(
                    user=self.user,
                    status__in=['pending', 'learning']
                ).select_related('skill')
            )
        return self._skill_gaps

    def get_market_trends(self, period: str = '30d') -> Dict[int, MarketTrend]:
        """Get market trends indexed by skill_id."""
        if self._market_trends is None:
            trends = MarketTrend.objects.filter(period=period).select_related('skill')
            self._market_trends = {t.skill_id: t for t in trends}
        return self._market_trends

    def generate_roadmap(
        self,
        target_role: Optional[str] = None,
        language: str = 'en',
        max_skills: int = 15
    ) -> Dict[str, Any]:
        """
        Generate personalized learning roadmap.

        Args:
            target_role: Target job role (uses user's desired_role if not provided)
            language: Response language (en, ru, uz)
            max_skills: Maximum number of skills to include

        Returns:
            Dict containing roadmap data and status
        """

        # Get target role
        if not target_role:
            try:
                profile = self.user.profile
                target_role = profile.desired_role or profile.current_job_position
            except UserProfile.DoesNotExist:
                pass

        if not target_role:
            return {
                'success': False,
                'error': 'No target role specified and user has no desired_role set',
            }

        # Get skill gaps
        gaps = self.skill_gaps
        if not gaps:
            return {
                'success': False,
                'error': 'No skill gaps found. Run skill gap analysis first.',
            }

        # Get market trends for prioritization
        market_trends = self.get_market_trends()

        # Prepare skills data for AI
        skills_for_ai = self._prepare_skills_for_ai(gaps, market_trends, max_skills)

        # Use AI to generate roadmap structure
        ai_roadmap = self._ai_generate_roadmap(
            target_role=target_role,
            user_skills=self.user_skill_names,
            skills_to_learn=skills_for_ai,
            language=language
        )

        # Create roadmap in database
        roadmap = self._create_roadmap(
            target_role=target_role,
            ai_roadmap=ai_roadmap,
            skills_for_ai=skills_for_ai
        )

        return {
            'success': True,
            'roadmap_id': roadmap.roadmap_id,
            'title': roadmap.title,
            'target_role': target_role,
            'description': roadmap.description,
            'total_estimated_hours': roadmap.total_estimated_hours,
            'items_count': roadmap.items.count(),
            'items': self._serialize_roadmap_items(roadmap),
        }

    def _prepare_skills_for_ai(
        self,
        gaps: List[SkillGap],
        market_trends: Dict[int, MarketTrend],
        max_skills: int
    ) -> List[Dict[str, Any]]:
        """Prepare skill data for AI processing."""

        skills_data = []
        for gap in gaps:
            trend = market_trends.get(gap.skill_id)
            demand_score = trend.demand_score if trend else 0

            skills_data.append({
                'skill_id': gap.skill_id,
                'skill_name': gap.skill.name_en,
                'category': gap.skill.category,
                'importance': gap.importance,
                'priority': gap.demand_priority,
                'demand_score': demand_score,
                'default_duration': self.DEFAULT_DURATIONS.get(
                    gap.skill.category, 30
                ),
            })

        # Sort by priority and demand score
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        skills_data.sort(
            key=lambda s: (priority_order.get(s['priority'], 2), -s['demand_score'])
        )

        return skills_data[:max_skills]

    def _ai_generate_roadmap(
        self,
        target_role: str,
        user_skills: List[str],
        skills_to_learn: List[Dict],
        language: str = 'en'
    ) -> Dict[str, Any]:
        """Use AI to generate roadmap structure."""

        language_instruction = {
            'en': 'Respond in English.',
            'ru': 'Respond in Russian (Русский).',
            'uz': "Respond in Uzbek (O'zbek tili).",
        }.get(language, 'Respond in English.')

        # Prepare skills summary
        skills_summary = "\n".join([
            f"- {s['skill_name']} (category: {s['category']}, importance: {s['importance']}, "
            f"priority: {s['priority']}, default_hours: {s['default_duration']})"
            for s in skills_to_learn
        ])

        prompt = f"""Create a personalized learning roadmap for someone targeting the "{target_role}" role.

CURRENT USER SKILLS:
{', '.join(user_skills) if user_skills else 'No skills listed'}

SKILLS TO LEARN (in priority order):
{skills_summary}

TASK:
1. Create a structured learning path
2. Sequence skills by logical dependency (learn fundamentals before advanced)
3. Adjust estimated learning duration for each skill (in hours)
4. Add brief learning notes/tips for each skill
5. Create a roadmap title and description

{language_instruction}

Return ONLY valid JSON in this exact format:
{{
    "title": "Path to {target_role}",
    "description": "Brief roadmap overview (2-3 sentences)",
    "skills": [
        {{
            "skill_name": "Python",
            "sequence_order": 1,
            "estimated_hours": 80,
            "priority": "high",
            "notes": "Start with basics: variables, functions, OOP concepts"
        }}
    ]
}}

Important:
- Order skills logically (fundamentals first)
- Adjust hours based on skill complexity
- Keep notes concise and actionable"""

        try:
            response = self.ollama.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=2500
            )

            result = self._parse_ai_response(response)
            return result

        except Exception as e:
            logger.error(f"AI roadmap generation failed: {e}")
            return self._fallback_roadmap(target_role, skills_to_learn)

    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response with multiple strategies."""

        if not response:
            return {'title': '', 'description': '', 'skills': []}

        # Strategy 1: Direct JSON parse
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass

        # Strategy 2: Extract JSON from markdown code blocks
        cleaned = re.sub(r'```json\s*', '', response)
        cleaned = re.sub(r'```\s*', '', cleaned)

        try:
            return json.loads(cleaned.strip())
        except json.JSONDecodeError:
            pass

        # Strategy 3: Find JSON object in text
        match = re.search(r'\{[\s\S]*\}', response)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        logger.warning("Could not parse AI response as JSON")
        return {'title': '', 'description': '', 'skills': []}

    def _fallback_roadmap(
        self,
        target_role: str,
        skills_to_learn: List[Dict]
    ) -> Dict[str, Any]:
        """Fallback roadmap when AI is unavailable."""

        return {
            'title': f'Path to {target_role}',
            'description': f'Learning roadmap with {len(skills_to_learn)} skills to master for the {target_role} role.',
            'skills': [
                {
                    'skill_name': s['skill_name'],
                    'sequence_order': idx + 1,
                    'estimated_hours': s['default_duration'],
                    'priority': s['priority'],
                    'notes': f"Focus on practical {s['category'].replace('_', ' ')} skills."
                }
                for idx, s in enumerate(skills_to_learn)
            ]
        }

    def _create_roadmap(
        self,
        target_role: str,
        ai_roadmap: Dict[str, Any],
        skills_for_ai: List[Dict]
    ) -> LearningRoadmap:
        """Create roadmap and items in database."""

        # Build skill lookup
        skill_lookup = {s['skill_name'].lower(): s for s in skills_for_ai}

        with transaction.atomic():
            # Deactivate previous roadmaps for same target role
            LearningRoadmap.objects.filter(
                user=self.user,
                target_role=target_role,
                is_active=True
            ).update(is_active=False)

            # Calculate total hours
            total_hours = sum(
                s.get('estimated_hours', 30)
                for s in ai_roadmap.get('skills', [])
            )

            # Create roadmap
            roadmap = LearningRoadmap.objects.create(
                user=self.user,
                title=ai_roadmap.get('title', f'Path to {target_role}'),
                target_role=target_role,
                description=ai_roadmap.get('description', ''),
                total_estimated_hours=total_hours,
                is_active=True,
                generated_by_ai=True,
            )

            # Create roadmap items
            ai_skills = ai_roadmap.get('skills', [])

            for ai_skill in ai_skills:
                skill_name = ai_skill.get('skill_name', '')
                skill_data = skill_lookup.get(skill_name.lower())

                if not skill_data:
                    # Try to find skill in database
                    skill = Skill.objects.filter(name_en__iexact=skill_name).first()
                    if not skill:
                        continue
                    skill_id = skill.skill_id
                else:
                    skill_id = skill_data['skill_id']

                # Map priority
                priority = ai_skill.get('priority', 'medium')
                if priority not in ('high', 'medium', 'low'):
                    priority = 'medium'

                RoadmapItem.objects.create(
                    roadmap=roadmap,
                    skill_id=skill_id,
                    sequence_order=ai_skill.get('sequence_order', 1),
                    estimated_duration_hours=ai_skill.get('estimated_hours', 30),
                    priority=priority,
                    status='pending',
                    notes=ai_skill.get('notes', ''),
                )

        return roadmap

    def _serialize_roadmap_items(self, roadmap: LearningRoadmap) -> List[Dict[str, Any]]:
        """Serialize roadmap items for response."""

        items = roadmap.items.select_related('skill').order_by('sequence_order')

        return [
            {
                'item_id': item.item_id,
                'skill_id': item.skill_id,
                'skill_name': item.skill.name_en,
                'skill_name_ru': item.skill.name_ru,
                'skill_name_uz': item.skill.name_uz,
                'category': item.skill.category,
                'sequence_order': item.sequence_order,
                'estimated_duration_hours': item.estimated_duration_hours,
                'priority': item.priority,
                'status': item.status,
                'notes': item.notes,
            }
            for item in items
        ]

    def get_user_roadmaps(
        self,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get user's roadmaps with progress."""

        queryset = LearningRoadmap.objects.filter(user=self.user)

        if active_only:
            queryset = queryset.filter(is_active=True)

        roadmaps = []
        for roadmap in queryset.prefetch_related('items__skill'):
            items = roadmap.items.all()
            completed = items.filter(status='completed').count()
            in_progress = items.filter(status='in_progress').count()
            total = items.count()

            roadmaps.append({
                'roadmap_id': roadmap.roadmap_id,
                'title': roadmap.title,
                'target_role': roadmap.target_role,
                'description': roadmap.description,
                'total_estimated_hours': roadmap.total_estimated_hours,
                'completion_percentage': roadmap.completion_percentage,
                'is_active': roadmap.is_active,
                'generated_by_ai': roadmap.generated_by_ai,
                'created_at': roadmap.created_at.isoformat(),
                'stats': {
                    'total_items': total,
                    'completed': completed,
                    'in_progress': in_progress,
                    'pending': total - completed - in_progress,
                },
                'items': self._serialize_roadmap_items(roadmap),
            })

        return roadmaps

    def get_roadmap_detail(self, roadmap_id: int) -> Optional[Dict[str, Any]]:
        """Get single roadmap with full details."""

        try:
            roadmap = LearningRoadmap.objects.prefetch_related(
                'items__skill'
            ).get(
                roadmap_id=roadmap_id,
                user=self.user
            )
        except LearningRoadmap.DoesNotExist:
            return None

        items = roadmap.items.all()
        completed = items.filter(status='completed').count()
        in_progress = items.filter(status='in_progress').count()

        return {
            'roadmap_id': roadmap.roadmap_id,
            'title': roadmap.title,
            'target_role': roadmap.target_role,
            'description': roadmap.description,
            'total_estimated_hours': roadmap.total_estimated_hours,
            'completion_percentage': roadmap.completion_percentage,
            'is_active': roadmap.is_active,
            'generated_by_ai': roadmap.generated_by_ai,
            'created_at': roadmap.created_at.isoformat(),
            'updated_at': roadmap.updated_at.isoformat(),
            'stats': {
                'total_items': items.count(),
                'completed': completed,
                'in_progress': in_progress,
                'pending': items.count() - completed - in_progress,
            },
            'items': self._serialize_roadmap_items(roadmap),
        }

    def update_item_status(
        self,
        item_id: int,
        status: str
    ) -> Optional[Dict[str, Any]]:
        """Update roadmap item status."""

        valid_statuses = ['pending', 'in_progress', 'completed', 'skipped']
        if status not in valid_statuses:
            return None

        try:
            item = RoadmapItem.objects.select_related(
                'skill', 'roadmap'
            ).get(
                item_id=item_id,
                roadmap__user=self.user
            )
        except RoadmapItem.DoesNotExist:
            return None

        old_status = item.status
        now = timezone.now()

        # Update status and timestamps
        item.status = status

        if status == 'in_progress' and not item.started_at:
            item.started_at = now

        if status == 'completed':
            item.completed_at = now
            # This also adds skill to user_skills via mark_as_completed
            item.mark_as_completed()
        else:
            item.save()
            # Update roadmap completion percentage
            item.roadmap.update_completion_percentage()

        return {
            'item_id': item.item_id,
            'skill_name': item.skill.name_en,
            'old_status': old_status,
            'new_status': status,
            'roadmap_id': item.roadmap.roadmap_id,
            'roadmap_completion': item.roadmap.completion_percentage,
            'updated': True,
        }

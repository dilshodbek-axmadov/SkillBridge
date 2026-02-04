"""
Skill Gap Analyzer Service
==========================
AI-powered skill gap detection and analysis.

Uses qwen2.5:7b for multilingual support (English, Russian, Uzbek).
"""

import json
import logging
import re
from typing import Dict, List, Optional, Any
from decimal import Decimal

from django.db import transaction
from django.db.models import Q

from apps.skills.models import Skill, UserSkill, SkillGap, MarketTrend
from apps.users.models import User, UserProfile
from core.ai.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class SkillGapAnalyzer:
    """
    AI-powered skill gap analysis service.

    Workflow:
    1. Fetch user's current skills
    2. Get market requirements for target role
    3. AI analyzes missing skills
    4. Classify gaps: core vs secondary
    5. Prioritize by demand score
    """

    MODEL = "qwen2.5:7b"

    def __init__(self, user: User):
        self.user = user
        self.ollama = OllamaClient(model=self.MODEL)
        self._user_skills: Optional[List[Skill]] = None
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

    def get_market_trends(self, period: str = '30d') -> Dict[int, MarketTrend]:
        """Get market trends indexed by skill_id."""
        if self._market_trends is None:
            trends = MarketTrend.objects.filter(period=period).select_related('skill')
            self._market_trends = {t.skill_id: t for t in trends}
        return self._market_trends

    def analyze_gaps(
        self,
        target_role: Optional[str] = None,
        period: str = '30d',
        language: str = 'en'
    ) -> Dict[str, Any]:
        """
        Perform full skill gap analysis.

        Args:
            target_role: Target job role (uses user's desired_role if not provided)
            period: Market trends period to use
            language: Response language (en, ru, uz)

        Returns:
            Dict containing:
            - user_skills: List of current skills
            - missing_skills: List of identified gaps
            - recommendations: AI-generated recommendations
            - analysis_summary: Overview of the analysis
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
                'user_skills': self.user_skill_names,
            }

        # Get market trends
        market_trends = self.get_market_trends(period)

        if not market_trends:
            return {
                'success': False,
                'error': 'No market trends data available. Run calculate_market_trends command first.',
                'user_skills': self.user_skill_names,
            }

        # Get top skills from market
        top_market_skills = self._get_top_market_skills(market_trends, limit=50)

        # Use AI to analyze gaps
        ai_analysis = self._ai_analyze_gaps(
            target_role=target_role,
            user_skills=self.user_skill_names,
            market_skills=top_market_skills,
            language=language
        )

        # Process and save gaps
        gaps = self._process_and_save_gaps(ai_analysis, market_trends)

        return {
            'success': True,
            'target_role': target_role,
            'user_skills': self.user_skill_names,
            'missing_skills': gaps,
            'recommendations': ai_analysis.get('recommendations', []),
            'analysis_summary': ai_analysis.get('summary', ''),
            'period': period,
        }

    def _get_top_market_skills(
        self,
        trends: Dict[int, MarketTrend],
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get top skills from market trends by demand score."""

        sorted_trends = sorted(
            trends.values(),
            key=lambda t: t.demand_score,
            reverse=True
        )[:limit]

        return [
            {
                'name': t.skill.name_en,
                'category': t.skill.category,
                'demand_score': t.demand_score,
                'job_count': t.job_count,
                'growth_rate': t.growth_rate,
            }
            for t in sorted_trends
        ]

    def _ai_analyze_gaps(
        self,
        target_role: str,
        user_skills: List[str],
        market_skills: List[Dict],
        language: str = 'en'
    ) -> Dict[str, Any]:
        """Use AI to analyze skill gaps."""

        language_instruction = {
            'en': 'Respond in English.',
            'ru': 'Respond in Russian (Русский).',
            'uz': "Respond in Uzbek (O'zbek tili).",
        }.get(language, 'Respond in English.')

        # Prepare market skills summary
        market_summary = "\n".join([
            f"- {s['name']} (demand: {s['demand_score']:.1f}, jobs: {s['job_count']}, growth: {s['growth_rate']:.1f}%)"
            for s in market_skills[:30]
        ])

        prompt = f"""Analyze skill gaps for a professional targeting the "{target_role}" role.

CURRENT USER SKILLS:
{', '.join(user_skills) if user_skills else 'No skills listed'}

TOP MARKET DEMAND SKILLS:
{market_summary}

TASK:
1. Identify which skills the user is MISSING that are important for "{target_role}"
2. Classify each missing skill as "core" (essential) or "secondary" (nice-to-have)
3. Prioritize based on market demand
4. Provide actionable recommendations

{language_instruction}

Return ONLY valid JSON in this exact format:
{{
    "missing_skills": [
        {{
            "skill_name": "Python",
            "importance": "core",
            "priority": "high",
            "reason": "Essential for data analysis roles"
        }}
    ],
    "recommendations": [
        "Start with Python fundamentals",
        "Focus on SQL for database work"
    ],
    "summary": "Brief analysis summary"
}}"""

        try:
            response = self.ollama.generate(
                prompt=prompt,
                temperature=0.2,
                max_tokens=2000
            )

            # Parse JSON from response
            result = self._parse_ai_response(response)
            return result

        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return self._fallback_analysis(user_skills, market_skills)

    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response with multiple strategies."""

        if not response:
            return {'missing_skills': [], 'recommendations': [], 'summary': ''}

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
        return {'missing_skills': [], 'recommendations': [], 'summary': response[:500]}

    def _fallback_analysis(
        self,
        user_skills: List[str],
        market_skills: List[Dict]
    ) -> Dict[str, Any]:
        """Fallback analysis when AI is unavailable."""

        user_skills_lower = {s.lower() for s in user_skills}

        missing = []
        for skill in market_skills:
            if skill['name'].lower() not in user_skills_lower:
                importance = 'core' if skill['demand_score'] > 50 else 'secondary'
                priority = 'high' if skill['demand_score'] > 70 else (
                    'medium' if skill['demand_score'] > 40 else 'low'
                )

                missing.append({
                    'skill_name': skill['name'],
                    'importance': importance,
                    'priority': priority,
                    'reason': f"High market demand ({skill['job_count']} jobs)"
                })

        return {
            'missing_skills': missing[:20],
            'recommendations': [
                'Focus on high-demand skills first',
                'Consider skills with positive growth rate',
            ],
            'summary': f'Found {len(missing)} potential skill gaps based on market demand.'
        }

    def _process_and_save_gaps(
        self,
        ai_analysis: Dict[str, Any],
        market_trends: Dict[int, MarketTrend]
    ) -> List[Dict[str, Any]]:
        """Process AI analysis and save to database."""

        missing_skills = ai_analysis.get('missing_skills', [])
        processed_gaps = []

        # Build skill name to trend lookup
        skill_lookup = {}
        for trend in market_trends.values():
            skill_lookup[trend.skill.name_en.lower()] = trend

        with transaction.atomic():
            for gap_info in missing_skills:
                skill_name = gap_info.get('skill_name', '')
                if not skill_name:
                    continue

                # Find the skill in database
                trend = skill_lookup.get(skill_name.lower())

                if not trend:
                    # Try fuzzy match
                    skill = Skill.objects.filter(
                        Q(name_en__iexact=skill_name) |
                        Q(name_ru__iexact=skill_name) |
                        Q(normalized_key__iexact=Skill.normalize_key(skill_name))
                    ).first()

                    if not skill:
                        logger.debug(f"Skill not found: {skill_name}")
                        continue
                else:
                    skill = trend.skill

                # Map importance and priority
                importance = gap_info.get('importance', 'secondary')
                if importance not in ('core', 'secondary'):
                    importance = 'secondary'

                priority = gap_info.get('priority', 'medium')
                if priority not in ('high', 'medium', 'low'):
                    priority = 'medium'

                # Create or update SkillGap
                gap, created = SkillGap.objects.update_or_create(
                    user=self.user,
                    skill=skill,
                    defaults={
                        'importance': importance,
                        'demand_priority': priority,
                        'status': 'pending',
                    }
                )

                # Get demand score from trend if available
                demand_score = 0
                if trend:
                    demand_score = trend.demand_score
                elif skill.skill_id in market_trends:
                    demand_score = market_trends[skill.skill_id].demand_score

                processed_gaps.append({
                    'gap_id': gap.gap_id,
                    'skill_id': skill.skill_id,
                    'skill_name': skill.name_en,
                    'category': skill.category,
                    'importance': importance,
                    'priority': priority,
                    'demand_score': demand_score,
                    'reason': gap_info.get('reason', ''),
                    'status': gap.status,
                    'created': created,
                })

        # Sort by priority and demand score
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        processed_gaps.sort(
            key=lambda g: (priority_order.get(g['priority'], 2), -g['demand_score'])
        )

        return processed_gaps

    def get_user_gaps(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get user's existing skill gaps."""

        queryset = SkillGap.objects.filter(user=self.user).select_related('skill')

        if status:
            queryset = queryset.filter(status=status)

        # Get market trends for demand scores
        market_trends = self.get_market_trends()

        gaps = []
        for gap in queryset:
            trend = market_trends.get(gap.skill_id)

            gaps.append({
                'gap_id': gap.gap_id,
                'skill_id': gap.skill_id,
                'skill_name': gap.skill.name_en,
                'skill_name_ru': gap.skill.name_ru,
                'skill_name_uz': gap.skill.name_uz,
                'category': gap.skill.category,
                'importance': gap.importance,
                'priority': gap.demand_priority,
                'status': gap.status,
                'demand_score': trend.demand_score if trend else 0,
                'job_count': trend.job_count if trend else 0,
                'growth_rate': trend.growth_rate if trend else 0,
                'identified_at': gap.identified_at.isoformat(),
            })

        # Sort by priority and demand score
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        gaps.sort(
            key=lambda g: (priority_order.get(g['priority'], 2), -g['demand_score'])
        )

        return gaps

    def update_gap_status(
        self,
        gap_id: int,
        status: str
    ) -> Optional[Dict[str, Any]]:
        """Update skill gap status."""

        valid_statuses = ['pending', 'learning', 'completed', 'skipped']
        if status not in valid_statuses:
            return None

        try:
            gap = SkillGap.objects.select_related('skill').get(
                gap_id=gap_id,
                user=self.user
            )
        except SkillGap.DoesNotExist:
            return None

        old_status = gap.status
        gap.status = status
        gap.save()

        # If completed, optionally create UserSkill
        if status == 'completed':
            UserSkill.objects.get_or_create(
                user=self.user,
                skill=gap.skill,
                defaults={
                    'proficiency_level': 'beginner',
                    'source': 'completed_learning',
                }
            )

        return {
            'gap_id': gap.gap_id,
            'skill_name': gap.skill.name_en,
            'old_status': old_status,
            'new_status': status,
            'updated': True,
        }

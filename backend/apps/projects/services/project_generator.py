"""
Project Idea Generator Service
==============================
AI-powered portfolio project idea generation.

Uses qwen2.5:7b to generate project ideas based on:
- Target role
- Experience level
- User's skill gaps
"""

import json
import logging
import re
from typing import Dict, List, Optional, Any

from django.db import transaction
from django.db.models import Q

from apps.projects.models import ProjectIdea, ProjectSkill, UserProject
from apps.skills.models import Skill, SkillGap, UserSkill
from apps.users.models import User
from core.ai.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class ProjectIdeaGenerator:
    """
    AI-powered project idea generator.

    Workflow:
    1. Collect user profile, skill gaps, target role
    2. AI generates relevant project ideas
    3. Store projects with required skills
    4. Link to user if requested
    """

    MODEL = "qwen2.5:7b"

    # Default estimated hours by difficulty
    DEFAULT_HOURS = {
        'beginner': 20,
        'intermediate': 40,
        'advanced': 80,
    }

    def __init__(self, user: Optional[User] = None):
        self.user = user
        self.ollama = OllamaClient(model=self.MODEL)

    def generate_projects(
        self,
        target_role: str,
        difficulty_level: str = 'beginner',
        skill_ids: Optional[List[int]] = None,
        language: str = 'en',
        count: int = 3
    ) -> Dict[str, Any]:
        """
        Generate project ideas using AI.

        Args:
            target_role: Target career role
            difficulty_level: beginner/intermediate/advanced
            skill_ids: Optional list of skill IDs to focus on
            language: Response language (en/ru/uz)
            count: Number of project ideas to generate

        Returns:
            Dict with generated projects
        """

        # Validate difficulty
        if difficulty_level not in ('beginner', 'intermediate', 'advanced'):
            difficulty_level = 'beginner'

        # Get skills to include
        skills = self._get_relevant_skills(skill_ids)

        # Use AI to generate projects
        ai_projects = self._ai_generate_projects(
            target_role=target_role,
            difficulty_level=difficulty_level,
            skills=skills,
            language=language,
            count=count
        )

        # Save projects to database
        saved_projects = self._save_projects(ai_projects, target_role, skills)

        return {
            'success': True,
            'target_role': target_role,
            'difficulty_level': difficulty_level,
            'count': len(saved_projects),
            'projects': saved_projects,
        }

    def _get_relevant_skills(
        self,
        skill_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """Get relevant skills for project generation."""

        if skill_ids:
            skills = Skill.objects.filter(skill_id__in=skill_ids)
        elif self.user:
            # Get user's skill gaps
            gap_skill_ids = SkillGap.objects.filter(
                user=self.user,
                status__in=['pending', 'learning']
            ).values_list('skill_id', flat=True)

            # Also include user's existing skills
            user_skill_ids = UserSkill.objects.filter(
                user=self.user
            ).values_list('skill_id', flat=True)

            all_skill_ids = list(set(gap_skill_ids) | set(user_skill_ids))
            skills = Skill.objects.filter(skill_id__in=all_skill_ids)
        else:
            # Get top skills by popularity
            skills = Skill.objects.filter(is_verified=True)[:20]

        return [
            {
                'skill_id': s.skill_id,
                'name': s.name_en,
                'category': s.category,
            }
            for s in skills
        ]

    def _ai_generate_projects(
        self,
        target_role: str,
        difficulty_level: str,
        skills: List[Dict],
        language: str = 'en',
        count: int = 3
    ) -> List[Dict[str, Any]]:
        """Use AI to generate project ideas."""

        language_instruction = {
            'en': 'Write in English.',
            'ru': 'Write in Russian (Русский).',
            'uz': "Write in Uzbek (O'zbek tili).",
        }.get(language, 'Write in English.')

        difficulty_desc = {
            'beginner': 'simple projects for beginners (20-30 hours), basic concepts',
            'intermediate': 'moderate complexity (40-60 hours), multiple features',
            'advanced': 'complex real-world projects (80+ hours), production-ready'
        }.get(difficulty_level, 'simple projects')

        skills_list = ", ".join([s['name'] for s in skills[:15]]) if skills else "general programming skills"

        prompt = f"""Generate {count} portfolio project ideas for a "{target_role}" role.

DIFFICULTY: {difficulty_level.upper()} - {difficulty_desc}

AVAILABLE SKILLS: {skills_list}

REQUIREMENTS:
1. Projects should be practical and portfolio-worthy
2. Each project should help demonstrate skills for {target_role}
3. Include clear learning objectives
4. Projects should be achievable at {difficulty_level} level

{language_instruction}

Return ONLY valid JSON array:
[
    {{
        "title": "Task Management API",
        "description": "Build a REST API for managing tasks with user authentication. Features include CRUD operations, task priorities, due dates, and user permissions. Great for demonstrating backend skills.",
        "difficulty_level": "{difficulty_level}",
        "estimated_hours": 30,
        "core_skills": ["Python", "Django", "REST API"],
        "secondary_skills": ["PostgreSQL", "JWT"]
    }}
]

Generate exactly {count} project ideas. Return ONLY the JSON array:"""

        try:
            response = self.ollama.generate(
                prompt=prompt,
                temperature=0.4,
                max_tokens=3000
            )

            projects = self._parse_ai_response(response)
            return projects[:count]

        except Exception as e:
            logger.error(f"AI project generation failed: {e}")
            return self._fallback_projects(target_role, difficulty_level, skills)

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

    def _fallback_projects(
        self,
        target_role: str,
        difficulty_level: str,
        skills: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Fallback projects when AI is unavailable."""

        skill_names = [s['name'] for s in skills[:5]] if skills else ['Python', 'SQL']
        hours = self.DEFAULT_HOURS.get(difficulty_level, 30)

        return [
            {
                'title': f'{target_role} Portfolio Project',
                'description': f'Build a practical project demonstrating your skills for the {target_role} role. '
                              f'Focus on implementing core features using {", ".join(skill_names[:3])}.',
                'difficulty_level': difficulty_level,
                'estimated_hours': hours,
                'core_skills': skill_names[:3],
                'secondary_skills': skill_names[3:5] if len(skill_names) > 3 else [],
            }
        ]

    def _save_projects(
        self,
        ai_projects: List[Dict[str, Any]],
        target_role: str,
        available_skills: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Save generated projects to database."""

        # Build skill name lookup
        skill_lookup = {s['name'].lower(): s['skill_id'] for s in available_skills}

        # Also get all skills for matching
        all_skills = {
            s.name_en.lower(): s.skill_id
            for s in Skill.objects.all()
        }
        skill_lookup.update(all_skills)

        saved_projects = []

        with transaction.atomic():
            for proj_data in ai_projects:
                # Validate difficulty
                difficulty = proj_data.get('difficulty_level', 'beginner')
                if difficulty not in ('beginner', 'intermediate', 'advanced'):
                    difficulty = 'beginner'

                # Check for duplicate title
                title = proj_data.get('title', 'Untitled Project')[:200]
                if ProjectIdea.objects.filter(title=title, target_role=target_role).exists():
                    # Add unique suffix
                    import uuid
                    title = f"{title} ({str(uuid.uuid4())[:8]})"

                # Create project
                project = ProjectIdea.objects.create(
                    title=title,
                    description=proj_data.get('description', '')[:2000],
                    target_role=target_role[:100],
                    difficulty_level=difficulty,
                    estimated_hours=proj_data.get('estimated_hours', self.DEFAULT_HOURS.get(difficulty, 30)),
                )

                # Link core skills
                core_skills = proj_data.get('core_skills', [])
                for skill_name in core_skills:
                    skill_id = skill_lookup.get(skill_name.lower())
                    if skill_id:
                        ProjectSkill.objects.create(
                            project=project,
                            skill_id=skill_id,
                            importance='core'
                        )

                # Link secondary skills
                secondary_skills = proj_data.get('secondary_skills', [])
                for skill_name in secondary_skills:
                    skill_id = skill_lookup.get(skill_name.lower())
                    if skill_id:
                        ProjectSkill.objects.create(
                            project=project,
                            skill_id=skill_id,
                            importance='secondary'
                        )

                saved_projects.append({
                    'project_id': project.project_id,
                    'title': project.title,
                    'description': project.description,
                    'target_role': project.target_role,
                    'difficulty_level': project.difficulty_level,
                    'estimated_hours': project.estimated_hours,
                    'core_skills': core_skills,
                    'secondary_skills': secondary_skills,
                })

        return saved_projects

    def get_projects_for_role(
        self,
        role_name: str,
        difficulty_level: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get existing project ideas for a role."""

        queryset = ProjectIdea.objects.filter(
            target_role__icontains=role_name
        ).prefetch_related('project_skills__skill')

        if difficulty_level:
            queryset = queryset.filter(difficulty_level=difficulty_level)

        projects = []
        for project in queryset[:limit]:
            core = [ps.skill.name_en for ps in project.project_skills.filter(importance='core')]
            secondary = [ps.skill.name_en for ps in project.project_skills.filter(importance='secondary')]

            # Check if user has started this project
            user_status = None
            if self.user:
                user_project = UserProject.objects.filter(
                    user=self.user,
                    project=project
                ).first()
                if user_project:
                    user_status = user_project.status

            projects.append({
                'project_id': project.project_id,
                'title': project.title,
                'description': project.description,
                'target_role': project.target_role,
                'difficulty_level': project.difficulty_level,
                'estimated_hours': project.estimated_hours,
                'core_skills': core,
                'secondary_skills': secondary,
                'user_status': user_status,
                'created_at': project.created_at.isoformat(),
            })

        return projects

    def get_project_skills(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Get skills for a specific project."""

        try:
            project = ProjectIdea.objects.prefetch_related(
                'project_skills__skill'
            ).get(project_id=project_id)
        except ProjectIdea.DoesNotExist:
            return None

        core_skills = []
        secondary_skills = []

        for ps in project.project_skills.all():
            skill_data = {
                'skill_id': ps.skill.skill_id,
                'name_en': ps.skill.name_en,
                'name_ru': ps.skill.name_ru,
                'name_uz': ps.skill.name_uz,
                'category': ps.skill.category,
            }

            if ps.importance == 'core':
                core_skills.append(skill_data)
            else:
                secondary_skills.append(skill_data)

        return {
            'project_id': project.project_id,
            'title': project.title,
            'description': project.description,
            'difficulty_level': project.difficulty_level,
            'estimated_hours': project.estimated_hours,
            'core_skills': core_skills,
            'secondary_skills': secondary_skills,
            'total_skills': len(core_skills) + len(secondary_skills),
        }

    def start_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Start a project for the user."""

        if not self.user:
            return None

        try:
            project = ProjectIdea.objects.get(project_id=project_id)
        except ProjectIdea.DoesNotExist:
            return None

        from django.utils import timezone

        user_project, created = UserProject.objects.get_or_create(
            user=self.user,
            project=project,
            defaults={
                'status': 'in_progress',
                'started_at': timezone.now(),
            }
        )

        if not created and user_project.status == 'planned':
            user_project.status = 'in_progress'
            user_project.started_at = timezone.now()
            user_project.save()

        return {
            'user_project_id': user_project.user_project_id,
            'project_id': project.project_id,
            'title': project.title,
            'status': user_project.status,
            'started_at': user_project.started_at.isoformat() if user_project.started_at else None,
            'created': created,
        }

    def update_project_status(
        self,
        project_id: int,
        status: str,
        github_url: Optional[str] = None,
        live_demo_url: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update user's project status."""

        if not self.user:
            return None

        valid_statuses = ['planned', 'in_progress', 'completed']
        if status not in valid_statuses:
            return None

        try:
            user_project = UserProject.objects.select_related('project').get(
                user=self.user,
                project_id=project_id
            )
        except UserProject.DoesNotExist:
            return None

        from django.utils import timezone

        old_status = user_project.status
        user_project.status = status

        if status == 'in_progress' and not user_project.started_at:
            user_project.started_at = timezone.now()

        if status == 'completed':
            user_project.completed_at = timezone.now()

        if github_url is not None:
            user_project.github_url = github_url

        if live_demo_url is not None:
            user_project.live_demo_url = live_demo_url

        if notes is not None:
            user_project.notes = notes

        user_project.save()

        return {
            'user_project_id': user_project.user_project_id,
            'project_id': user_project.project_id,
            'title': user_project.project.title,
            'old_status': old_status,
            'new_status': status,
            'started_at': user_project.started_at.isoformat() if user_project.started_at else None,
            'completed_at': user_project.completed_at.isoformat() if user_project.completed_at else None,
            'github_url': user_project.github_url,
            'live_demo_url': user_project.live_demo_url,
        }

    def get_user_projects(
        self,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all projects for the user."""

        if not self.user:
            return []

        queryset = UserProject.objects.filter(
            user=self.user
        ).select_related('project').prefetch_related('project__project_skills__skill')

        if status:
            queryset = queryset.filter(status=status)

        projects = []
        for up in queryset:
            core = [ps.skill.name_en for ps in up.project.project_skills.filter(importance='core')]
            secondary = [ps.skill.name_en for ps in up.project.project_skills.filter(importance='secondary')]

            projects.append({
                'user_project_id': up.user_project_id,
                'project_id': up.project.project_id,
                'title': up.project.title,
                'description': up.project.description,
                'target_role': up.project.target_role,
                'difficulty_level': up.project.difficulty_level,
                'estimated_hours': up.project.estimated_hours,
                'status': up.status,
                'github_url': up.github_url,
                'live_demo_url': up.live_demo_url,
                'notes': up.notes,
                'started_at': up.started_at.isoformat() if up.started_at else None,
                'completed_at': up.completed_at.isoformat() if up.completed_at else None,
                'core_skills': core,
                'secondary_skills': secondary,
                'completion_percentage': up.completion_percentage(),
            })

        return projects

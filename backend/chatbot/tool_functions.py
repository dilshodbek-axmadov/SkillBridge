"""
Tool functions for AI chatbot
These functions are called by the AI to fetch real data
"""
from django.db.models import Count, Avg, Q
from users.models import User, UserProfile
from skills.models import Skill, UserSkill, SkillLevel
from career.models import Role, RoleRequiredSkill, SkillGapAnalysis, MissingSkill, UserRecommendedRole
from jobs.models import JobPosting, JobSkill
from learning.models import LearningResource, LearningRoadmap


# Tool definitions for Groq API
AVAILABLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_user_profile",
            "description": "Get the current user's profile information including their skills, experience level, and career goals",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_skills",
            "description": "Get the list of skills the user has learned or is currently learning",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["all", "learned", "in_progress", "not_started"],
                        "description": "Filter by skill status"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_skill_gap_analysis",
            "description": "Analyze the gap between user's current skills and requirements for a target role",
            "parameters": {
                "type": "object",
                "properties": {
                    "role_name": {
                        "type": "string",
                        "description": "The target role name (e.g., 'Backend Developer', 'Data Scientist')"
                    }
                },
                "required": ["role_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_recommended_roles",
            "description": "Get career roles recommended for the user based on their current skills",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of roles to return"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_market_trends",
            "description": "Get current IT job market trends including in-demand skills and salary information",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Filter by skill category (e.g., 'programming_language', 'framework', 'devops')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of trends to return"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_learning_recommendations",
            "description": "Get personalized learning resource recommendations for a specific skill",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_name": {
                        "type": "string",
                        "description": "Name of the skill to get learning resources for"
                    }
                },
                "required": ["skill_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_career_paths",
            "description": "Compare two or more career paths in terms of salary, demand, and required skills",
            "parameters": {
                "type": "object",
                "properties": {
                    "role_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of role names to compare"
                    }
                },
                "required": ["role_names"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_job_opportunities",
            "description": "Get current job opportunities matching user's skills or a specific role",
            "parameters": {
                "type": "object",
                "properties": {
                    "role_name": {
                        "type": "string",
                        "description": "Optional role name to filter jobs"
                    },
                    "location": {
                        "type": "string",
                        "description": "Optional location to filter jobs (e.g., 'Tashkent', 'Samarkand')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of jobs to return"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_roadmap",
            "description": "Get the user's current learning roadmap and progress",
            "parameters": {
                "type": "object",
                "properties": {
                },
                "required": []
            }
        }
    }
]


def execute_tool(tool_name, args):
    """Execute a tool function and return the result"""
    tools = {
        "get_user_profile": get_user_profile,
        "get_user_skills": get_user_skills,
        "get_skill_gap_analysis": get_skill_gap_analysis,
        "get_recommended_roles": get_recommended_roles,
        "get_market_trends": get_market_trends,
        "get_learning_recommendations": get_learning_recommendations,
        "compare_career_paths": compare_career_paths,
        "get_job_opportunities": get_job_opportunities,
        "get_user_roadmap": get_user_roadmap
    }

    if tool_name in tools:
        try:
            return tools[tool_name](**args)
        except Exception as e:
            return {"error": str(e)}
    else:
        return {"error": f"Unknown tool: {tool_name}"}


def get_user_profile(user_id):
    """Get user profile information"""
    try:
        user = User.objects.get(id=user_id)
        profile = getattr(user, 'userprofile', None)

        # Get skill counts
        skills = UserSkill.objects.filter(user=user)
        learned_count = skills.filter(status='learned').count()
        in_progress_count = skills.filter(status='in_progress').count()

        return {
            "name": f"{user.first_name} {user.last_name}".strip() or user.email,
            "email": user.email,
            "experience_level": profile.experience_level if profile else None,
            "current_role": profile.current_role if profile else None,
            "bio": profile.bio if profile else None,
            "skills_learned": learned_count,
            "skills_in_progress": in_progress_count,
            "profile_completion": user.profile_completion_percentage,
            "onboarding_completed": user.onboarding_completed,
            "location": user.location
        }
    except User.DoesNotExist:
        return {"error": "User not found"}


def get_user_skills(user_id, status="all"):
    """Get user's skills with details"""
    try:
        user = User.objects.get(id=user_id)
        queryset = UserSkill.objects.filter(user=user).select_related('skill', 'level')

        if status != "all":
            queryset = queryset.filter(status=status)

        skills = []
        for us in queryset:
            skills.append({
                "name": us.skill.name,
                "category": us.skill.category,
                "level": us.level.name if us.level else "Not specified",
                "status": us.status,
                "learning_duration": us.get_learning_duration_display()
            })

        return {
            "total_count": len(skills),
            "skills": skills
        }
    except User.DoesNotExist:
        return {"error": "User not found"}


def get_skill_gap_analysis(user_id, role_name):
    """Analyze skill gap for a target role"""
    try:
        user = User.objects.get(id=user_id)

        # Find the role
        role = Role.objects.filter(
            Q(title__iexact=role_name) | Q(title__icontains=role_name)
        ).first()

        if not role:
            # Return general advice if role not found
            return {
                "error": f"Role '{role_name}' not found in our database",
                "suggestion": "Try searching for similar roles like: Backend Developer, Frontend Developer, Data Scientist, DevOps Engineer"
            }

        # Get required skills for the role
        required_skills = RoleRequiredSkill.objects.filter(role=role).select_related('skill', 'minimum_level')

        # Get user's current skills
        user_skills = {us.skill_id: us for us in UserSkill.objects.filter(user=user, status='learned').select_related('skill', 'level')}

        matching_skills = []
        missing_skills = []
        partially_matching = []

        for req in required_skills:
            if req.skill_id in user_skills:
                user_skill = user_skills[req.skill_id]
                user_level = user_skill.level.level_order if user_skill.level else 0
                required_level = req.minimum_level.level_order if req.minimum_level else 2

                if user_level >= required_level:
                    matching_skills.append({
                        "skill": req.skill.name,
                        "importance": req.importance,
                        "your_level": user_skill.level.name if user_skill.level else "Unknown"
                    })
                else:
                    partially_matching.append({
                        "skill": req.skill.name,
                        "importance": req.importance,
                        "your_level": user_skill.level.name if user_skill.level else "Unknown",
                        "required_level": req.minimum_level.name if req.minimum_level else "Intermediate"
                    })
            else:
                missing_skills.append({
                    "skill": req.skill.name,
                    "importance": req.importance,
                    "required_level": req.minimum_level.name if req.minimum_level else "Intermediate"
                })

        total_required = len(required_skills)
        match_percentage = (len(matching_skills) / total_required * 100) if total_required > 0 else 0

        return {
            "role": role.title,
            "role_description": role.description,
            "match_percentage": round(match_percentage, 1),
            "matching_skills": matching_skills,
            "partially_matching_skills": partially_matching,
            "missing_skills": missing_skills,
            "salary_range": {
                "min": float(role.average_salary_min) if role.average_salary_min else None,
                "max": float(role.average_salary_max) if role.average_salary_max else None,
                "currency": "UZS"
            },
            "demand_score": role.demand_score,
            "recommendation": _get_gap_recommendation(match_percentage, len(missing_skills))
        }
    except User.DoesNotExist:
        return {"error": "User not found"}


def _get_gap_recommendation(match_percentage, missing_count):
    """Generate recommendation based on gap analysis"""
    if match_percentage >= 80:
        return "You're almost job-ready for this role! Focus on polishing your existing skills and gaining practical experience."
    elif match_percentage >= 60:
        return f"Good progress! You have a solid foundation. Focus on learning the {missing_count} missing skills to become competitive."
    elif match_percentage >= 40:
        return "You're on your way! Create a learning roadmap to systematically acquire the missing skills."
    else:
        return "This role requires significant skill development. Consider starting with foundational skills and building up gradually."


def get_recommended_roles(user_id, limit=5):
    """Get recommended roles for user"""
    try:
        user = User.objects.get(id=user_id)

        # Check for existing recommendations
        recommendations = UserRecommendedRole.objects.filter(
            user=user, is_active=True
        ).select_related('role')[:limit]

        if recommendations:
            return {
                "recommended_roles": [
                    {
                        "role": rec.role.title,
                        "match_percentage": rec.match_percentage,
                        "readiness_score": rec.readiness_score,
                        "missing_skills_count": rec.missing_skills_count,
                        "description": rec.role.description,
                        "demand_score": rec.role.demand_score
                    }
                    for rec in recommendations
                ]
            }

        # Generate on-the-fly recommendations based on user skills
        user_skill_ids = set(UserSkill.objects.filter(
            user=user, status='learned'
        ).values_list('skill_id', flat=True))

        roles = Role.objects.all()
        role_matches = []

        for role in roles:
            required = RoleRequiredSkill.objects.filter(role=role)
            required_ids = set(required.values_list('skill_id', flat=True))

            if not required_ids:
                continue

            matching = user_skill_ids & required_ids
            match_pct = len(matching) / len(required_ids) * 100

            role_matches.append({
                "role": role.title,
                "match_percentage": round(match_pct, 1),
                "missing_skills_count": len(required_ids - user_skill_ids),
                "description": role.description,
                "demand_score": role.demand_score
            })

        # Sort by match percentage
        role_matches.sort(key=lambda x: x['match_percentage'], reverse=True)

        return {"recommended_roles": role_matches[:limit]}

    except User.DoesNotExist:
        return {"error": "User not found"}


def get_market_trends(category=None, limit=10):
    """Get market trends for skills"""
    queryset = Skill.objects.all()

    if category:
        queryset = queryset.filter(category=category)

    # Get top skills by popularity
    top_skills = queryset.order_by('-popularity_score')[:limit]

    # Get job counts per skill
    skills_data = []
    for skill in top_skills:
        job_count = JobSkill.objects.filter(skill=skill).count()
        skills_data.append({
            "skill": skill.name,
            "category": skill.get_category_display() if hasattr(skill, 'get_category_display') else skill.category,
            "popularity_score": skill.popularity_score,
            "job_count": job_count
        })

    # Get category distribution
    category_stats = Skill.objects.values('category').annotate(
        count=Count('id'),
        avg_popularity=Avg('popularity_score')
    ).order_by('-avg_popularity')

    return {
        "top_skills": skills_data,
        "category_trends": list(category_stats),
        "total_jobs_in_market": JobPosting.objects.filter(is_active=True).count()
    }


def get_learning_recommendations(skill_name, user_id=None):
    """Get learning resources for a skill"""
    # Find the skill
    skill = Skill.objects.filter(
        Q(name__iexact=skill_name) | Q(name__icontains=skill_name)
    ).first()

    if not skill:
        return {
            "error": f"Skill '{skill_name}' not found",
            "suggestion": "Try searching for a more common skill name"
        }

    # Get learning resources for this skill
    resources = LearningResource.objects.filter(skill=skill).order_by('-rating')[:10]

    resources_data = []
    for res in resources:
        resources_data.append({
            "title": res.title,
            "type": res.resource_type,
            "platform": res.platform,
            "url": res.url,
            "duration_hours": res.duration_hours,
            "is_free": res.is_free,
            "rating": float(res.rating) if res.rating else None,
            "language": res.language
        })

    # Get related skills
    related_skills = Skill.objects.filter(
        category=skill.category
    ).exclude(id=skill.id)[:5]

    return {
        "skill": skill.name,
        "category": skill.category,
        "description": skill.description,
        "learning_resources": resources_data,
        "related_skills": [s.name for s in related_skills],
        "popularity_score": skill.popularity_score
    }


def compare_career_paths(role_names):
    """Compare multiple career paths"""
    comparisons = []

    for role_name in role_names:
        role = Role.objects.filter(
            Q(title__iexact=role_name) | Q(title__icontains=role_name)
        ).first()

        if role:
            required_skills = RoleRequiredSkill.objects.filter(role=role).select_related('skill')
            critical_skills = required_skills.filter(importance='critical')

            comparisons.append({
                "role": role.title,
                "description": role.description,
                "salary_range": {
                    "min": float(role.average_salary_min) if role.average_salary_min else None,
                    "max": float(role.average_salary_max) if role.average_salary_max else None,
                    "currency": "UZS"
                },
                "demand_score": role.demand_score,
                "growth_potential": role.growth_potential,
                "required_skills_count": required_skills.count(),
                "critical_skills": [rs.skill.name for rs in critical_skills]
            })
        else:
            comparisons.append({
                "role": role_name,
                "error": "Role not found in database"
            })

    return {"comparison": comparisons}


def get_job_opportunities(user_id=None, role_name=None, location=None, limit=10):
    """Get job opportunities"""
    queryset = JobPosting.objects.filter(is_active=True)

    if role_name:
        queryset = queryset.filter(
            Q(title__icontains=role_name) | Q(description_text__icontains=role_name) | Q(key_skills__icontains=role_name)
        )
    
    if location:
        queryset = queryset.filter(location__icontains=location)

    if user_id:
        try:
            user = User.objects.get(id=user_id)
            user_skill_ids = UserSkill.objects.filter(
                user=user, status='learned'
            ).values_list('skill_id', flat=True)

            # Prioritize jobs matching user skills
            queryset = queryset.annotate(
                matching_skills=Count(
                    'job_skills',  
                    filter=Q(job_skills__skill_id__in=user_skill_ids) 
                )
            ).order_by('-matching_skills', '-published_at')
        except User.DoesNotExist:
            queryset = queryset.order_by('-published_at')
    else:
        queryset = queryset.order_by('-published_at')

    jobs = queryset[:limit]

    jobs_data = []
    for job in jobs:
        required_skills = JobSkill.objects.filter(
            job_posting=job, 
            is_required=True
        ).select_related('skill')

        jobs_data.append({
            "title": job.title,
            "company": job.company_name,
            "location": job.location,
            "work_type": job.work_type,
            "employment_type": job.employment_type,
            "salary_min": float(job.salary_min) if job.salary_min else None,
            "salary_max": float(job.salary_max) if job.salary_max else None,
            "salary_currency": job.salary_currency,
            "experience_required": job.experience_required,
            "published_at": job.published_at.isoformat() if job.published_at else None,
            "required_skills": [js.skill.name for js in required_skills],
            "posting_url": job.posting_url if hasattr(job, 'posting_url') else (job.alternate_url or ""),
            "is_fresh": job.is_fresh(),
            "age_days": job.get_age_in_days()
        })

    return {
        "total_found": queryset.count(),
        "jobs": jobs_data
    }

def get_user_roadmap(user_id):
    """Get user's learning roadmap"""
    try:
        user = User.objects.get(id=user_id)

        roadmaps = LearningRoadmap.objects.filter(user=user).select_related('role')

        if not roadmaps:
            return {
                "message": "No learning roadmap found",
                "suggestion": "Consider creating a learning roadmap based on your career goals"
            }

        roadmaps_data = []
        for roadmap in roadmaps:
            # Get current item in progress
            current_item = roadmap.roadmap_items.filter(status='in_progress').first()
            next_item = roadmap.get_next_skill()

            roadmaps_data.append({
                "roadmap_id": roadmap.id,
                "target_role": roadmap.role.title if roadmap.role else None,
                "completion_percentage": roadmap.completion_percentage,
                "created_date": roadmap.created_date.isoformat(),
                "is_active": roadmap.is_active,
                "current_skill": current_item.skill.name if current_item else None,
                "next_skill": next_item.skill.name if next_item else None,
                "estimated_completion_date": roadmap.estimated_completion_date.isoformat() if roadmap.estimated_completion_date else None
            })

        return {"roadmaps": roadmaps_data}

    except User.DoesNotExist:
        return {"error": "User not found"}

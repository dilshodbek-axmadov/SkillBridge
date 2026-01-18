"""
Career services for skill gap analysis and recommendations
"""
from career.models import (
    Role, RoleRequiredSkill, SkillGapAnalysis, 
    MissingSkill, UserRecommendedRole
)
from skills.models import UserSkill


class SkillGapAnalyzer:
    """
    Analyze skill gaps between user and target role
    """
    
    def analyze_user_for_role(self, user, role):
        """
        Perform skill gap analysis for a user targeting a specific role
        
        Args:
            user: User object
            role: Role object
            
        Returns:
            dict with analysis results
        """
        # Get user's current skills
        user_skills = set(
            UserSkill.objects.filter(
                user=user,
                status='learned'
            ).values_list('skill_id', flat=True)
        )
        
        # Get required skills for role
        required_skills = RoleRequiredSkill.objects.filter(role=role)
        required_skill_ids = set(required_skills.values_list('skill_id', flat=True))
        
        # Calculate match
        matching_skills = user_skills & required_skill_ids
        missing_skill_ids = required_skill_ids - user_skills
        
        # Calculate match percentage
        if len(required_skill_ids) > 0:
            match_percentage = (len(matching_skills) / len(required_skill_ids)) * 100
        else:
            match_percentage = 0
        
        # Determine readiness level
        if match_percentage >= 80:
            readiness_level = 'job_ready'
            readiness_score = match_percentage
        elif match_percentage >= 50:
            readiness_level = 'partially_ready'
            readiness_score = match_percentage * 0.8
        else:
            readiness_level = 'not_ready'
            readiness_score = match_percentage * 0.6
        
        # Estimate learning time (4 weeks per missing critical skill, 2 weeks per important)
        estimated_weeks = 0
        for req_skill in required_skills:
            if req_skill.skill_id in missing_skill_ids:
                if req_skill.importance == 'critical':
                    estimated_weeks += 4
                elif req_skill.importance == 'important':
                    estimated_weeks += 2
                else:
                    estimated_weeks += 1
        
        # Create or update gap analysis
        gap_analysis, created = SkillGapAnalysis.objects.update_or_create(
            user=user,
            role=role,
            defaults={
                'overall_match_percentage': match_percentage,
                'readiness_level': readiness_level,
                'estimated_learning_time_weeks': estimated_weeks
            }
        )
        
        # Clear old missing skills
        gap_analysis.missing_skills.all().delete()
        
        # Create missing skill records
        for req_skill in required_skills:
            if req_skill.skill_id in missing_skill_ids:
                # Determine priority based on importance
                if req_skill.importance == 'critical':
                    priority = 'high'
                elif req_skill.importance == 'important':
                    priority = 'medium'
                else:
                    priority = 'low'
                
                # Estimate learning time
                if priority == 'high':
                    learning_weeks = 4
                elif priority == 'medium':
                    learning_weeks = 2
                else:
                    learning_weeks = 1
                
                MissingSkill.objects.create(
                    gap_analysis=gap_analysis,
                    skill=req_skill.skill,
                    required_level=req_skill.minimum_level,
                    current_level=None,
                    priority=priority,
                    estimated_learning_weeks=learning_weeks
                )
        
        # Create or update recommended role
        UserRecommendedRole.objects.update_or_create(
            user=user,
            role=role,
            defaults={
                'match_percentage': match_percentage,
                'readiness_score': readiness_score,
                'missing_skills_count': len(missing_skill_ids),
                'is_active': True
            }
        )
        
        return {
            'match_percentage': match_percentage,
            'readiness_level': readiness_level,
            'readiness_score': readiness_score,
            'matching_skills_count': len(matching_skills),
            'missing_skills_count': len(missing_skill_ids),
            'estimated_learning_weeks': estimated_weeks,
            'gap_analysis_id': gap_analysis.id
        }
    
    def get_user_skill_gaps(self, user, role):
        """
        Get detailed skill gaps for a user and role
        
        Returns:
            dict with matching skills, missing skills, and recommendations
        """
        # Get user's current skills with details
        user_skills_qs = UserSkill.objects.filter(
            user=user,
            status='learned'
        ).select_related('skill', 'level')
        
        user_skills_dict = {
            us.skill_id: {
                'skill_name': us.skill.name,
                'level': us.level.name if us.level else 'Unknown',
                'level_order': us.level.level_order if us.level else 0
            }
            for us in user_skills_qs
        }
        
        # Get required skills with details
        required_skills_qs = RoleRequiredSkill.objects.filter(
            role=role
        ).select_related('skill', 'minimum_level')
        
        matching_skills = []
        missing_skills = []
        
        for req_skill in required_skills_qs:
            if req_skill.skill_id in user_skills_dict:
                # User has this skill
                user_skill = user_skills_dict[req_skill.skill_id]
                
                # Check if level is sufficient
                required_level_order = req_skill.minimum_level.level_order if req_skill.minimum_level else 1
                user_level_order = user_skill['level_order']
                
                is_level_sufficient = user_level_order >= required_level_order
                
                matching_skills.append({
                    'skill_name': req_skill.skill.name,
                    'user_level': user_skill['level'],
                    'required_level': req_skill.minimum_level.name if req_skill.minimum_level else 'Any',
                    'is_level_sufficient': is_level_sufficient,
                    'importance': req_skill.importance
                })
            else:
                # User doesn't have this skill
                missing_skills.append({
                    'skill_name': req_skill.skill.name,
                    'required_level': req_skill.minimum_level.name if req_skill.minimum_level else 'Any',
                    'importance': req_skill.importance,
                    'priority': 'high' if req_skill.importance == 'critical' else 'medium'
                })
        
        return {
            'matching_skills': matching_skills,
            'missing_skills': missing_skills,
            'total_required': len(required_skills_qs),
            'total_matching': len(matching_skills),
            'total_missing': len(missing_skills)
        }
    
    def recommend_roles_for_user(self, user, top_n=5):
        """
        Recommend best matching roles for a user based on their current skills
        
        Args:
            user: User object
            top_n: Number of top recommendations to return
            
        Returns:
            list of recommended roles with match scores
        """
        # Get user's skills
        user_skill_ids = set(
            UserSkill.objects.filter(
                user=user,
                status='learned'
            ).values_list('skill_id', flat=True)
        )
        
        if not user_skill_ids:
            # User has no skills yet, return popular roles
            return Role.objects.order_by('-demand_score')[:top_n]
        
        # Get all roles
        roles = Role.objects.all()
        
        role_scores = []
        
        for role in roles:
            # Get required skills for this role
            required_skill_ids = set(
                RoleRequiredSkill.objects.filter(
                    role=role
                ).values_list('skill_id', flat=True)
            )
            
            if not required_skill_ids:
                continue
            
            # Calculate match
            matching = user_skill_ids & required_skill_ids
            match_percentage = (len(matching) / len(required_skill_ids)) * 100
            
            # Calculate score (combine match percentage with demand score)
            score = (match_percentage * 0.7) + (role.demand_score * 0.3)
            
            role_scores.append({
                'role': role,
                'match_percentage': match_percentage,
                'score': score,
                'missing_skills_count': len(required_skill_ids - user_skill_ids)
            })
        
        # Sort by score
        role_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top N
        return role_scores[:top_n]


class RoadmapGenerator:
    """
    Generate learning roadmaps for users
    """
    
    def generate_roadmap(self, user, role):
        """
        Generate a learning roadmap for a user to achieve a target role
        
        Args:
            user: User object
            role: Role object
            
        Returns:
            LearningRoadmap object
        """
        from learning.models import LearningRoadmap, RoadmapItem
        from skills.models import SkillLevel
        
        # First, perform gap analysis
        analyzer = SkillGapAnalyzer()
        gap_analysis = analyzer.analyze_user_for_role(user, role)
        
        # Get the SkillGapAnalysis object
        gap_analysis_obj = SkillGapAnalysis.objects.get(
            id=gap_analysis['gap_analysis_id']
        )
        
        # Create or get roadmap
        roadmap, created = LearningRoadmap.objects.get_or_create(
            user=user,
            role=role,
            defaults={
                'is_active': True,
                'completion_percentage': 0.0
            }
        )
        
        # Clear existing roadmap items if recreating
        if not created:
            roadmap.roadmap_items.all().delete()
        
        # Get missing skills ordered by priority
        missing_skills = gap_analysis_obj.missing_skills.all().order_by(
            '-priority', 'skill__name'
        )
        
        # Create roadmap items
        sequence = 1
        for missing_skill in missing_skills:
            # Determine priority
            if missing_skill.priority == 'high':
                priority = 'high'
            elif missing_skill.priority == 'medium':
                priority = 'medium'
            else:
                priority = 'low'
            
            RoadmapItem.objects.create(
                roadmap=roadmap,
                skill=missing_skill.skill,
                sequence_order=sequence,
                status='pending',
                priority=priority,
                estimated_duration_weeks=missing_skill.estimated_learning_weeks
            )
            sequence += 1
        
        # Calculate estimated completion date
        from datetime import timedelta
        from django.utils import timezone
        
        total_weeks = gap_analysis['estimated_learning_weeks']
        estimated_date = timezone.now().date() + timedelta(weeks=total_weeks)
        roadmap.estimated_completion_date = estimated_date
        roadmap.save()
        
        return roadmap
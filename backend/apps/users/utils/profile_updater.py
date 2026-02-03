"""
Profile Updater
===============
backend/apps/users/utils/profile_updater.py

Updates user profile from CV extraction.
CRITICAL: Accurate data storage for learning roadmap.
"""

import logging
from typing import Dict
from django.db import transaction

from apps.users.models import User
from apps.skills.models import UserSkill

logger = logging.getLogger(__name__)


class ProfileUpdater:
    """Update user profile from CV data."""
    
    @transaction.atomic
    def update_from_cv(self, user: User, extracted_data: Dict) -> Dict:
        """
        Update profile from extracted CV data.
        
        Returns:
            {
                'updated_fields': List[str],
                'skills_added': int,
                'skills_total': int,
                'profile_completed': bool
            }
        """
        try:
            profile = user.profile
            updated_fields = []
            
            # 1. Job position
            if extracted_data.get('job_position'):
                profile.current_job_position = extracted_data['job_position']
                updated_fields.append('job_position')
            
            # 2. Experience level (CRITICAL for roadmap)
            if extracted_data.get('experience_level'):
                profile.experience_level = extracted_data['experience_level']
                updated_fields.append('experience_level')
            
            # 3. Bio
            if extracted_data.get('bio'):
                profile.bio = extracted_data['bio'][:500]
                updated_fields.append('bio')
            
            # 4. Phone
            if extracted_data.get('phone') and not user.phone:
                user.phone = extracted_data['phone']
                user.save()
                updated_fields.append('phone')
            
            # 5. Save profile
            profile.profile_source = 'cv_upload'
            profile.save()
            
            # 6. Add skills (CRITICAL for roadmap)
            skills_result = self._add_skills(user, extracted_data)
            
            # 7. Mark profile complete
            profile_complete = self._check_completeness(profile, user)
            if profile_complete:
                user.profile_completed = True
                user.save()
            
            logger.info(f"✅ Updated: {len(updated_fields)} fields, "
                       f"{skills_result['added']} skills added")
            
            return {
                'updated_fields': updated_fields,
                'skills_added': skills_result['added'],
                'skills_total': skills_result['total'],
                'profile_completed': profile_complete
            }
        
        except Exception as e:
            logger.error(f"❌ Update failed: {e}", exc_info=True)
            raise
    
    def _add_skills(self, user: User, extracted_data: Dict) -> Dict:
        """Add skills to profile."""
        skill_ids = extracted_data.get('skills', [])
        years = extracted_data.get('years_of_experience', 0.0)
        
        # Determine proficiency
        proficiency = self._get_proficiency(years)
        
        added = 0
        for skill_id in skill_ids:
            try:
                _, created = UserSkill.objects.get_or_create(
                    user=user,
                    skill_id=skill_id,
                    defaults={
                        'source': 'cv',
                        'proficiency_level': proficiency,
                        'years_of_experience': years
                    }
                )
                if created:
                    added += 1
            except Exception as e:
                logger.warning(f"Failed to add skill {skill_id}: {e}")
        
        total = UserSkill.objects.filter(user=user).count()
        
        return {'added': added, 'total': total}
    
    def _get_proficiency(self, years: float) -> str:
        """Determine skill proficiency from years."""
        if years == 0:
            return 'beginner'
        elif years < 2:
            return 'beginner'
        elif years < 4:
            return 'intermediate'
        elif years < 7:
            return 'advanced'
        else:
            return 'expert'
    
    def _check_completeness(self, profile, user: User) -> bool:
        """Check if profile is complete for roadmap."""
        has_position = bool(profile.current_job_position or profile.desired_role)
        has_skills = UserSkill.objects.filter(user=user).count() >= 3
        has_level = bool(profile.experience_level)
        
        return has_position and has_skills and has_level
    
    def validate_for_roadmap(self, user: User) -> Dict:
        """
        Validate profile for learning roadmap.
        
        Returns:
            {
                'ready': bool,
                'missing': List[str],
                'warnings': List[str]
            }
        """
        missing = []
        warnings = []
        
        try:
            profile = user.profile
            
            # Required
            if not (profile.current_job_position or profile.desired_role):
                missing.append('job_position')
            
            skills_count = UserSkill.objects.filter(user=user).count()
            if skills_count < 3:
                missing.append(f'skills (have {skills_count}, need 3+)')
            
            if not profile.experience_level:
                missing.append('experience_level')
            
            # Warnings
            if skills_count < 5:
                warnings.append(f'Only {skills_count} skills - limited roadmap')
            
            return {
                'ready': len(missing) == 0,
                'missing': missing,
                'warnings': warnings
            }
        
        except Exception as e:
            return {
                'ready': False,
                'missing': ['error'],
                'warnings': [str(e)]
            }
"""
Job Skill Linker (Phase C: Linking)
====================================
backend/apps/skills/utils/job_skill_linker.py

Links jobs to canonical skills using resolved aliases.

Workflow:
1. Get job-alias mappings (JobSkillExtraction)
2. Check if alias is resolved
3. Create JobSkill link if resolved
4. Track statistics
"""

import logging
from typing import Dict, Optional
from django.db import transaction
from django.db.models import Count, Q
from apps.jobs.models import JobPosting, JobSkill
from apps.skills.models import SkillAlias, Skill
from apps.jobs.models import JobSkillExtraction

logger = logging.getLogger(__name__)


class JobSkillLinker:
    """
    Links jobs to canonical skills via resolved aliases.
    """
    
    def __init__(self):
        self.stats = {
            'total_jobs': 0,
            'jobs_processed': 0,
            'jobs_skipped': 0,
            'job_skills_created': 0,
            'job_skills_existing': 0,
            'unresolved_aliases_skipped': 0,
            'errors': 0,
        }
    
    def link_all_jobs(self, limit: Optional[int] = None) -> Dict:
        """
        Link all jobs to canonical skills.
        
        Args:
            limit: Maximum number of jobs to process (None = all)
        
        Returns:
            Statistics dict
        """
        logger.info("Starting job-skill linking...")
        
        # Get all jobs
        jobs = JobPosting.objects.all()
        
        if limit:
            jobs = jobs[:limit]
        
        self.stats['total_jobs'] = jobs.count()
        
        logger.info(f"Processing {self.stats['total_jobs']} jobs")
        
        # Process each job
        for i, job in enumerate(jobs, 1):
            try:
                if i % 100 == 0:
                    logger.info(f"Progress: {i}/{self.stats['total_jobs']}")
                
                result = self.link_single_job(job)
                
                if result['processed']:
                    self.stats['jobs_processed'] += 1
                else:
                    self.stats['jobs_skipped'] += 1
                
                self.stats['job_skills_created'] += result['created']
                self.stats['job_skills_existing'] += result['existing']
                self.stats['unresolved_aliases_skipped'] += result['unresolved']
            
            except Exception as e:
                logger.error(f"Error linking job {job.job_id}: {e}")
                self.stats['errors'] += 1
        
        return self.stats
    
    def link_single_job(self, job: JobPosting) -> Dict:
        """
        Link one job to its canonical skills.
        
        Uses JobSkillExtraction table to find which aliases
        were extracted from this job, then creates JobSkill
        links for resolved aliases.
        
        Returns:
            {
                'processed': bool,
                'created': int,
                'existing': int,
                'unresolved': int
            }
        """
        result = {
            'processed': False,
            'created': 0,
            'existing': 0,
            'unresolved': 0,
        }
        
        # Get all aliases extracted from this job
        extractions = JobSkillExtraction.objects.filter(
            job_posting=job
        ).select_related('alias', 'alias__skill')
        
        if not extractions.exists():
            logger.debug(f"Job {job.job_id}: No extractions found")
            return result
        
        result['processed'] = True
        
        with transaction.atomic():
            for extraction in extractions:
                alias = extraction.alias
                
                # Check if alias is resolved
                if alias.status != 'resolved' or not alias.skill:
                    result['unresolved'] += 1
                    logger.debug(f"  - Skipped unresolved: {alias.alias_text}")
                    continue
                
                # Create JobSkill link
                job_skill, created = JobSkill.objects.get_or_create(
                    job_posting=job,
                    skill=alias.skill,
                    defaults={'importance': extraction.importance}
                )
                
                if created:
                    result['created'] += 1
                    logger.debug(f"  + Created link: {alias.skill.name_en}")
                else:
                    result['existing'] += 1
                    logger.debug(f"  = Existing link: {alias.skill.name_en}")
        
        return result
    
    def relink_job(self, job_id: int) -> Dict:
        """
        Relink a specific job (useful after re-resolution).
        
        Args:
            job_id: Job posting ID
        
        Returns:
            Statistics dict
        """
        try:
            job = JobPosting.objects.get(job_id=job_id)
            
            # Delete existing links
            JobSkill.objects.filter(job_posting=job).delete()
            
            # Relink
            return self.link_single_job(job)
        
        except JobPosting.DoesNotExist:
            logger.error(f"Job {job_id} not found")
            return {'processed': False, 'created': 0, 'existing': 0, 'unresolved': 0}
    
    def get_stats(self) -> Dict:
        """Get linking statistics."""
        return self.stats.copy()
    
    def print_stats(self):
        """Print linking statistics."""
        print("\n" + "="*60)
        print("PHASE C: LINKING COMPLETE")
        print("="*60)
        print(f"\n📊 JOB PROCESSING:")
        print(f"  Total jobs:          {self.stats['total_jobs']:>6}")
        print(f"  Jobs processed:      {self.stats['jobs_processed']:>6}")
        print(f"  Jobs skipped:        {self.stats['jobs_skipped']:>6}")
        
        print(f"\n🔗 JOB-SKILL LINKS:")
        print(f"  Links created:       {self.stats['job_skills_created']:>6}")
        print(f"  Links existing:      {self.stats['job_skills_existing']:>6}")
        print(f"  Unresolved skipped:  {self.stats['unresolved_aliases_skipped']:>6}")
        
        if self.stats['errors'] > 0:
            print(f"\n⚠️  ERRORS:")
            print(f"  Errors:              {self.stats['errors']:>6}")
        
        # Calculate success rate
        total_processed = self.stats['jobs_processed']
        if total_processed > 0:
            avg_skills = self.stats['job_skills_created'] / total_processed
            print(f"\n📈 AVERAGES:")
            print(f"  Avg skills/job:      {avg_skills:>6.1f}")
        
        print("\n" + "="*60)
        print("ALL PHASES COMPLETE! Jobs are now linked to canonical skills.")
        print("="*60 + "\n")


# ==================== UTILITY FUNCTIONS ====================

def get_linking_summary() -> Dict:
    """
    Get summary of linking status across all jobs.
    """
    # Total aliases
    total_aliases = SkillAlias.objects.count()

    # Aliases by status
    status_counts = SkillAlias.objects.values('status').annotate(
        count=Count('alias_id')
    )

    # Jobs with/without skills
    total_jobs = JobPosting.objects.count()
    jobs_with_skills = JobPosting.objects.filter(
        job_skills__isnull=False
    ).distinct().count()

    # Total job-skill links
    total_job_skills = JobSkill.objects.count()

    # Canonical skills
    total_skills = Skill.objects.count()
    verified_skills = Skill.objects.filter(is_verified=True).count()

    return {
        'aliases': {
            'total': total_aliases,
            'by_status': {item['status']: item['count'] for item in status_counts}
        },
        'skills': {
            'total': total_skills,
            'verified': verified_skills,
            'unverified': total_skills - verified_skills
        },
        'jobs': {
            'total': total_jobs,
            'with_skills': jobs_with_skills,
            'without_skills': total_jobs - jobs_with_skills
        },
        'job_skills': {
            'total': total_job_skills,
            'avg_per_job': total_job_skills / total_jobs if total_jobs > 0 else 0
        }
    }


def print_linking_summary():
    """Print linking summary in readable format."""
    summary = get_linking_summary()
    
    print("\n" + "="*60)
    print("SKILL SYSTEM SUMMARY")
    print("="*60)
    
    print(f"\n🏷️  SKILL ALIASES:")
    print(f"  Total aliases:       {summary['aliases']['total']:>6}")
    for status, count in summary['aliases']['by_status'].items():
        print(f"  - {status:20s} {count:>6}")
    
    print(f"\n🎯 CANONICAL SKILLS:")
    print(f"  Total skills:        {summary['skills']['total']:>6}")
    print(f"  - Verified:          {summary['skills']['verified']:>6}")
    print(f"  - Unverified:        {summary['skills']['unverified']:>6}")
    
    print(f"\n💼 JOBS:")
    print(f"  Total jobs:          {summary['jobs']['total']:>6}")
    print(f"  - With skills:       {summary['jobs']['with_skills']:>6}")
    print(f"  - Without skills:    {summary['jobs']['without_skills']:>6}")
    
    print(f"\n🔗 JOB-SKILL LINKS:")
    print(f"  Total links:         {summary['job_skills']['total']:>6}")
    print(f"  Avg per job:         {summary['job_skills']['avg_per_job']:>6.1f}")
    
    print("\n" + "="*60 + "\n")
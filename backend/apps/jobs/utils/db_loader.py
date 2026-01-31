"""
Database Loader (UPDATED - Phase A: Ingestion)
===============================================
backend/apps/jobs/utils/db_loader.py

Phase A: Raw skill extraction and storage
- Extract skills from jobs
- Store in skill_aliases with status='unresolved'
- Track job-alias mapping in job_skill_extractions
- Do NOT create canonical skills yet
"""

import logging
from typing import Dict, List, Tuple
from django.db import transaction
from apps.jobs.models import JobPosting
from apps.skills.models import SkillAlias
from apps.jobs.models import JobSkillExtraction

logger = logging.getLogger(__name__)


class DatabaseLoader:
    """
    Phase A: Loads job postings and raw skill aliases.
    
    Workflow:
    1. Load job posting
    2. Extract raw skills → SkillAlias (unresolved)
    3. Track job-alias mapping → JobSkillExtraction
    4. Skills table remains untouched (resolution happens later)
    """
    
    def __init__(self):
        self.stats = {
            'jobs_created': 0,
            'jobs_updated': 0,
            'jobs_skipped': 0,
            'aliases_created': 0,
            'aliases_reused': 0,
            'extractions_created': 0,
            'errors': 0,
        }
    
    def load_vacancy(self, vacancy_data: Dict, skills_data: List[Dict]) -> Tuple[JobPosting, Dict]:
        """
        Load single vacancy with raw skill aliases.
        
        Args:
            vacancy_data: Transformed job data
            skills_data: List of skill dicts from extractor:
                [
                    {
                        'skill_text': 'Python',
                        'language_code': 'en',
                        'importance': 'core',
                        'source': 'key_skills'
                    },
                    ...
                ]
        
        Returns:
            (JobPosting instance, stats dict)
        """
        stats = {
            'created': False,
            'updated': False,
            'aliases_created': 0,
            'aliases_reused': 0,
            'extractions_created': 0,
        }
        
        try:
            with transaction.atomic():
                # Step 1: Get or create job posting
                job, created = JobPosting.objects.update_or_create(
                    external_job_id=vacancy_data['external_job_id'],
                    defaults=vacancy_data
                )
                
                if created:
                    stats['created'] = True
                    logger.debug(f"✓ Created job: {job.job_title}")
                else:
                    stats['updated'] = True
                    logger.debug(f"↻ Updated job: {job.job_title}")
                
                # Step 2: Load raw skill aliases
                if skills_data:
                    alias_stats = self._ingest_raw_skills(job, skills_data)
                    stats.update(alias_stats)
                
                return job, stats
        
        except Exception as e:
            logger.error(f"Error loading vacancy {vacancy_data.get('external_job_id')}: {e}")
            raise
    
    def _ingest_raw_skills(self, job: JobPosting, skills_data: List[Dict]) -> Dict:
        """
        Phase A: Ingest raw skills into skill_aliases.
        
        DO NOT create canonical skills here!
        Just store raw strings with status='unresolved'.
        
        Args:
            job: JobPosting instance
            skills_data: List of extracted skills
        
        Returns:
            Stats dict
        """
        stats = {
            'aliases_created': 0,
            'aliases_reused': 0,
            'extractions_created': 0,
        }
        
        for skill_data in skills_data:
            try:
                skill_text = skill_data['skill_text'].strip()
                language_code = skill_data.get('language_code', 'en')
                importance = skill_data.get('importance', 'secondary')
                source = skill_data.get('source', 'hh.uz')
                
                if not skill_text:
                    continue
                
                # Get or create skill alias (unresolved)
                alias, alias_created = self._get_or_create_alias(
                    skill_text=skill_text,
                    language_code=language_code,
                    source=source
                )
                
                if alias_created:
                    stats['aliases_created'] += 1
                    logger.debug(f"  + New alias: {skill_text} ({language_code})")
                else:
                    stats['aliases_reused'] += 1
                    logger.debug(f"  ↻ Reused alias: {skill_text} ({language_code})")
                
                # Track job-alias mapping
                extraction, extraction_created = JobSkillExtraction.objects.get_or_create(
                    job_posting=job,
                    alias=alias,
                    defaults={'importance': importance}
                )
                
                if extraction_created:
                    stats['extractions_created'] += 1
            
            except Exception as e:
                logger.error(f"Error ingesting skill '{skill_data.get('skill_text')}': {e}")
                continue
        
        return stats
    
    def _get_or_create_alias(
        self,
        skill_text: str,
        language_code: str,
        source: str
    ) -> Tuple[SkillAlias, bool]:
        """
        Get or create SkillAlias (unresolved).
        
        Key points:
        - skill_id = NULL (not resolved yet)
        - status = 'unresolved'
        - If alias exists, increment usage_count
        
        Args:
            skill_text: Raw skill text
            language_code: 'en', 'ru', or 'uz'
            source: Where skill came from
        
        Returns:
            (SkillAlias instance, created)
        """
        
        # Try to find existing alias
        alias = SkillAlias.objects.filter(
            alias_text=skill_text,
            language_code=language_code,
            source=source
        ).first()
        
        if alias:
            # Increment usage count
            alias.usage_count += 1
            alias.save(update_fields=['usage_count'])
            return alias, False
        
        # Create new alias (unresolved)
        alias = SkillAlias.objects.create(
            skill=None,  # ← KEY: Not resolved yet
            alias_text=skill_text,
            language_code=language_code,
            source=source,
            status='unresolved',
            usage_count=1
        )
        
        return alias, True
    
    def load_batch(self, vacancies: List[Dict]) -> Dict:
        """
        Load batch of vacancies.
        
        Args:
            vacancies: List of vacancy dicts, each with 'skills' key
        
        Returns:
            Overall statistics dict
        """
        for vacancy_data in vacancies:
            try:
                # Extract skills from vacancy_data
                skills_data = vacancy_data.pop('skills', [])
                
                # Load job with skills
                job, job_stats = self.load_vacancy(vacancy_data, skills_data)
                
                # Update overall stats
                if job_stats['created']:
                    self.stats['jobs_created'] += 1
                elif job_stats['updated']:
                    self.stats['jobs_updated'] += 1
                else:
                    self.stats['jobs_skipped'] += 1
                
                self.stats['aliases_created'] += job_stats['aliases_created']
                self.stats['aliases_reused'] += job_stats['aliases_reused']
                self.stats['extractions_created'] += job_stats['extractions_created']
            
            except Exception as e:
                logger.error(f"Error in batch: {e}")
                self.stats['errors'] += 1
        
        return self.stats
    
    def get_stats(self) -> Dict:
        """Get loading statistics."""
        return self.stats.copy()
    
    def print_stats(self):
        """Print loading statistics in readable format."""
        print("\n" + "="*60)
        print("PHASE A: INGESTION COMPLETE")
        print("="*60)
        print(f"\n📊 JOB POSTINGS:")
        print(f"  Jobs created:    {self.stats['jobs_created']:>6}")
        print(f"  Jobs updated:    {self.stats['jobs_updated']:>6}")
        print(f"  Jobs skipped:    {self.stats['jobs_skipped']:>6}")
        
        print(f"\n🏷️  SKILL ALIASES (Raw):")
        print(f"  New aliases:     {self.stats['aliases_created']:>6}")
        print(f"  Reused aliases:  {self.stats['aliases_reused']:>6}")
        print(f"  Total unique:    {self.stats['aliases_created']:>6}")
        
        print(f"\n🔗 JOB-ALIAS MAPPINGS:")
        print(f"  Extractions:     {self.stats['extractions_created']:>6}")
        
        if self.stats['errors'] > 0:
            print(f"\n⚠️  ERRORS:")
            print(f"  Errors:          {self.stats['errors']:>6}")
        
        print("\n" + "="*60)
        print("NEXT STEP: Run skill resolver to create canonical skills")
        print("Command: python manage.py resolve_skills")
        print("="*60 + "\n")
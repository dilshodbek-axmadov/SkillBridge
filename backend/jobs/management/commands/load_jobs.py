"""
Django management command to scrape and load jobs from hh.uz
"""
import sys
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from jobs.models import JobPosting, JobSkill, JobCategory, JobPostingCategory
from skills.models import Skill
from pathlib import Path

# Add scrapers to path
ROOT_DIR = Path(__file__).resolve().parents[4]
sys.path.append(str(ROOT_DIR))

from scrapers.hh_uz_scraper import HHUzScraper
from scrapers.config import IT_PROFESSIONAL_ROLES


class Command(BaseCommand):
    help = 'Scrape jobs from hh.uz and load into database'
    
    def add_arguments(self, parser):
        """Add command line arguments"""
        parser.add_argument(
            '--roles',
            nargs='+',
            type=int,
            help='Specific professional role IDs to scrape (default: all IT roles)'
        )
        parser.add_argument(
            '--max-vacancies',
            type=int,
            help='Maximum number of vacancies to scrape (for testing)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without saving to database (for testing)'
        )
    
    def handle(self, *args, **options):
        """Main command logic"""
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('Starting hh.uz Job Scraper'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        # Get options
        roles = options.get('roles') or IT_PROFESSIONAL_ROLES
        max_vacancies = options.get('max_vacancies')
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be saved'))
        
        # Initialize scraper
        self.stdout.write('Initializing scraper...')
        scraper = HHUzScraper()
        
        # Scrape jobs
        self.stdout.write(f'Scraping {len(roles)} professional roles...')
        vacancies = scraper.scrape(
            professional_roles=roles,
            max_vacancies=max_vacancies
        )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Scraped {len(vacancies)} vacancies'))
        
        if not vacancies:
            self.stdout.write(self.style.WARNING('No vacancies found. Exiting.'))
            return
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Dry run complete. No data saved.'))
            self._show_all_vacancies(vacancies)
            return
        
        # Load into database
        self.stdout.write('Loading data into database...')
        stats = self._load_vacancies(vacancies)
        
        # Display results
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('RESULTS:'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f"Jobs created: {stats['created']}")
        self.stdout.write(f"Jobs updated: {stats['updated']}")
        self.stdout.write(f"Skills created: {stats['skills_created']}")
        self.stdout.write(f"Skills linked: {stats['skills_linked']}")
        self.stdout.write(f"Errors: {stats['errors']}")
        self.stdout.write(self.style.SUCCESS('='*60))
    
    def _load_vacancies(self, vacancies):
        """Load vacancies into database"""
        stats = {
            'created': 0,
            'updated': 0,
            'skills_created': 0,
            'skills_linked': 0,
            'errors': 0,
        }
        
        for i, vacancy_data in enumerate(vacancies, 1):
            self.stdout.write(f'Processing vacancy {i}/{len(vacancies)}: {vacancy_data["title"]}')
            
            try:
                with transaction.atomic():
                    # Create or update job posting
                    job, created = self._create_or_update_job(vacancy_data)
                    
                    if created:
                        stats['created'] += 1
                    else:
                        stats['updated'] += 1
                    
                    # Link skills
                    skills_count = self._link_skills(job, vacancy_data)
                    stats['skills_linked'] += skills_count
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error: {str(e)}'))
                stats['errors'] += 1
                continue
        
        return stats
    
    def _create_or_update_job(self, vacancy_data):
        """Create or update a job posting"""
        job, created = JobPosting.objects.update_or_create(
            external_id=vacancy_data['external_id'],
            source_platform=vacancy_data['source_platform'],
            defaults={
                # Basic info
                'title': vacancy_data['title'],
                'company_name': vacancy_data['company_name'],
                'company_id': vacancy_data.get('company_id'),
                'location': vacancy_data['location'],
                'area_id': vacancy_data.get('area_id'),
                
                # Job type
                'work_type': vacancy_data['work_type'],
                'employment_type': vacancy_data['employment_type'],
                'experience_required': vacancy_data['experience_required'],
                
                # Salary
                'salary_min': vacancy_data['salary_min'],
                'salary_max': vacancy_data['salary_max'],
                'salary_currency': vacancy_data['salary_currency'],
                'salary_gross': vacancy_data['salary_gross'],
                
                # URLs
                'posting_url': vacancy_data['posting_url'],
                'alternate_url': vacancy_data.get('alternate_url'),
                
                # Description
                'description_text': vacancy_data['description_text'],
                
                # JSON fields
                'key_skills': vacancy_data['key_skills'],
                'professional_roles': vacancy_data['professional_roles'],
                
                # Dates
                'published_at': vacancy_data['published_at'],
                'created_at': vacancy_data.get('created_at'),
                
                # Flags
                'archived': vacancy_data['archived'],
                'is_active': not vacancy_data['archived'],
                'premium': vacancy_data['premium'],
                'has_test': vacancy_data['has_test'],
                'response_letter_required': vacancy_data['response_letter_required'],
            }
        )
        
        action = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'  ✓ {action}: {job.title}'))
        
        return job, created
    
    def _link_skills(self, job, vacancy_data):
        """Link skills to job posting"""
        # Clear existing skills for this job (in case of update)
        JobSkill.objects.filter(job_posting=job).delete()
        
        skills_linked = 0
        
        # Combine API skills and extracted skills
        all_skill_names = set()
        
        # Add API key_skills
        all_skill_names.update([s.lower().strip() for s in vacancy_data.get('key_skills', [])])
        
        # Add extracted skills from description
        all_skill_names.update([s.lower().strip() for s in vacancy_data.get('extracted_skills', [])])
        
        # Create/get skills and link to job
        for skill_name in all_skill_names:
            if not skill_name:
                continue
            
            try:
                # Get or create skill
                skill, created = Skill.objects.get_or_create(
                    name__iexact=skill_name,
                    defaults={
                        'name': skill_name,
                        'category': self._guess_skill_category(skill_name),
                    }
                )
                
                # Link skill to job
                # Skills from API key_skills are marked as required
                is_required = skill_name in [s.lower() for s in vacancy_data.get('key_skills', [])]
                
                JobSkill.objects.create(
                    job_posting=job,
                    skill=skill,
                    is_required=is_required,
                    importance_level='critical' if is_required else 'important'
                )
                
                skills_linked += 1
                
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'    ! Could not link skill "{skill_name}": {e}'))
        
        self.stdout.write(f'  → Linked {skills_linked} skills')
        return skills_linked
    
    def _guess_skill_category(self, skill_name):
        """Guess skill category based on name"""
        skill_lower = skill_name.lower()
        
        # Programming languages
        prog_langs = ['python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php', 'ruby', 'go', 'swift', 'kotlin', 'rust']
        if any(lang in skill_lower for lang in prog_langs):
            return 'programming_language'
        
        # Frameworks
        frameworks = ['django', 'flask', 'react', 'vue', 'angular', 'spring', 'laravel', 'express']
        if any(fw in skill_lower for fw in frameworks):
            return 'framework'
        
        # Databases
        databases = ['sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'oracle', 'cassandra']
        if any(db in skill_lower for db in databases):
            return 'database'
        
        # DevOps
        devops = ['docker', 'kubernetes', 'jenkins', 'git', 'ci/cd', 'ansible', 'terraform']
        if any(tool in skill_lower for tool in devops):
            return 'devops'
        
        # Cloud
        cloud = ['aws', 'azure', 'gcp', 'cloud']
        if any(c in skill_lower for c in cloud):
            return 'cloud'
        
        # Default to tool
        return 'tool'
    
    def _show_all_vacancies(self, vacancies):
        """Display all scraped vacancies (for dry run)"""
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS(f'SCRAPED {len(vacancies)} VACANCIES:'))
        self.stdout.write(self.style.SUCCESS('='*60))
    
        for i, vacancy in enumerate(vacancies, 1):
            self.stdout.write(f'\n[{i}] {vacancy["title"]}')
            self.stdout.write(f'    Company: {vacancy["company_name"]}')
            self.stdout.write(f'    Location: {vacancy["location"]}')
            self.stdout.write(f'    Experience: {vacancy["experience_required"]}')
            self.stdout.write(f'    Work Type: {vacancy["work_type"]}')
            
            # Show salary if available
            if vacancy['salary_min'] or vacancy['salary_max']:
                salary = f"{vacancy['salary_min'] or '?'} - {vacancy['salary_max'] or '?'} {vacancy['salary_currency']}"
                self.stdout.write(f'    Salary: {salary}')
            else:
                self.stdout.write(f'    Salary: Not specified')
            
            # Show skills (limited to first 8)
            api_skills = vacancy.get('key_skills', [])
            extracted_skills = vacancy.get('extracted_skills', [])
            
            if api_skills:
                self.stdout.write(f'    API Skills: {", ".join(api_skills[:8])}')
            
            if extracted_skills:
                self.stdout.write(f'    Extracted Skills: {", ".join(extracted_skills[:8])}')
            
            self.stdout.write(f'    URL: {vacancy["posting_url"]}')
            self.stdout.write(f'    Published: {vacancy["published_at"]}')
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
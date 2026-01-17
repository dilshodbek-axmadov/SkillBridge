"""
Django management command to update popularity scores for all skills
"""
from django.core.management.base import BaseCommand
from skills.models import Skill


class Command(BaseCommand):
    help = 'Update popularity scores for all skills based on job demand'
    
    def add_arguments(self, parser):
        """Add command line arguments"""
        parser.add_argument(
            '--skill-id',
            type=int,
            help='Update only a specific skill by ID'
        )
        parser.add_argument(
            '--min-jobs',
            type=int,
            default=0,
            help='Only update skills that appear in at least this many jobs'
        )
    
    def handle(self, *args, **options):
        """Main command logic"""
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('Updating Skill Popularity Scores'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        # Get skills to update
        skill_id = options.get('skill_id')
        min_jobs = options.get('min_jobs', 0)
        
        if skill_id:
            # Update single skill
            try:
                skills = [Skill.objects.get(id=skill_id)]
                self.stdout.write(f'Updating single skill: {skills[0].name}\n')
            except Skill.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Skill with ID {skill_id} not found'))
                return
        else:
            # Update all skills
            skills = Skill.objects.all()
            self.stdout.write(f'Updating all {skills.count()} skills...\n')
        
        # Update each skill
        updated = 0
        unchanged = 0
        
        for i, skill in enumerate(skills, 1):
            # Get job count before update
            from jobs.models import JobSkill
            job_count = JobSkill.objects.filter(skill=skill).count()
            
            # Skip if below minimum
            if job_count < min_jobs:
                continue
            
            # Store old score
            old_score = skill.popularity_score
            
            # Update score
            new_score = skill.update_popularity_score()
            
            # Check if changed
            if abs(old_score - new_score) > 0.01:  # Changed by more than 0.01
                updated += 1
                self.stdout.write(
                    f'[{i}/{len(skills)}] {skill.name}: {old_score:.1f} → {new_score:.1f} ({job_count} jobs)'
                )
            else:
                unchanged += 1
                if options['verbosity'] >= 2:  # Only show if verbose
                    self.stdout.write(
                        f'[{i}/{len(skills)}] {skill.name}: {old_score:.1f} (unchanged, {job_count} jobs)'
                    )
        
        # Display summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('SUMMARY:'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f'Total skills processed: {len(skills)}')
        self.stdout.write(f'Scores updated: {updated}')
        self.stdout.write(f'Scores unchanged: {unchanged}')
        self.stdout.write(self.style.SUCCESS('='*60))
        
        # Show top 10 most popular skills
        self.stdout.write(self.style.SUCCESS('\nTop 10 Most Popular Skills:'))
        self.stdout.write(self.style.SUCCESS('='*60))
        top_skills = Skill.objects.order_by('-popularity_score')[:10]
        for i, skill in enumerate(top_skills, 1):
            self.stdout.write(f'{i}. {skill.name}: {skill.popularity_score:.1f}')
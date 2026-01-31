"""
Management Command: Link Job Skills
====================================
File: backend/apps/skills/management/commands/link_job_skills.py

Phase C: Link jobs to canonical skills via resolved aliases.

Usage:
    python manage.py link_job_skills [--limit N] [--relink]
"""

from django.core.management.base import BaseCommand
from apps.skills.utils.job_skill_linker import JobSkillLinker, print_linking_summary


class Command(BaseCommand):
    help = 'Link jobs to canonical skills via resolved aliases (Phase C)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Maximum number of jobs to process'
        )
        
        parser.add_argument(
            '--relink',
            action='store_true',
            help='Delete existing links and recreate (useful after re-resolution)'
        )
        
        parser.add_argument(
            '--summary',
            action='store_true',
            help='Show summary and exit (no processing)'
        )
    
    def handle(self, *args, **options):
        # Show summary and exit
        if options['summary']:
            print_linking_summary()
            return
        
        self.stdout.write(self.style.SUCCESS('\n=== PHASE C: JOB-SKILL LINKING ===\n'))
        
        # Initialize linker
        linker = JobSkillLinker()
        
        # Show configuration
        if options['limit']:
            self.stdout.write(f"Limit: {options['limit']} jobs\n")
        
        if options['relink']:
            self.stdout.write(
                self.style.WARNING(
                    "⚠️  RELINK MODE: Existing job_skills will be deleted and recreated\n"
                )
            )
            
            # Confirm
            confirm = input("Continue? [y/N]: ")
            if confirm.lower() != 'y':
                self.stdout.write("Cancelled.")
                return
            
            # Delete existing links
            from apps.jobs.models import JobSkill
            deleted_count = JobSkill.objects.all().delete()[0]
            self.stdout.write(f"Deleted {deleted_count} existing job-skill links\n")
        
        # Link
        try:
            stats = linker.link_all_jobs(limit=options['limit'])
            
            # Print results
            linker.print_stats()
            
            # Warnings
            if stats['unresolved_aliases_skipped'] > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"\n⚠️  {stats['unresolved_aliases_skipped']} unresolved aliases were skipped."
                    )
                )
                self.stdout.write(
                    "   Run 'python manage.py resolve_skills' to resolve them, then relink.\n"
                )
            
            if stats['errors'] > 0:
                self.stdout.write(
                    self.style.ERROR(
                        f"\n❌ {stats['errors']} errors occurred during linking."
                    )
                )
            
            self.stdout.write(self.style.SUCCESS('\n✓ Linking complete!\n'))
            
            # Show summary
            self.stdout.write("\nFinal summary:")
            print_linking_summary()
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Linking failed: {e}\n')
            )
            raise
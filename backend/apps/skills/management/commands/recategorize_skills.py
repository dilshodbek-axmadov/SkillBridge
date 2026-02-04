"""
Management command to recategorize all skills using the new 18-category system.

Usage:
    python manage.py recategorize_skills
    python manage.py recategorize_skills --dry-run  # Preview changes without saving
"""

from django.core.management.base import BaseCommand
from apps.skills.models import Skill
from apps.jobs.scrapers.enhanced_skill_extractor import categorize_skill


class Command(BaseCommand):
    help = 'Recategorize all skills using the comprehensive 18-category system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without saving to database',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be saved\n'))

        skills = Skill.objects.all()
        total = skills.count()

        self.stdout.write(f'Processing {total} skills...\n')

        # Track changes by category
        category_counts = {}
        changed_count = 0
        unchanged_count = 0

        for skill in skills:
            old_category = skill.category
            new_category = categorize_skill(skill.name_en)

            # Count by new category
            category_counts[new_category] = category_counts.get(new_category, 0) + 1

            if old_category != new_category:
                changed_count += 1
                self.stdout.write(
                    f'  {skill.name_en}: {old_category} -> {self.style.SUCCESS(new_category)}'
                )

                if not dry_run:
                    skill.category = new_category
                    skill.save(update_fields=['category'])
            else:
                unchanged_count += 1

        # Print summary
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS(f'\nSummary:'))
        self.stdout.write(f'  Total skills: {total}')
        self.stdout.write(f'  Changed: {changed_count}')
        self.stdout.write(f'  Unchanged: {unchanged_count}')

        self.stdout.write(self.style.SUCCESS(f'\nCategory distribution:'))
        for category, count in sorted(category_counts.items(), key=lambda x: -x[1]):
            percentage = (count / total * 100) if total > 0 else 0
            bar = '#' * int(percentage / 2)
            self.stdout.write(f'  {category:30} {count:4} ({percentage:5.1f}%) {bar}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN - No changes were saved'))
        else:
            self.stdout.write(self.style.SUCCESS('\nAll skills have been recategorized!'))

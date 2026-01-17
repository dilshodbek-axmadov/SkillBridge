from django.core.management.base import BaseCommand
from skills.models import SkillLevel


class Command(BaseCommand):
    help = 'Load initial skill levels into database'
    
    def handle(self, *args, **options):
        skill_levels = [
            {'name': 'Beginner', 'level_order': 1, 'description': 'Basic understanding and limited practical experience'},
            {'name': 'Intermediate', 'level_order': 2, 'description': 'Good working knowledge and some practical experience'},
            {'name': 'Advanced', 'level_order': 3, 'description': 'Deep expertise and extensive practical experience'},
            {'name': 'Expert', 'level_order': 4, 'description': 'Master-level proficiency and leadership in the skill'},
        ]
        
        created = 0
        for level_data in skill_levels:
            level, created_now = SkillLevel.objects.get_or_create(
                name=level_data['name'],
                defaults={
                    'level_order': level_data['level_order'],
                    'description': level_data['description']
                }
            )
            if created_now:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created: {level.name}'))
            else:
                self.stdout.write(f'  Already exists: {level.name}')
        
        self.stdout.write(self.style.SUCCESS(f'\nTotal created: {created}'))
"""
Calculate skill combinations from job postings
"""
from django.core.management.base import BaseCommand
from analytics.models import SkillCombination


class Command(BaseCommand):
    help = 'Calculate which skills commonly appear together in job postings'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('Calculate Skill Combinations'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        self.stdout.write('Analyzing job postings...\n')
        
        count = SkillCombination.calculate_combinations()
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('SUMMARY:'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f'Skill combinations found: {count}')
        self.stdout.write(self.style.SUCCESS('='*60))
        
        # Show top 10 combinations
        top_combinations = SkillCombination.objects.order_by('-co_occurrence_count')[:10]
        
        if top_combinations:
            self.stdout.write(self.style.SUCCESS('\nTop 10 Skill Combinations:'))
            self.stdout.write(self.style.SUCCESS('='*60))
            for i, combo in enumerate(top_combinations, 1):
                self.stdout.write(
                    f'{i}. {combo.skill_1.name} + {combo.skill_2.name}: '
                    f'{combo.co_occurrence_count} jobs '
                    f'({combo.correlation_score*100:.1f}% correlation)'
                )
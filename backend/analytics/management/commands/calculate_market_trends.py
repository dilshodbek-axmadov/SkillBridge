"""
Calculate market trends for all skills
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from skills.models import Skill
from analytics.models import MarketTrend


class Command(BaseCommand):
    help = 'Calculate market trends for skills'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--month',
            type=int,
            help='Month to calculate (1-12). Default: current month'
        )
        parser.add_argument(
            '--year',
            type=int,
            help='Year to calculate. Default: current year'
        )
        parser.add_argument(
            '--top-skills',
            type=int,
            help='Only calculate for top N most popular skills'
        )
    
    def handle(self, *args, **options):
        today = timezone.now()
        month = options.get('month') or today.month
        year = options.get('year') or today.year
        top_skills = options.get('top_skills')
        
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('Calculate Market Trends'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f'Period: {month}/{year}\n')
        
        # Get skills to process
        if top_skills:
            skills = Skill.objects.order_by('-popularity_score')[:top_skills]
            self.stdout.write(f'Processing top {top_skills} skills...\n')
        else:
            skills = Skill.objects.all()
            self.stdout.write(f'Processing all {skills.count()} skills...\n')
        
        created = 0
        updated = 0
        
        for i, skill in enumerate(skills, 1):
            self.stdout.write(f'[{i}/{len(skills)}] {skill.name}...')
            
            trend = MarketTrend.calculate_for_skill(skill, month, year)
            
            if trend:
                if trend.demand_count > 0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  → {trend.demand_count} jobs, '
                            f'{trend.get_trend_direction_display()}'
                        )
                    )
                    created += 1
                else:
                    updated += 1
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('SUMMARY:'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f'Trends calculated: {created}')
        self.stdout.write(f'Skills with no demand: {updated}')
        self.stdout.write(self.style.SUCCESS('='*60))
"""
Market analytics and trend models
"""
from django.db import models
from skills.models import Skill


class MarketTrend(models.Model):
    """
    Track skill demand trends over time
    """
    TREND_DIRECTIONS = [
        ('rising', 'Rising'),
        ('stable', 'Stable'),
        ('declining', 'Declining'),
    ]
    
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='market_trends'
    )
    month = models.IntegerField(
        help_text="Month (1-12)"
    )
    year = models.IntegerField(
        help_text="Year (e.g., 2024)"
    )
    demand_count = models.IntegerField(
        default=0,
        help_text="Number of job postings requiring this skill"
    )
    average_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average salary for jobs requiring this skill"
    )
    trend_direction = models.CharField(
        max_length=20,
        choices=TREND_DIRECTIONS,
        default='stable'
    )
    
    class Meta:
        db_table = 'market_trends'
        verbose_name = 'Market Trend'
        verbose_name_plural = 'Market Trends'
        unique_together = ['skill', 'month', 'year']
        ordering = ['-year', '-month', '-demand_count']
        indexes = [
            models.Index(fields=['skill', '-year', '-month']),
            models.Index(fields=['-demand_count']),
        ]
    
    def __str__(self):
        return f"{self.skill.name} - {self.year}/{self.month:02d} ({self.demand_count} jobs)"
    
    def get_period_display(self):
        """Get formatted month/year string"""
        from datetime import date
        month_name = date(self.year, self.month, 1).strftime('%B')
        return f"{month_name} {self.year}"
    
    @classmethod
    def calculate_for_skill(cls, skill, month, year):
        """
        Calculate market trend for a specific skill in a given month/year
        """
        from jobs.models import JobPosting, JobSkill
        from django.db.models import Avg
        from datetime import date
        
        # Get first and last day of the month
        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year
        
        start_date = date(year, month, 1)
        end_date = date(next_year, next_month, 1)
        
        # Count jobs posted in this month that require this skill
        job_skills = JobSkill.objects.filter(
            skill=skill,
            job_posting__published_at__gte=start_date,
            job_posting__published_at__lt=end_date
        )
        
        demand_count = job_skills.count()
        
        # Calculate average salary
        jobs_with_salary = JobPosting.objects.filter(
            id__in=job_skills.values_list('job_posting_id', flat=True),
            salary_min__isnull=False
        )
        
        avg_salary = jobs_with_salary.aggregate(
            avg=Avg('salary_min')
        )['avg']
        
        # Determine trend direction (compare with previous month)
        previous_month = month - 1 if month > 1 else 12
        previous_year = year if month > 1 else year - 1
        
        try:
            previous_trend = cls.objects.get(
                skill=skill,
                month=previous_month,
                year=previous_year
            )
            
            if demand_count > previous_trend.demand_count * 1.1:
                trend_direction = 'rising'
            elif demand_count < previous_trend.demand_count * 0.9:
                trend_direction = 'declining'
            else:
                trend_direction = 'stable'
        except cls.DoesNotExist:
            trend_direction = 'stable'
        
        # Create or update trend
        trend, created = cls.objects.update_or_create(
            skill=skill,
            month=month,
            year=year,
            defaults={
                'demand_count': demand_count,
                'average_salary': avg_salary,
                'trend_direction': trend_direction,
            }
        )
        
        return trend


class SkillCombination(models.Model):
    """
    Track which skills commonly appear together in job postings
    Helps identify skill stacks and dependencies
    """
    skill_1 = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='combinations_as_first'
    )
    skill_2 = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='combinations_as_second'
    )
    co_occurrence_count = models.IntegerField(
        default=0,
        help_text="Number of jobs requiring both skills"
    )
    correlation_score = models.FloatField(
        default=0.0,
        help_text="How strongly these skills correlate (0-1)"
    )
    
    class Meta:
        db_table = 'skill_combinations'
        verbose_name = 'Skill Combination'
        verbose_name_plural = 'Skill Combinations'
        unique_together = ['skill_1', 'skill_2']
        ordering = ['-co_occurrence_count', '-correlation_score']
        indexes = [
            models.Index(fields=['skill_1', '-co_occurrence_count']),
            models.Index(fields=['skill_2', '-co_occurrence_count']),
        ]
    
    def __str__(self):
        return f"{self.skill_1.name} + {self.skill_2.name} ({self.co_occurrence_count} jobs)"
    
    @classmethod
    def calculate_combinations(cls):
        """
        Calculate skill combinations based on current job postings
        This should be run periodically to update the data
        """
        from jobs.models import JobPosting, JobSkill
        from django.db.models import Count
        
        # Clear old combinations
        cls.objects.all().delete()
        
        # Get all active job postings
        active_jobs = JobPosting.objects.filter(is_active=True)
        
        # For each job, find skill pairs
        combinations = {}
        
        for job in active_jobs:
            job_skills = list(job.job_skills.values_list('skill_id', flat=True))
            
            # Create pairs
            for i in range(len(job_skills)):
                for j in range(i + 1, len(job_skills)):
                    skill_1_id = min(job_skills[i], job_skills[j])
                    skill_2_id = max(job_skills[i], job_skills[j])
                    
                    key = (skill_1_id, skill_2_id)
                    combinations[key] = combinations.get(key, 0) + 1
        
        # Create SkillCombination records
        created_count = 0
        for (skill_1_id, skill_2_id), count in combinations.items():
            if count >= 2:  # Only store combinations that appear at least twice
                skill_1 = Skill.objects.get(id=skill_1_id)
                skill_2 = Skill.objects.get(id=skill_2_id)
                
                # Calculate correlation score
                skill_1_jobs = JobSkill.objects.filter(skill=skill_1).count()
                skill_2_jobs = JobSkill.objects.filter(skill=skill_2).count()
                
                if skill_1_jobs > 0 and skill_2_jobs > 0:
                    # Jaccard similarity coefficient
                    correlation = count / (skill_1_jobs + skill_2_jobs - count)
                else:
                    correlation = 0.0
                
                cls.objects.create(
                    skill_1=skill_1,
                    skill_2=skill_2,
                    co_occurrence_count=count,
                    correlation_score=correlation
                )
                created_count += 1
        
        return created_count
    
    def get_related_skills(self):
        """Get all skills that commonly appear with this combination"""
        from django.db.models import Q
        
        related = SkillCombination.objects.filter(
            Q(skill_1=self.skill_1) | Q(skill_1=self.skill_2) |
            Q(skill_2=self.skill_1) | Q(skill_2=self.skill_2)
        ).exclude(
            id=self.id
        ).order_by('-co_occurrence_count')[:10]
        
        return related
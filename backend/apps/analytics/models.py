from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.skills.models import Skill


class MarketTrend(models.Model):
    """
    Aggregated market demand trends for skills.
    Derived from job postings over time.
    """

    PERIOD_CHOICES = [
        ('7d', _('Last 7 days')),
        ('30d', _('Last 30 days')),
        ('90d', _('Last 90 days')),
        ('1y', _('Last year')),
    ]

    trend_id = models.AutoField(primary_key=True)

    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='market_trends',
        verbose_name=_('skill')
    )

    period = models.CharField(
        _('period'),
        max_length=10,
        choices=PERIOD_CHOICES
    )

    demand_score = models.FloatField(
        _('demand score'),
        help_text=_("Normalized demand index (0–100)")
    )

    job_count = models.IntegerField(
        _('job count'),
        help_text=_("Number of job postings containing this skill")
    )

    growth_rate = models.FloatField(
        _('growth rate (%)'),
        help_text=_("Demand growth compared to previous period")
    )

    avg_salary = models.DecimalField(
        _('average salary'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    calculated_at = models.DateTimeField(
        _('calculated at'),
        auto_now_add=True
    )

    class Meta:
        db_table = 'market_trends'
        unique_together = [('skill', 'period')]
        ordering = ['-calculated_at']
        verbose_name = _('market trend')
        verbose_name_plural = _('market trends')

    def __str__(self):
        return f"{self.skill.canonical_key} – {self.period}"

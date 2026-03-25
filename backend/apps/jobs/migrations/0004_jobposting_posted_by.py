# Generated manually

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('jobs', '0003_extractionrun_jobs_deactivated'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobposting',
            name='posted_by',
            field=models.ForeignKey(
                blank=True,
                help_text='Recruiter who created this listing on the platform; null for scraped jobs (e.g. hh.uz).',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='employer_job_postings',
                to=settings.AUTH_USER_MODEL,
                verbose_name='posted by',
            ),
        ),
        migrations.AddIndex(
            model_name='jobposting',
            index=models.Index(fields=['posted_by', '-posted_date'], name='job_post_posted_by_idx'),
        ),
        migrations.AddIndex(
            model_name='jobposting',
            index=models.Index(fields=['source', 'is_active'], name='job_post_source_act_idx'),
        ),
    ]

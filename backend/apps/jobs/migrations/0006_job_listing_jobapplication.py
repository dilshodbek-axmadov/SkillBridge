# Generated manually for recruiter job lifecycle + applications.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def set_listing_status_from_active(apps, schema_editor):
    JobPosting = apps.get_model('jobs', 'JobPosting')
    for row in JobPosting.objects.all().only('pk', 'is_active'):
        row.listing_status = 'active' if row.is_active else 'archived'
        row.save(update_fields=['listing_status'])


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('jobs', '0005_rename_job_post_posted_by_idx_job_posting_posted__a04c81_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobposting',
            name='listing_status',
            field=models.CharField(
                choices=[('draft', 'Draft'), ('active', 'Active'), ('archived', 'Archived')],
                db_index=True,
                default='active',
                help_text='draft = not public; active = visible in job search; archived = closed listing.',
                max_length=20,
                verbose_name='listing status',
            ),
        ),
        migrations.AddField(
            model_name='jobposting',
            name='view_count',
            field=models.PositiveIntegerField(default=0, verbose_name='view count'),
        ),
        migrations.AlterField(
            model_name='jobposting',
            name='job_url',
            field=models.URLField(blank=True, default='', max_length=500, verbose_name='job URL'),
        ),
        migrations.RunPython(set_listing_status_from_active, migrations.RunPython.noop),
        migrations.CreateModel(
            name='JobApplication',
            fields=[
                ('application_id', models.AutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='applied at')),
                (
                    'applicant',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='job_applications',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='applicant',
                    ),
                ),
                (
                    'job_posting',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='applications',
                        to='jobs.jobposting',
                        verbose_name='job posting',
                    ),
                ),
            ],
            options={
                'verbose_name': 'job application',
                'verbose_name_plural': 'job applications',
                'db_table': 'job_applications',
            },
        ),
        migrations.AddConstraint(
            model_name='jobapplication',
            constraint=models.UniqueConstraint(fields=('job_posting', 'applicant'), name='unique_job_applicant'),
        ),
        migrations.AddIndex(
            model_name='jobapplication',
            index=models.Index(fields=['job_posting', '-created_at'], name='job_applicat_job_pos_7b8c7f_idx'),
        ),
    ]

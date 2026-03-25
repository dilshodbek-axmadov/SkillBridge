# Generated manually for UserActivity feed

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserActivity',
            fields=[
                ('activity_id', models.AutoField(primary_key=True, serialize=False)),
                (
                    'activity_type',
                    models.CharField(
                        choices=[
                            ('account_created', 'Account created'),
                            ('profile_setup', 'Profile set up'),
                            ('cv_uploaded', 'CV uploaded'),
                            ('skill_added', 'Skill added'),
                            ('skills_bulk_added', 'Skills bulk added'),
                            ('skill_removed', 'Skill removed'),
                            ('gap_analyzed', 'Skill gap analyzed'),
                            ('gap_status', 'Skill gap updated'),
                            ('gaps_cleared', 'Skill gaps cleared'),
                            ('roadmap_created', 'Learning roadmap created'),
                            ('roadmap_progress', 'Roadmap progress'),
                        ],
                        max_length=32,
                        verbose_name='activity type',
                    ),
                ),
                ('description', models.CharField(max_length=500, verbose_name='description')),
                ('metadata', models.JSONField(blank=True, default=dict, verbose_name='metadata')),
                ('link_path', models.CharField(blank=True, max_length=200, verbose_name='link path')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='created at')),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='activities',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='user',
                    ),
                ),
            ],
            options={
                'verbose_name': 'user activity',
                'verbose_name_plural': 'user activities',
                'db_table': 'user_activities',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='useractivity',
            index=models.Index(fields=['user', '-created_at'], name='ua_user_created_desc'),
        ),
    ]

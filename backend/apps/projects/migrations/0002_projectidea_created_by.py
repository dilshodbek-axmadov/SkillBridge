# Generated manually

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectidea',
            name='created_by',
            field=models.ForeignKey(
                blank=True,
                help_text='User who generated this idea; only this user can view or use it via the API.',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='created_project_ideas',
                to=settings.AUTH_USER_MODEL,
                verbose_name='created by',
            ),
        ),
        migrations.AddIndex(
            model_name='projectidea',
            index=models.Index(fields=['created_by', '-created_at'], name='proj_idea_owner_created'),
        ),
    ]

# Generated manually — developer vs recruiter marketplace fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_rename_ua_user_created_desc_user_activi_user_id_47a698_idx'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='user_type',
            field=models.CharField(
                choices=[('developer', 'Developer'), ('recruiter', 'Recruiter')],
                db_index=True,
                default='developer',
                help_text='Developer (talent) or recruiter (employer) account; set at registration.',
                max_length=20,
                verbose_name='user type',
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='recruiter_plan',
            field=models.CharField(
                choices=[('free', 'Free'), ('pro', 'Pro')],
                default='free',
                help_text='Subscription tier for recruiter accounts; ignored for developers.',
                max_length=10,
                verbose_name='recruiter plan',
            ),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['user_type', '-created_at'], name='users_user_type_cr_idx'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='open_to_recruiters',
            field=models.BooleanField(
                default=True,
                help_text='If true, this developer profile may appear in recruiter search (subject to product rules).',
                verbose_name='open to recruiters',
            ),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='company_name',
            field=models.CharField(
                blank=True,
                help_text='Employer or agency name; used for recruiter accounts.',
                max_length=255,
                verbose_name='company name',
            ),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='company_website',
            field=models.URLField(blank=True, null=True, verbose_name='company website'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='company_description',
            field=models.TextField(
                blank=True,
                help_text='Short company overview for candidate-facing pages.',
                verbose_name='company description',
            ),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='recruiter_title',
            field=models.CharField(
                blank=True,
                help_text='e.g. HR Business Partner, Technical Recruiter.',
                max_length=200,
                verbose_name='recruiter title at company',
            ),
        ),
    ]

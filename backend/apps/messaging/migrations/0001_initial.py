from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MessageThread',
            fields=[
                ('thread_id', models.AutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_message_at', models.DateTimeField(blank=True, null=True)),
                ('developer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='message_threads_as_developer', to=settings.AUTH_USER_MODEL)),
                ('recruiter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='message_threads_as_recruiter', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'message_threads',
            },
        ),
        migrations.CreateModel(
            name='ThreadMessage',
            fields=[
                ('message_id', models.AutoField(primary_key=True, serialize=False)),
                ('body', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('read_at', models.DateTimeField(blank=True, null=True)),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_messages', to=settings.AUTH_USER_MODEL)),
                ('thread', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='messaging.messagethread')),
            ],
            options={
                'db_table': 'thread_messages',
                'ordering': ['created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='threadmessage',
            index=models.Index(fields=['thread', 'created_at'], name='thread_mess_thread__b8da2e_idx'),
        ),
        migrations.AddConstraint(
            model_name='messagethread',
            constraint=models.UniqueConstraint(fields=('recruiter', 'developer'), name='uniq_thread_recruiter_developer'),
        ),
        migrations.AddConstraint(
            model_name='messagethread',
            constraint=models.CheckConstraint(check=~Q(('recruiter', models.F('developer'))), name='chk_thread_not_self'),
        ),
    ]


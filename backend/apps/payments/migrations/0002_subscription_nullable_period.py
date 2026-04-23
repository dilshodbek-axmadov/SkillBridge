"""
Make Subscription period fields nullable.

Stripe API versions from 2024+ expose `current_period_start` / `current_period_end`
on subscription items rather than the top-level subscription object, so the
subscription webhook/verify flows can legitimately receive a subscription
payload without those fields set at the top level.

We also relax `stripe_price_id` and `status` because some lifecycle events
arrive with partial data and we still want a DB row to exist for auditing.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='current_period_start',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='current_period_end',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='stripe_price_id',
            field=models.CharField(max_length=255, blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='status',
            field=models.CharField(max_length=50, blank=True, default='',
                                   choices=[
                                       ('active', 'Active'),
                                       ('canceled', 'Canceled'),
                                       ('incomplete', 'Incomplete'),
                                       ('past_due', 'Past Due'),
                                       ('trialing', 'Trialing'),
                                       ('unpaid', 'Unpaid'),
                                   ]),
        ),
    ]

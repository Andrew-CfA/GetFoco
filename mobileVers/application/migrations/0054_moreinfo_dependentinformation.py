# Generated by Django 3.1.7 on 2021-10-12 03:35

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0053_auto_20211011_2030'),
    ]

    operations = [
        migrations.AddField(
            model_name='moreinfo',
            name='dependentInformation',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
    ]

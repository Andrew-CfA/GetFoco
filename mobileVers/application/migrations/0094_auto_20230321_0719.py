# Generated by Django 3.1.7 on 2023-03-21 13:19

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0093_programs_rearch_is_active'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={},
        ),
        migrations.AddField(
            model_name='user',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(1970, 1, 1, 0, 0)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='user',
            name='modified',
            field=models.DateTimeField(auto_now=True),
        ),
    ]

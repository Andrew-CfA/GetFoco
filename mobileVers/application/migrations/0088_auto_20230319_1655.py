# Generated by Django 3.1.7 on 2023-03-19 22:55

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0087_auto_20230319_1443'),
    ]

    operations = [
        migrations.AddField(
            model_name='moreinfo_rearch',
            name='created_at_init_temp',
            field=models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='moreinfo_rearch',
            name='modified_at_init_temp',
            field=models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0)),
            preserve_default=False,
        ),
    ]

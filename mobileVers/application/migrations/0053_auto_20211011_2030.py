# Generated by Django 3.1.7 on 2021-10-12 03:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0052_auto_20211006_1811'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='moreinfo',
            name='dependent',
        ),
        migrations.RemoveField(
            model_name='moreinfo',
            name='dependentsBirthdate',
        ),
        migrations.RemoveField(
            model_name='moreinfo',
            name='dependentsName',
        ),
    ]

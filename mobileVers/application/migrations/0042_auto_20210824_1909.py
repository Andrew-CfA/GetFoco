# Generated by Django 3.1.7 on 2021-08-25 02:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0041_futureemails_connexioncommunication'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eligibility',
            name='DEqualified',
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name='eligibility',
            name='GRqualified',
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name='eligibility',
            name='RecreationQualified',
            field=models.CharField(max_length=20),
        ),
    ]

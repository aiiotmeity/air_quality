# Generated by Django 5.0.3 on 2024-12-17 06:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('air_pollution', '0015_rename_sername_healthassessment_username'),
    ]

    operations = [
        migrations.AlterField(
            model_name='healthassessment',
            name='smoking_history',
            field=models.TextField(),
        ),
    ]

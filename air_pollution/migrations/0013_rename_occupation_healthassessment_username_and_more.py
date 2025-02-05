# Generated by Django 5.0.3 on 2024-12-17 05:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('air_pollution', '0012_remove_healthassessment_exposure_type_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='healthassessment',
            old_name='occupation',
            new_name='username',
        ),
        migrations.RemoveField(
            model_name='healthassessment',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='healthassessment',
            name='environment',
        ),
        migrations.RemoveField(
            model_name='healthassessment',
            name='medical_condition',
        ),
        migrations.RemoveField(
            model_name='healthassessment',
            name='respiratory',
        ),
        migrations.RemoveField(
            model_name='healthassessment',
            name='symptom',
        ),
        migrations.RemoveField(
            model_name='healthassessment',
            name='user',
        ),
        migrations.AddField(
            model_name='healthassessment',
            name='common_symptoms',
            field=models.TextField(default='No Symptoms'),
        ),
        migrations.AddField(
            model_name='healthassessment',
            name='living_environment',
            field=models.TextField(default='Unknown'),
        ),
        migrations.AddField(
            model_name='healthassessment',
            name='medical_history',
            field=models.TextField(default='None'),
        ),
        migrations.AddField(
            model_name='healthassessment',
            name='occupational_exposure',
            field=models.CharField(default='No Exposure', max_length=50),
        ),
        migrations.AddField(
            model_name='healthassessment',
            name='respiratory_conditions',
            field=models.TextField(default='No Conditions'),
        ),
        migrations.AlterField(
            model_name='healthassessment',
            name='age_group',
            field=models.CharField(default='Unknown', max_length=20),
        ),
        migrations.AlterField(
            model_name='healthassessment',
            name='gender',
            field=models.CharField(default='Not Specified', max_length=20),
        ),
        migrations.AlterField(
            model_name='healthassessment',
            name='smoking_history',
            field=models.CharField(default='Never Smoked', max_length=50),
        ),
    ]

# Generated by Django 5.0.3 on 2024-10-22 05:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('air_pollution', '0008_healthquestionnaire'),
    ]

    operations = [
        migrations.CreateModel(
            name='AirQualityData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('aqi', models.FloatField()),
                ('co', models.FloatField()),
                ('nh3', models.FloatField()),
                ('no2', models.FloatField()),
                ('o3', models.FloatField()),
                ('pm10', models.FloatField()),
                ('pm25', models.FloatField()),
                ('so2', models.FloatField()),
            ],
        ),
    ]

# Generated by Django 5.0.3 on 2024-10-01 07:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('air_pollution', '0002_rename_registration1_aqi_index'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(max_length=15, unique=True)),
                ('firebase_uid', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.DeleteModel(
            name='aqi_index',
        ),
    ]

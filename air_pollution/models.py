from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin
import os
from django.db import models

class User(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, unique=True)
    otp = models.CharField(max_length=6, blank=True, null=True)


    def __str__(self):
        return self.name


class login(models.Model):
    phone_number = models.CharField(max_length=15, unique=True)
    otp_code = models.CharField(max_length=6, null=True, blank=True)
    otp_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.phone_number

class HealthQuestionnaire(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Assuming you have a User model
    question1 = models.CharField(max_length=100)  # Adjust field types as necessary
    question2 = models.CharField(max_length=100)
    # Add additional questions as needed

    def __str__(self):
        return f"Health Questionnaire for {self.user.name}"
class AirQualityData(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    aqi = models.FloatField()
    co = models.FloatField()
    nh3 = models.FloatField()
    no2 = models.FloatField()
    o3 = models.FloatField()
    pm10 = models.FloatField()
    pm25 = models.FloatField()
    so2 = models.FloatField()

    def __str__(self):
        return f"AQData at {self.timestamp}"
class HealthAssessment(models.Model):
    username = models.CharField(max_length=100)
    age_group = models.CharField(max_length=20)
    gender = models.CharField(max_length=20)
    respiratory_conditions = models.TextField()  # Stores JSON or comma-separated list
    smoking_history = models.TextField()
    living_environment = models.TextField()  # Stores JSON or comma-separated list
    common_symptoms = models.TextField()  # Stores JSON or comma-separated list
    occupational_exposure = models.CharField(max_length=50)
    medical_history = models.TextField()  #
    health_score = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.username} - Health Assessment"
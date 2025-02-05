from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
#from .models import aqi_index
from django.contrib.auth import login
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import json
import re
from .models import User,login,HealthAssessment
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password
from twilio.rest import Client
from django.contrib.auth.decorators import login_required
from django.conf import settings
import  matplotlib
import matplotlib.pyplot as plt
import plotly.express as px
from django.shortcuts import render
from django.contrib.sessions.models import Session
import csv
import os
import io
import pyrebase
from decimal import Decimal
import boto3
import numpy as np
import pandas as pd
from . import ml_model
from django.utils.timezone import now
from django.utils.timezone import now
from .dynamodb import get_all_items, get_device_data, parse_payload
from datetime import datetime

from django.core.paginator import Paginator



# Create your views here.
def home(request):
    items = get_all_items()
    for item in items:
        parsed_payload = parse_payload(item['payload'])
        item.update({
            'co': parsed_payload.get('co'),
            'nh3': parsed_payload.get('nh3'),
            'no2': parsed_payload.get('no2'),
            'o3': parsed_payload.get('o3'),
            'pm25': parsed_payload.get('pm25'),
            'pm10': parsed_payload.get('pm10'),
            'so2': parsed_payload.get('so2'),
            'hum': parsed_payload.get('hum'),
            'date': parsed_payload.get('date'),
            'time' : parsed_payload.get('time'),
        })

    # Check if items are available
    if not items:
        return JsonResponse({'error': 'No data available'}, status=400)

    # Sort items by date
    items.sort(
        key=lambda x: datetime.strptime(
            truncate_nanoseconds(x['received_at']).strip(),
            '%Y-%m-%dT%H:%M:%S.%fZ'
        ),
        reverse=True
    )

    latest_24_items = items[:24]  # Get the latest 24 items

    # Initialize sum and count for averaging
    parameters = ['nh3', 'no2', 'o3', 'pm25', 'pm10', 'so2', 'co']
    sums = {param: 0 for param in parameters}
    counts = {param: 0 for param in parameters}

    # Compute sums and counts
    for item in latest_24_items:
        parsed_payload = parse_payload(item['payload'])
        for param in parameters:
            value = parsed_payload.get(param)
            if value is not None:
                sums[param] += value
                counts[param] += 1

    # Calculate averages
    averages = {
        param: (sums[param] / counts[param]) if counts[param] > 0 else None
        for param in parameters
    }
    print("averages", averages)

    # Calculate sub-indices
    sub_indices = calculate_subindices(averages)

    print("sub_indices", sub_indices)

    # Get the highest sub-index
    valid_indices = [index for index in sub_indices.values() if index is not None]
    highest_sub_index = round(max(valid_indices)) if valid_indices else None
    print(highest_sub_index)

    # Get the latest item for display
    latest_item = latest_24_items[0] if latest_24_items else None

    if latest_item:
        received_at = datetime.strptime(
            truncate_nanoseconds(latest_item['received_at']).strip(),
            '%Y-%m-%dT%H:%M:%S.%fZ'
        )
        latest_item['received_at'] = received_at.strftime('%Y-%m-%d %H:%M:%S')

    # Return JSON for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'latest_item': latest_item,
            'averages': averages,
            'sub_indices': {k: round(v, 2) if v is not None else None for k, v in sub_indices.items()},
            'highest_sub_index': highest_sub_index
        })


    return render(request, 'index1.html', {
            "latest_item": latest_item,
            "averages": averages,
            "sub_indices": {k: round(v, 2) if v is not None else None for k, v in sub_indices.items()},
            "highest_sub_index": highest_sub_index
        })

def weather_map(request):
    return render(request, 'weather.html')
def weather_forecast(request):
    return render(request,'googlemap.html')
def load_csv_data():
    data = []
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_file_path = os.path.join(base_dir, 'air_pollution', 'test_data2.csv')
    with open(csv_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append({
                'lat': float(row['Latitude']),
                'lon': float(row['Longitude']),
               'city': row['City'],
                'aqi': int(row['AQI']),
                'pm25': float(row['PM25']),
                'pm10': float(row['PM10']),
                'so2': float(row['SO2']),
                'o3': float(row['O3']),
                'co': float(row['CO']),
                'no2': float(row['NO2']),
            })
    return data


"""

def air_quality_graph(request):
    csv_path = os.path.join(os.path.dirname(__file__), 'test_data2.csv')
    try:
            # Read the CSV file
            df = pd.read_csv(csv_path, on_bad_lines='skip')

            # Filter data for Kalady and Matoor
            df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
            df_kalady = df[df['City'].str.lower() == 'kalady']
            df_matoor = df[df['City'].str.lower() == 'matoor']

            if df_kalady.empty and df_matoor.empty:
                return render(request, 'error.html', {'error': 'No data available for these locations'})

            # Generate the line graph for Kalady
            df_kalady['date'] = pd.to_datetime(df_kalady['date'])
            fig_kalady = px.line(df_kalady, x='date', y='AQI', title='Air Quality Index (AQI) for Kalady')

            # Generate the line graph for Matoor
            df_matoor['date'] = pd.to_datetime(df_matoor['date'])
            fig_matoor = px.line(df_matoor, x='date', y='AQI', title='Air Quality Index (AQI) for Matoor')

            # Convert the figures to HTML for rendering in the template
            graph_kalady = fig_kalady.to_html(full_html=False)
            graph_matoor = fig_matoor.to_html(full_html=False)

            # Render the graphs as part of the response
            return render(request, 'air_quality_graph.html', {
                'graph_kalady': graph_kalady,
                'graph_matoor': graph_matoor
            })

    except pd.errors.ParserError as e:
            # Handle parsing errors and render an error template
            return render(request, 'error.html', {'error': str(e)})
matplotlib.use('Agg')

def aqi_graphs(request):
    # Load the CSV file
    csv_path = os.path.join(os.path.dirname(__file__), 'test_data2.csv')
    df = pd.read_csv(csv_path, on_bad_lines='skip')

    # Group data by city and date
    grouped_df = df.groupby(['City', 'date'])['AQI'].mean().reset_index()

    # Create the figure
    fig, ax = plt.subplots(figsize=(10, 6))

    for city in grouped_df['City'].unique():
        city_data = grouped_df[grouped_df['City'] == city]
        ax.plot(city_data['date'], city_data['AQI'], label=city)

    ax.set_xlabel('Date')
    ax.set_ylabel('AQI')
    ax.set_title('AQI Forecasting')
    ax.legend()
    plt.xticks(rotation=45)
    plt.grid(True)

    # Save the plot to a BytesIO object (in memory)
    buffer = io.BytesIO()
    canvas = FigureCanvas(fig)
    canvas.print_png(buffer)
    buffer.seek(0)

    # Return the image as an HTTP response
    return HttpResponse(buffer.getvalue(), content_type='image/png')
"""

def calculate_subindices(averages):
    """Calculate sub-indices for all parameters from their average values"""

    def safe_float(value):
        """Safely convert value to float, handling Decimal types"""
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def calculate_pm25_subindex(value):
        value = safe_float(value)
        if value is None or value < 0:  # Ensure value is valid
            return None
        if value <= 30.0:
            return (value * 50.0) / 30.0
        elif value <= 60.0:
            return 50.0 + ((value - 30.0) * 50.0) / 30.0
        elif value <= 90.0:
            return 100.0 + ((value - 60.0) * 100.0) / 30.0
        elif value <= 120.0:
            return 200.0 + ((value - 90.0) * 100.0) / 30.0
        elif value <= 250.0:
            return 300.0 + ((value - 120.0) * 100.0) / 130.0
        else:
            return 400.0 + ((value - 250.0) * 100.0) / 130.0

    def calculate_pm10_subindex(value):
        value = safe_float(value)
        if value is None:
            return None
        if value <= 50.0:
            return value
        elif value <= 100.0:
            return value
        elif value <= 250.0:
            return 100.0 + ((value - 100.0) * 100.0) / 150.0
        elif value <= 350.0:
            return 200.0 + ((value - 250.0) * 100.0) / 100.0
        elif value <= 430.0:
            return 300.0 + ((value - 350.0) * 100.0) / 80.0
        else:
            return 400.0 + ((value - 430.0) * 100.0) / 80.0

    def calculate_so2_subindex(value):
        value = safe_float(value)
        if value is None:
            return None
        if value <= 40.0:
            return (value * 50.0) / 40.0
        elif value <= 80.0:
            return 50.0 + ((value - 40.0) * 50.0) / 40.0
        elif value <= 380.0:
            return 100.0 + ((value - 80.0) * 100.0) / 300.0
        elif value <= 800.0:
            return 200.0 + ((value - 380.0) * 100.0) / 420.0
        elif value <= 1600.0:
            return 300.0 + ((value - 800.0) * 100.0) / 800.0
        else:
            return 400.0 + ((value - 1600.0) * 100.0) / 800.0

    def calculate_no2_subindex(value):
        value = safe_float(value)
        if value is None:
            return None
        if value <= 40.0:
            return (value * 50.0) / 40.0
        elif value <= 80.0:
            return 50.0 + ((value - 40.0) * 50.0) / 40.0
        elif value <= 180.0:
            return 100.0 + ((value - 80.0) * 100.0) / 100.0
        elif value <= 280.0:
            return 200.0 + ((value - 180.0) * 100.0) / 100.0
        elif value <= 400.0:
            return 300.0 + ((value - 280.0) * 100.0) / 120.0
        else:
            return 400.0 + ((value - 400.0) * 100.0) / 120.0

    def calculate_co_subindex(value):
        value = safe_float(value)
        if value is None:
            return None
        ppm = value * 0.873  # Convert mg/m3 to ppm
        if ppm <= 1.0:
            return (ppm * 50.0) / 1.0
        elif ppm <= 2.0:
            return 50.0 + ((ppm - 1.0) * 50.0) / 1.0
        elif ppm <= 10.0:
            return 100.0 + ((ppm - 2.0) * 100.0) / 8.0
        elif ppm <= 17.0:
            return 200.0 + ((ppm - 10.0) * 100.0) / 7.0
        elif ppm <= 34.0:
            return 300.0 + ((ppm - 17.0) * 100.0) / 17.0
        else:
            return 400.0 + ((ppm - 34.0) * 100.0) / 17.0

    def calculate_o3_subindex(value):
        value = safe_float(value)
        if value is None:
            return None
        if value <= 50.0:
            return (value * 50.0) / 50.0
        elif value <= 100.0:
            return 50.0 + ((value - 50.0) * 50.0) / 50.0
        elif value <= 168.0:
            return 100.0 + ((value - 100.0) * 100.0) / 68.0
        elif value <= 208.0:
            return 200.0 + ((value - 168.0) * 100.0) / 40.0
        elif value <= 748.0:
            return 300.0 + ((value - 208.0) * 100.0) / 540.0
        else:
            return 400.0 + ((value - 748.0) * 100.0) / 540.0

    def calculate_nh3_subindex(value):
        value = safe_float(value)
        if value is None:
            return None
        if value <= 200.0:
            return (value * 50.0) / 200.0
        elif value <= 400.0:
            return 50.0 + ((value - 200.0) * 50.0) / 200.0
        elif value <= 800.0:
            return 100.0 + ((value - 400.0) * 100.0) / 400.0
        elif value <= 1200.0:
            return 200.0 + ((value - 800.0) * 100.0) / 400.0
        elif value <= 1800.0:
            return 300.0 + ((value - 1200.0) * 100.0) / 600.0
        else:
            return 400.0 + ((value - 1800.0) * 100.0) / 600.0

    # Convert all average values to float before calculation
    safe_averages = {k: safe_float(v) for k, v in averages.items()}
    # Calculate sub-indices for each parameter
    sub_indices = {
        'pm25': calculate_pm25_subindex(safe_averages.get('pm25')),
        'pm10': calculate_pm10_subindex(safe_averages.get('pm10')),
        'so2': calculate_so2_subindex(safe_averages.get('so2')),
        'no2': calculate_no2_subindex(safe_averages.get('no2')),
        'co': calculate_co_subindex(safe_averages.get('co')),
        'o3': calculate_o3_subindex(safe_averages.get('o3')),
        'nh3': calculate_nh3_subindex(safe_averages.get('nh3'))
    }


    return sub_indices


def risk_assessment(request, username=None):
    username = username or request.session.get('name')

    if not username:
        return redirect('signup')

    try:
        health_assessment = HealthAssessment.objects.get(username=username)

        # Fetch all AQI items
        items = get_all_items()
        for item in items:
            parsed_payload = parse_payload(item['payload'])
            item.update({
                'co': parsed_payload.get('co'),
                'nh3': parsed_payload.get('nh3'),
                'no2': parsed_payload.get('no2'),
                'o3': parsed_payload.get('o3'),
                'pm25': parsed_payload.get('pm25'),
                'pm10': parsed_payload.get('pm10'),
                'so2': parsed_payload.get('so2'),
                'hum': parsed_payload.get('hum'),
                'pre' :parsed_payload.get('pre'),
                'temp' :parsed_payload.get('temp'),
                'date' :parsed_payload.get('date'),
            })

        # Check if items are available
        if not items:
            return JsonResponse({'error': 'No data available'}, status=400)

        # Sort items by date
        items.sort(
            key=lambda x: datetime.strptime(
                truncate_nanoseconds(x['received_at']).strip(),
                '%Y-%m-%dT%H:%M:%S.%fZ'
            ),
            reverse=True
        )

        latest_24_items = items[:24]  # Get the latest 24 items

        # Initialize sum and count for averaging
        parameters = ['nh3', 'no2', 'o3', 'pm25', 'pm10', 'so2', 'co']
        sums = {param: 0 for param in parameters}
        counts = {param: 0 for param in parameters}

        # Compute sums and counts
        for item in latest_24_items:
            parsed_payload = parse_payload(item['payload'])
            for param in parameters:
                value = parsed_payload.get(param)
                if value is not None:
                    sums[param] += value
                    counts[param] += 1

        # Calculate averages
        averages = {
            param: (sums[param] / counts[param]) if counts[param] > 0 else None
            for param in parameters
        }
        print("averages",averages)

        # Calculate sub-indices
        sub_indices = calculate_subindices(averages)

        print("sub_indices",sub_indices)


        # Get the highest sub-index
        valid_indices = [index for index in sub_indices.values() if index is not None]
        highest_sub_index = round(max(valid_indices)) if valid_indices else None
        print(highest_sub_index)


        # Get the latest item for display
        latest_item = latest_24_items[0] if latest_24_items else None

        if latest_item:
            received_at = datetime.strptime(
                truncate_nanoseconds(latest_item['received_at']).strip(),
                '%Y-%m-%dT%H:%M:%S.%fZ'
            )
            latest_item['received_at'] = received_at.strftime('%Y-%m-%d %H:%M:%S')

        # Return JSON for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'latest_item': latest_item,
                'averages': averages,
                'sub_indices': {k: round(v, 2) if v is not None else None for k, v in sub_indices.items()},
                'highest_sub_index': highest_sub_index
            })

        # Render template for non-AJAX requests
        return render(request, 'Userprofile.html', {
            "username": username,
            "health_assessment": health_assessment,
            "latest_item": latest_item,
            "health_score": health_assessment.health_score,
            "averages": averages,
            "sub_indices": {k: round(v, 2) if v is not None else None for k, v in sub_indices.items()},
            "highest_sub_index": highest_sub_index
        })

    except HealthAssessment.DoesNotExist:
        return redirect('signup')
    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({'error': str(e)}, status=500)
def health_questions(request, username):


    # Check if the user already has a health assessment entry
    try:
        assessments = HealthAssessment.objects.filter(username=username)

        if assessments.count() > 1:
            # Handle multiple assessments, e.g., take the latest one or merge them
            existing_assessment = assessments.latest('id')  # This assumes there's a field 'id' that increments
        elif assessments.count() == 1:
            existing_assessment = assessments.first()
        else:
            existing_assessment = None

        # If the method is POST, handle the form submission
        if request.method == 'POST':
            # If there's an existing assessment, update it
            if existing_assessment:
                age_group = request.POST.get('age_group', None)
                gender = request.POST.get('gender', None)
                respiratory_conditions = request.POST.getlist('respiratory_conditions')
                smoking_history = request.POST.getlist('smoking_history')
                living_environment = request.POST.getlist('living_environment')
                common_symptoms = request.POST.getlist('common_symptoms')
                occupational_exposure = request.POST.get('occupational_exposure', '')
                medical_history = request.POST.getlist('medical_history')

                # Update the existing assessment
                existing_assessment.age_group = age_group
                existing_assessment.gender = gender
                existing_assessment.respiratory_conditions = respiratory_conditions
                existing_assessment.smoking_history = smoking_history
                existing_assessment.living_environment = living_environment
                existing_assessment.common_symptoms = common_symptoms
                existing_assessment.occupational_exposure = occupational_exposure
                existing_assessment.medical_history = medical_history
                existing_assessment.save()

                # Recalculate the score and save
                score = calculate_health_score(request)
                existing_assessment.health_score = score
                existing_assessment.save()

                return render(request, 'health_questions.html', {
                    "username": username,
                    "health_score": score,
                    "existing_assessment": existing_assessment
                })

            else:
                # If no existing assessment, create a new one
                age_group = request.POST.get('age_group', None)
                gender = request.POST.get('gender', None)
                respiratory_conditions = request.POST.getlist('respiratory_conditions')
                smoking_history = request.POST.getlist('smoking_history')
                living_environment = request.POST.getlist('living_environment')
                common_symptoms = request.POST.getlist('common_symptoms')
                occupational_exposure = request.POST.get('occupational_exposure', '')
                medical_history = request.POST.getlist('medical_history')

                # Create new health assessment entry
                HealthAssessment.objects.create(
                    username=username,
                    age_group=age_group,
                    gender=gender,
                    respiratory_conditions=respiratory_conditions,
                    smoking_history=smoking_history,
                    living_environment=living_environment,
                    common_symptoms=common_symptoms,
                    occupational_exposure=occupational_exposure,
                    medical_history=medical_history,
                    health_score=calculate_health_score(request)
                )

                # Recalculate the score
                score = calculate_health_score(request)
                return render(request, 'health_questions.html', {
                    "username": username,
                    "health_score": score
                })

        # If the method is GET, render the page with existing data if present
        if existing_assessment:
            return render(request, 'health_questions.html', {
                "username": username,
                "health_score": existing_assessment.health_score,
                "existing_assessment": existing_assessment
            })
        else:
            # If there's no existing assessment, render the empty form
            return render(request, 'health_questions.html', {
                "username": username,
                "health_score": 0  # Start with 0 if no health assessment is available
            })

    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)

def calculate_health_score(request):
    score = 0

    # 1. Age Group
    age_group = request.POST.get('age_group')
    if age_group == "0-12 years":
        score += 5
    elif age_group == "13-18 years":
        score += 8
    elif age_group == "19-40 years":
        score += 10
    elif age_group == "41-60 years":
        score += 15
    elif age_group == "61 years and above":
        score += 20

    # 2. Gender
    gender = request.POST.get('gender')
    score += 2 if gender == "Male" else 1

    # 3. Respiratory Conditions
    respiratory_conditions = request.POST.getlist('respiratory_conditions')
    if "None" not in respiratory_conditions:
        score += len(respiratory_conditions) * 3

    # 4. Smoking History
    smoking = request.POST.get('smoking_history')
    smoking_scores = {
        "Never smoked": 0,
        "Former smoker": 10,
        "Current smoker": 25,
        "Exposed to secondhand smoke": 8
    }
    score += smoking_scores.get(smoking, 0)

    # 5. Living Environment
    living_env = request.POST.getlist('living_environment')
    environment_scores = {
        "Urban area": 10,
        "Industrial zone": 15,
        "Rural area": 3,
        "Coastal area": 2
    }
    for env in living_env:
        score += environment_scores.get(env, 0)

    # 6. Common Symptoms
    symptoms = request.POST.getlist('common_symptoms')
    symptom_scores = {
        "Frequent coughing": 8,
        "Shortness of breath": 10,
        "Wheezing": 8,
        "Chest tightness": 9
    }
    for symptom in symptoms:
        score += symptom_scores.get(symptom, 0)

    # 7. Occupational Exposure
    occupation = request.POST.get('occupational_exposure')
    occupation_scores = {
        "Construction/Mining": 15,
        "Chemical Industry": 15,
        "Healthcare": 8,
        "Agriculture": 10,
        "Office Environment": 3,
        "Other": 5
    }
    score += occupation_scores.get(occupation, 0)

    # 8. Medical History
    medical_history = request.POST.getlist('medical_history')
    condition_scores = {
        "Hypertension": 8,
        "Diabetes": 8,
        "Heart Disease": 10,
        "Allergies": 5,
        "Immunocompromised": 12
    }
    for condition in medical_history:
        score += condition_scores.get(condition, 0)

    return score

def calculate_health_score_from_existing(existing_assessment):
    # Logic to calculate score from existing health assessment
    score = 0
    # You would use the fields of `existing_assessment` to calculate the score as you did in `calculate_health_score`.
    return score
@csrf_exempt  # Only use this if absolutely necessary, or else remove it.
def signup(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone_number = request.POST.get('phone_number')
        # Phone number validation
        phone_pattern = re.compile(r'^\+\d{1,3}\d{9,14}$')  # Example: +123456789012
        if not phone_pattern.match(phone_number):
            return HttpResponse('Invalid phone number format. Use format: +CountryCodeNumber', status=400)

        # Check if the phone number is already in use
        if User.objects.filter(phone_number=phone_number).exists():
            return HttpResponse('Phone number already registered', status=400)

        # Create and save the new user
        user = User.objects.create(name=name, phone_number=phone_number)
        user.save()

        # Redirect to login page after successful signup
        return redirect('login')  # Ensure 'login' matches the name of your login URL

    # If the request is GET, render the signup form
    return render(request, 'signup.html')



def login(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        user = authenticate(request,phone_number=phone_number)
        user1=login.objects.create(phone_number=phone_number)
        user1.save()
        if user is not None:
            login(request, user)
            messages.success(request, 'Logged in Successfully!')
            return redirect(home)
        else:
            messages.error(request, 'Invalid Credentials!')
            return redirect(login)
    return render(request, 'login.html')


TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
VERIFY_SERVICE_SID = os.getenv("VERIFY_SERVICE_SID")



client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


@csrf_exempt
def send_otp(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')

        # Check if the phone number exists in the User model
        if User.objects.filter(phone_number=phone_number).exists():
            # Send OTP to phone number via Twilio Verify Service
            try:
                verification = client.verify \
                    .services(VERIFY_SERVICE_SID) \
                    .verifications \
                    .create(to=phone_number, channel='sms')
                request.session['phone_number'] = phone_number  # Store the phone number in the session
                return redirect('verify_otp')
            except Exception as e:
                return HttpResponse(f'Error: {str(e)}', status=500)
        else:
            # Phone number not found in the User model
            return HttpResponse('Phone number not registered.', status=400)

    return render(request, 'login.html')


@csrf_exempt
def verify_otp(request):
    if request.method == 'POST':

        otp_code = request.POST.get('otp_code')  # Ensure OTP code is fetched properly
        phone_number = request.session.get('phone_number')  # Ensure phone number is available

        if not otp_code:
            return HttpResponse('OTP code is missing.', status=400)

        try:
            # Verify OTP through Twilio
            verification_check = client.verify \
                .services(VERIFY_SERVICE_SID) \
                .verification_checks \
                .create(to=phone_number, code=otp_code)

            if verification_check.status == "approved":
                # OTP is correct; user can now be logged in
                request.session['otp_verified'] = True  # Mark the session as verified

                try:
                    user = User.objects.get(phone_number=phone_number)

                    request.session['name'] = user.name
                    # Check if the user has completed the health questionnaire
                    if not HealthAssessment.objects.filter(
                            username=user).exists():  # Check if the user exists in the HealthQuestionnaire table
                        # User has not completed the questionnaire
                        return redirect('health_questions',
                                        username=user.name)  # Pass the user's name to the health questionnaire page
                    else:
                        # User has completed the questionnaire
                        return redirect('home')

                except User.DoesNotExist:
                    return HttpResponse('User with this phone number does not exist', status=400)

            else:
                    return HttpResponse('OTP verification failed', status=400)
        except Exception as e:
                return HttpResponse(f'Error: {str(e)}', status=500)

    return render(request, 'otp_verification.html')




def logout(request):
    # Clear the session on logout
    request.session.flush()  # Removes all session data
    return redirect('login')  # Redirect to the login page after logging

def AQI_forecast(request):
    items = get_all_items()

    for item in items:
        parsed_payload = parse_payload(item['payload'])
        item['aqi'] = parsed_payload.get('aqi', None)
        item['pm25'] = parsed_payload.get('pm25', None)
        item['pm10'] = parsed_payload.get('pm10', None)
        item['no2'] = parsed_payload.get('no2', None)
        item['co'] = parsed_payload.get('co', None)
        item['o3'] = parsed_payload.get('o3', None)

    items.sort(key=lambda x: datetime.strptime(truncate_nanoseconds(x['received_at']).strip(), '%Y-%m-%dT%H:%M:%S.%fZ'),
               reverse=True)
    latest_item = items[0] if items else None

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'latest_item': latest_item})

    return render(request, 'AQI_forecast.html', {'latest_item': latest_item})



"""def user_login(request):
    if request.user.is_authenticated:
                 # Check if health questionnaire is completed
            if not user.is_health_questionnaire_completed:  # Assuming this is a boolean field in the User model
                # If not completed, redirect to the health questionnaire page
                return redirect('health_questionnaire')
            else:
                # If completed, redirect to the home page (dashboard)
                return redirect('home')
    else:
            # If login fails, show an error message
            messages.error(request, "Invalid phone number or password")"""



    # Render the login page for GET request or after an invalid login attempt

"""

config={
    "apiKey": "AIzaSyC6S6gIlQCPtPs0QQDT_EHYGekLX_BPTAg",
    "authDomain": "lora-5c160.firebaseapp.com",
    "databaseURL": "https://lora-5c160-default-rtdb.asia-southeast1.firebasedatabase.app",
    "projectId": "lora-5c160",
    "storageBucket": "lora-5c160.appspot.com",
    "messagingSenderId": "691553667840",
    "appId": "1:691553667840:web:2babf8f9f020434fb401e5"
}
firebase =pyrebase.initialize_app(config)
authe =firebase.auth()
database=firebase.database()


def admin_view(request):
    # Existing logic to get the latest sensor data
    sensor_data = database.child('ttn').child('mq131').get()

    latest_co = None
    latest_aqi = None
    latest_nh3 = None
    latest_no2 = None
    latest_o3 = None
    latest_pm10 = None
    latest_pm25 = None
    latest_so2 = None
    latest_temperature=None
    latest_humidity=None
    latest_pressure=None
    latest_date = None
    latest_time=None


    if sensor_data.each():
        for sensor in sensor_data.each():
            uplink_message = sensor.val().get('uplink_message', {})
            decoded_payload = uplink_message.get('decoded_payload', {})

            # Extract values
            latest_co = decoded_payload.get('co', latest_co)
            latest_aqi = decoded_payload.get('aqi', latest_aqi)
            latest_nh3 = decoded_payload.get('nh3', latest_nh3)
            latest_no2 = decoded_payload.get('no2', latest_no2)
            latest_o3 = decoded_payload.get('o3', latest_o3)
            latest_pm10 = decoded_payload.get('pm10', latest_pm10)
            latest_pm25 = decoded_payload.get('pm25', latest_pm25)
            latest_so2 = decoded_payload.get('so2', latest_so2)
            latest_temperature = decoded_payload.get('temp',latest_temperature)
            latest_humidity = decoded_payload.get('hum',latest_humidity)
            latest_pressure = decoded_payload.get('pressure',latest_pressure)
            latest_date = decoded_payload.get('date', latest_date)
            latest_time = decoded_payload.get('time', latest_time)


    # Render initial page
    if request.method == 'GET':
        return render(request, 'admin.html', {
            'latest_co': latest_co,
            'latest_aqi': latest_aqi,
            'latest_nh3': latest_nh3,
            'latest_no2': latest_no2,
            'latest_o3': latest_o3,
            'latest_pm10': latest_pm10,
            'latest_pm25': latest_pm25,
            'latest_so2': latest_so2,
            'latest_temperature':latest_temperature,
            'latest_humidity':latest_humidity,
            'latest_pressure':latest_pressure,
            'latest_date':latest_date,
            'latest_time':latest_time,

        })
def fetch_latest_data(request):
    sensor_data = database.child('ttn').child('mq131').get()

    response_data = {
        'latest_co': None,
        'latest_aqi': None,
        'latest_nh3': None,
        'latest_no2': None,
        'latest_o3': None,
        'latest_pm10': None,
        'latest_pm25': None,
        'latest_so2': None,
        'latest_temperature' : None,
        'latest_humidity': None,
        'latest_pressure': None,
        'latest_date':None,
        'latest_time':None,

    }

    if sensor_data.each():
        for sensor in sensor_data.each():
            uplink_message = sensor.val().get('uplink_message', {})
            decoded_payload = uplink_message.get('decoded_payload', {})

            # Extract values
            response_data['latest_co'] = decoded_payload.get('co', response_data['latest_co'])
            response_data['latest_aqi'] = decoded_payload.get('aqi', response_data['latest_aqi'])
            response_data['latest_nh3'] = decoded_payload.get('nh3', response_data['latest_nh3'])
            response_data['latest_no2'] = decoded_payload.get('no2', response_data['latest_no2'])
            response_data['latest_o3'] = decoded_payload.get('o3', response_data['latest_o3'])
            response_data['latest_pm10'] = decoded_payload.get('pm10', response_data['latest_pm10'])
            response_data['latest_pm25'] = decoded_payload.get('pm25', response_data['latest_pm25'])
            response_data['latest_so2'] = decoded_payload.get('so2', response_data['latest_so2'])
            response_data['latest_temperature']=decoded_payload.get('temperature',response_data['latest_temperature'])
            response_data['latest_humidity'] =decoded_payload.get('humidity',response_data['latest_humidity'])
            response_data['latest_pressure'] =decoded_payload.get('pressure',response_data['latest_pressure'])
            response_data['latest_date'] = decoded_payload.get('date', response_data['latest_date'])
            response_data['latest_time'] = decoded_payload.get('time', response_data['latest_time'])
    return JsonResponse(response_data)


"""

def map_view(request):
    items = get_all_items()
    for item in items:
        parsed_payload = parse_payload(item['payload'])
        item.update({
            'co': parsed_payload.get('co'),
            'nh3': parsed_payload.get('nh3'),
            'no2': parsed_payload.get('no2'),
            'o3': parsed_payload.get('o3'),
            'pm25': parsed_payload.get('pm25'),
            'pm10': parsed_payload.get('pm10'),
            'so2': parsed_payload.get('so2'),
            'hum': parsed_payload.get('hum'),
            'date': parsed_payload.get('date'),
            'time': parsed_payload.get('time'),
        })

    # Check if items are available
    if not items:
        return JsonResponse({'error': 'No data available'}, status=400)

    # Sort items by date
    items.sort(
        key=lambda x: datetime.strptime(
            truncate_nanoseconds(x['received_at']).strip(),
            '%Y-%m-%dT%H:%M:%S.%fZ'
        ),
        reverse=True
    )

    latest_24_items = items[:24]  # Get the latest 24 items

    # Initialize sum and count for averaging
    parameters = ['nh3', 'no2', 'o3', 'pm25', 'pm10', 'so2', 'co']
    sums = {param: 0 for param in parameters}
    counts = {param: 0 for param in parameters}

    # Compute sums and counts
    for item in latest_24_items:
        parsed_payload = parse_payload(item['payload'])
        for param in parameters:
            value = parsed_payload.get(param)
            if value is not None:
                sums[param] += value
                counts[param] += 1

    # Calculate averages
    averages = {
        param: (sums[param] / counts[param]) if counts[param] > 0 else None
        for param in parameters
    }
    print("averages", averages)

    # Calculate sub-indices
    sub_indices = calculate_subindices(averages)

    print("sub_indices", sub_indices)

    # Get the highest sub-index
    valid_indices = [index for index in sub_indices.values() if index is not None]
    highest_sub_index = round(max(valid_indices)) if valid_indices else None
    print(highest_sub_index)

    # Get the latest item for display
    latest_item = latest_24_items[0] if latest_24_items else None

    if latest_item:
        received_at = datetime.strptime(
            truncate_nanoseconds(latest_item['received_at']).strip(),
            '%Y-%m-%dT%H:%M:%S.%fZ'
        )
        latest_item['received_at'] = received_at.strftime('%Y-%m-%d %H:%M:%S')

    # Return JSON for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'latest_item': latest_item,
            'averages': averages,
            'sub_indices': {k: round(v, 2) if v is not None else None for k, v in sub_indices.items()},
            'highest_sub_index': highest_sub_index
        })

    # Render the map page and pass the latest data to the template
    return render(request, 'map.html', {
        'latest_item': latest_item,
        'highest_sub_index': highest_sub_index
    })
#def map_view(request):
 #   csv_data = load_csv_data()
  #  return render(request, 'map.html', {'locations': csv_data})


trained_models = None
last_sequence = None
last_date = None
accuracies = None

def initialize_model():
    global trained_models, last_sequence, last_date, accuracies
    if trained_models is None:
        # Adjust the path to your CSV file
        df = pd.read_csv(os.path.join(settings.BASE_DIR, 'air_pollution', 'ELO.csv'))
        trained_models, accuracies, X, y, dates = ml_model.train_model(df)
        last_sequence = X[-1]
        last_date = dates[-1]

def index_test(request):
    initialize_model()
    future_predictions = ml_model.forecast_next_days(trained_models, last_sequence, last_date, n_days=4)
    context = {
        'predictions': future_predictions.to_html(index=False, classes='table table-striped'),
        'accuracies': accuracies
    }
    return render(request, 'ml_model.html', context)

def predict_api(request):
    initialize_model()
    future_predictions = ml_model.forecast_next_days(trained_models, last_sequence, last_date, n_days=4)
    return JsonResponse(future_predictions.to_dict(orient='records'), safe=False)


def list_all_data(request):
    """View to list all items in the DynamoDB table."""
    items = get_all_items()

    # Parse payload for better readability
    for item in items:
        item['payload'] = parse_payload(item['payload'])

    # Sort the items by 'received_at' to get the latest data
    items.sort(key=lambda x: datetime.strptime(truncate_nanoseconds(x['received_at']).strip(), '%Y-%m-%dT%H:%M:%S.%fZ'),
               reverse=True)

    # Get only the latest item
    latest_item = items[0] if items else None

    return JsonResponse({'data': latest_item})


def truncate_nanoseconds(timestamp):
    """Truncate nanoseconds to microseconds for correct parsing."""
    # Split at the dot and keep the first 6 digits of microseconds
    parts = timestamp.split('T')
    date_part = parts[0]
    time_part = parts[1]
    time_parts = time_part.split('Z')[0]  # Remove 'Z'

    # Truncate nanoseconds to 6 digits (microseconds)
    if '.' in time_parts:
        time_parts = time_parts[:time_parts.index('.') + 7]  # Keep first 6 digits of microseconds

    return f'{date_part}T{time_parts}Z'

def get_data_by_device(request, device_id):
    """View to get data by device ID."""
    items = get_device_data(device_id)
    for item in items:
        item['payload'] = parse_payload(item['payload'])
    return JsonResponse({'data': items})

def decimal_default(obj):
    """Convert Decimal to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {obj} not serializable")

def display_all_data(request):
    # Retrieve all items
    items = get_all_items()

    for item in items:
        parsed_payload = parse_payload(item['payload'])
        item['aqi'] = parsed_payload.get('aqi', None)
        item['co'] = parsed_payload.get('co', None)
        item['nh3'] = parsed_payload.get('nh3', None)
        item['no2'] = parsed_payload.get('no2', None)
        item['o3'] = parsed_payload.get('o3', None)
        item['pm25'] = parsed_payload.get('pm25', None)

    items.sort(key=lambda x: datetime.strptime(truncate_nanoseconds(x['received_at']).strip(), '%Y-%m-%dT%H:%M:%S.%fZ'), reverse=True)
    latest_item = items[0] if items else None

    # Return JSON for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'latest_item': latest_item})

    # Render the page for non-AJAX requests
    return render(request, 'test.html', {'latest_item': latest_item})


def health_report(request):
    try:
        username = request.session.get('name')
        if not username:
            return redirect('home')

        # Retrieve latest health assessment
        latest_assessment = HealthAssessment.objects.filter(username=username).latest('id')

        # Fetch AQI data
        items = get_all_items()
        if not items:
            return render(request, 'Health_report.html', {
                "username": username,
                "alert_message": "No real-time air quality data available.",
            })

        # Process AQI data
        for item in items:
            parsed_payload = parse_payload(item['payload'])
            item.update(parsed_payload)

        # Sort data by latest timestamp
        items.sort(key=lambda x: datetime.strptime(x['received_at'][:19], '%Y-%m-%dT%H:%M:%S'), reverse=True)
        latest_item = items[0] if items else None

        if not latest_item:
            return render(request, 'Health_report.html', {"username": username, "alert_message": "No recent AQI data available."})

        # Extract AQI levels
        co_level, nh3_level, no2_level, o3_level = latest_item['co'], latest_item['nh3'], latest_item['no2'], latest_item['o3']
        pm25_level, pm10_level, so2_level = latest_item['pm25'], latest_item['pm10'], latest_item['so2']

        # WHO AQI limits (24-hour exposure)
        WHO_LIMITS = {"co": 4, "so2": 40, "pm25": 15, "pm10": 45, "no2": 28, "o3": 64, "nh3": 200}

        alerts = []
        respiratory_conditions = latest_assessment.respiratory_conditions
        living_environment = latest_assessment.living_environment
        medical_history = latest_assessment.medical_history
        smoking_history = latest_assessment.smoking_history

        is_smoker = "Current smoker" in smoking_history
        is_industrial_area = "Industrial zone" in living_environment
        has_copd = "COPD" in respiratory_conditions
        has_asthma = "Asthma" in respiratory_conditions

        # Check if any AQI gas exceeds the WHO limits
        exceeded_gases = {gas: level for gas, level in {
            "co": co_level, "so2": so2_level, "pm25": pm25_level,
            "pm10": pm10_level, "no2": no2_level, "o3": o3_level, "nh3": nh3_level
        }.items() if level > WHO_LIMITS[gas]}

        if exceeded_gases:
            # Adjust thresholds based on user history
            def exceeds_limit(pollutant, level):
                threshold = WHO_LIMITS[pollutant]
                if has_copd or has_asthma:
                    threshold *= 0.7  # Stricter for respiratory patients
                if is_smoker:
                    threshold *= 0.8  # Stricter for smokers
                if is_industrial_area:
                    threshold *= 1.2  # Higher tolerance in industrial areas
                return level > threshold

            # Generate personalized alerts
            if has_copd:
                if exceeds_limit("co", co_level):
                    alerts.append("⚠️ High CO levels detected. COPD patients should stay indoors and use air purifiers.")
                if exceeds_limit("pm25", pm25_level):
                    alerts.append("⚠️ High PM2.5 levels detected. Wear an N95 mask or avoid outdoor exposure.")
                if exceeds_limit("so2", so2_level):
                    alerts.append("⚠️ Elevated SO₂ levels. Avoid outdoor activities.")

            if has_asthma:
                if exceeds_limit("no2", no2_level):
                    alerts.append("⚠️ Elevated NO₂ levels. Avoid high-traffic areas.")
                if exceeds_limit("o3", o3_level):
                    alerts.append("⚠️ High O₃ levels. Stay indoors during peak sunlight hours.")

            # Environmental exposure alerts
            if "Urban area" in living_environment and exceeds_limit("co", co_level):
                alerts.append("⚠️ Urban exposure detected. High CO levels affect lung health.")

            # Smoking-based alerts
            if is_smoker and exceeds_limit("co", co_level):
                alerts.append("⚠️ CO levels are dangerous for smokers. Reduce exposure.")

            # Occupational exposure alerts
            if latest_assessment.occupational_exposure and exceeds_limit("so2", so2_level):
                alerts.append("⚠️ Occupational hazard detected with SO₂ exposure. Follow safety protocols.")

            # General alerts (for all users)
            if exceeds_limit("pm10", pm10_level):
                alerts.append("⚠️ High PM10 levels detected. Reduce outdoor activities and wear a mask.")
            if exceeds_limit("nh3", nh3_level):
                alerts.append("⚠️ High NH₃ levels detected. Ensure good indoor ventilation.")

        # Radar Chart Data
        radar_data = {
            "Respiratory": {
                "value": len(latest_assessment.respiratory_conditions.split(',')),
                "details": latest_assessment.respiratory_conditions.split(',')
            },
            "Lifestyle": {
                "value": len(latest_assessment.smoking_history.split(',')),
                "details": latest_assessment.smoking_history.split(',')
            },
            "Environmental": {
                "value": len(latest_assessment.living_environment.split(',')),
                "details": latest_assessment.living_environment.split(',')
            },
            "Medical": {
                "value": len(latest_assessment.medical_history.split(',')),
                "details": latest_assessment.medical_history.split(',')
            },
            "Occupational": {
                "value": 1 if latest_assessment.occupational_exposure else 0,
                "details": [latest_assessment.occupational_exposure] if latest_assessment.occupational_exposure else []
            },
            "Age Group": {
                "value": len(latest_assessment.age_group.split(',')) if latest_assessment.age_group else 0,
                "details": latest_assessment.age_group.split(',') if latest_assessment.age_group else []
            },
            "Gender": {
                "value": 1 if latest_assessment.gender else 0,
                "details": [latest_assessment.gender] if latest_assessment.gender else []
            },
            "Symptoms": {
                "value": len(latest_assessment.common_symptoms.split(',')) if latest_assessment.common_symptoms else 0,
                "details": latest_assessment.common_symptoms.split(',') if latest_assessment.common_symptoms else []
            },
        }

        return render(request, 'Health_report.html', {
            "health_score": latest_assessment.health_score,
            "username": username,
            "assessment": latest_assessment,
            "radar_labels": list(radar_data.keys()),
            "radar_values": [item["value"] for item in radar_data.values()],
            "radar_details": {key: item["details"] for key, item in radar_data.items()},
            "alert_message": " | ".join(alerts) if alerts else "✅ No critical alerts detected.",
            "aqi_data": {"co_level": co_level, "nh3_level": nh3_level, "no2_level": no2_level, "o3_level": o3_level, "pm25_level": pm25_level, "pm10_level": pm10_level, "so2_level": so2_level},
        })

    except HealthAssessment.DoesNotExist:
        return redirect('home')

    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

from django.contrib import admin
from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from .import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home,name='home'),
    path('weather', views.weather_map,name='weather'),
    path('weather_forecast', views.weather_forecast,name='weather_forecast'),
    path('load_csv_data', views.load_csv_data, name='load_csv_data'),
    path('map_view', views.map_view, name='map_view'),
   # path('air_quality_graph', views.air_quality_graph, name='air_quality_graph'),
    path('AQI_forecast', views.AQI_forecast, name='AQI_forecast'),
    path('risk_assessment/', views.risk_assessment, name='risk_assessment'),
    path('health_questions/<str:username>/', views.health_questions, name='health_questions'),
   # path('aqi_graphs', views.aqi_graphs, name='aqi_graphs'),
    path('login',views.login,name='login'),
    path('send_otp/', views.send_otp, name='send_otp'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('signup',views.signup,name='signup'),
  #  path('signup_send_otp',views.signup_send_otp,name='signup_send_otp'),
   # path('signup_verify_otp',views.signup_verify_otp,name='signup_verify_otp'),
    path('logout',views.logout,name='logout'),
  #  path('user_login',views.user_login,name='user_login'),

  #  path('admin_view',views.admin_view,name='admin_view'),
   # path('fetch-latest-data/', views.fetch_latest_data, name='fetch_latest_data'),

    path('index_test', views.index_test, name='index_test'),
    path('predict_api', views.predict_api, name='predict_api'),

    path('all-data/', views.list_all_data, name='list_all_data'),
    path('device/<str:device_id>/', views.get_data_by_device, name='get_data_by_device'),
    path('display-data/', views.display_all_data, name='display_all_data'),
    path('health_report',views.health_report, name='health_report'),

]




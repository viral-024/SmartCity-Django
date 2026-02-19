from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_redirect, name='dashboard'),
    path('citizen/', views.citizen_dashboard, name='citizen'),
    path('gov/', views.gov_dashboard, name='gov'),
    path('utility/', views.utility_dashboard, name='utility'),
    path('emergency/', views.emergency_dashboard, name='emergency'),
    path('driver/', views.driver_dashboard, name='driver'),
]
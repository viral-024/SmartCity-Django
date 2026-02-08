from django.urls import path
from . import views

urlpatterns = [
    path("government/", views.gov_dashboard, name="gov_dashboard"),
    path("emergency/", views.emergency_dashboard, name="emergency_dashboard"),
    path("utility/", views.utility_dashboard, name="utility_dashboard"),
    path("worker/", views.worker_dashboard, name="worker_dashboard"),
    path("citizen/", views.citizen_dashboard, name="citizen_dashboard"),
]

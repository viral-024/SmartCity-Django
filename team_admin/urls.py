from django.urls import path
from . import views

app_name = 'team_admin'

urlpatterns = [
    path('workers/create/', views.create_worker, name='create_worker'),
    path('workers/', views.manage_workers, name='manage_workers'),
    
    path('emergency-teams/create/', views.create_emergency_team, name='create_emergency_team'),
    path('emergency-teams/', views.manage_emergency_teams, name='manage_emergency_teams'),
    path('emergency-teams/<int:team_id>/add-worker/', views.add_worker_to_emergency_team, name='add_worker_to_emergency_team'),
    
    path('utility-teams/create/', views.create_utility_team, name='create_utility_team'),
    path('utility-teams/', views.manage_utility_teams, name='manage_utility_teams'),
    path('utility-teams/<int:team_id>/add-worker/', views.add_worker_to_utility_team, name='add_worker_to_utility_team'),
    
    path('vehicles/create/', views.create_vehicle, name='create_vehicle'),
    path('vehicles/', views.manage_vehicles, name='manage_vehicles'),
    path('vehicles/<int:vehicle_id>/delete/', views.delete_vehicle, name='delete_vehicle'),
]
from django.urls import path
from . import views

app_name = 'emergency'

urlpatterns = [
    # Citizen URLs
    path('report/', views.citizen_emergency_request, name='report_emergency'),
    path('my-requests/', views.my_emergency_requests, name='my_requests'),
    path('detail/<int:request_id>/', views.emergency_detail, name='detail'),
    path('detail/<int:request_id>/cancel/', views.cancel_emergency_request, name='cancel_request'),

    # Operator URLs
    path('operator/', views.operator_dashboard, name='operator_dashboard'),
    path('assign-team/<int:emergency_id>/', views.assign_team, name='assign_team'),
    path('update-team-status/<int:assignment_id>/', views.update_team_status, name='update_team_status'),
    path('manage-teams/', views.manage_teams, name='manage_teams'),
    path('add-worker/<int:team_id>/', views.add_worker_to_team, name='add_worker_to_team'),
    path('manage-vehicles/', views.manage_vehicles, name='manage_vehicles'),
    path('vehicles/delete/<int:vehicle_id>/', views.delete_vehicle, name='delete_vehicle'),
]

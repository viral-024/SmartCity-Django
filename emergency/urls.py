from django.urls import path
from . import views

app_name = 'emergency'

urlpatterns = [
    # Citizen URLs
    path('report/', views.citizen_emergency_request, name='report_emergency'),
    path('my-requests/', views.my_emergency_requests, name='my_requests'),
    path('detail/<int:request_id>/', views.emergency_detail, name='detail'),
    
    # Operator URLs - TEAM-BASED WORKFLOW (ONLY EXISTING VIEWS)
    path('operator/', views.operator_dashboard, name='operator_dashboard'),
    path('assign-team/<int:emergency_id>/', views.assign_team, name='assign_team'),
    path('update-team-status/<int:assignment_id>/', views.update_team_status, name='update_team_status'),  # ← MUST EXIST IN VIEWS
    path('manage-teams/', views.manage_teams, name='manage_teams'),
    path('add-worker/<int:team_id>/', views.add_worker_to_team, name='add_worker_to_team'),
    
    # Vehicle Management (kept separate)
    path('manage-vehicles/', views.manage_vehicles, name='manage_vehicles'),
    path('vehicles/delete/<int:vehicle_id>/', views.delete_vehicle, name='delete_vehicle'),
    
    # ⚠️ REMOVED: worker-dashboard pattern (causing error - view not found)
    # path('worker-dashboard/', views.worker_dashboard, name='worker_dashboard'),
    
    # ⚠️ REMOVED: Deprecated vehicle assignment patterns (views don't exist)
    # path('assign/<int:emergency_id>/', views.assign_vehicle, name='assign_vehicle'),
    # path('dispatch/update/<int:dispatch_id>/', views.update_dispatch_status, name='update_dispatch_status'),
]
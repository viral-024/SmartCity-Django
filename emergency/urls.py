from django.urls import path
from . import views

app_name = 'emergency'

urlpatterns = [
    # Citizen URLs
    path('report/', views.citizen_emergency_request, name='report_emergency'),
    path('my-requests/', views.my_emergency_requests, name='my_requests'),
    path('detail/<int:request_id>/', views.emergency_detail, name='detail'),
    
    # Operator URLs
    path('operator/', views.operator_dashboard, name='operator_dashboard'),
    path('assign/<int:emergency_id>/', views.assign_vehicle, name='assign_vehicle'),
    path('dispatch/update/<int:dispatch_id>/', views.update_dispatch_status, name='update_dispatch_status'),
    path('vehicles/', views.manage_vehicles, name='manage_vehicles'),
    path('vehicles/delete/<int:vehicle_id>/', views.delete_vehicle, name='delete_vehicle'),
]
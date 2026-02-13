from django.urls import path
from . import views

app_name = 'emergency'

urlpatterns = [
    path('report/', views.citizen_emergency_request, name='report_emergency'),
    path('my-requests/', views.my_emergency_requests, name='my_requests'),
    path('detail/<int:request_id>/', views.emergency_detail, name='detail'),
]
from django.urls import path
from . import views

app_name = 'utilities'

urlpatterns = [
    # Citizen URLs
    path('submit/', views.citizen_submit_complaint, name='submit_complaint'),
    path('my-complaints/', views.my_complaints, name='my_complaints'),
    path('detail/<str:complaint_id>/', views.complaint_detail, name='detail'),
    path('detail/<str:complaint_id>/rate/', views.rate_complaint, name='rate_complaint'),

    # Officer URLs
    path('officer/', views.officer_dashboard, name='officer_dashboard'),
    path('assign-team/<int:complaint_id>/', views.assign_utility_team, name='assign_utility_team'),
    path('update-team-status/<int:assignment_id>/', views.update_team_assignment_status, name='update_team_assignment_status'),
]

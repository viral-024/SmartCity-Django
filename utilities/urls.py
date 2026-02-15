from django.urls import path
from . import views

app_name = 'utilities'

urlpatterns = [
    path('submit/', views.citizen_submit_complaint, name='submit_complaint'),
    path('my-complaints/', views.my_complaints, name='my_complaints'),
    path('detail/<str:complaint_id>/', views.complaint_detail, name='detail'),
    
    path('officer/', views.officer_dashboard, name='officer_dashboard'),
    path('assign/<int:complaint_id>/', views.assign_complaint, name='assign_complaint'),
    path('update/<int:complaint_id>/', views.update_complaint_status, name='update_complaint_status'),
]
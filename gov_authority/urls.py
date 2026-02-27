from django.urls import path
from . import views

app_name = 'gov_authority'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('staff/', views.staff_list, name='staff_list'),
    path('escalations/', views.escalations, name='escalations'),
]
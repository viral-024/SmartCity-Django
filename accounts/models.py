from django.db import models
from django.contrib.auth.models import AbstractUser

from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # Add 'team_admin' to ROLE_CHOICES
    ROLE_CHOICES = [
        ('citizen', 'Citizen'),
        ('government_authority', 'Government Authority'),
        ('emergency_operator', 'Emergency Operator'),
        ('utility_officer', 'Utility Officer'),
        ('team_admin', 'Team Administrator'),  # ← NEW ROLE
        ('worker', 'Worker'),
    ]
    
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='citizen')
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"
    
    def get_dashboard_url(self):
        """Redirect to role-specific dashboard"""
        dashboard_urls = {
            'citizen': '/dashboard/citizen/',
            'government_authority': '/dashboard/gov/',
            'utility_officer': '/dashboard/utility/',
            'emergency_operator': '/dashboard/emergency/',
            'worker': '/dashboard/worker/',  # ← NEW
        }
        return dashboard_urls.get(self.role, '/dashboard/')
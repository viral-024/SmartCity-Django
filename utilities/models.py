from django.db import models
from django.utils import timezone
from accounts.models import User

class UtilityType(models.Model):
    """Types of utility issues (water, electricity, garbage, etc.)"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    department = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='wrench')
    
    def __str__(self):
        return self.name


class Complaint(models.Model):
    """Utility complaint submitted by citizens"""

    citizen = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='complaints'
    )
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('escalated', 'Escalated'),
        ('rejected', 'Rejected'),
    ]
    
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    # Basic Information
    citizen = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints')
    utility_type = models.ForeignKey(UtilityType, on_delete=models.PROTECT)
    complaint_id = models.CharField(max_length=20, unique=True, editable=False)
    
    # Complaint Details
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Location
    location_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    address = models.TextField()
    landmark = models.CharField(max_length=200, blank=True)
    
    # Assignment
    assigned_officer = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_complaints',
        limit_choices_to={'role': 'utility_officer'}
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    escalated_at = models.DateTimeField(null=True, blank=True)
    
    # Resolution
    resolution_notes = models.TextField(blank=True)
    satisfaction_rating = models.IntegerField(
        null=True, 
        blank=True, 
        choices=[(i, i) for i in range(1, 6)],
        help_text="Rate 1-5 after resolution"
    )
    
    def __str__(self):
        return f"Complaint {self.complaint_id} - {self.title}"
    
    def save(self, *args, **kwargs):
        # Generate complaint ID if not exists
        if not self.complaint_id:
            prefix = self.utility_type.name[:3].upper()
            count = Complaint.objects.count() + 1
            self.complaint_id = f"{prefix}-{count:06d}"
        
        # Update timestamps
        if self.status == 'assigned' and not self.assigned_at:
            self.assigned_at = timezone.now()
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
        if self.status == 'escalated' and not self.escalated_at:
            self.escalated_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def escalate_to_authority(self):
        """Escalate unresolved complaint to government authority"""
        from accounts.models import User
        authorities = User.objects.filter(role='government_authority')
        
        if authorities.exists():
            self.status = 'escalated'
            self.priority = 'high'
            self.save()
            return True
        return False


class ComplaintUpdate(models.Model):
    """Track updates/comments on complaints"""
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='updates')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    update_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Update for {self.complaint.complaint_id}"



class UtilityTeam(models.Model):
    """Utility repair team with multiple workers and vehicles"""
    TEAM_TYPE_CHOICES = [
        ('water', 'Water Supply Response'),
        ('electricity', 'Electricity Response'),
        ('road_maintenance', 'Road Maintenance'),
        ('garbage', 'Garbage Management'),
        ('public_works', 'Public Works'),
        ('special_operations', 'Special Operations'),
    ]
    
    name = models.CharField(max_length=100)
    team_type = models.CharField(max_length=50, choices=TEAM_TYPE_CHOICES, default='water')
    team_size = models.IntegerField(default=0)
    workers = models.ManyToManyField(
        'accounts.User', 
        limit_choices_to={'role': 'worker'}, 
        related_name='utility_teams'
    )
    vehicles = models.ManyToManyField(
        'emergency.EmergencyVehicle',  # Reuse emergency vehicles for utility teams
        related_name='utility_teams',
        blank=True
    )
    equipment = models.TextField(blank=True)
    team_leader = models.ForeignKey(
        'accounts.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='led_utility_teams',
        limit_choices_to={'role': 'worker'},
        blank=True
    )
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Utility Team {self.name} ({self.team_size} members)"
    
    class Meta:
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        """Save team without accessing M2M relationships during initial save"""
        # Only calculate team_size if the instance already exists in DB (has ID)
        if self.pk:
            self.team_size = self.workers.count()
        super().save(*args, **kwargs)

class UtilityTeamAssignment(models.Model):
    """Team assigned to a utility complaint"""
    complaint = models.ForeignKey('Complaint', on_delete=models.CASCADE, related_name='team_assignments')
    team = models.ForeignKey('UtilityTeam', on_delete=models.PROTECT)
    assigned_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='utility_assignments_made')
    assigned_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ], default='assigned')
    
    def __str__(self):
        return f"Team {self.team.name} → Complaint {self.complaint.complaint_id}"
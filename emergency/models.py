from django.db import models
from django.utils import timezone
from accounts.models import User

class EmergencyType(models.Model):
    """Types of emergencies (fire, medical, accident, etc.)"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='exclamation-triangle')
    
    def __str__(self):
        return self.name


class EmergencyRequest(models.Model):
    """Emergency request submitted by citizens"""
    citizen = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='emergency_requests'
    )
    
    PRIORITY_CHOICES = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('en_route', 'En Route'),
        ('on_scene', 'On Scene'),
        ('resolved', 'Resolved'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    citizen = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emergency_requests')
    emergency_type = models.ForeignKey(EmergencyType, on_delete=models.PROTECT)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Location Details
    location_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)  # Changed
    location_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)  # Changed
    address = models.TextField()
    landmark = models.CharField(max_length=200, blank=True)
    
    # Emergency Details
    description = models.TextField()
    contact_number = models.CharField(max_length=15)
    additional_info = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Emergency #{self.id} - {self.emergency_type.name} - {self.citizen.username}"
    
    def save(self, *args, **kwargs):
        # Auto-set contact number from citizen profile if not provided
        if not self.contact_number and self.citizen.phone_number:
            self.contact_number = self.citizen.phone_number
        
        # Update timestamps based on status
        if self.status == 'assigned' and not self.assigned_at:
            self.assigned_at = timezone.now()
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
        
        super().save(*args, **kwargs)


class EmergencyVehicle(models.Model):
    """Emergency vehicles (ambulance, fire truck, police car, etc.)"""
    
    VEHICLE_TYPE_CHOICES = [
        ('ambulance', 'Ambulance'),
        ('fire_truck', 'Fire Truck'),
        ('police_car', 'Police Car'),
        ('rescue_vehicle', 'Rescue Vehicle'),
    ]
    
    vehicle_type = models.CharField(max_length=50, choices=VEHICLE_TYPE_CHOICES)
    vehicle_number = models.CharField(max_length=20, unique=True)
    driver_name = models.CharField(max_length=100)
    driver_contact = models.CharField(max_length=15)
    is_available = models.BooleanField(default=True)
    current_location = models.CharField(max_length=200, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_vehicle_type_display()} - {self.vehicle_number}"
    
    class Meta:
        ordering = ['vehicle_type', 'vehicle_number']


class DispatchRecord(models.Model):
    """Records of emergency dispatches"""
    
    emergency_request = models.ForeignKey(EmergencyRequest, on_delete=models.CASCADE, related_name='dispatches')
    vehicle = models.ForeignKey(EmergencyVehicle, on_delete=models.PROTECT)
    assigned_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='dispatches_made')
    assigned_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('assigned', 'Assigned'),
        ('en_route', 'En Route'),
        ('on_scene', 'On Scene'),
        ('completed', 'Completed'),
    ], default='assigned')
    
    def __str__(self):
        return f"Dispatch #{self.id} for Emergency #{self.emergency_request.id}"
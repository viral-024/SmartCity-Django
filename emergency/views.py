from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone  # ← FIXED: Added missing import
from .models import EmergencyRequest, EmergencyType, EmergencyVehicle, DispatchRecord
from .forms import EmergencyRequestForm, EmergencyVehicleForm

@login_required
def citizen_emergency_request(request):
    """Citizen submits emergency request"""
    if request.user.role != 'citizen':
        messages.error(request, 'Access denied. Only citizens can report emergencies.')
        return redirect('dashboard:dashboard')
    
    # Create default emergency types if none exist
    if not EmergencyType.objects.exists():
        EmergencyType.objects.create(
            name='Medical Emergency',
            description='Medical emergencies including accidents, heart attacks, etc.',
            icon='heartbeat'
        )
        EmergencyType.objects.create(
            name='Fire',
            description='Fire incidents in buildings, vehicles, or forests',
            icon='fire'
        )
        EmergencyType.objects.create(
            name='Accident',
            description='Road accidents, falls, or other accidents',
            icon='car-crash'
        )
        EmergencyType.objects.create(
            name='Crime',
            description='Criminal activities requiring police assistance',
            icon='shield-alt'
        )
    
    if request.method == 'POST':
        form = EmergencyRequestForm(request.POST, user=request.user)
        if form.is_valid():
            emergency = form.save(commit=False)
            emergency.citizen = request.user
            emergency.save()
            
            messages.success(request, f'Emergency request submitted successfully! Request ID: #{emergency.id}')
            return redirect('emergency:my_requests')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EmergencyRequestForm(user=request.user)
    
    emergency_types = EmergencyType.objects.all()
    return render(request, 'emergency/citizen_request.html', {
        'form': form,
        'emergency_types': emergency_types,
    })


@login_required
def my_emergency_requests(request):
    """Citizen views their emergency requests"""
    if request.user.role != 'citizen':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    requests = EmergencyRequest.objects.filter(citizen=request.user).order_by('-created_at')
    
    return render(request, 'emergency/my_requests.html', {
        'requests': requests,
    })


@login_required
def emergency_detail(request, request_id):
    """View details of a specific emergency request"""
    emergency = EmergencyRequest.objects.get(id=request_id)
    
    # Check if user has permission to view this request
    if request.user.role != 'citizen' or emergency.citizen != request.user:
        if request.user.role not in ['emergency_operator', 'government_authority']:
            messages.error(request, 'Access denied.')
            return redirect('dashboard:dashboard')
    
    return render(request, 'emergency/emergency_detail.html', {
        'emergency': emergency,
    })


@login_required
def operator_dashboard(request):
    """Emergency operator dashboard - view pending emergencies"""
    if request.user.role != 'emergency_operator':
        messages.error(request, 'Access denied. Only emergency operators can access this page.')
        return redirect('dashboard:dashboard')
    
    # Get pending emergencies
    pending_emergencies = EmergencyRequest.objects.filter(status='pending').order_by('-created_at')
    
    # Get active dispatches
    active_dispatches = DispatchRecord.objects.filter(
        status__in=['assigned', 'en_route', 'on_scene']
    ).select_related('emergency_request', 'vehicle').order_by('-assigned_at')
    
    # Get statistics
    total_pending = pending_emergencies.count()
    total_active = active_dispatches.count()
    total_vehicles = EmergencyVehicle.objects.count()
    available_vehicles = EmergencyVehicle.objects.filter(is_available=True).count()
    
    # Calculate status counts
    active_emergencies = EmergencyRequest.objects.filter(status__in=['assigned', 'en_route', 'on_scene']).count()
    on_scene = DispatchRecord.objects.filter(status='on_scene').count()
    resolved_today = EmergencyRequest.objects.filter(
        status='resolved',
        resolved_at__date=timezone.now().date()  # ← Now works because timezone is imported
    ).count()
    
    context = {
        'pending_emergencies': pending_emergencies,
        'active_dispatches': active_dispatches,
        'total_pending': total_pending,
        'total_active': total_active,
        'total_vehicles': total_vehicles,
        'available_vehicles': available_vehicles,
        'active_emergencies': active_emergencies,
        'on_scene': on_scene,
        'resolved_today': resolved_today,
    }
    
    return render(request, 'emergency/operator_dashboard.html', context)


@login_required
def assign_vehicle(request, emergency_id):
    """Assign a vehicle to an emergency"""
    if request.user.role != 'emergency_operator':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    emergency = EmergencyRequest.objects.get(id=emergency_id)
    
    # Get available vehicles
    available_vehicles = EmergencyVehicle.objects.filter(is_available=True)
    
    if request.method == 'POST':
        vehicle_id = request.POST.get('vehicle_id')
        vehicle = EmergencyVehicle.objects.get(id=vehicle_id)
        
        # Create dispatch record
        dispatch = DispatchRecord.objects.create(
            emergency_request=emergency,
            vehicle=vehicle,
            assigned_by=request.user,
            status='assigned'
        )
        
        # Update emergency status
        emergency.status = 'assigned'
        emergency.save()
        
        # Mark vehicle as unavailable
        vehicle.is_available = False
        vehicle.save()
        
        messages.success(request, f'Vehicle {vehicle.vehicle_number} assigned successfully!')
        return redirect('emergency:operator_dashboard')
    
    return render(request, 'emergency/assign_vehicle.html', {
        'emergency': emergency,
        'available_vehicles': available_vehicles,
    })


@login_required
def update_dispatch_status(request, dispatch_id):
    """Update dispatch status (en route, on scene, completed)"""
    if request.user.role != 'emergency_operator':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    dispatch = DispatchRecord.objects.get(id=dispatch_id)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        
        # FIX: Convert 'completed' to 'resolved' for emergency request
        emergency_status = 'resolved' if status == 'completed' else status
        
        # Update dispatch record
        dispatch.status = status
        dispatch.save()
        
        # Update emergency request status with correct mapping
        dispatch.emergency_request.status = emergency_status
        dispatch.emergency_request.save()
        
        # If completed, mark vehicle as available
        if status == 'completed':
            dispatch.vehicle.is_available = True
            dispatch.vehicle.save()
        
        messages.success(request, 'Dispatch status updated successfully!')
        return redirect('emergency:operator_dashboard')
    
    return render(request, 'emergency/update_dispatch_status.html', {
        'dispatch': dispatch,
    })


@login_required
def manage_vehicles(request):
    """Manage emergency vehicles (add, edit, delete)"""
    if request.user.role != 'emergency_operator':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    vehicles = EmergencyVehicle.objects.all().order_by('vehicle_type', 'vehicle_number')
    
    if request.method == 'POST':
        form = EmergencyVehicleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vehicle added successfully!')
            return redirect('emergency:manage_vehicles')
    else:
        form = EmergencyVehicleForm()
    
    return render(request, 'emergency/manage_vehicles.html', {
        'vehicles': vehicles,
        'form': form,
    })


@login_required
def delete_vehicle(request, vehicle_id):
    """Delete an emergency vehicle"""
    if request.user.role != 'emergency_operator':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    vehicle = EmergencyVehicle.objects.get(id=vehicle_id)
    vehicle.delete()
    messages.success(request, 'Vehicle deleted successfully!')
    return redirect('emergency:manage_vehicles')


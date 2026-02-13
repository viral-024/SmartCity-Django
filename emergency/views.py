from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import EmergencyRequest, EmergencyType
from .forms import EmergencyRequestForm

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
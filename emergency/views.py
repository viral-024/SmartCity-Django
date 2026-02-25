from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import (
    EmergencyRequest, EmergencyType, EmergencyVehicle,
    EmergencyTeam, TeamAssignment  # ← REMOVED DispatchRecord (not used in team system)
)
from .forms import EmergencyRequestForm, EmergencyVehicleForm
from accounts.models import User

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
    """Emergency operator dashboard - view pending emergencies with TEAM assignments"""
    if request.user.role != 'emergency_operator':
        messages.error(request, 'Access denied. Only emergency operators can access this page.')
        return redirect('dashboard:dashboard')
    
    # Get pending emergencies (not assigned to any team)
    pending_emergencies = EmergencyRequest.objects.filter(status='pending').order_by('-created_at')
    
    # Get active team assignments (replaces individual dispatches)
    active_assignments = TeamAssignment.objects.filter(
        status__in=['assigned', 'en_route', 'on_scene']
    ).select_related('emergency_request', 'team').order_by('-assigned_at')
    
    # Get statistics
    total_pending = pending_emergencies.count()
    total_active = active_assignments.count()
    total_teams = EmergencyTeam.objects.count()
    available_teams = EmergencyTeam.objects.filter(is_available=True).count()
    
    # Calculate status counts
    active_emergencies = EmergencyRequest.objects.filter(status__in=['assigned', 'en_route', 'on_scene']).count()
    on_scene = TeamAssignment.objects.filter(status='on_scene').count()
    resolved_today = EmergencyRequest.objects.filter(
        status='resolved',
        resolved_at__date=timezone.now().date()
    ).count()
    
    context = {
        'pending_emergencies': pending_emergencies,
        'active_assignments': active_assignments,  # ← RENAMED from active_dispatches
        'total_pending': total_pending,
        'total_active': total_active,
        'total_teams': total_teams,  # ← CHANGED from total_vehicles
        'available_teams': available_teams,  # ← CHANGED from available_vehicles
        'active_emergencies': active_emergencies,
        'on_scene': on_scene,
        'resolved_today': resolved_today,
    }
    
    return render(request, 'emergency/operator_dashboard.html', context)


@login_required
def assign_team(request, emergency_id):
    """Assign a TEAM (not individual vehicle) to an emergency"""
    if request.user.role != 'emergency_operator':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    emergency = EmergencyRequest.objects.get(id=emergency_id)
    available_teams = EmergencyTeam.objects.filter(is_available=True)
    
    if request.method == 'POST':
        team_id = request.POST.get('team_id')
        team = EmergencyTeam.objects.get(id=team_id)
        
        # Create team assignment
        TeamAssignment.objects.create(
            emergency_request=emergency,
            team=team,
            assigned_by=request.user,
            status='assigned'
        )
        
        # Update emergency status
        emergency.status = 'assigned'
        emergency.save()
        
        # Mark team as unavailable
        team.is_available = False
        team.save()
        
        messages.success(request, f'Team {team.name} assigned successfully!')
        return redirect('emergency:operator_dashboard')
    
    return render(request, 'emergency/assign_team.html', {
        'emergency': emergency,
        'available_teams': available_teams,
    })


@login_required
def update_team_status(request, assignment_id):
    """Update team assignment status (replaces individual dispatch status)"""
    if request.user.role != 'emergency_operator':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    assignment = TeamAssignment.objects.get(id=assignment_id)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        
        # Update assignment status
        assignment.status = status
        assignment.save()
        
        # Update emergency request status
        emergency_status = 'resolved' if status == 'completed' else status
        assignment.emergency_request.status = emergency_status
        assignment.emergency_request.save()
        
        # If completed, mark team as available
        if status == 'completed':
            assignment.team.is_available = True
            assignment.team.save()
        
        messages.success(request, f'Team status updated to {status}!')
        return redirect('emergency:operator_dashboard')
    
    return render(request, 'emergency/update_team_status.html', {
        'assignment': assignment,
    })


@login_required
def manage_teams(request):
    """Manage emergency teams (view, create, edit)"""
    if request.user.role != 'emergency_operator':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    teams = EmergencyTeam.objects.all().order_by('name')
    
    # Get available workers (not in any team)
    all_workers = User.objects.filter(role='worker')
    workers_in_teams = User.objects.filter(teams__isnull=False).distinct()
    available_workers = all_workers.exclude(id__in=workers_in_teams)
    
    # Get available vehicles (not assigned to any team)
    all_vehicles = EmergencyVehicle.objects.all()
    vehicles_in_teams = EmergencyVehicle.objects.filter(teams__isnull=False).distinct()
    available_vehicles = all_vehicles.exclude(id__in=vehicles_in_teams)
    
    # Pass team type choices to template
    TEAM_TYPE_CHOICES = EmergencyTeam.TEAM_TYPE_CHOICES
    
    if request.method == 'POST':
        # Create new team WITHOUT workers/vehicles first
        team_name = request.POST.get('team_name')
        team_type = request.POST.get('team_type')
        
        # Create team first (without M2M relationships)
        team = EmergencyTeam.objects.create(
            name=team_name,
            team_type=team_type,
            team_size=0
        )
        
        # Add workers AFTER team is saved
        worker_ids = request.POST.getlist('workers')
        for worker_id in worker_ids:
            worker = User.objects.get(id=worker_id)
            team.workers.add(worker)
        
        # Set team leader AFTER workers are added
        team_leader_id = request.POST.get('team_leader')
        if team_leader_id and team_leader_id in worker_ids:
            team.team_leader = User.objects.get(id=team_leader_id)
            team.save()  # Save leader
        
        # Add vehicles AFTER team is saved
        vehicle_ids = request.POST.getlist('vehicles')
        for vehicle_id in vehicle_ids:
            vehicle = EmergencyVehicle.objects.get(id=vehicle_id)
            team.vehicles.add(vehicle)
        
        # Add equipment (optional)
        equipment = request.POST.get('equipment')
        if equipment:
            team.equipment = equipment
            team.save()
        
        # Calculate and save team size
        team.team_size = team.workers.count()
        team.save()
        
        messages.success(request, f'Team "{team.name}" created successfully with {team.team_size} members!')
        return redirect('emergency:manage_teams')
    
    return render(request, 'emergency/manage_teams.html', {
        'teams': teams,
        'vehicles': available_vehicles,  # Only show available vehicles
        'available_workers': available_workers,
        'TEAM_TYPE_CHOICES': TEAM_TYPE_CHOICES,
    })


@login_required
def add_worker_to_team(request, team_id):
    """Add workers to an existing team"""
    if request.user.role != 'emergency_operator':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    team = EmergencyTeam.objects.get(id=team_id)
    
    # Get available workers (not in any team)
    all_workers = User.objects.filter(role='worker')
    workers_in_teams = User.objects.filter(teams__isnull=False).distinct()
    available_workers = all_workers.exclude(id__in=workers_in_teams)
    
    if request.method == 'POST':
        # Add workers
        worker_ids = request.POST.getlist('worker_ids')
        for worker_id in worker_ids:
            worker = User.objects.get(id=worker_id)
            team.workers.add(worker)
        
        # Update team leader if selected
        team_leader_id = request.POST.get('team_leader')
        if team_leader_id and team_leader_id in worker_ids:
            team.team_leader = User.objects.get(id=team_leader_id)
        
        # Calculate and save team size
        team.team_size = team.workers.count()
        team.save()
        
        messages.success(request, f'Workers added to {team.name} successfully!')
        return redirect('emergency:manage_teams')
    
    return render(request, 'emergency/add_worker_to_team.html', {
        'team': team,
        'available_workers': available_workers,
    })
    

@login_required
def manage_vehicles(request):
    """Manage emergency vehicles (add, edit, delete) - kept for vehicle management"""
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
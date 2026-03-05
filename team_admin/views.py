from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import User
from emergency.models import EmergencyTeam, EmergencyVehicle
from utilities.models import UtilityTeam

@login_required
def create_worker(request):
    """Team admin creates worker accounts WITH DASHBOARD STATISTICS"""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied. Only Team Administrators can create workers.')
        return redirect('dashboard:dashboard')
    
    # ✅ CALCULATE ACTUAL STATISTICS FOR DASHBOARD
    total_workers = User.objects.filter(role='worker').count()
    emergency_teams = EmergencyTeam.objects.count()
    utility_teams = UtilityTeam.objects.count()
    total_vehicles = EmergencyVehicle.objects.count()
    
    if request.method == 'POST':
        username = request.POST.get('username').strip()
        password = request.POST.get('password')
        phone = request.POST.get('phone_number').strip()
        email = request.POST.get('email').strip()
        
        # ... existing validation code ...
        
        # Create worker account
        worker = User.objects.create_user(
            username=username,
            password=password,
            role='worker',
            phone_number=phone,
            email=email
        )
        
        messages.success(request, f'Worker "{username}" created successfully!')
        return redirect('team_admin:manage_workers')
    
    # ✅ PASS STATISTICS TO TEMPLATE
    context = {
        'total_workers': total_workers,
        'emergency_teams': emergency_teams,
        'utility_teams': utility_teams,
        'total_vehicles': total_vehicles,
    }
    return render(request, 'team_admin/create_worker.html', context)

# @login_required
# def manage_workers(request):
#     """View all workers"""
#     if request.user.role != 'team_admin':
#         messages.error(request, 'Access denied.')
#         return redirect('dashboard:dashboard')
    
#     workers = User.objects.filter(role='worker').order_by('username')
#     return render(request, 'team_admin/manage_workers.html', {'workers': workers})

@login_required
def manage_workers(request):
    """View all workers WITH dashboard statistics"""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    # Get workers list
    workers = User.objects.filter(role='worker').order_by('username')
    
    # ✅ CALCULATE ACTUAL STATISTICS FOR DASHBOARD
    total_workers = workers.count()
    emergency_teams = EmergencyTeam.objects.count()
    utility_teams = UtilityTeam.objects.count()
    total_vehicles = EmergencyVehicle.objects.count()
    
    # ✅ PASS STATISTICS TO TEMPLATE
    context = {
        'workers': workers,
        'total_workers': total_workers,      # Actual count
        'emergency_teams': emergency_teams,  # Actual count
        'utility_teams': utility_teams,      # Actual count
        'total_vehicles': total_vehicles,    # Actual count
    }
    return render(request, 'team_admin/manage_workers.html', context)

@login_required
def create_emergency_team(request):
    """Create emergency response team"""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    # Get available resources
    available_workers = User.objects.filter(role='worker', teams__isnull=True)
    available_vehicles = EmergencyVehicle.objects.filter(teams__isnull=True)
    
    if request.method == 'POST':
        team_name = request.POST.get('team_name').strip()
        team_type = request.POST.get('team_type')
        worker_ids = request.POST.getlist('workers')
        vehicle_ids = request.POST.getlist('vehicles')
        team_leader_id = request.POST.get('team_leader')
        
        if not team_name or not worker_ids:
            messages.error(request, 'Team name and at least one worker are required.')
            return redirect('team_admin:create_emergency_team')
        
        # Create team
        team = EmergencyTeam.objects.create(
            name=team_name,
            team_type=team_type,
            team_size=len(worker_ids)
        )
        
        # Add workers
        for worker_id in worker_ids:
            worker = User.objects.get(id=worker_id)
            team.workers.add(worker)
        
        # Set team leader
        if team_leader_id and team_leader_id in worker_ids:
            team.team_leader = User.objects.get(id=team_leader_id)
        
        # Add vehicles
        for vehicle_id in vehicle_ids:
            vehicle = EmergencyVehicle.objects.get(id=vehicle_id)
            team.vehicles.add(vehicle)
        
        team.save()
        messages.success(request, f'Emergency Team "{team_name}" created successfully!')
        return redirect('team_admin:manage_emergency_teams')
    
    return render(request, 'team_admin/create_emergency_team.html', {
        'available_workers': available_workers,
        'available_vehicles': available_vehicles,
        'TEAM_TYPE_CHOICES': EmergencyTeam.TEAM_TYPE_CHOICES,
    })

@login_required
def manage_emergency_teams(request):
    """View all emergency teams"""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    teams = EmergencyTeam.objects.all().order_by('name')

    # Add before return statement:
    context = {
        'teams': teams,
        'total_workers': User.objects.filter(role='worker').count(),
        'emergency_teams': EmergencyTeam.objects.count(),
        'utility_teams': UtilityTeam.objects.count(),
        'total_vehicles': EmergencyVehicle.objects.count(),
    }
    return render(request, 'team_admin/manage_emergency_teams.html', context)
    
    # return render(request, 'team_admin/manage_emergency_teams.html', {'teams': teams})

@login_required
def add_worker_to_emergency_team(request, team_id):
    """Add worker to existing emergency team"""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    team = get_object_or_404(EmergencyTeam, id=team_id)
    
    # FIXED: Get workers NOT in ANY team (emergency OR utility)
    available_workers = User.objects.filter(
        role='worker',
        teams__isnull=True,          # Not in emergency teams
        utility_teams__isnull=True   # Not in utility teams
    )
    
    if request.method == 'POST':
        worker_ids = request.POST.getlist('worker_ids')
        
        if not worker_ids:
            messages.error(request, 'Please select at least one worker to add.')
            return redirect('team_admin:add_worker_to_emergency_team', team_id=team_id)
        
        # Add workers to team
        added_count = 0
        for worker_id in worker_ids:
            try:
                worker = User.objects.get(id=worker_id, role='worker')
                team.workers.add(worker)
                added_count += 1
            except User.DoesNotExist:
                continue
        
        # Update team leader if selected
        team_leader_id = request.POST.get('team_leader')
        if team_leader_id and team_leader_id in worker_ids:
            try:
                team.team_leader = User.objects.get(id=team_leader_id, role='worker')
            except User.DoesNotExist:
                pass
        
        team.save()
        
        messages.success(request, f'{added_count} worker(s) added to {team.name} successfully!')
        return redirect('team_admin:manage_emergency_teams')
    
    return render(request, 'team_admin/add_worker_to_team.html', {
        'team': team,
        'available_workers': available_workers,
        'team_type': 'emergency'
    })

@login_required
def create_utility_team(request):
    """Create utility response team"""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    # Get available resources
    available_workers = User.objects.filter(
        role='worker',
        teams__isnull=True,
        utility_teams__isnull=True
    )
    available_vehicles = EmergencyVehicle.objects.filter(
        teams__isnull=True,
        utility_teams__isnull=True
    )
    
    if request.method == 'POST':
        team_name = request.POST.get('team_name').strip()
        team_type = request.POST.get('team_type')
        worker_ids = request.POST.getlist('workers')
        vehicle_ids = request.POST.getlist('vehicles')
        team_leader_id = request.POST.get('team_leader')
        equipment = request.POST.get('equipment', '')
        
        if not team_name or not worker_ids:
            messages.error(request, 'Team name and at least one worker are required.')
            return redirect('team_admin:create_utility_team')
        
        # Create team
        team = UtilityTeam.objects.create(
            name=team_name,
            team_type=team_type,
            team_size=len(worker_ids),
            equipment=equipment
        )
        
        # Add workers
        for worker_id in worker_ids:
            worker = User.objects.get(id=worker_id)
            team.workers.add(worker)
        
        # Set team leader
        if team_leader_id and team_leader_id in worker_ids:
            team.team_leader = User.objects.get(id=team_leader_id)
        
        # Add vehicles
        for vehicle_id in vehicle_ids:
            vehicle = EmergencyVehicle.objects.get(id=vehicle_id)
            team.vehicles.add(vehicle)
        
        team.save()
        messages.success(request, f'Utility Team "{team_name}" created successfully!')
        return redirect('team_admin:manage_utility_teams')
    
    return render(request, 'team_admin/create_utility_team.html', {
        'available_workers': available_workers,
        'available_vehicles': available_vehicles,
        'TEAM_TYPE_CHOICES': UtilityTeam.TEAM_TYPE_CHOICES,
    })
    
@login_required
def manage_utility_teams(request):
    """View all utility teams"""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    teams = UtilityTeam.objects.all().order_by('name')

    context = {
        'teams': teams,
        'total_workers': User.objects.filter(role='worker').count(),
        'emergency_teams': EmergencyTeam.objects.count(),
        'utility_teams': UtilityTeam.objects.count(),
        'total_vehicles': EmergencyVehicle.objects.count(),
    }
    return render(request, 'team_admin/manage_utility_teams.html', context)
    # return render(request, 'team_admin/manage_utility_teams.html', {'teams': teams})

@login_required
def add_worker_to_utility_team(request, team_id):
    """Add worker to existing utility team"""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    team = get_object_or_404(UtilityTeam, id=team_id)
    
    # FIXED: Get workers NOT in ANY team (emergency OR utility)
    available_workers = User.objects.filter(
        role='worker',
        teams__isnull=True,          # Not in emergency teams
        utility_teams__isnull=True   # Not in utility teams
    )
    
    if request.method == 'POST':
        worker_ids = request.POST.getlist('worker_ids')
        
        if not worker_ids:
            messages.error(request, 'Please select at least one worker to add.')
            return redirect('team_admin:add_worker_to_utility_team', team_id=team_id)
        
        # Add workers to team
        added_count = 0
        for worker_id in worker_ids:
            try:
                worker = User.objects.get(id=worker_id, role='worker')
                team.workers.add(worker)
                added_count += 1
            except User.DoesNotExist:
                continue
        
        # Update team leader if selected
        team_leader_id = request.POST.get('team_leader')
        if team_leader_id and team_leader_id in worker_ids:
            try:
                team.team_leader = User.objects.get(id=team_leader_id, role='worker')
            except User.DoesNotExist:
                pass
        
        team.save()
        
        messages.success(request, f'{added_count} worker(s) added to {team.name} successfully!')
        return redirect('team_admin:manage_utility_teams')
    
    return render(request, 'team_admin/add_worker_to_team.html', {
        'team': team,
        'available_workers': available_workers,
        'team_type': 'utility'
    })

@login_required
def create_vehicle(request):
    """Create emergency vehicle"""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        vehicle_number = request.POST.get('vehicle_number').strip()
        vehicle_type = request.POST.get('vehicle_type')
        driver_name = request.POST.get('driver_name').strip()
        driver_contact = request.POST.get('driver_contact').strip()
        current_location = request.POST.get('current_location', '')
        
        if not vehicle_number or not vehicle_type or not driver_name or not driver_contact:
            messages.error(request, 'All vehicle fields are required.')
            return redirect('team_admin:create_vehicle')
        
        if EmergencyVehicle.objects.filter(vehicle_number=vehicle_number).exists():
            messages.error(request, f'Vehicle "{vehicle_number}" already exists.')
            return redirect('team_admin:create_vehicle')
        
        EmergencyVehicle.objects.create(
            vehicle_number=vehicle_number,
            vehicle_type=vehicle_type,
            driver_name=driver_name,
            driver_contact=driver_contact,
            current_location=current_location,
            is_available=True
        )
        messages.success(request, f'Vehicle "{vehicle_number}" created successfully!')
        return redirect('team_admin:manage_vehicles')
    
    return render(request, 'team_admin/create_vehicle.html')

@login_required
def manage_vehicles(request):
    """View all vehicles"""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    vehicles = EmergencyVehicle.objects.all().order_by('vehicle_number')

    # Add before return statement:
    context = {
        'vehicles': vehicles,
        'total_workers': User.objects.filter(role='worker').count(),
        'emergency_teams': EmergencyTeam.objects.count(),
        'utility_teams': UtilityTeam.objects.count(),
        'total_vehicles': EmergencyVehicle.objects.count(),
    }
    return render(request, 'team_admin/manage_vehicles.html', context)
    # return render(request, 'team_admin/manage_vehicles.html', {'vehicles': vehicles})

@login_required
def delete_vehicle(request, vehicle_id):
    """Delete vehicle"""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    vehicle = get_object_or_404(EmergencyVehicle, id=vehicle_id)
    vehicle_number = vehicle.vehicle_number
    vehicle.delete()
    messages.success(request, f'Vehicle "{vehicle_number}" deleted successfully!')
    return redirect('team_admin:manage_vehicles')
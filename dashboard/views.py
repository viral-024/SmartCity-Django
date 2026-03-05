from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from accounts.models import User
from emergency.models import EmergencyTeam, TeamAssignment
from utilities.models import UtilityTeam, UtilityTeamAssignment

@login_required
def dashboard_redirect(request):
    """Redirect to role-specific dashboard"""
    role = request.user.role
    
    if role == 'citizen':
        return redirect('dashboard:citizen')
    elif role == 'government_authority':
        return redirect('gov_authority:dashboard')
    elif role == 'utility_officer':
        return redirect('utilities:officer_dashboard')
    elif role == 'emergency_operator':
        return redirect('emergency:operator_dashboard')
    elif role == 'team_admin':
        return redirect('team_admin:manage_workers')
    elif role == 'worker':
        return redirect('dashboard:worker')
    else:
        return redirect('accounts:profile')


@login_required
def citizen_dashboard(request):
    """Citizen dashboard - show their requests"""
    if request.user.role != 'citizen':
        return redirect('dashboard:dashboard')
    
    # Get actual statistics from database
    pending_emergencies = request.user.emergency_requests.filter(status='pending').count()
    pending_complaints = request.user.complaints.filter(status='pending').count()
    resolved_requests = (
        request.user.emergency_requests.filter(status='resolved').count() + 
        request.user.complaints.filter(status='resolved').count()
    )
    total_requests = (
        request.user.emergency_requests.count() + 
        request.user.complaints.count()
    )
    
    context = {
        'title': 'Citizen Dashboard',
        'user': request.user,
        'pending_emergencies': pending_emergencies,
        'pending_complaints': pending_complaints,
        'resolved_requests': resolved_requests,
        'total_requests': total_requests,
    }
    return render(request, 'dashboard/citizen.html', context)


@login_required
def gov_dashboard(request):
    """Government authority dashboard - show city stats"""
    if request.user.role != 'government_authority':
        return redirect('dashboard:dashboard')
    
    # Get system statistics
    total_users = User.objects.count()
    citizens = User.objects.filter(role='citizen').count()
    staff = total_users - citizens
    
    # Team statistics
    total_emergency_teams = EmergencyTeam.objects.count()
    available_emergency_teams = EmergencyTeam.objects.filter(is_available=True).count()
    total_utility_teams = UtilityTeam.objects.count()
    available_utility_teams = UtilityTeam.objects.filter(is_available=True).count()
    
    # Assignment statistics
    active_emergency_assignments = TeamAssignment.objects.filter(
        status__in=['assigned', 'en_route', 'on_scene']
    ).count()
    active_utility_assignments = UtilityTeamAssignment.objects.filter(
        status__in=['assigned', 'in_progress']
    ).count()
    
    context = {
        'title': 'Government Dashboard',
        'user': request.user,
        'total_users': total_users,
        'citizens': citizens,
        'staff': staff,
        'total_emergency_teams': total_emergency_teams,
        'available_emergency_teams': available_emergency_teams,
        'total_utility_teams': total_utility_teams,
        'available_utility_teams': available_utility_teams,
        'active_emergency_assignments': active_emergency_assignments,
        'active_utility_assignments': active_utility_assignments,
    }
    return render(request, 'dashboard/gov.html', context)


@login_required
def worker_dashboard(request):
    """Worker dashboard - show team assignments and tasks"""
    if request.user.role != 'worker':
        return redirect('dashboard:dashboard')
    
    # Get teams this worker belongs to
    emergency_teams = EmergencyTeam.objects.filter(workers=request.user)
    utility_teams = UtilityTeam.objects.filter(workers=request.user)

    teams = list(emergency_teams) + list(utility_teams)
    
    # Get active emergency assignments
    active_emergency_assignments = TeamAssignment.objects.filter(
        team__in=EmergencyTeam.objects.filter(workers=request.user),
        status__in=['assigned', 'en_route', 'on_scene']
    ).select_related('emergency_request', 'team').order_by('-assigned_at')
    
    # Get active utility assignments
    active_utility_assignments = UtilityTeamAssignment.objects.filter(
        team__in=UtilityTeam.objects.filter(workers=request.user),
        status__in=['assigned', 'in_progress']
    ).select_related('complaint', 'team').order_by('-assigned_at')
    
    context = {
        'title': 'Worker Dashboard',
        'user': request.user,
        'teams': teams,
        'active_emergency_assignments': active_emergency_assignments,
        'active_utility_assignments': active_utility_assignments,
        'total_assignments': active_emergency_assignments.count() + active_utility_assignments.count(),
    }
    return render(request, 'dashboard/worker.html', context)
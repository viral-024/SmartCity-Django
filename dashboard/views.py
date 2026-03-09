from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.models import User
from emergency.models import EmergencyTeam, TeamAssignment
from utilities.models import UtilityTeam, UtilityTeamAssignment


@login_required
def dashboard_redirect(request):
    """Redirect to role-specific dashboard"""
    role = request.user.role

    if role == 'citizen':
        return redirect('dashboard:citizen')
    if role == 'government_authority':
        return redirect('gov_authority:dashboard')
    if role == 'utility_officer':
        return redirect('utilities:officer_dashboard')
    if role == 'emergency_operator':
        return redirect('emergency:operator_dashboard')
    if role == 'team_admin':
        return redirect('team_admin:manage_workers')
    if role == 'worker':
        return redirect('dashboard:worker')
    return redirect('accounts:profile')


@login_required
def citizen_dashboard(request):
    """Citizen dashboard with quick stats and recent activity"""
    if request.user.role != 'citizen':
        return redirect('dashboard:dashboard')

    emergency_open_statuses = ['pending', 'assigned', 'en_route', 'on_scene']
    complaint_open_statuses = ['pending', 'assigned', 'in_progress', 'escalated']

    open_emergencies = request.user.emergency_requests.filter(status__in=emergency_open_statuses).count()
    open_complaints = request.user.complaints.filter(status__in=complaint_open_statuses).count()

    resolved_requests = (
        request.user.emergency_requests.filter(status='resolved').count()
        + request.user.complaints.filter(status='resolved').count()
    )
    total_requests = request.user.emergency_requests.count() + request.user.complaints.count()

    attention_required = (
        request.user.emergency_requests.filter(
            status__in=emergency_open_statuses,
            priority__in=['critical', 'high'],
        ).count()
        + request.user.complaints.filter(
            status__in=complaint_open_statuses,
            priority='high',
        ).count()
    )

    recent_emergencies = request.user.emergency_requests.select_related('emergency_type').order_by('-created_at')[:5]
    recent_complaints = request.user.complaints.select_related('utility_type').order_by('-created_at')[:5]

    context = {
        'title': 'Citizen Dashboard',
        'user': request.user,
        'open_emergencies': open_emergencies,
        'open_complaints': open_complaints,
        'resolved_requests': resolved_requests,
        'total_requests': total_requests,
        'attention_required': attention_required,
        'recent_emergencies': recent_emergencies,
        'recent_complaints': recent_complaints,
    }
    return render(request, 'dashboard/citizen.html', context)


@login_required
def gov_dashboard(request):
    """Government authority dashboard - show city stats"""
    if request.user.role != 'government_authority':
        return redirect('dashboard:dashboard')

    total_users = User.objects.count()
    citizens = User.objects.filter(role='citizen').count()
    staff = total_users - citizens

    total_emergency_teams = EmergencyTeam.objects.count()
    available_emergency_teams = EmergencyTeam.objects.filter(is_available=True).count()
    total_utility_teams = UtilityTeam.objects.count()
    available_utility_teams = UtilityTeam.objects.filter(is_available=True).count()

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

    emergency_teams = EmergencyTeam.objects.filter(workers=request.user)
    utility_teams = UtilityTeam.objects.filter(workers=request.user)
    teams = sorted(list(emergency_teams) + list(utility_teams), key=lambda team: team.name.lower())

    active_emergency_assignments = TeamAssignment.objects.filter(
        team__in=EmergencyTeam.objects.filter(workers=request.user),
        status__in=['assigned', 'en_route', 'on_scene'],
    ).select_related('emergency_request', 'team', 'emergency_request__emergency_type').order_by('-assigned_at')

    active_utility_assignments = UtilityTeamAssignment.objects.filter(
        team__in=UtilityTeam.objects.filter(workers=request.user),
        status__in=['assigned', 'in_progress'],
    ).select_related('complaint', 'team', 'complaint__utility_type').order_by('-assigned_at')

    emergency_task_count = active_emergency_assignments.count()
    utility_task_count = active_utility_assignments.count()

    context = {
        'title': 'Worker Dashboard',
        'user': request.user,
        'teams': teams,
        'active_emergency_assignments': active_emergency_assignments,
        'active_utility_assignments': active_utility_assignments,
        'team_count': len(teams),
        'emergency_task_count': emergency_task_count,
        'utility_task_count': utility_task_count,
        'total_assignments': emergency_task_count + utility_task_count,
    }
    return render(request, 'dashboard/worker.html', context)

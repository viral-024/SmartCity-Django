from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Avg, Q
from accounts.models import User
from emergency.models import EmergencyTeam, EmergencyRequest, EmergencyVehicle
from utilities.models import UtilityTeam, Complaint


@login_required
def dashboard(request):
    """Government authority dashboard with city-wide operational analytics"""
    if request.user.role != 'government_authority':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    today = timezone.now().date()
    thirty_days_ago = timezone.now() - timedelta(days=30)

    total_users = User.objects.count()
    total_citizens = User.objects.filter(role='citizen').count()
    total_workers = User.objects.filter(role='worker').count()

    active_emergencies = EmergencyRequest.objects.filter(
        status__in=['pending', 'assigned', 'en_route', 'on_scene']
    ).count()
    active_complaints = Complaint.objects.filter(
        status__in=['pending', 'assigned', 'in_progress', 'escalated']
    ).count()

    total_emergency_teams = EmergencyTeam.objects.count()
    total_utility_teams = UtilityTeam.objects.count()
    total_vehicles = EmergencyVehicle.objects.count()

    available_emergency_teams = EmergencyTeam.objects.filter(is_available=True).count()
    available_utility_teams = UtilityTeam.objects.filter(is_available=True).count()
    vehicles_deployed = EmergencyVehicle.objects.filter(is_available=False).count()

    emergency_team_availability_pct = (
        round((available_emergency_teams / total_emergency_teams) * 100, 1)
        if total_emergency_teams
        else 0
    )
    utility_team_availability_pct = (
        round((available_utility_teams / total_utility_teams) * 100, 1)
        if total_utility_teams
        else 0
    )
    vehicles_available = max(total_vehicles - vehicles_deployed, 0)
    vehicle_availability_pct = (
        round((vehicles_available / total_vehicles) * 100, 1) if total_vehicles else 0
    )

    emergencies_resolved_today = EmergencyRequest.objects.filter(
        status='resolved',
        resolved_at__date=today,
    ).count()
    complaints_resolved_today = Complaint.objects.filter(
        status='resolved',
        resolved_at__date=today,
    ).count()

    emergency_categories_raw = (
        EmergencyRequest.objects.filter(created_at__gte=thirty_days_ago)
        .values('emergency_type__name')
        .annotate(count=Count('id'))
        .order_by('-count')[:6]
    )
    emergency_categories = [
        {
            'name': category['emergency_type__name'] or 'Other',
            'count': category['count'],
        }
        for category in emergency_categories_raw
    ]

    complaint_categories_raw = (
        Complaint.objects.filter(created_at__gte=thirty_days_ago)
        .values('utility_type__name')
        .annotate(count=Count('id'))
        .order_by('-count')[:6]
    )
    complaint_categories = [
        {
            'name': category['utility_type__name'] or 'Other',
            'count': category['count'],
        }
        for category in complaint_categories_raw
    ]

    emergency_team_workload_raw = (
        EmergencyTeam.objects.annotate(
            active_assignments=Count(
                'teamassignment',
                filter=Q(teamassignment__status__in=['assigned', 'en_route', 'on_scene']),
            )
        )
        .values('name', 'active_assignments')
        .order_by('-active_assignments', 'name')[:5]
    )
    emergency_team_workload = [
        {'name': team['name'], 'assignments': team['active_assignments']}
        for team in emergency_team_workload_raw
    ]

    utility_team_workload_raw = (
        UtilityTeam.objects.annotate(
            active_assignments=Count(
                'utilityteamassignment',
                filter=Q(utilityteamassignment__status__in=['assigned', 'in_progress']),
            )
        )
        .values('name', 'active_assignments')
        .order_by('-active_assignments', 'name')[:5]
    )
    utility_team_workload = [
        {'name': team['name'], 'assignments': team['active_assignments']}
        for team in utility_team_workload_raw
    ]

    resolved_emergencies = EmergencyRequest.objects.filter(
        status='resolved',
        resolved_at__gte=thirty_days_ago,
        assigned_at__isnull=False,
    )
    resolved_complaints = Complaint.objects.filter(
        status='resolved',
        resolved_at__gte=thirty_days_ago,
        assigned_at__isnull=False,
    )

    emergency_durations = []
    complaint_durations = []
    sla_emergencies = 0
    sla_complaints = 0

    for req in resolved_emergencies:
        if req.assigned_at and req.resolved_at:
            duration = req.resolved_at - req.assigned_at
            emergency_durations.append(duration.total_seconds())
            if duration <= timedelta(minutes=30):
                sla_emergencies += 1

    for comp in resolved_complaints:
        if comp.assigned_at and comp.resolved_at:
            duration = comp.resolved_at - comp.assigned_at
            complaint_durations.append(duration.total_seconds())
            if duration <= timedelta(hours=24):
                sla_complaints += 1

    total_sla_applicable = len(emergency_durations) + len(complaint_durations)
    sla_compliance = (
        round(((sla_emergencies + sla_complaints) / total_sla_applicable) * 100, 1)
        if total_sla_applicable
        else 0
    )

    avg_response_time = (
        round((sum(emergency_durations) / len(emergency_durations)) / 60, 1)
        if emergency_durations
        else 0
    )
    avg_resolution_time = (
        round((sum(complaint_durations) / len(complaint_durations)) / 3600, 1)
        if complaint_durations
        else 0
    )

    alerts_count = (
        EmergencyRequest.objects.filter(
            status__in=['pending', 'assigned', 'en_route', 'on_scene'],
            priority__in=['critical', 'high'],
        ).count()
        + Complaint.objects.filter(status='escalated').count()
    )

    rated_feedback = Complaint.objects.filter(satisfaction_rating__isnull=False)
    avg_citizen_rating = rated_feedback.aggregate(avg=Avg('satisfaction_rating'))['avg'] or 0

    context = {
        'total_users': total_users,
        'total_citizens': total_citizens,
        'total_workers': total_workers,
        'active_emergencies': active_emergencies,
        'active_complaints': active_complaints,
        'total_emergency_teams': total_emergency_teams,
        'total_utility_teams': total_utility_teams,
        'total_vehicles': total_vehicles,
        'available_emergency_teams': available_emergency_teams,
        'available_utility_teams': available_utility_teams,
        'vehicles_deployed': vehicles_deployed,
        'vehicles_available': vehicles_available,
        'emergency_team_availability_pct': emergency_team_availability_pct,
        'utility_team_availability_pct': utility_team_availability_pct,
        'vehicle_availability_pct': vehicle_availability_pct,
        'emergencies_resolved_today': emergencies_resolved_today,
        'complaints_resolved_today': complaints_resolved_today,
        'sla_compliance': sla_compliance,
        'avg_response_time': avg_response_time,
        'avg_resolution_time': avg_resolution_time,
        'alerts_count': alerts_count,
        'emergency_categories': emergency_categories,
        'complaint_categories': complaint_categories,
        'emergency_team_workload': emergency_team_workload,
        'utility_team_workload': utility_team_workload,
        'avg_citizen_rating': round(avg_citizen_rating, 2),
        'citizen_feedback_count': rated_feedback.count(),
    }

    return render(request, 'gov_authority/dashboard.html', context)


@login_required
def staff_list(request):
    """List and manage staff accounts with basic filtering."""
    if request.user.role != 'government_authority':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    staff_roles = ['emergency_operator', 'utility_officer', 'team_admin', 'worker', 'government_authority']

    staff_accounts = User.objects.filter(role__in=staff_roles)

    search_query = request.GET.get('q', '').strip()
    selected_role = request.GET.get('role', '').strip()
    selected_status = request.GET.get('status', '').strip()

    if selected_role in staff_roles:
        staff_accounts = staff_accounts.filter(role=selected_role)
    else:
        selected_role = ''

    if selected_status == 'active':
        staff_accounts = staff_accounts.filter(is_active=True)
    elif selected_status == 'inactive':
        staff_accounts = staff_accounts.filter(is_active=False)
    else:
        selected_status = ''

    if search_query:
        staff_accounts = staff_accounts.filter(
            Q(username__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(phone_number__icontains=search_query)
        )

    staff_accounts = staff_accounts.order_by('-date_joined')

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')

        try:
            user = User.objects.get(id=user_id)
            if action == 'deactivate':
                if user.id == request.user.id:
                    messages.error(request, 'You cannot deactivate your own account.')
                else:
                    user.is_active = False
                    user.save()
                    messages.success(request, f'{user.username} has been deactivated.')
            elif action == 'reactivate':
                user.is_active = True
                user.save()
                messages.success(request, f'{user.username} has been reactivated.')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')

        return redirect('gov_authority:staff_list')

    return render(
        request,
        'gov_authority/staff_list.html',
        {
            'staff_accounts': staff_accounts,
            'search_query': search_query,
            'selected_role': selected_role,
            'selected_status': selected_status,
            'role_options': User.ROLE_CHOICES,
        },
    )


@login_required
def escalations(request):
    """View escalated complaints (read-only)."""
    if request.user.role != 'government_authority':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    escalated_complaints = Complaint.objects.filter(
        status='escalated'
    ).select_related('citizen', 'utility_type').order_by('-escalated_at')

    return render(
        request,
        'gov_authority/escalations.html',
        {
            'escalated_complaints': escalated_complaints,
        },
    )

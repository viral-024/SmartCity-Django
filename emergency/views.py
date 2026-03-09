from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import (
    EmergencyRequest,
    EmergencyType,
    EmergencyVehicle,
    EmergencyTeam,
    TeamAssignment,
)
from .forms import EmergencyRequestForm, EmergencyVehicleForm
from accounts.models import User


def ensure_default_emergency_types():
    """Create baseline emergency categories if they do not exist."""
    default_types = [
        {
            'name': 'Medical Emergency',
            'description': 'Medical emergencies including accidents, heart attacks, etc.',
            'icon': 'heartbeat',
        },
        {
            'name': 'Fire',
            'description': 'Fire incidents in buildings, vehicles, or forests',
            'icon': 'fire',
        },
        {
            'name': 'Accident',
            'description': 'Road accidents, falls, or other accidents',
            'icon': 'car-crash',
        },
        {
            'name': 'Crime',
            'description': 'Criminal activities requiring police assistance',
            'icon': 'shield-alt',
        },
    ]

    for emergency_type in default_types:
        EmergencyType.objects.get_or_create(
            name=emergency_type['name'],
            defaults=emergency_type,
        )


@login_required
def citizen_emergency_request(request):
    """Citizen submits emergency request"""
    if request.user.role != 'citizen':
        messages.error(request, 'Access denied. Only citizens can report emergencies.')
        return redirect('dashboard:dashboard')

    ensure_default_emergency_types()

    if request.method == 'POST':
        form = EmergencyRequestForm(request.POST, user=request.user)
        if form.is_valid():
            emergency = form.save(commit=False)
            emergency.citizen = request.user
            emergency.save()

            messages.success(request, f'Emergency request submitted successfully. Request ID: #{emergency.id}')
            return redirect('emergency:my_requests')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = EmergencyRequestForm(user=request.user)

    emergency_types = EmergencyType.objects.all()
    return render(
        request,
        'emergency/citizen_request.html',
        {
            'form': form,
            'emergency_types': emergency_types,
        },
    )


@login_required
def my_emergency_requests(request):
    """Citizen views and filters their emergency requests"""
    if request.user.role != 'citizen':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    base_queryset = EmergencyRequest.objects.filter(citizen=request.user).select_related('emergency_type')
    requests_queryset = base_queryset.order_by('-created_at')

    selected_status = request.GET.get('status', '').strip()
    selected_priority = request.GET.get('priority', '').strip()
    search_query = request.GET.get('q', '').strip()

    valid_statuses = {choice[0] for choice in EmergencyRequest.STATUS_CHOICES}
    valid_priorities = {choice[0] for choice in EmergencyRequest.PRIORITY_CHOICES}

    if selected_status in valid_statuses:
        requests_queryset = requests_queryset.filter(status=selected_status)
    else:
        selected_status = ''

    if selected_priority in valid_priorities:
        requests_queryset = requests_queryset.filter(priority=selected_priority)
    else:
        selected_priority = ''

    if search_query:
        search_filter = (
            Q(address__icontains=search_query)
            | Q(landmark__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(emergency_type__name__icontains=search_query)
        )
        if search_query.isdigit():
            search_filter |= Q(id=int(search_query))
        requests_queryset = requests_queryset.filter(search_filter)

    open_count = base_queryset.filter(status__in=['pending', 'assigned', 'en_route', 'on_scene']).count()
    resolved_count = base_queryset.filter(status='resolved').count()
    cancelled_count = base_queryset.filter(status='cancelled').count()

    return render(
        request,
        'emergency/my_requests.html',
        {
            'requests': requests_queryset,
            'status_options': EmergencyRequest.STATUS_CHOICES,
            'priority_options': EmergencyRequest.PRIORITY_CHOICES,
            'selected_status': selected_status,
            'selected_priority': selected_priority,
            'search_query': search_query,
            'total_results': requests_queryset.count(),
            'open_count': open_count,
            'resolved_count': resolved_count,
            'cancelled_count': cancelled_count,
        },
    )


@login_required
def emergency_detail(request, request_id):
    """View details of a specific emergency request"""
    emergency = get_object_or_404(EmergencyRequest.objects.select_related('emergency_type', 'citizen'), id=request_id)

    if request.user.role != 'citizen' or emergency.citizen != request.user:
        if request.user.role not in ['emergency_operator', 'government_authority']:
            messages.error(request, 'Access denied.')
            return redirect('dashboard:dashboard')

    can_cancel = (
        request.user.role == 'citizen'
        and emergency.citizen_id == request.user.id
        and emergency.status == 'pending'
    )

    return render(
        request,
        'emergency/emergency_detail.html',
        {
            'emergency': emergency,
            'can_cancel': can_cancel,
        },
    )


@login_required
def cancel_emergency_request(request, request_id):
    """Allow citizens to cancel only pending emergency requests."""
    if request.user.role != 'citizen':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    emergency = get_object_or_404(EmergencyRequest, id=request_id, citizen=request.user)

    if request.method != 'POST':
        return redirect('emergency:detail', request_id=emergency.id)

    if emergency.status != 'pending':
        messages.error(request, 'Only pending emergency requests can be cancelled.')
        return redirect('emergency:detail', request_id=emergency.id)

    emergency.status = 'cancelled'
    emergency.save()

    messages.success(request, f'Emergency request #{emergency.id} has been cancelled.')
    return redirect('emergency:my_requests')


@login_required
def operator_dashboard(request):
    """Emergency operator dashboard - pending emergencies and active team assignments"""
    if request.user.role != 'emergency_operator':
        messages.error(request, 'Access denied. Only emergency operators can access this page.')
        return redirect('dashboard:dashboard')

    selected_priority = request.GET.get('priority', '').strip()
    search_query = request.GET.get('q', '').strip()
    valid_priorities = {choice[0] for choice in EmergencyRequest.PRIORITY_CHOICES}

    pending_emergencies = EmergencyRequest.objects.filter(status='pending').select_related('citizen', 'emergency_type')

    if selected_priority in valid_priorities:
        pending_emergencies = pending_emergencies.filter(priority=selected_priority)
    else:
        selected_priority = ''

    if search_query:
        pending_filter = (
            Q(address__icontains=search_query)
            | Q(landmark__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(citizen__username__icontains=search_query)
            | Q(emergency_type__name__icontains=search_query)
        )
        if search_query.isdigit():
            pending_filter |= Q(id=int(search_query))
        pending_emergencies = pending_emergencies.filter(pending_filter)

    pending_emergencies = pending_emergencies.order_by('-created_at')

    active_assignments = TeamAssignment.objects.filter(
        status__in=['assigned', 'en_route', 'on_scene']
    ).select_related('emergency_request', 'team', 'team__team_leader').order_by('-assigned_at')

    if search_query:
        active_assignments = active_assignments.filter(
            Q(team__name__icontains=search_query)
            | Q(emergency_request__address__icontains=search_query)
            | Q(emergency_request__citizen__username__icontains=search_query)
        )

    total_pending = EmergencyRequest.objects.filter(status='pending').count()
    total_active = TeamAssignment.objects.filter(status__in=['assigned', 'en_route', 'on_scene']).count()
    total_teams = EmergencyTeam.objects.count()
    available_teams = EmergencyTeam.objects.filter(is_available=True).count()

    active_emergencies = EmergencyRequest.objects.filter(status__in=['assigned', 'en_route', 'on_scene']).count()
    on_scene = TeamAssignment.objects.filter(status='on_scene').count()
    resolved_today = EmergencyRequest.objects.filter(
        status='resolved',
        resolved_at__date=timezone.now().date(),
    ).count()
    critical_pending = EmergencyRequest.objects.filter(status='pending', priority='critical').count()
    available_vehicles = EmergencyVehicle.objects.filter(is_available=True).count()

    context = {
        'pending_emergencies': pending_emergencies,
        'active_assignments': active_assignments,
        'total_pending': total_pending,
        'total_active': total_active,
        'total_teams': total_teams,
        'available_teams': available_teams,
        'active_emergencies': active_emergencies,
        'on_scene': on_scene,
        'resolved_today': resolved_today,
        'critical_pending': critical_pending,
        'available_vehicles': available_vehicles,
        'priority_options': EmergencyRequest.PRIORITY_CHOICES,
        'selected_priority': selected_priority,
        'search_query': search_query,
        'filtered_pending_count': pending_emergencies.count(),
        'filtered_active_count': active_assignments.count(),
    }

    return render(request, 'emergency/operator_dashboard.html', context)


@login_required
def assign_team(request, emergency_id):
    """Assign a team to an emergency"""
    if request.user.role != 'emergency_operator':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    emergency = get_object_or_404(EmergencyRequest, id=emergency_id)
    available_teams = EmergencyTeam.objects.filter(is_available=True)

    if request.method == 'POST':
        if emergency.status != 'pending':
            messages.error(request, 'This emergency is no longer pending.')
            return redirect('emergency:operator_dashboard')

        team_id = request.POST.get('team_id')
        team = get_object_or_404(EmergencyTeam, id=team_id, is_available=True)

        TeamAssignment.objects.create(
            emergency_request=emergency,
            team=team,
            assigned_by=request.user,
            status='assigned',
        )

        emergency.status = 'assigned'
        emergency.save()

        team.is_available = False
        team.save()

        messages.success(request, f'Team {team.name} assigned successfully.')
        return redirect('emergency:operator_dashboard')

    return render(
        request,
        'emergency/assign_team.html',
        {
            'emergency': emergency,
            'available_teams': available_teams,
        },
    )


@login_required
def update_team_status(request, assignment_id):
    """Update team assignment status"""
    if request.user.role != 'emergency_operator':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    assignment = get_object_or_404(TeamAssignment.objects.select_related('emergency_request', 'team'), id=assignment_id)
    valid_statuses = {choice[0] for choice in TeamAssignment._meta.get_field('status').choices}

    if request.method == 'POST':
        status = request.POST.get('status')

        if status not in valid_statuses:
            messages.error(request, 'Invalid status selected.')
            return redirect('emergency:update_team_status', assignment_id=assignment.id)

        assignment.status = status
        assignment.save()

        emergency_status = 'resolved' if status == 'completed' else status
        assignment.emergency_request.status = emergency_status
        assignment.emergency_request.save()

        if status == 'completed':
            assignment.team.is_available = True
            assignment.team.save()

        messages.success(request, f'Team status updated to {status.replace("_", " ").title()}.')
        return redirect('emergency:operator_dashboard')

    return render(
        request,
        'emergency/update_team_status.html',
        {
            'assignment': assignment,
        },
    )


@login_required
def manage_teams(request):
    """Manage emergency teams (view, create, edit)"""
    if request.user.role != 'emergency_operator':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    teams = EmergencyTeam.objects.all().order_by('name')

    all_workers = User.objects.filter(role='worker')
    workers_in_teams = User.objects.filter(teams__isnull=False).distinct()
    available_workers = all_workers.exclude(id__in=workers_in_teams)

    all_vehicles = EmergencyVehicle.objects.all()
    vehicles_in_teams = EmergencyVehicle.objects.filter(teams__isnull=False).distinct()
    available_vehicles = all_vehicles.exclude(id__in=vehicles_in_teams)

    if request.method == 'POST':
        team_name = request.POST.get('team_name')
        team_type = request.POST.get('team_type')

        team = EmergencyTeam.objects.create(
            name=team_name,
            team_type=team_type,
            team_size=0,
        )

        worker_ids = request.POST.getlist('workers')
        for worker_id in worker_ids:
            worker = get_object_or_404(User, id=worker_id)
            team.workers.add(worker)

        team_leader_id = request.POST.get('team_leader')
        if team_leader_id and team_leader_id in worker_ids:
            team.team_leader = get_object_or_404(User, id=team_leader_id)
            team.save()

        vehicle_ids = request.POST.getlist('vehicles')
        for vehicle_id in vehicle_ids:
            vehicle = get_object_or_404(EmergencyVehicle, id=vehicle_id)
            team.vehicles.add(vehicle)

        equipment = request.POST.get('equipment')
        if equipment:
            team.equipment = equipment
            team.save()

        team.team_size = team.workers.count()
        team.save()

        messages.success(request, f'Team "{team.name}" created successfully with {team.team_size} members.')
        return redirect('emergency:manage_teams')

    return render(
        request,
        'emergency/manage_teams.html',
        {
            'teams': teams,
            'vehicles': available_vehicles,
            'available_workers': available_workers,
            'TEAM_TYPE_CHOICES': EmergencyTeam.TEAM_TYPE_CHOICES,
        },
    )


@login_required
def add_worker_to_team(request, team_id):
    """Add workers to an existing team"""
    if request.user.role != 'emergency_operator':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    team = get_object_or_404(EmergencyTeam, id=team_id)

    all_workers = User.objects.filter(role='worker')
    workers_in_teams = User.objects.filter(teams__isnull=False).distinct()
    available_workers = all_workers.exclude(id__in=workers_in_teams)

    if request.method == 'POST':
        worker_ids = request.POST.getlist('worker_ids')
        for worker_id in worker_ids:
            worker = get_object_or_404(User, id=worker_id)
            team.workers.add(worker)

        team_leader_id = request.POST.get('team_leader')
        if team_leader_id and team_leader_id in worker_ids:
            team.team_leader = get_object_or_404(User, id=team_leader_id)

        team.team_size = team.workers.count()
        team.save()

        messages.success(request, f'Workers added to {team.name} successfully.')
        return redirect('emergency:manage_teams')

    return render(
        request,
        'emergency/add_worker_to_team.html',
        {
            'team': team,
            'available_workers': available_workers,
        },
    )


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
            messages.success(request, 'Vehicle added successfully.')
            return redirect('emergency:manage_vehicles')
    else:
        form = EmergencyVehicleForm()

    return render(
        request,
        'emergency/manage_vehicles.html',
        {
            'vehicles': vehicles,
            'form': form,
        },
    )


@login_required
def delete_vehicle(request, vehicle_id):
    """Delete an emergency vehicle"""
    if request.user.role != 'emergency_operator':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    vehicle = get_object_or_404(EmergencyVehicle, id=vehicle_id)
    vehicle.delete()
    messages.success(request, 'Vehicle deleted successfully.')
    return redirect('emergency:manage_vehicles')

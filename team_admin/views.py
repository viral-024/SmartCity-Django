from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from accounts.models import User
from emergency.models import DispatchRecord, EmergencyTeam, EmergencyVehicle, TeamAssignment
from utilities.models import UtilityTeam, UtilityTeamAssignment


def _team_admin_stats():
    """Shared metrics for team admin pages."""
    return {
        'total_workers': User.objects.filter(role='worker').count(),
        'emergency_teams': EmergencyTeam.objects.count(),
        'utility_teams': UtilityTeam.objects.count(),
        'total_vehicles': EmergencyVehicle.objects.count(),
    }


@login_required
def create_worker(request):
    """Team admin creates worker accounts."""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied. Only Team Administrators can create workers.')
        return redirect('dashboard:dashboard')

    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''
        first_name = (request.POST.get('first_name') or '').strip()
        last_name = (request.POST.get('last_name') or '').strip()
        phone = (request.POST.get('phone_number') or '').strip()
        email = (request.POST.get('email') or '').strip()
        address = (request.POST.get('address') or '').strip()

        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return redirect('team_admin:create_worker')

        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
            return redirect('team_admin:create_worker')

        if User.objects.filter(username=username).exists():
            messages.error(request, f'Worker username "{username}" already exists.')
            return redirect('team_admin:create_worker')

        User.objects.create_user(
            username=username,
            password=password,
            role='worker',
            first_name=first_name,
            last_name=last_name,
            phone_number=phone,
            email=email,
            address=address,
        )

        messages.success(request, f'Worker "{username}" created successfully.')
        return redirect('team_admin:manage_workers')

    context = _team_admin_stats()
    return render(request, 'team_admin/create_worker.html', context)


@login_required
def manage_workers(request):
    """View all workers with team and profile info."""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    search_query = (request.GET.get('q') or '').strip()
    selected_status = (request.GET.get('status') or '').strip()
    selected_assignment = (request.GET.get('assignment') or '').strip()

    workers = User.objects.filter(role='worker').prefetch_related('teams', 'utility_teams').order_by('username')
    if search_query:
        tokens = [token for token in search_query.split() if token]

        if User.objects.filter(role='worker', username__iexact=search_query).exists():
            workers = workers.filter(username__iexact=search_query)
        else:
            search_filters = (
                Q(username__icontains=search_query)
                | Q(first_name__icontains=search_query)
                | Q(last_name__icontains=search_query)
                | Q(phone_number__icontains=search_query)
                | Q(email__icontains=search_query)
                | Q(address__icontains=search_query)
            )

            if len(tokens) > 1:
                full_name_filters = Q()
                for token in tokens:
                    full_name_filters &= (Q(first_name__icontains=token) | Q(last_name__icontains=token))
                search_filters |= full_name_filters

            workers = workers.filter(search_filters)

    if selected_status == 'active':
        workers = workers.filter(is_active=True)
    elif selected_status == 'inactive':
        workers = workers.filter(is_active=False)
    else:
        selected_status = ''

    if selected_assignment == 'assigned':
        workers = workers.filter(Q(teams__isnull=False) | Q(utility_teams__isnull=False))
    elif selected_assignment == 'unassigned':
        workers = workers.filter(teams__isnull=True, utility_teams__isnull=True)
    elif selected_assignment == 'emergency':
        workers = workers.filter(teams__isnull=False)
    elif selected_assignment == 'utility':
        workers = workers.filter(utility_teams__isnull=False)
    else:
        selected_assignment = ''

    workers = workers.distinct().order_by('username')

    context = {
        'workers': workers,
        'search_query': search_query,
        'selected_status': selected_status,
        'selected_assignment': selected_assignment,
        **_team_admin_stats(),
    }
    return render(request, 'team_admin/manage_workers.html', context)

@login_required
def worker_detail(request, worker_id):
    """Show worker profile and assignment history."""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    worker = get_object_or_404(User, id=worker_id, role='worker')

    emergency_teams = worker.teams.all().prefetch_related('vehicles').order_by('name')
    utility_teams = worker.utility_teams.all().prefetch_related('vehicles').order_by('name')

    emergency_team_ids = list(emergency_teams.values_list('id', flat=True))
    utility_team_ids = list(utility_teams.values_list('id', flat=True))

    emergency_records = TeamAssignment.objects.none()
    emergency_record_count = 0
    if emergency_team_ids:
        emergency_queryset = TeamAssignment.objects.filter(
            team_id__in=emergency_team_ids
        ).select_related(
            'team',
            'emergency_request',
            'emergency_request__emergency_type',
        ).order_by('-assigned_at')
        emergency_record_count = emergency_queryset.count()
        emergency_records = emergency_queryset[:100]

    utility_records = UtilityTeamAssignment.objects.none()
    utility_record_count = 0
    if utility_team_ids:
        utility_queryset = UtilityTeamAssignment.objects.filter(
            team_id__in=utility_team_ids
        ).select_related(
            'team',
            'complaint',
            'complaint__utility_type',
        ).order_by('-assigned_at')
        utility_record_count = utility_queryset.count()
        utility_records = utility_queryset[:100]

    context = {
        'worker': worker,
        'worker_emergency_teams': emergency_teams,
        'worker_utility_teams': utility_teams,
        'emergency_records': emergency_records,
        'utility_records': utility_records,
        'emergency_record_count': emergency_record_count,
        'utility_record_count': utility_record_count,
        **_team_admin_stats(),
    }
    return render(request, 'team_admin/worker_detail.html', context)


@login_required
def delete_worker(request, worker_id):
    """Delete a worker account from the system."""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    worker = get_object_or_404(User, id=worker_id, role='worker')

    if request.method != 'POST':
        return redirect('team_admin:worker_detail', worker_id=worker.id)

    team_memberships = worker.teams.count() + worker.utility_teams.count()
    username = worker.username
    worker.delete()

    messages.success(
        request,
        f'Worker "{username}" deleted successfully. Removed from {team_memberships} team membership(s).',
    )
    return redirect('team_admin:manage_workers')

@login_required
def update_worker_status(request, worker_id):
    """Activate or deactivate a worker account."""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    worker = get_object_or_404(User, id=worker_id, role='worker')
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')

    if request.method != 'POST':
        return redirect('team_admin:worker_detail', worker_id=worker.id)

    desired_status = (request.POST.get('status') or '').strip().lower()
    if desired_status not in ['active', 'inactive']:
        messages.error(request, 'Invalid status value.')
        if isinstance(next_url, str) and next_url.startswith('/'):
            return redirect(next_url)
        return redirect('team_admin:manage_workers')

    worker.is_active = desired_status == 'active'
    worker.save(update_fields=['is_active'])

    messages.success(
        request,
        f'Worker "{worker.username}" is now {"Active" if worker.is_active else "Inactive"}.',
    )

    if isinstance(next_url, str) and next_url.startswith('/'):
        return redirect(next_url)
    return redirect('team_admin:manage_workers')

@login_required
def create_emergency_team(request):
    """Create emergency response team."""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    available_workers = User.objects.filter(
        role='worker',
        teams__isnull=True,
        utility_teams__isnull=True,
    )
    available_vehicles = EmergencyVehicle.objects.filter(teams__isnull=True, utility_teams__isnull=True)

    if request.method == 'POST':
        team_name = (request.POST.get('team_name') or '').strip()
        team_type = request.POST.get('team_type')
        worker_ids = request.POST.getlist('workers')
        vehicle_ids = request.POST.getlist('vehicles')
        team_leader_id = request.POST.get('team_leader')

        if not team_name or not worker_ids:
            messages.error(request, 'Team name and at least one worker are required.')
            return redirect('team_admin:create_emergency_team')

        team = EmergencyTeam.objects.create(
            name=team_name,
            team_type=team_type,
            team_size=len(worker_ids),
        )

        for worker_id in worker_ids:
            worker = get_object_or_404(User, id=worker_id)
            team.workers.add(worker)

        if team_leader_id and team_leader_id in worker_ids:
            team.team_leader = get_object_or_404(User, id=team_leader_id)

        for vehicle_id in vehicle_ids:
            vehicle = get_object_or_404(EmergencyVehicle, id=vehicle_id)
            team.vehicles.add(vehicle)

        team.save()
        messages.success(request, f'Emergency Team "{team_name}" created successfully!')
        return redirect('team_admin:manage_emergency_teams')

    return render(
        request,
        'team_admin/create_emergency_team.html',
        {
            'available_workers': available_workers,
            'available_vehicles': available_vehicles,
            'TEAM_TYPE_CHOICES': EmergencyTeam.TEAM_TYPE_CHOICES,
            **_team_admin_stats(),
        },
    )


@login_required
def manage_emergency_teams(request):
    """View and filter emergency teams."""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    search_query = (request.GET.get('q') or '').strip()
    selected_type = (request.GET.get('team_type') or '').strip()
    selected_status = (request.GET.get('status') or '').strip()

    teams = EmergencyTeam.objects.select_related('team_leader').prefetch_related('vehicles').all().order_by('name')

    valid_types = {choice[0] for choice in EmergencyTeam.TEAM_TYPE_CHOICES}
    if selected_type in valid_types:
        teams = teams.filter(team_type=selected_type)
    else:
        selected_type = ''

    if selected_status == 'available':
        teams = teams.filter(is_available=True)
    elif selected_status == 'assigned':
        teams = teams.filter(is_available=False)
    else:
        selected_status = ''

    if search_query:
        teams = teams.filter(
            Q(name__icontains=search_query)
            | Q(team_leader__username__icontains=search_query)
            | Q(equipment__icontains=search_query)
        ).distinct()

    context = {
        'teams': teams,
        'search_query': search_query,
        'selected_type': selected_type,
        'selected_status': selected_status,
        'team_type_choices': EmergencyTeam.TEAM_TYPE_CHOICES,
        **_team_admin_stats(),
    }
    return render(request, 'team_admin/manage_emergency_teams.html', context)


@login_required
def add_worker_to_emergency_team(request, team_id):
    """Add worker to existing emergency team."""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    team = get_object_or_404(EmergencyTeam, id=team_id)
    available_workers = User.objects.filter(
        role='worker',
        teams__isnull=True,
        utility_teams__isnull=True,
    )

    if request.method == 'POST':
        worker_ids = request.POST.getlist('worker_ids')

        if not worker_ids:
            messages.error(request, 'Please select at least one worker to add.')
            return redirect('team_admin:add_worker_to_emergency_team', team_id=team_id)

        added_count = 0
        for worker_id in worker_ids:
            try:
                worker = User.objects.get(id=worker_id, role='worker')
                team.workers.add(worker)
                added_count += 1
            except User.DoesNotExist:
                continue

        team_leader_id = request.POST.get('team_leader')
        if team_leader_id and team_leader_id in worker_ids:
            try:
                team.team_leader = User.objects.get(id=team_leader_id, role='worker')
            except User.DoesNotExist:
                pass

        team.save()
        messages.success(request, f'{added_count} worker(s) added to {team.name} successfully!')
        return redirect('team_admin:manage_emergency_teams')

    return render(
        request,
        'team_admin/add_worker_to_team.html',
        {
            'team': team,
            'available_workers': available_workers,
            'team_type': 'emergency',
            **_team_admin_stats(),
        },
    )


@login_required
def emergency_team_detail(request, team_id):
    """View emergency team details and assignment history."""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    team = get_object_or_404(
        EmergencyTeam.objects.select_related('team_leader').prefetch_related('workers', 'vehicles'),
        id=team_id,
    )
    assignment_queryset = TeamAssignment.objects.filter(team=team).select_related(
        'emergency_request',
        'emergency_request__emergency_type',
        'assigned_by',
    ).order_by('-assigned_at')

    context = {
        'team': team,
        'assignments': assignment_queryset[:100],
        'assignment_count': assignment_queryset.count(),
        'active_assignment_count': assignment_queryset.filter(
            status__in=['assigned', 'en_route', 'on_scene']
        ).count(),
        **_team_admin_stats(),
    }
    return render(request, 'team_admin/emergency_team_detail.html', context)


@login_required
def delete_emergency_team(request, team_id):
    """Delete emergency team if not protected by assignment history."""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    team = get_object_or_404(EmergencyTeam, id=team_id)

    if request.method != 'POST':
        return redirect('team_admin:emergency_team_detail', team_id=team.id)

    team_name = team.name
    try:
        team.delete()
        messages.success(request, f'Emergency team "{team_name}" deleted successfully.')
    except ProtectedError:
        messages.error(
            request,
            f'Cannot delete "{team_name}" because it has assignment history. Complete/archive related records first.',
        )
    return redirect('team_admin:manage_emergency_teams')


@login_required
def create_utility_team(request):
    """Create utility response team."""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    available_workers = User.objects.filter(
        role='worker',
        teams__isnull=True,
        utility_teams__isnull=True,
    )
    available_vehicles = EmergencyVehicle.objects.filter(
        teams__isnull=True,
        utility_teams__isnull=True,
    )

    if request.method == 'POST':
        team_name = (request.POST.get('team_name') or '').strip()
        team_type = request.POST.get('team_type')
        worker_ids = request.POST.getlist('workers')
        vehicle_ids = request.POST.getlist('vehicles')
        team_leader_id = request.POST.get('team_leader')
        equipment = request.POST.get('equipment', '')

        if not team_name or not worker_ids:
            messages.error(request, 'Team name and at least one worker are required.')
            return redirect('team_admin:create_utility_team')

        team = UtilityTeam.objects.create(
            name=team_name,
            team_type=team_type,
            team_size=len(worker_ids),
            equipment=equipment,
        )

        for worker_id in worker_ids:
            worker = get_object_or_404(User, id=worker_id)
            team.workers.add(worker)

        if team_leader_id and team_leader_id in worker_ids:
            team.team_leader = get_object_or_404(User, id=team_leader_id)

        for vehicle_id in vehicle_ids:
            vehicle = get_object_or_404(EmergencyVehicle, id=vehicle_id)
            team.vehicles.add(vehicle)

        team.save()
        messages.success(request, f'Utility Team "{team_name}" created successfully!')
        return redirect('team_admin:manage_utility_teams')

    return render(
        request,
        'team_admin/create_utility_team.html',
        {
            'available_workers': available_workers,
            'available_vehicles': available_vehicles,
            'TEAM_TYPE_CHOICES': UtilityTeam.TEAM_TYPE_CHOICES,
            **_team_admin_stats(),
        },
    )


@login_required
def manage_utility_teams(request):
    """View and filter utility teams."""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    search_query = (request.GET.get('q') or '').strip()
    selected_type = (request.GET.get('team_type') or '').strip()
    selected_status = (request.GET.get('status') or '').strip()

    teams = UtilityTeam.objects.select_related('team_leader').prefetch_related('vehicles').all().order_by('name')

    valid_types = {choice[0] for choice in UtilityTeam.TEAM_TYPE_CHOICES}
    if selected_type in valid_types:
        teams = teams.filter(team_type=selected_type)
    else:
        selected_type = ''

    if selected_status == 'available':
        teams = teams.filter(is_available=True)
    elif selected_status == 'assigned':
        teams = teams.filter(is_available=False)
    else:
        selected_status = ''

    if search_query:
        teams = teams.filter(
            Q(name__icontains=search_query)
            | Q(team_leader__username__icontains=search_query)
            | Q(equipment__icontains=search_query)
        ).distinct()

    context = {
        'teams': teams,
        'search_query': search_query,
        'selected_type': selected_type,
        'selected_status': selected_status,
        'team_type_choices': UtilityTeam.TEAM_TYPE_CHOICES,
        **_team_admin_stats(),
    }
    return render(request, 'team_admin/manage_utility_teams.html', context)


@login_required
def add_worker_to_utility_team(request, team_id):
    """Add worker to existing utility team."""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    team = get_object_or_404(UtilityTeam, id=team_id)
    available_workers = User.objects.filter(
        role='worker',
        teams__isnull=True,
        utility_teams__isnull=True,
    )

    if request.method == 'POST':
        worker_ids = request.POST.getlist('worker_ids')

        if not worker_ids:
            messages.error(request, 'Please select at least one worker to add.')
            return redirect('team_admin:add_worker_to_utility_team', team_id=team_id)

        added_count = 0
        for worker_id in worker_ids:
            try:
                worker = User.objects.get(id=worker_id, role='worker')
                team.workers.add(worker)
                added_count += 1
            except User.DoesNotExist:
                continue

        team_leader_id = request.POST.get('team_leader')
        if team_leader_id and team_leader_id in worker_ids:
            try:
                team.team_leader = User.objects.get(id=team_leader_id, role='worker')
            except User.DoesNotExist:
                pass

        team.save()
        messages.success(request, f'{added_count} worker(s) added to {team.name} successfully!')
        return redirect('team_admin:manage_utility_teams')

    return render(
        request,
        'team_admin/add_worker_to_team.html',
        {
            'team': team,
            'available_workers': available_workers,
            'team_type': 'utility',
            **_team_admin_stats(),
        },
    )


@login_required
def utility_team_detail(request, team_id):
    """View utility team details and assignment history."""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    team = get_object_or_404(
        UtilityTeam.objects.select_related('team_leader').prefetch_related('workers', 'vehicles'),
        id=team_id,
    )
    assignment_queryset = UtilityTeamAssignment.objects.filter(team=team).select_related(
        'complaint',
        'complaint__utility_type',
        'assigned_by',
    ).order_by('-assigned_at')

    context = {
        'team': team,
        'assignments': assignment_queryset[:100],
        'assignment_count': assignment_queryset.count(),
        'active_assignment_count': assignment_queryset.filter(
            status__in=['assigned', 'in_progress']
        ).count(),
        **_team_admin_stats(),
    }
    return render(request, 'team_admin/utility_team_detail.html', context)


@login_required
def delete_utility_team(request, team_id):
    """Delete utility team if not protected by assignment history."""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    team = get_object_or_404(UtilityTeam, id=team_id)

    if request.method != 'POST':
        return redirect('team_admin:utility_team_detail', team_id=team.id)

    team_name = team.name
    try:
        team.delete()
        messages.success(request, f'Utility team "{team_name}" deleted successfully.')
    except ProtectedError:
        messages.error(
            request,
            f'Cannot delete "{team_name}" because it has assignment history. Complete/archive related records first.',
        )
    return redirect('team_admin:manage_utility_teams')


@login_required
def create_vehicle(request):
    """Create emergency vehicle."""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    if request.method == 'POST':
        vehicle_number = (request.POST.get('vehicle_number') or '').strip()
        vehicle_type = request.POST.get('vehicle_type')
        driver_name = (request.POST.get('driver_name') or '').strip()
        driver_contact = (request.POST.get('driver_contact') or '').strip()
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
            is_available=True,
        )
        messages.success(request, f'Vehicle "{vehicle_number}" created successfully!')
        return redirect('team_admin:manage_vehicles')

    return render(request, 'team_admin/create_vehicle.html', _team_admin_stats())


@login_required
def manage_vehicles(request):
    """View all vehicles."""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    vehicles = EmergencyVehicle.objects.all().order_by('vehicle_number')

    context = {
        'vehicles': vehicles,
        **_team_admin_stats(),
    }
    return render(request, 'team_admin/manage_vehicles.html', context)


@login_required
def vehicle_detail(request, vehicle_id):
    """Show vehicle profile and assignment history across emergency/utility teams."""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    vehicle = get_object_or_404(EmergencyVehicle, id=vehicle_id)

    emergency_teams_for_vehicle = vehicle.teams.all().select_related('team_leader').order_by('name')
    utility_teams_for_vehicle = vehicle.utility_teams.all().select_related('team_leader').order_by('name')

    emergency_history_queryset = TeamAssignment.objects.filter(
        team__vehicles=vehicle,
    ).select_related(
        'team',
        'emergency_request',
        'emergency_request__emergency_type',
        'assigned_by',
    ).distinct().order_by('-assigned_at')

    utility_history_queryset = UtilityTeamAssignment.objects.filter(
        team__vehicles=vehicle,
    ).select_related(
        'team',
        'complaint',
        'complaint__utility_type',
        'assigned_by',
    ).distinct().order_by('-assigned_at')

    dispatch_history_queryset = DispatchRecord.objects.filter(
        vehicle=vehicle,
    ).select_related(
        'emergency_request',
        'emergency_request__emergency_type',
        'assigned_by',
    ).order_by('-assigned_at')

    context = {
        'vehicle': vehicle,
        'emergency_teams_for_vehicle': emergency_teams_for_vehicle,
        'utility_teams_for_vehicle': utility_teams_for_vehicle,
        'emergency_history': emergency_history_queryset[:100],
        'utility_history': utility_history_queryset[:100],
        'dispatch_history': dispatch_history_queryset[:100],
        'emergency_history_count': emergency_history_queryset.count(),
        'utility_history_count': utility_history_queryset.count(),
        'dispatch_history_count': dispatch_history_queryset.count(),
        **_team_admin_stats(),
    }
    return render(request, 'team_admin/vehicle_detail.html', context)


@login_required
def delete_vehicle(request, vehicle_id):
    """Delete vehicle."""
    if request.user.role != 'team_admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    vehicle = get_object_or_404(EmergencyVehicle, id=vehicle_id)

    if request.method != 'POST':
        return redirect('team_admin:vehicle_detail', vehicle_id=vehicle.id)

    vehicle_number = vehicle.vehicle_number
    try:
        vehicle.delete()
        messages.success(request, f'Vehicle "{vehicle_number}" deleted successfully!')
    except ProtectedError:
        messages.error(
            request,
            f'Cannot delete vehicle "{vehicle_number}" because it has dispatch/assignment history.',
        )

    return redirect('team_admin:manage_vehicles')

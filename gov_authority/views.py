from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from emergency.models import EmergencyTeam, EmergencyRequest
from utilities.models import UtilityTeam, Complaint

@login_required
def dashboard(request):
    """Government authority main dashboard - NO vehicle details"""
    if request.user.role != 'government_authority':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    # Real-time team resources (NO VEHICLES)
    total_emergency_teams = EmergencyTeam.objects.count()
    available_emergency_teams = EmergencyTeam.objects.filter(is_available=True).count()
    assigned_emergency_teams = total_emergency_teams - available_emergency_teams
    
    total_utility_teams = UtilityTeam.objects.count()
    available_utility_teams = UtilityTeam.objects.filter(is_available=True).count()
    assigned_utility_teams = total_utility_teams - available_utility_teams
    
    # Performance trends (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Emergencies metrics
    resolved_emergencies = EmergencyRequest.objects.filter(
        status='resolved',
        resolved_at__gte=thirty_days_ago
    ).count()
    
    # Calculate average response time for resolved emergencies
    resolved_requests = EmergencyRequest.objects.filter(
        status='resolved',
        resolved_at__gte=thirty_days_ago,
        assigned_at__isnull=False
    )
    avg_response_time = 0
    if resolved_requests.exists():
        total_seconds = sum(
            (req.resolved_at - req.assigned_at).total_seconds() 
            for req in resolved_requests if req.resolved_at and req.assigned_at
        )
        avg_response_time = round(total_seconds / resolved_requests.count() / 60, 1)  # in minutes
    
    # Complaints metrics
    resolved_complaints = Complaint.objects.filter(
        status='resolved',
        resolved_at__gte=thirty_days_ago
    ).count()
    
    # Calculate average resolution time for resolved complaints
    resolved_complaint_objs = Complaint.objects.filter(
        status='resolved',
        resolved_at__gte=thirty_days_ago,
        assigned_at__isnull=False
    )
    avg_resolution_time = 0
    if resolved_complaint_objs.exists():
        total_seconds = sum(
            (comp.resolved_at - comp.assigned_at).total_seconds()
            for comp in resolved_complaint_objs if comp.resolved_at and comp.assigned_at
        )
        avg_resolution_time = round(total_seconds / resolved_complaint_objs.count() / 3600, 1)  # in hours
    
    # SLA Compliance (simplified calculation)
    sla_emergencies = 0
    for req in resolved_requests:
        if req.assigned_at and req.resolved_at:
            response_time = req.resolved_at - req.assigned_at
            if response_time <= timedelta(minutes=30):
                sla_emergencies += 1
    
    sla_complaints = 0
    for comp in resolved_complaint_objs:
        if comp.assigned_at and comp.resolved_at:
            resolution_time = comp.resolved_at - comp.assigned_at
            if resolution_time <= timedelta(hours=24):
                sla_complaints += 1
    
    total_sla_applicable = resolved_requests.count() + resolved_complaint_objs.count()
    sla_compliance = 0
    if total_sla_applicable > 0:
        sla_compliance = round(((sla_emergencies + sla_complaints) / total_sla_applicable) * 100, 1)
    
    # Active incidents
    active_emergencies = EmergencyRequest.objects.filter(
        status__in=['pending', 'assigned', 'en_route', 'on_scene']
    ).count()
    
    active_complaints = Complaint.objects.filter(
        status__in=['pending', 'assigned', 'in_progress']
    ).count()
    
    # Alerts (items exceeding time thresholds)
    delayed_emergencies = EmergencyRequest.objects.filter(
        status__in=['assigned', 'en_route'],
        assigned_at__lt=timezone.now() - timedelta(minutes=30)
    ).count()
    
    delayed_complaints = Complaint.objects.filter(
        status='assigned',
        assigned_at__lt=timezone.now() - timedelta(hours=24)
    ).count()
    
    alerts_count = delayed_emergencies + delayed_complaints
    
    context = {
        'total_emergency_teams': total_emergency_teams,
        'available_emergency_teams': available_emergency_teams,
        'assigned_emergency_teams': assigned_emergency_teams,
        'emergency_avail_pct': round((available_emergency_teams / total_emergency_teams * 100), 1) if total_emergency_teams > 0 else 0,
        
        'total_utility_teams': total_utility_teams,
        'available_utility_teams': available_utility_teams,
        'assigned_utility_teams': assigned_utility_teams,
        'utility_avail_pct': round((available_utility_teams / total_utility_teams * 100), 1) if total_utility_teams > 0 else 0,
        
        'resolved_emergencies': resolved_emergencies,
        'avg_response_time': avg_response_time,
        'resolved_complaints': resolved_complaints,
        'avg_resolution_time': avg_resolution_time,
        'sla_compliance': sla_compliance,
        
        'active_emergencies': active_emergencies,
        'active_complaints': active_complaints,
        'alerts_count': alerts_count,
        'delayed_emergencies': delayed_emergencies,
        'delayed_complaints': delayed_complaints,
    }
    
    return render(request, 'gov_authority/dashboard.html', context)


@login_required
def staff_list(request):
    """List and manage all staff accounts (VIEW ONLY + deactivate/reactivate)"""
    if request.user.role != 'government_authority':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    # Get all staff accounts (non-citizens)
    staff_accounts = User.objects.filter(
        role__in=['emergency_operator', 'utility_officer', 'team_admin', 'worker', 'government_authority']
    ).order_by('-date_joined')
    
    # Handle deactivation/reactivation
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        
        try:
            user = User.objects.get(id=user_id)
            if action == 'deactivate':
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
    
    return render(request, 'gov_authority/staff_list.html', {'staff_accounts': staff_accounts})


@login_required
def escalations(request):
    """View escalated complaints (READ-ONLY)"""
    if request.user.role != 'government_authority':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    # Get all escalated complaints (READ-ONLY)
    escalated_complaints = Complaint.objects.filter(
        status='escalated'
    ).select_related('citizen', 'utility_type').order_by('-escalated_at')
    
    return render(request, 'gov_authority/escalations.html', {
        'escalated_complaints': escalated_complaints
    })
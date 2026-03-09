from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Avg
from .models import (
    Complaint,
    UtilityType,
    ComplaintUpdate,
    UtilityTeam,
    UtilityTeamAssignment,
)
from .forms import ComplaintForm, ComplaintFeedbackForm


def ensure_default_utility_types():
    """Create baseline utility categories if they do not exist."""
    default_types = [
        {
            'name': 'Water Supply',
            'description': 'Water supply issues including leaks, low pressure, contamination',
            'department': 'Water Department',
            'icon': 'tint',
        },
        {
            'name': 'Electricity',
            'description': 'Power outages, electrical faults, billing issues',
            'department': 'Electricity Board',
            'icon': 'bolt',
        },
        {
            'name': 'Garbage Management',
            'description': 'Garbage collection, waste disposal, cleanliness issues',
            'department': 'Municipal Corporation',
            'icon': 'trash',
        },
        {
            'name': 'Road Maintenance',
            'description': 'Potholes, road damage, street lighting issues',
            'department': 'Public Works',
            'icon': 'road',
        },
    ]

    for utility_type in default_types:
        UtilityType.objects.get_or_create(
            name=utility_type['name'],
            defaults=utility_type,
        )


@login_required
def citizen_submit_complaint(request):
    """Citizen submits utility complaint"""
    if request.user.role != 'citizen':
        messages.error(request, 'Access denied. Only citizens can report complaints.')
        return redirect('dashboard:dashboard')

    ensure_default_utility_types()

    if request.method == 'POST':
        form = ComplaintForm(request.POST, user=request.user)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.citizen = request.user
            complaint.save()

            messages.success(request, f'Complaint submitted successfully. Complaint ID: {complaint.complaint_id}')
            return redirect('utilities:my_complaints')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = ComplaintForm(user=request.user)

    utility_types = UtilityType.objects.all()
    return render(
        request,
        'utilities/citizen_submit_complaint.html',
        {
            'form': form,
            'utility_types': utility_types,
        },
    )


@login_required
def my_complaints(request):
    """Citizen views and filters their complaints"""
    if request.user.role != 'citizen':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    base_queryset = Complaint.objects.filter(citizen=request.user).select_related('utility_type')
    complaints_queryset = base_queryset.order_by('-created_at')

    selected_status = request.GET.get('status', '').strip()
    selected_priority = request.GET.get('priority', '').strip()
    search_query = request.GET.get('q', '').strip()

    valid_statuses = {choice[0] for choice in Complaint.STATUS_CHOICES}
    valid_priorities = {choice[0] for choice in Complaint.PRIORITY_CHOICES}

    if selected_status in valid_statuses:
        complaints_queryset = complaints_queryset.filter(status=selected_status)
    else:
        selected_status = ''

    if selected_priority in valid_priorities:
        complaints_queryset = complaints_queryset.filter(priority=selected_priority)
    else:
        selected_priority = ''

    if search_query:
        search_filter = (
            Q(complaint_id__icontains=search_query)
            | Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(address__icontains=search_query)
            | Q(landmark__icontains=search_query)
            | Q(utility_type__name__icontains=search_query)
        )
        complaints_queryset = complaints_queryset.filter(search_filter)

    open_count = base_queryset.filter(status__in=['pending', 'assigned', 'in_progress', 'escalated']).count()
    resolved_count = base_queryset.filter(status='resolved').count()
    escalated_count = base_queryset.filter(status='escalated').count()

    return render(
        request,
        'utilities/my_complaints.html',
        {
            'complaints': complaints_queryset,
            'status_options': Complaint.STATUS_CHOICES,
            'priority_options': Complaint.PRIORITY_CHOICES,
            'selected_status': selected_status,
            'selected_priority': selected_priority,
            'search_query': search_query,
            'total_results': complaints_queryset.count(),
            'open_count': open_count,
            'resolved_count': resolved_count,
            'escalated_count': escalated_count,
        },
    )


@login_required
def complaint_detail(request, complaint_id):
    """View details of a specific complaint"""
    complaint = get_object_or_404(Complaint.objects.select_related('citizen', 'utility_type'), complaint_id=complaint_id)

    if request.user.role != 'citizen' or complaint.citizen != request.user:
        if request.user.role not in ['utility_officer', 'government_authority']:
            messages.error(request, 'Access denied.')
            return redirect('dashboard:dashboard')

    updates = complaint.updates.all().order_by('-created_at')

    can_rate = (
        request.user.role == 'citizen'
        and complaint.citizen_id == request.user.id
        and complaint.status == 'resolved'
    )

    feedback_form = None
    if can_rate:
        feedback_form = ComplaintFeedbackForm(
            initial={'satisfaction_rating': complaint.satisfaction_rating or 5}
        )

    return render(
        request,
        'utilities/complaint_detail.html',
        {
            'complaint': complaint,
            'updates': updates,
            'can_rate': can_rate,
            'feedback_form': feedback_form,
        },
    )


@login_required
def rate_complaint(request, complaint_id):
    """Citizen rates a resolved complaint and can leave optional feedback."""
    if request.user.role != 'citizen':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    complaint = get_object_or_404(Complaint, complaint_id=complaint_id, citizen=request.user)

    if request.method != 'POST':
        return redirect('utilities:detail', complaint_id=complaint.complaint_id)

    if complaint.status != 'resolved':
        messages.error(request, 'Only resolved complaints can be rated.')
        return redirect('utilities:detail', complaint_id=complaint.complaint_id)

    form = ComplaintFeedbackForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Please select a valid rating.')
        return redirect('utilities:detail', complaint_id=complaint.complaint_id)

    rating = int(form.cleaned_data['satisfaction_rating'])
    feedback_text = form.cleaned_data['feedback_text'].strip()

    complaint.satisfaction_rating = rating
    complaint.save()

    if feedback_text:
        ComplaintUpdate.objects.create(
            complaint=complaint,
            updated_by=request.user,
            update_text=f'Citizen feedback ({rating}/5): {feedback_text}',
        )

    messages.success(request, 'Thank you. Your feedback has been saved.')
    return redirect('utilities:detail', complaint_id=complaint.complaint_id)


@login_required
def officer_dashboard(request):
    """Utility officer dashboard - team assignment workflow with filtering and feedback metrics"""
    if request.user.role != 'utility_officer':
        messages.error(request, 'Access denied. Only utility officers can access this page.')
        return redirect('dashboard:dashboard')

    selected_priority = request.GET.get('priority', '').strip()
    search_query = request.GET.get('q', '').strip()
    valid_priorities = {choice[0] for choice in Complaint.PRIORITY_CHOICES}

    pending_complaints = Complaint.objects.filter(status='pending').select_related('citizen', 'utility_type')
    assigned_complaints = Complaint.objects.filter(
        status__in=['assigned', 'in_progress']
    ).select_related('citizen', 'utility_type').prefetch_related('team_assignments__team')

    if selected_priority in valid_priorities:
        pending_complaints = pending_complaints.filter(priority=selected_priority)
        assigned_complaints = assigned_complaints.filter(priority=selected_priority)
    else:
        selected_priority = ''

    if search_query:
        search_filter = (
            Q(complaint_id__icontains=search_query)
            | Q(title__icontains=search_query)
            | Q(address__icontains=search_query)
            | Q(citizen__username__icontains=search_query)
            | Q(utility_type__name__icontains=search_query)
        )
        pending_complaints = pending_complaints.filter(search_filter)
        assigned_complaints = assigned_complaints.filter(search_filter)

    pending_complaints = pending_complaints.order_by('-created_at')
    assigned_complaints = assigned_complaints.order_by('-created_at')

    total_assigned = Complaint.objects.filter(status__in=['assigned', 'in_progress']).count()
    total_pending = Complaint.objects.filter(status='pending').count()
    in_progress = Complaint.objects.filter(status='in_progress').count()
    resolved_today = Complaint.objects.filter(
        status='resolved',
        resolved_at__date=timezone.now().date(),
    ).count()
    total_teams = UtilityTeam.objects.count()
    available_teams = UtilityTeam.objects.filter(is_available=True).count()

    rated_queryset = Complaint.objects.filter(status='resolved', satisfaction_rating__isnull=False)
    average_satisfaction = rated_queryset.aggregate(avg=Avg('satisfaction_rating'))['avg'] or 0

    context = {
        'assigned_complaints': assigned_complaints,
        'pending_complaints': pending_complaints,
        'total_assigned': total_assigned,
        'total_pending': total_pending,
        'in_progress': in_progress,
        'resolved_today': resolved_today,
        'total_teams': total_teams,
        'available_teams': available_teams,
        'average_satisfaction': round(average_satisfaction, 2),
        'rated_resolved_count': rated_queryset.count(),
        'priority_options': Complaint.PRIORITY_CHOICES,
        'selected_priority': selected_priority,
        'search_query': search_query,
        'filtered_pending_count': pending_complaints.count(),
        'filtered_assigned_count': assigned_complaints.count(),
    }

    return render(request, 'utilities/officer_dashboard.html', context)


@login_required
def assign_utility_team(request, complaint_id):
    """Assign a team to a utility complaint"""
    if request.user.role != 'utility_officer':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    complaint = get_object_or_404(Complaint, id=complaint_id)
    available_teams = UtilityTeam.objects.filter(is_available=True)

    if request.method == 'POST':
        if complaint.status != 'pending':
            messages.error(request, 'This complaint is no longer pending.')
            return redirect('utilities:officer_dashboard')

        team_id = request.POST.get('team_id')
        team = get_object_or_404(UtilityTeam, id=team_id, is_available=True)

        UtilityTeamAssignment.objects.create(
            complaint=complaint,
            team=team,
            assigned_by=request.user,
            status='assigned',
        )

        complaint.status = 'assigned'
        complaint.assigned_officer = request.user
        complaint.save()

        team.is_available = False
        team.save()

        messages.success(request, f'Team {team.name} assigned successfully.')
        return redirect('utilities:officer_dashboard')

    return render(
        request,
        'utilities/assign_utility_team.html',
        {
            'complaint': complaint,
            'available_teams': available_teams,
        },
    )


@login_required
def update_team_assignment_status(request, assignment_id):
    """Update utility team assignment status"""
    if request.user.role != 'utility_officer':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    assignment = get_object_or_404(UtilityTeamAssignment.objects.select_related('complaint', 'team'), id=assignment_id)
    valid_statuses = {choice[0] for choice in UtilityTeamAssignment._meta.get_field('status').choices}

    if request.method == 'POST':
        status = request.POST.get('status')

        if status not in valid_statuses:
            messages.error(request, 'Invalid status selected.')
            return redirect('utilities:update_team_assignment_status', assignment_id=assignment.id)

        assignment.status = status
        assignment.save()

        complaint_status = 'resolved' if status == 'resolved' else status
        assignment.complaint.status = complaint_status
        assignment.complaint.save()

        if status == 'resolved':
            assignment.team.is_available = True
            assignment.team.save()

        messages.success(request, f'Team status updated to {status.replace("_", " ").title()}.')
        return redirect('utilities:officer_dashboard')

    return render(
        request,
        'utilities/update_team_assignment_status.html',
        {
            'assignment': assignment,
        },
    )

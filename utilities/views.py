from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import (
    Complaint, UtilityType, ComplaintUpdate,
    UtilityTeam, UtilityTeamAssignment  # ← Team-based models
)
from .forms import ComplaintForm
from accounts.models import User


@login_required
def citizen_submit_complaint(request):
    """Citizen submits utility complaint"""
    if request.user.role != 'citizen':
        messages.error(request, 'Access denied. Only citizens can report complaints.')
        return redirect('dashboard:dashboard')
    
    # Create default utility types if none exist
    if not UtilityType.objects.exists():
        UtilityType.objects.create(
            name='Water Supply',
            description='Water supply issues including leaks, low pressure, contamination',
            department='Water Department',
            icon='tint'
        )
        UtilityType.objects.create(
            name='Electricity',
            description='Power outages, electrical faults, billing issues',
            department='Electricity Board',
            icon='bolt'
        )
        UtilityType.objects.create(
            name='Garbage Management',
            description='Garbage collection, waste disposal, cleanliness issues',
            department='Municipal Corporation',
            icon='trash'
        )
        UtilityType.objects.create(
            name='Road Maintenance',
            description='Potholes, road damage, street lighting issues',
            department='Public Works',
            icon='road'
        )
    
    if request.method == 'POST':
        form = ComplaintForm(request.POST, user=request.user)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.citizen = request.user
            complaint.save()
            
            messages.success(request, f'Complaint submitted successfully! Complaint ID: {complaint.complaint_id}')
            return redirect('utilities:my_complaints')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ComplaintForm(user=request.user)
    
    utility_types = UtilityType.objects.all()
    return render(request, 'utilities/citizen_submit_complaint.html', {
        'form': form,
        'utility_types': utility_types,
    })


@login_required
def my_complaints(request):
    """Citizen views their complaints"""
    if request.user.role != 'citizen':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    complaints = Complaint.objects.filter(citizen=request.user).order_by('-created_at')
    
    return render(request, 'utilities/my_complaints.html', {
        'complaints': complaints,
    })


@login_required
def complaint_detail(request, complaint_id):
    """View details of a specific complaint"""
    complaint = Complaint.objects.get(complaint_id=complaint_id)
    
    # Check if user has permission to view this complaint
    if request.user.role != 'citizen' or complaint.citizen != request.user:
        if request.user.role not in ['utility_officer', 'government_authority']:
            messages.error(request, 'Access denied.')
            return redirect('dashboard:dashboard')
    
    updates = complaint.updates.all().order_by('-created_at')
    
    return render(request, 'utilities/complaint_detail.html', {
        'complaint': complaint,
        'updates': updates,
    })


@login_required
def officer_dashboard(request):
    """Utility officer dashboard - view team assignments (NOT self-assignments)"""
    if request.user.role != 'utility_officer':
        messages.error(request, 'Access denied. Only utility officers can access this page.')
        return redirect('dashboard:dashboard')
    
    # Get complaints assigned to teams (not to individual officers)
    assigned_complaints = Complaint.objects.filter(
        status__in=['assigned', 'in_progress']
    ).order_by('-created_at')
    
    # Get pending complaints (not assigned to any team)
    pending_complaints = Complaint.objects.filter(
        status='pending'
    ).order_by('-created_at')
    
    # Get statistics (INT values - no .count() calls needed later)
    total_assigned = assigned_complaints.count()
    total_pending = pending_complaints.count()
    in_progress = assigned_complaints.filter(status='in_progress').count()
    resolved_today = Complaint.objects.filter(
        status='resolved',
        resolved_at__date=timezone.now().date()
    ).count()
    total_teams = UtilityTeam.objects.count()
    available_teams = UtilityTeam.objects.filter(is_available=True).count()
    
    context = {
        'assigned_complaints': assigned_complaints,
        'pending_complaints': pending_complaints,
        'total_assigned': total_assigned,
        'total_pending': total_pending,
        'in_progress': in_progress,
        'resolved_today': resolved_today,
        'total_teams': total_teams,
        'available_teams': available_teams,
    }
    
    return render(request, 'utilities/officer_dashboard.html', context)


@login_required
def assign_utility_team(request, complaint_id):
    """Assign a TEAM to a utility complaint (replaces self-assignment)"""
    if request.user.role != 'utility_officer':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    complaint = Complaint.objects.get(id=complaint_id)
    available_teams = UtilityTeam.objects.filter(is_available=True)
    
    if request.method == 'POST':
        team_id = request.POST.get('team_id')
        team = UtilityTeam.objects.get(id=team_id)
        
        # Create team assignment
        UtilityTeamAssignment.objects.create(
            complaint=complaint,
            team=team,
            assigned_by=request.user,
            status='assigned'
        )
        
        # Update complaint status
        complaint.status = 'assigned'
        complaint.assigned_officer = request.user  # Track which officer made assignment
        complaint.save()
        
        # Mark team as unavailable
        team.is_available = False
        team.save()
        
        messages.success(request, f'Team {team.name} assigned successfully!')
        return redirect('utilities:officer_dashboard')
    
    return render(request, 'utilities/assign_utility_team.html', {
        'complaint': complaint,
        'available_teams': available_teams,
    })


@login_required
def update_team_assignment_status(request, assignment_id):
    """Update utility team assignment status (replaces individual complaint status update)"""
    if request.user.role != 'utility_officer':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    assignment = UtilityTeamAssignment.objects.get(id=assignment_id)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        
        # Update assignment status
        assignment.status = status
        assignment.save()
        
        # Update complaint status
        complaint_status = 'resolved' if status == 'resolved' else status
        assignment.complaint.status = complaint_status
        assignment.complaint.save()
        
        # If resolved, mark team as available
        if status == 'resolved':
            assignment.team.is_available = True
            assignment.team.save()
        
        messages.success(request, f'Team status updated to {status}!')
        return redirect('utilities:officer_dashboard')
    
    return render(request, 'utilities/update_team_assignment_status.html', {
        'assignment': assignment,
    })
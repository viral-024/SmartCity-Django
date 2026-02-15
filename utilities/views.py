from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Complaint, UtilityType, ComplaintUpdate
from .forms import ComplaintForm

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
    """Utility officer dashboard - view assigned complaints"""
    if request.user.role != 'utility_officer':
        messages.error(request, 'Access denied. Only utility officers can access this page.')
        return redirect('dashboard:dashboard')
    
    # Get complaints assigned to this officer
    assigned_complaints = Complaint.objects.filter(assigned_officer=request.user).order_by('-created_at')
    
    # Get pending complaints (not assigned to anyone)
    pending_complaints = Complaint.objects.filter(
        status='pending',
        assigned_officer__isnull=True
    ).order_by('-created_at')
    
    # Get statistics
    total_assigned = assigned_complaints.count()
    total_pending = pending_complaints.count()
    in_progress = assigned_complaints.filter(status='in_progress').count()
    resolved_today = assigned_complaints.filter(
        status='resolved',
        resolved_at__date=timezone.now().date()
    ).count()
    
    context = {
        'assigned_complaints': assigned_complaints,
        'pending_complaints': pending_complaints,
        'total_assigned': total_assigned,
        'total_pending': total_pending,
        'in_progress': in_progress,
        'resolved_today': resolved_today,
    }
    
    return render(request, 'utilities/officer_dashboard.html', context)


@login_required
def assign_complaint(request, complaint_id):
    """Assign complaint to an officer"""
    if request.user.role != 'utility_officer':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    complaint = Complaint.objects.get(id=complaint_id)
    
    if request.method == 'POST':
        # Assign to current officer
        complaint.assigned_officer = request.user
        complaint.status = 'assigned'
        complaint.save()
        
        messages.success(request, f'Complaint {complaint.complaint_id} assigned to you successfully!')
        return redirect('utilities:officer_dashboard')
    
    return render(request, 'utilities/assign_complaint.html', {
        'complaint': complaint,
    })


@login_required
def update_complaint_status(request, complaint_id):
    """Update complaint status and add notes"""
    if request.user.role != 'utility_officer':
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    complaint = Complaint.objects.get(id=complaint_id)
    
    # Verify officer is assigned to this complaint
    if complaint.assigned_officer != request.user:
        messages.error(request, 'You are not assigned to this complaint.')
        return redirect('utilities:officer_dashboard')
    
    if request.method == 'POST':
        status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        # Update complaint status
        complaint.status = status
        complaint.save()
        
        # Add update note if provided
        if notes:
            ComplaintUpdate.objects.create(
                complaint=complaint,
                updated_by=request.user,
                update_text=notes
            )
        
        messages.success(request, 'Complaint status updated successfully!')
        return redirect('utilities:officer_dashboard')
    
    return render(request, 'utilities/update_complaint_status.html', {
        'complaint': complaint,
    })
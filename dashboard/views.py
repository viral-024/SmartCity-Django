from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from accounts.models import User

@login_required
def dashboard_redirect(request):
    """Redirect to role-specific dashboard"""
    role = request.user.role
    
    if role == 'citizen':
        return redirect('dashboard:citizen')
    elif role == 'government_authority':
        return redirect('dashboard:gov')
    elif role == 'utility_officer':
        return redirect('dashboard:utility')
    elif role == 'emergency_operator':
        return redirect('emergency:operator_dashboard')  # DIRECT REDIRECT
    elif role == 'vehicle_driver':
        return redirect('dashboard:driver')
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
    resolved_requests = request.user.emergency_requests.filter(status='resolved').count() + request.user.complaints.filter(status='resolved').count()
    total_requests = request.user.emergency_requests.count() + request.user.complaints.count()
    
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
    
    # Get system statistics (will populate later)
    total_users = User.objects.count()
    citizens = User.objects.filter(role='citizen').count()
    staff = total_users - citizens
    
    context = {
        'title': 'Government Dashboard',
        'user': request.user,
        'total_users': total_users,
        'citizens': citizens,
        'staff': staff,
        'total_emergencies': 0,
        'pending_emergencies': 0,
        'resolved_emergencies': 0,
    }
    return render(request, 'dashboard/gov.html', context)


@login_required
def utility_dashboard(request):
    """Utility officer dashboard"""
    if request.user.role != 'utility_officer':
        return redirect('dashboard:dashboard')
    
    context = {
        'title': 'Utility Dashboard',
        'user': request.user,
        'pending_complaints': 0,
        'in_progress': 0,
        'resolved_today': 0,
    }
    return render(request, 'dashboard/utility.html', context)


@login_required
def emergency_dashboard(request):
    """Emergency operator dashboard"""
    if request.user.role != 'emergency_operator':
        return redirect('dashboard:dashboard')
    
    context = {
        'title': 'Emergency Dashboard',
        'user': request.user,
        'active_emergencies': 0,
        'available_vehicles': 0,
        'on_scene': 0,
        'resolved_today': 0,
    }
    return render(request, 'dashboard/emergency.html', context)


@login_required
def driver_dashboard(request):
    """Vehicle driver dashboard"""
    if request.user.role != 'vehicle_driver':
        return redirect('dashboard:dashboard')
    
    context = {
        'title': 'Driver Dashboard',
        'user': request.user,
        'current_assignment': 'None',
        'status': 'Available',
        'completed_today': 0,
        'total_distance': '0 km',
    }
    return render(request, 'dashboard/driver.html', context)
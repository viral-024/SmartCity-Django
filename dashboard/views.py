from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

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
        return redirect('dashboard:emergency')
    elif role == 'vehicle_driver':
        return redirect('dashboard:driver')
    else:
        return redirect('accounts:profile')


@login_required
def citizen_dashboard(request):
    """Citizen dashboard"""
    if request.user.role != 'citizen':
        return redirect('dashboard:dashboard')
    
    context = {
        'title': 'Citizen Dashboard',
        'welcome_message': 'Welcome to your SmartCity EMS Portal',
        'quick_actions': [
            {'name': 'Report Emergency', 'icon': 'ambulance', 'url': '#'},
            {'name': 'Report Utility Issue', 'icon': 'tools', 'url': '#'},
            {'name': 'Track Requests', 'icon': 'history', 'url': '#'},
            {'name': 'Request History', 'icon': 'file-alt', 'url': '#'},
        ]
    }
    return render(request, 'dashboard/citizen.html', context)


@login_required
def gov_dashboard(request):
    """Government authority dashboard"""
    if request.user.role != 'government_authority':
        return redirect('dashboard:dashboard')
    
    context = {
        'title': 'Government Dashboard',
        'welcome_message': 'City Performance & Analytics',
        'stats': [
            {'label': 'Total Emergencies', 'value': '0', 'icon': 'ambulance', 'color': 'primary'},
            {'label': 'Avg Response Time', 'value': '0 min', 'icon': 'clock', 'color': 'success'},
            {'label': 'Pending Complaints', 'value': '0', 'icon': 'exclamation-triangle', 'color': 'warning'},
            {'label': 'Resolved Issues', 'value': '0', 'icon': 'check-circle', 'color': 'info'},
        ]
    }
    return render(request, 'dashboard/gov.html', context)


@login_required
def utility_dashboard(request):
    """Utility officer dashboard"""
    if request.user.role != 'utility_officer':
        return redirect('dashboard:dashboard')
    
    context = {
        'title': 'Utility Management',
        'welcome_message': 'Utility Complaint Management System',
        'stats': [
            {'label': 'Pending Complaints', 'value': '0', 'icon': 'list', 'color': 'warning'},
            {'label': 'In Progress', 'value': '0', 'icon': 'sync', 'color': 'primary'},
            {'label': 'Resolved Today', 'value': '0', 'icon': 'check', 'color': 'success'},
            {'label': 'Workers Assigned', 'value': '0', 'icon': 'users', 'color': 'info'},
        ]
    }
    return render(request, 'dashboard/utility.html', context)


@login_required
def emergency_dashboard(request):
    """Emergency operator dashboard"""
    if request.user.role != 'emergency_operator':
        return redirect('dashboard:dashboard')
    
    context = {
        'title': 'Emergency Operations',
        'welcome_message': 'Emergency Response Management',
        'stats': [
            {'label': 'Active Emergencies', 'value': '0', 'icon': 'bell', 'color': 'danger'},
            {'label': 'Available Vehicles', 'value': '0', 'icon': 'truck', 'color': 'success'},
            {'label': 'On Scene', 'value': '0', 'icon': 'map-marker', 'color': 'warning'},
            {'label': 'Resolved Today', 'value': '0', 'icon': 'check-circle', 'color': 'info'},
        ]
    }
    return render(request, 'dashboard/emergency.html', context)


@login_required
def driver_dashboard(request):
    """Vehicle driver dashboard"""
    if request.user.role != 'vehicle_driver':
        return redirect('dashboard:dashboard')
    
    context = {
        'title': 'Driver Dashboard',
        'welcome_message': 'Emergency Vehicle Operations',
        'stats': [
            {'label': 'Current Assignment', 'value': 'None', 'icon': 'map-marked', 'color': 'primary'},
            {'label': 'Status', 'value': 'Available', 'icon': 'check-circle', 'color': 'success'},
            {'label': 'Completed Today', 'value': '0', 'icon': 'tasks', 'color': 'info'},
            {'label': 'Total Distance', 'value': '0 km', 'icon': 'road', 'color': 'warning'},
        ]
    }
    return render(request, 'dashboard/driver.html', context)
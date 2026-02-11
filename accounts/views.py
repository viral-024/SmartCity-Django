from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CitizenRegistrationForm
from .models import User

def register_view(request):
    """Simple citizen registration"""
    if request.user.is_authenticated:
        return redirect('accounts:profile')
    
    if request.method == 'POST':
        form = CitizenRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Account created successfully! Welcome, {user.username}')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CitizenRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """Role-based login with access codes"""
    if request.user.is_authenticated:
        return redirect('accounts:profile')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role')
        access_code = request.POST.get('access_code', '').strip()
        
        # Define access codes for each role
        ACCESS_CODES = {
            'government_authority': '1111',
            'utility_officer': '2222',
            'emergency_operator': '3333',
            'vehicle_driver': '4444',
            'citizen': ''  # No code required for citizens
        }
        
        # Check access code
        if role != 'citizen' and access_code != ACCESS_CODES.get(role):
            messages.error(request, 'Invalid access code for this role.')
            return render(request, 'accounts/login.html', {
                'username': username,
                'role': role
            })
        
        # Authenticate user
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # Check if user's role matches selected role
            if user.role == role:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('accounts:profile')
            else:
                messages.error(request, f'This account is registered as {user.get_role_display()}, not {dict(User.ROLE_CHOICES)[role]}.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """Redirect to role-based dashboard"""
    return redirect('dashboard:dashboard')
from django.shortcuts import render

def gov_dashboard(request):
    return render(request, "dashboard/gov_dashboard.html")

def emergency_dashboard(request):
    return render(request, "dashboard/emergency_dashboard.html")

def utility_dashboard(request):
    return render(request, "dashboard/utility_dashboard.html")

def worker_dashboard(request):
    return render(request, "dashboard/worker_dashboard.html")

def citizen_dashboard(request):
    return render(request, "dashboard/citizen_dashboard.html")

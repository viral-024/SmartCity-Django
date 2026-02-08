from django.shortcuts import render, redirect

def login_view(request):
    if request.method == "POST":
        role = request.POST.get("role")

        if role == "government":
            return redirect("gov_dashboard")
        elif role == "emergency":
            return redirect("emergency_dashboard")
        elif role == "utility":
            return redirect("utility_dashboard")
        elif role == "worker":
            return redirect("worker_dashboard")
        elif role == "citizen":
            return redirect("citizen_dashboard")

    return render(request, "accounts/login.html")


def register_view(request):
    if request.method == "POST":
        return redirect("login")
    return render(request, "accounts/register.html")

# accounts/views.py
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required

def home(request):
    # If the user is authenticated, go to dashboard; otherwise, send to login.
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        return redirect('login')

# accounts/views.py
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect

def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)  # This creates the session.
            return redirect('dashboard')
        else:
            context = {'error': 'Invalid credentials'}
            return render(request, 'accounts/login.html', context)
    return render(request, 'accounts/login.html')


@login_required
def dashboard(request):
    return render(request, 'accounts/dashboard.html')

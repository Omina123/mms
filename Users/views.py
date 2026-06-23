
from urllib3 import request
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import*
from django.contrib.auth import authenticate, login

from Home import views

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            # Explicitly clear any existing session to force a fresh login
            from django.contrib.auth import logout
            logout(request) 
            
            messages.success(request, f"Account created for {user.username}! Please log in to continue.")
            
            # Ensure 'Login' matches the 'name=' in your urls.py
            return redirect('Login') 
        else:
            # If registration fails, it stays on the register page and shows errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = RegistrationForm()

    return render(request, 'register.html', {'form': form})

from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.contenttypes.models import ContentType
from .forms import LoginForm
from Home.models import ActivityLog

def get_client_ip(request):
    """Extract the client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def Login(request):
    # Already logged in? Redirect with role-based logic
    if request.user.is_authenticated:
        return redirect_user_by_role(request.user)

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username_or_phone = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username_or_phone, password=password)

            if user is not None:
                # --- SUCCESSFUL LOGIN ---
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name}!")

                # Log the activity
                ActivityLog.objects.create(
                    user=user,
                    action='LOGIN',
                    description=f"Successful login from IP {get_client_ip(request)}",
                    content_type=ContentType.objects.get_for_model(user),
                    object_id=user.id
                )

                # Handle 'next' parameter
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)

                # Redirect by role
                return redirect_user_by_role(user)

            else:
                # --- FAILED LOGIN ---
                # Log failed attempt (user doesn't exist or password wrong)
                # We'll try to get the user object if exists (to associate if possible)
                user_obj = None
                try:
                    # Attempt to find a user with that username/phone (case-insensitive)
                    user_obj = CustomUser.objects.get(username=username_or_phone)
                except CustomUser.DoesNotExist:
                    # Maybe it's a phone number? Adjust if your User model has a phone field.
                    # For simplicity, we'll just set user_obj = None
                    pass

                ActivityLog.objects.create(
                    user=user_obj,  # could be None
                    action='LOGIN',
                    description=f"Failed login attempt for username '{username_or_phone}' from IP {get_client_ip(request)}",
                    content_type=ContentType.objects.get_for_model(CustomUser),
                    object_id=user_obj.id if user_obj else 0
                )

                messages.error(request, "Invalid email/phone or password.")
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

def redirect_user_by_role(user):
    """
    Helper function to centralize redirection logic based on USER_TYPE_CHOICES.
    1: Admin, 2: Landlord, 3: Manager/Treasurer, 4: Tenant/Member
    """
    if user.user_type ==1 or user.is_superuser:
        return redirect('Admin')
    elif user.user_type == '3':
        return redirect('manager_dashboard')
    else:
        return redirect('Admin') # Fallback
# views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
from .models import CustomUser
def Logout(request):
    logout(request)
    #messages(request,'You have logged out  succesfully')
    return redirect('Login')

def is_admin(user):
    return user.is_superuser or user.user_type == '1'

@user_passes_test(is_admin)
def users_system(request):

    users = CustomUser.objects.all().order_by('-date_joined')

    return render(request, 'users_system.html', {
        'users': users
    })

@login_required
@user_passes_test(is_admin)
def edit_user_role(request, user_id):

    print("RECEIVED USER ID:", user_id)

    target_user = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'POST':

        new_role = request.POST.get('user_type')

        if new_role:
            target_user.user_type = new_role
            target_user.save()

            messages.success(
                request,
                f"{target_user.username} updated successfully."
            )

    return redirect('users_system')
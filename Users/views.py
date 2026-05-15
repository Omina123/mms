
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



def Login(request):
    # 1. Logic: Redirect already logged-in users based on their role
    if request.user.is_authenticated:
        return redirect_user_by_role(request.user)

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username_or_phone = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(request, username=username_or_phone, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name}!")
                
                # 2. Logic: Handle 'next' parameter safely
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                
                # 3. Logic: Dynamic Dashboard Routing
                return redirect_user_by_role(user)
            else:
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
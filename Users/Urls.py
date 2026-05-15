from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.Login, name='Login'),
    path('manage-users/edit-role/<int:user_id>/', views.edit_user_role, name='edit_user_role'),
    path('users_system', views.users_system, name='users_system'),
    path ('Logout',views.Logout, name='Logout')
]
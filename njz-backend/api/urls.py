from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # Public endpoints
    path('health/', views.health_check, name='health_check'),
    path('info/', views.api_info, name='api_info'),
    
    # Authentication endpoints
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/profile/', views.ProfileView.as_view(), name='profile'),
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='change_password'),
] 
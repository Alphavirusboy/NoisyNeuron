from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Web views
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('register/', views.SignUpView.as_view(), name='register'),  # Alias for signup
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # API views
    path('api/profile/', views.api_user_profile, name='api_profile'),
    path('api/profile/update/', views.api_update_profile, name='api_profile_update'),
]
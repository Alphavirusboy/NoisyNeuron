from django.urls import path
from . import views

app_name = 'premium'

urlpatterns = [
    # Premium features and pricing
    path('', views.premium_features, name='features'),
    
    # Subscription management
    path('subscription/', views.subscription_dashboard, name='subscription_dashboard'),
    path('checkout/', views.create_checkout_session, name='create_checkout'),
    path('success/', views.subscription_success, name='subscription_success'),
    path('cancel/', views.cancel_subscription, name='cancel_subscription'),
    path('upgrade/', views.upgrade_subscription, name='upgrade_subscription'),
    
    # Premium analytics
    path('analytics/', views.premium_analytics, name='analytics'),
    
    # API access
    path('api/', views.premium_api_access, name='api_access'),
    
    # Mock success for demo
    path('mock-success/', views.subscription_success, name='mock_success'),
]
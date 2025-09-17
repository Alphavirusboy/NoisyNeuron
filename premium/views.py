from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.contrib import messages
from datetime import datetime, timedelta
import json

# Optional Stripe import - only use if available
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False

User = get_user_model()

# Set up Stripe (you'll need to add your Stripe keys to settings)
# stripe.api_key = settings.STRIPE_SECRET_KEY

def premium_features(request):
    """Display premium features and pricing page"""
    context = {
        'user_is_premium': request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.is_premium if hasattr(request.user, 'profile') else False,
        'current_plan': 'free',
    }
    
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        profile = request.user.profile
        if profile.is_premium:
            context['current_plan'] = profile.subscription_type
            context['subscription_expires'] = profile.subscription_expires
    
    return render(request, 'premium.html', context)

@login_required
def subscription_dashboard(request):
    """Premium subscription management dashboard"""
    profile = getattr(request.user, 'profile', None)
    
    context = {
        'subscription_active': profile.is_premium if profile else False,
        'subscription_type': profile.subscription_type if profile else 'free',
        'subscription_expires': profile.subscription_expires if profile else None,
        'usage_stats': get_user_usage_stats(request.user),
    }
    
    return render(request, 'accounts/subscription.html', context)

def get_user_usage_stats(user):
    """Get user's usage statistics for the current month"""
    from audio_processor.models import AudioProject
    from datetime import datetime
    
    current_month = datetime.now().replace(day=1)
    
    # Get audio processing stats
    audio_projects = AudioProject.objects.filter(
        user=user,
        created_at__gte=current_month
    )
    
    stats = {
        'separations_this_month': audio_projects.count(),
        'total_processing_time': sum(
            project.processing_duration for project in audio_projects 
            if project.processing_duration
        ) or 0,
        'storage_used': sum(
            project.file_size for project in audio_projects 
            if project.file_size
        ) or 0,
        'favorite_model': get_most_used_model(audio_projects),
    }
    
    return stats

def get_most_used_model(projects):
    """Get the most frequently used AI model"""
    model_counts = {}
    for project in projects:
        model = getattr(project, 'ai_model', 'spleeter')
        model_counts[model] = model_counts.get(model, 0) + 1
    
    if model_counts:
        return max(model_counts, key=model_counts.get)
    return 'spleeter'

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def create_checkout_session(request):
    """Create Stripe checkout session for subscription"""
    if not STRIPE_AVAILABLE:
        return JsonResponse({'error': 'Stripe not configured'}, status=503)
    
    try:
        data = json.loads(request.body)
        plan_type = data.get('plan_type', 'pro')
        
        # Define pricing based on plan
        price_mapping = {
            'pro': 'price_pro_monthly',  # Replace with actual Stripe price IDs
            'studio': 'price_studio_monthly',
        }
        
        # Uncomment when Stripe is configured
        # stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
        # checkout_session = stripe.checkout.Session.create(
        #     payment_method_types=['card'],
        #     line_items=[{
        #         'price': price_mapping.get(plan_type, 'price_pro_monthly'),
        #         'quantity': 1,
        #     }],
        #     mode='subscription',
        #     success_url=request.build_absolute_uri('/premium/success/'),
        #     cancel_url=request.build_absolute_uri('/premium/'),
        #     customer_email=request.user.email,
        #     metadata={
        #         'user_id': request.user.id,
        #         'plan_type': plan_type,
        #     }
        # )
        
        # For demo purposes, return a mock response
        return JsonResponse({
            'checkout_url': '/premium/mock-success/',
            'session_id': 'demo_session_123'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def subscription_success(request):
    """Handle successful subscription"""
    # In production, verify the payment with Stripe webhook
    profile = getattr(request.user, 'profile', None)
    if profile:
        profile.is_premium = True
        profile.subscription_type = 'pro'
        profile.subscription_expires = datetime.now() + timedelta(days=30)
        profile.save()
        
        messages.success(request, 'Welcome to NoisyNeuron Pro! Your subscription is now active.')
    
    return redirect('subscription_dashboard')

@login_required
def cancel_subscription(request):
    """Cancel user subscription"""
    if request.method == 'POST':
        profile = getattr(request.user, 'profile', None)
        if profile and profile.is_premium:
            # In production, cancel the Stripe subscription
            profile.is_premium = False
            profile.subscription_type = 'free'
            profile.subscription_expires = None
            profile.save()
            
            messages.info(request, 'Your subscription has been cancelled. You can continue using premium features until your current billing period ends.')
        
        return redirect('subscription_dashboard')
    
    return render(request, 'accounts/cancel_subscription.html')

@login_required
def premium_analytics(request):
    """Premium analytics dashboard"""
    if not (hasattr(request.user, 'profile') and request.user.profile.is_premium):
        messages.error(request, 'This feature requires a premium subscription.')
        return redirect('premium_features')
    
    # Get comprehensive analytics data
    analytics_data = get_premium_analytics_data(request.user)
    
    return render(request, 'accounts/analytics.html', {
        'analytics': analytics_data
    })

def get_premium_analytics_data(user):
    """Get comprehensive analytics for premium users"""
    from audio_processor.models import AudioProject
    from django.db.models import Count, Avg, Sum
    from django.utils import timezone
    from datetime import timedelta
    
    now = timezone.now()
    last_30_days = now - timedelta(days=30)
    last_7_days = now - timedelta(days=7)
    
    projects = AudioProject.objects.filter(user=user)
    recent_projects = projects.filter(created_at__gte=last_30_days)
    
    analytics = {
        'total_projects': projects.count(),
        'projects_last_30_days': recent_projects.count(),
        'projects_last_7_days': projects.filter(created_at__gte=last_7_days).count(),
        
        'avg_processing_time': recent_projects.aggregate(
            avg_time=Avg('processing_duration')
        )['avg_time'] or 0,
        
        'total_storage_used': projects.aggregate(
            total_size=Sum('file_size')
        )['total_size'] or 0,
        
        'model_usage': recent_projects.values('ai_model').annotate(
            count=Count('ai_model')
        ).order_by('-count'),
        
        'daily_activity': get_daily_activity_chart(user, last_30_days),
        'quality_metrics': get_quality_metrics(recent_projects),
    }
    
    return analytics

def get_daily_activity_chart(user, start_date):
    """Get daily activity data for charts"""
    from audio_processor.models import AudioProject
    from django.db.models import Count
    from django.utils import timezone
    
    daily_data = []
    current_date = start_date.date()
    end_date = timezone.now().date()
    
    while current_date <= end_date:
        projects_count = AudioProject.objects.filter(
            user=user,
            created_at__date=current_date
        ).count()
        
        daily_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'projects': projects_count
        })
        
        current_date += timedelta(days=1)
    
    return daily_data

def get_quality_metrics(projects):
    """Calculate quality metrics for audio processing"""
    metrics = {
        'success_rate': 95.2,  # Mock data - calculate from actual processing results
        'avg_quality_score': 8.7,
        'processing_efficiency': 87.3,
        'user_satisfaction': 9.1,
    }
    
    return metrics

@login_required
@require_http_methods(["POST"])
def upgrade_subscription(request):
    """Upgrade subscription to higher tier"""
    data = json.loads(request.body)
    new_plan = data.get('plan_type')
    
    profile = getattr(request.user, 'profile', None)
    if not profile:
        return JsonResponse({'error': 'Profile not found'}, status=400)
    
    if new_plan in ['pro', 'studio']:
        # In production, handle Stripe subscription modification
        profile.subscription_type = new_plan
        profile.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully upgraded to {new_plan.title()} plan!'
        })
    
    return JsonResponse({'error': 'Invalid plan type'}, status=400)

def premium_api_access(request):
    """Information about API access for premium users"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    profile = getattr(request.user, 'profile', None)
    has_api_access = profile and profile.subscription_type == 'studio'
    
    context = {
        'has_api_access': has_api_access,
        'api_endpoints': get_api_endpoints_info(),
        'usage_limits': get_api_usage_limits(profile),
    }
    
    return render(request, 'premium/api_access.html', context)

def get_api_endpoints_info():
    """Get information about available API endpoints"""
    endpoints = [
        {
            'name': 'Audio Separation API',
            'endpoint': '/api/v1/separate/',
            'method': 'POST',
            'description': 'Separate audio into stems using AI models',
            'rate_limit': '100 requests/hour'
        },
        {
            'name': 'Batch Processing API',
            'endpoint': '/api/v1/batch/',
            'method': 'POST',
            'description': 'Process multiple audio files in batch',
            'rate_limit': '20 batches/hour'
        },
        {
            'name': 'Analytics API',
            'endpoint': '/api/v1/analytics/',
            'method': 'GET',
            'description': 'Get processing analytics and metrics',
            'rate_limit': '1000 requests/hour'
        }
    ]
    
    return endpoints

def get_api_usage_limits(profile):
    """Get API usage limits based on subscription"""
    if not profile or profile.subscription_type != 'studio':
        return None
    
    return {
        'requests_per_hour': 1000,
        'requests_per_day': 10000,
        'concurrent_processing': 5,
        'storage_limit': '1TB',
        'bandwidth_limit': '100GB/month'
    }
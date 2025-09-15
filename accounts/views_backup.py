from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import View, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny
import json
from datetime import datetime, timedelta
from django.utils import timezone

from .models import CustomUser, UserProfile
from .serializers import UserSerializer, UserProfileSerializer
from .forms import SignUpForm, ProfileUpdateForm, UserUpdateForm
from audio_processor.models import AudioProject


class SignUpView(CreateView):
    """User registration view."""
    model = CustomUser
    form_class = SignUpForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:profile')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.instance
        
        # Create user profile
        UserProfile.objects.create(user=user)
        
        # Create free subscription
        UserSubscription.objects.create(user=user, plan='free')
        
        # Log the user in
        login(self.request, user)
        
        # Track activity
        UserActivity.objects.create(
            user=user,
            activity_type='login',
            description='User registered and logged in',
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        
        messages.success(self.request, 'Welcome to NoisyNeuron! Your account has been created.')
        return response
    
    def get_client_ip(self):
        """Get client IP address."""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class LoginView(View):
    """Enhanced login view."""
    template_name = 'accounts/login.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, self.template_name)
    
    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        if email and password:
            user = authenticate(request, username=email, password=password)
            if user:
                login(request, user)
                
                # Set session expiry
                if not remember_me:
                    request.session.set_expiry(0)  # Browser session
                else:
                    request.session.set_expiry(1209600)  # 2 weeks
                
                # Track login activity
                UserActivity.objects.create(
                    user=user,
                    activity_type='login',
                    description='User logged in',
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                # Redirect to next or dashboard
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Please provide both email and password.')
        
        return render(request, self.template_name)
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LogoutView(View):
    """Logout view."""
    
    def post(self, request):
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return redirect('home')


@method_decorator(login_required, name='dispatch')
class ProfileView(DetailView):
    """User profile view."""
    model = UserProfile
    template_name = 'accounts/profile.html'
    context_object_name = 'profile'
    
    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user statistics
        context.update({
            'recent_projects': AudioProject.objects.filter(user=user)[:5],
            'total_projects': AudioProject.objects.filter(user=user).count(),
            'subscription': getattr(user, 'subscription', None),
            'recent_activities': UserActivity.objects.filter(user=user)[:10],
        })
        
        return context


@method_decorator(login_required, name='dispatch')
class ProfileUpdateView(UpdateView):
    """Update user profile."""
    model = UserProfile
    form_class = ProfileUpdateForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_form'] = UserUpdateForm(instance=self.request.user)
        return context
    
    def form_valid(self, form):
        user_form = UserUpdateForm(self.request.POST, instance=self.request.user)
        
        if user_form.is_valid():
            with transaction.atomic():
                user_form.save()
                form.save()
            messages.success(self.request, 'Profile updated successfully!')
        else:
            messages.error(self.request, 'Please correct the errors below.')
            return self.form_invalid(form)
        
        return super().form_valid(form)


# API Views
class UserViewSet(viewsets.ModelViewSet):
    """API viewset for user management."""
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Users can only access their own data
        return CustomUser.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get', 'patch'])
    def me(self, request):
        """Get or update current user."""
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        
        elif request.method == 'PATCH':
            serializer = self.get_serializer(request.user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get user statistics."""
        user = request.user
        profile = getattr(user, 'profile', None)
        
        stats = {
            'total_projects': AudioProject.objects.filter(user=user).count(),
            'completed_projects': AudioProject.objects.filter(user=user, status='completed').count(),
            'total_processing_time': profile.total_processing_time if profile else 0,
            'total_separations': profile.total_separations if profile else 0,
            'account_age_days': (timezone.now() - user.created_at).days,
            'subscription_plan': getattr(user.subscription, 'plan', 'free') if hasattr(user, 'subscription') else 'free',
        }
        
        return Response(stats)


class UserProfileViewSet(viewsets.ModelViewSet):
    """API viewset for user profiles."""
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AudioProjectViewSet(viewsets.ModelViewSet):
    """API viewset for audio projects."""
    queryset = AudioProject.objects.all()
    serializer_class = AudioProjectSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = AudioProject.objects.filter(user=self.request.user)
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by tags if provided
        tags = self.request.query_params.get('tags')
        if tags:
            tag_list = tags.split(',')
            queryset = queryset.filter(tags__overlap=tag_list)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        """Toggle project favorite status."""
        project = self.get_object()
        project.is_favorite = not project.is_favorite
        project.save()
        
        return Response({
            'is_favorite': project.is_favorite,
            'message': 'Project added to favorites' if project.is_favorite else 'Project removed from favorites'
        })
    
    @action(detail=True, methods=['post'])
    def toggle_public(self, request, pk=None):
        """Toggle project public status."""
        project = self.get_object()
        project.is_public = not project.is_public
        project.save()
        
        return Response({
            'is_public': project.is_public,
            'message': 'Project made public' if project.is_public else 'Project made private'
        })


@api_view(['POST'])
@permission_classes([AllowAny])
def api_register(request):
    """API endpoint for user registration."""
    try:
        data = request.data
        
        # Validate required fields
        if not all(k in data for k in ('email', 'password', 'username')):
            return Response(
                {'error': 'Email, password, and username are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user already exists
        if CustomUser.objects.filter(email=data['email']).exists():
            return Response(
                {'error': 'User with this email already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user
        with transaction.atomic():
            user = CustomUser.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password']
            )
            
            # Create profile
            UserProfile.objects.create(user=user)
            
            # Create subscription
            UserSubscription.objects.create(user=user, plan='free')
            
            # Create auth token
            token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'message': 'User created successfully',
            'token': token.key,
            'user_id': user.id,
            'email': user.email
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    """API endpoint for user login."""
    try:
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'error': 'Email and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(username=email, password=password)
        
        if user:
            token, created = Token.objects.get_or_create(user=user)
            
            # Track login activity
            UserActivity.objects.create(
                user=user,
                activity_type='login',
                description='API login',
                metadata={'api_version': 'v1'}
            )
            
            return Response({
                'token': token.key,
                'user_id': user.id,
                'email': user.email,
                'is_premium': user.is_premium
            })
        else:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_logout(request):
    """API endpoint for user logout."""
    try:
        # Delete the user's token
        Token.objects.filter(user=request.user).delete()
        
        return Response({'message': 'Logged out successfully'})
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

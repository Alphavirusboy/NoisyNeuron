from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

class CustomUser(AbstractUser):
    """Enhanced user model with additional fields for music professionals."""
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_premium = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    subscription_expires = models.DateTimeField(null=True, blank=True)
    
    # User preferences
    preferred_language = models.CharField(max_length=10, default='en')
    timezone = models.CharField(max_length=50, default='UTC')
    newsletter_subscribed = models.BooleanField(default=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email
    
    @property
    def is_subscription_active(self):
        """Check if premium subscription is active."""
        if not self.is_premium:
            return False
        if self.subscription_expires:
            return timezone.now() < self.subscription_expires
        return True

class UserProfile(models.Model):
    """Extended user profile with music-specific preferences."""
    
    SKILL_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('professional', 'Professional'),
    ]
    
    INSTRUMENT_CHOICES = [
        ('guitar', 'Guitar'),
        ('piano', 'Piano'),
        ('drums', 'Drums'),
        ('bass', 'Bass'),
        ('vocals', 'Vocals'),
        ('violin', 'Violin'),
        ('saxophone', 'Saxophone'),
        ('other', 'Other'),
    ]
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True, default='')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    # Music-related preferences
    primary_instrument = models.CharField(max_length=20, choices=INSTRUMENT_CHOICES, blank=True)
    skill_level = models.CharField(max_length=20, choices=SKILL_LEVELS, default='beginner')
    favorite_genres = models.JSONField(default=list, blank=True)
    
    # Usage statistics
    total_audio_processed = models.IntegerField(default=0)
    total_processing_time = models.FloatField(default=0.0)  # in seconds
    total_separations = models.IntegerField(default=0)
    last_activity = models.DateTimeField(auto_now=True)
    
    # Learning progress
    completed_tutorials = models.JSONField(default=list, blank=True)
    learning_goals = models.TextField(blank=True)
    practice_time_goal = models.IntegerField(default=30, validators=[MinValueValidator(0), MaxValueValidator(480)])  # minutes per day
    
    # Privacy settings
    public_profile = models.BooleanField(default=False)
    show_statistics = models.BooleanField(default=True)
    allow_collaboration = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email}'s Profile"
    
    @property
    def average_session_time(self):
        """Calculate average processing session time."""
        if self.total_separations == 0:
            return 0
        return self.total_processing_time / self.total_separations

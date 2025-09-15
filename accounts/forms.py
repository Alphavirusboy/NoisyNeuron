from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import CustomUser, UserProfile


class SignUpForm(UserCreationForm):
    """Enhanced user registration form."""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last name'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    
    def clean_email(self):
        """Validate email uniqueness."""
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email
    
    def save(self, commit=True):
        """Save user with email as username."""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    """Form for updating user information."""
    
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 'preferred_language',
            'timezone', 'newsletter_subscribed'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'preferred_language': forms.Select(attrs={'class': 'form-select'}),
            'timezone': forms.Select(attrs={'class': 'form-select'}),
            'newsletter_subscribed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_email(self):
        """Validate email uniqueness."""
        email = self.cleaned_data.get('email')
        if self.instance and self.instance.email == email:
            return email
        
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile."""
    
    GENRE_CHOICES = [
        ('rock', 'Rock'),
        ('pop', 'Pop'),
        ('jazz', 'Jazz'),
        ('classical', 'Classical'),
        ('electronic', 'Electronic'),
        ('hip-hop', 'Hip-Hop'),
        ('country', 'Country'),
        ('folk', 'Folk'),
        ('blues', 'Blues'),
        ('reggae', 'Reggae'),
        ('metal', 'Metal'),
        ('punk', 'Punk'),
        ('indie', 'Indie'),
        ('alternative', 'Alternative'),
        ('funk', 'Funk'),
        ('soul', 'Soul'),
        ('r&b', 'R&B'),
        ('world', 'World'),
        ('ambient', 'Ambient'),
        ('experimental', 'Experimental'),
    ]
    
    favorite_genres = forms.MultipleChoiceField(
        choices=GENRE_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'bio', 'avatar', 'primary_instrument', 'skill_level',
            'favorite_genres', 'learning_goals', 'practice_time_goal',
            'public_profile', 'show_statistics', 'allow_collaboration'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell us about yourself and your musical journey...'
            }),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'primary_instrument': forms.Select(attrs={'class': 'form-select'}),
            'skill_level': forms.Select(attrs={'class': 'form-select'}),
            'learning_goals': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'What are your musical learning goals?'
            }),
            'practice_time_goal': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 480
            }),
            'public_profile': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_statistics': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_collaboration': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_avatar(self):
        """Validate avatar upload."""
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            if avatar.size > 5 * 1024 * 1024:  # 5MB limit
                raise ValidationError("Avatar file size cannot exceed 5MB.")
            
            if not avatar.content_type.startswith('image/'):
                raise ValidationError("Avatar must be an image file.")
        
        return avatar


class PasswordChangeForm(forms.Form):
    """Form for changing password."""
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Current password'
        })
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'New password'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_current_password(self):
        """Validate current password."""
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise ValidationError("Current password is incorrect.")
        return current_password
    
    def clean(self):
        """Validate password confirmation."""
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password:
            if new_password != confirm_password:
                raise ValidationError("New passwords don't match.")
        
        return cleaned_data


class ProjectFilterForm(forms.Form):
    """Form for filtering audio projects."""
    STATUS_CHOICES = [
        ('', 'All Status'),
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    SORT_CHOICES = [
        ('-created_at', 'Newest First'),
        ('created_at', 'Oldest First'),
        ('title', 'Title A-Z'),
        ('-title', 'Title Z-A'),
        ('-duration', 'Longest First'),
        ('duration', 'Shortest First'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search projects...'
        })
    )
    
    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='-created_at',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    favorites_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    public_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
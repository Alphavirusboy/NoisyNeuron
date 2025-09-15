from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser, UserProfile


class UserSerializer(serializers.ModelSerializer):
    """Serializer for CustomUser model."""
    
    class Meta:
        model = CustomUser
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_premium', 'is_verified', 'subscription_expires',
            'preferred_language', 'timezone', 'newsletter_subscribed',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'is_verified')


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'password', 'password_confirm')
    
    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs
    
    def create(self, validated_data):
        """Create user with validated data."""
        validated_data.pop('password_confirm')
        user = CustomUser.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = (
            'bio', 'avatar', 'primary_instrument', 'skill_level', 'favorite_genres',
            'total_audio_processed', 'total_processing_time', 'total_separations',
            'last_activity', 'completed_tutorials', 'learning_goals', 'practice_time_goal',
            'public_profile', 'show_statistics', 'allow_collaboration',
            'created_at', 'updated_at', 'user_email', 'user_name'
        )
        read_only_fields = (
            'total_audio_processed', 'total_processing_time', 'total_separations',
            'last_activity', 'created_at', 'updated_at', 'user_email', 'user_name'
        )


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change."""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        """Validate password change data."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match.")
        return attrs
    
    def validate_old_password(self, value):
        """Validate old password."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
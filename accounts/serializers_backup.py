from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser, UserProfile


class UserSerializer(serializers.ModelSerializer):
    """Serializer for CustomUser model."""
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_premium', 'is_verified', 'preferred_language', 'timezone',
            'newsletter_subscribed', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'is_verified']
    
    def validate_email(self, value):
        """Validate email uniqueness."""
        if self.instance and self.instance.email == value:
            return value
        
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        
        return value


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user_email', 'user_name', 'bio', 'avatar',
            'primary_instrument', 'skill_level', 'favorite_genres',
            'total_audio_processed', 'total_processing_time', 'total_separations',
            'completed_tutorials', 'learning_goals', 'practice_time_goal',
            'public_profile', 'show_statistics', 'allow_collaboration',
            'last_activity', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_email', 'user_name', 'total_audio_processed',
            'total_processing_time', 'total_separations', 'last_activity',
            'created_at', 'updated_at'
        ]
    
    def validate_favorite_genres(self, value):
        """Validate favorite genres list."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Favorite genres must be a list.")
        
        valid_genres = [
            'rock', 'pop', 'jazz', 'classical', 'electronic', 'hip-hop',
            'country', 'folk', 'blues', 'reggae', 'metal', 'punk', 'indie',
            'alternative', 'funk', 'soul', 'r&b', 'world', 'ambient', 'experimental'
        ]
        
        for genre in value:
            if genre not in valid_genres:
                raise serializers.ValidationError(f"'{genre}' is not a valid genre.")
        
        return value


class AudioProjectSerializer(serializers.ModelSerializer):
    """Serializer for AudioProject model."""
    user_email = serializers.CharField(source='user.email', read_only=True)
    file_size_mb = serializers.SerializerMethodField()
    duration_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = AudioProject
        fields = [
            'id', 'user_email', 'title', 'description', 'original_filename',
            'file_size', 'file_size_mb', 'duration', 'duration_formatted',
            'separation_method', 'processing_options', 'status', 'progress',
            'stems', 'processing_time', 'quality_metrics', 'tags',
            'is_public', 'is_favorite', 'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'user_email', 'original_filename', 'file_size', 'duration',
            'stems', 'processing_time', 'quality_metrics', 'status', 'progress',
            'created_at', 'updated_at', 'completed_at'
        ]
    
    def get_file_size_mb(self, obj):
        """Convert file size to MB."""
        return round(obj.file_size / (1024 * 1024), 2)
    
    def get_duration_formatted(self, obj):
        """Format duration as MM:SS."""
        minutes = int(obj.duration // 60)
        seconds = int(obj.duration % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def validate_tags(self, value):
        """Validate tags list."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Tags must be a list.")
        
        if len(value) > 10:
            raise serializers.ValidationError("Maximum 10 tags allowed.")
        
        for tag in value:
            if not isinstance(tag, str) or len(tag) > 50:
                raise serializers.ValidationError("Each tag must be a string with maximum 50 characters.")
        
        return value


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for UserSubscription model."""
    user_email = serializers.CharField(source='user.email', read_only=True)
    usage_percentage = serializers.SerializerMethodField()
    storage_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSubscription
        fields = [
            'id', 'user_email', 'plan', 'status', 'monthly_processing_limit',
            'monthly_processing_used', 'usage_percentage', 'storage_limit',
            'storage_used', 'storage_percentage', 'started_at', 'expires_at'
        ]
        read_only_fields = [
            'id', 'user_email', 'monthly_processing_used', 'storage_used',
            'started_at'
        ]
    
    def get_usage_percentage(self, obj):
        """Calculate processing usage percentage."""
        if obj.monthly_processing_limit == 0:
            return 0
        return round((obj.monthly_processing_used / obj.monthly_processing_limit) * 100, 1)
    
    def get_storage_percentage(self, obj):
        """Calculate storage usage percentage."""
        if obj.storage_limit == 0:
            return 0
        return round((obj.storage_used / obj.storage_limit) * 100, 1)


class UserActivitySerializer(serializers.ModelSerializer):
    """Serializer for UserActivity model."""
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = UserActivity
        fields = [
            'id', 'user_email', 'activity_type', 'description', 'metadata',
            'created_at'
        ]
        read_only_fields = ['id', 'user_email', 'created_at']


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)
    
    def validate_new_password(self, value):
        """Validate new password."""
        validate_password(value)
        return value
    
    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("New passwords don't match.")
        
        return attrs


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'preferred_language', 'timezone'
        ]
    
    def validate_password(self, value):
        """Validate password."""
        validate_password(value)
        return value
    
    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match.")
        
        attrs.pop('confirm_password')
        return attrs
    
    def create(self, validated_data):
        """Create new user."""
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(password=password, **validated_data)
        return user
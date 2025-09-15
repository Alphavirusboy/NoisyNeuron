from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import AudioProject, AudioFile, SeparatedTrack, ProcessingJob

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_premium', 'created_at')

class AudioProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioProject
        fields = '__all__'

class AudioFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioFile
        fields = '__all__'

class SeparatedTrackSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeparatedTrack
        fields = '__all__'

class ProcessingJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessingJob
        fields = '__all__'

class AudioUploadSerializer(serializers.Serializer):
    audio_file = serializers.FileField()
    project_name = serializers.CharField(max_length=255, required=False)
    
class ProcessingOptionsSerializer(serializers.Serializer):
    separate_vocals = serializers.BooleanField(default=True)
    separate_drums = serializers.BooleanField(default=True)
    separate_bass = serializers.BooleanField(default=True)
    separate_other = serializers.BooleanField(default=True)
    markov_order = serializers.IntegerField(default=2, min_value=1, max_value=3)
    quality_level = serializers.ChoiceField(choices=['fast', 'balanced', 'high'], default='balanced')
    output_format = serializers.ChoiceField(choices=['wav', 'mp3', 'flac'], default='wav')

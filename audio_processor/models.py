from django.db import models
from django.contrib.auth import get_user_model
import uuid
import os

User = get_user_model()

class AudioProject(models.Model):
    """Model for audio processing projects"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audio_projects')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.user.username}"

class AudioFile(models.Model):
    """Model for uploaded audio files"""
    PROCESSING_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(AudioProject, on_delete=models.CASCADE, related_name='audio_files')
    original_filename = models.CharField(max_length=255)
    file = models.FileField(upload_to='audio/uploads/')
    file_size = models.BigIntegerField()  # in bytes
    duration = models.FloatField(null=True, blank=True)  # in seconds
    sample_rate = models.IntegerField(null=True, blank=True)
    channels = models.IntegerField(null=True, blank=True)
    format = models.CharField(max_length=10)  # mp3, wav, etc.
    
    # Processing status
    processing_status = models.CharField(max_length=20, choices=PROCESSING_STATUS_CHOICES, default='pending')
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)
    processing_error = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.original_filename} - {self.project.name}"
    
    @property
    def processing_duration(self):
        if self.processing_started_at and self.processing_completed_at:
            return (self.processing_completed_at - self.processing_started_at).total_seconds()
        return None

class SeparatedTrack(models.Model):
    """Model for separated audio tracks"""
    TRACK_TYPE_CHOICES = [
        ('vocals', 'Vocals'),
        ('drums', 'Drums'),
        ('bass', 'Bass'),
        ('piano', 'Piano'),
        ('guitar', 'Guitar'),
        ('other', 'Other'),
        ('accompaniment', 'Accompaniment'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audio_file = models.ForeignKey(AudioFile, on_delete=models.CASCADE, related_name='separated_tracks')
    track_type = models.CharField(max_length=20, choices=TRACK_TYPE_CHOICES)
    file = models.FileField(upload_to='audio/outputs/')
    confidence_score = models.FloatField(default=0.0)  # Markov model confidence
    file_size = models.BigIntegerField()
    
    # Markov model analysis results
    markov_patterns = models.JSONField(default=dict)  # Store pattern analysis
    separation_quality = models.FloatField(default=0.0)  # Quality score from Markov analysis
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['audio_file', 'track_type']
    
    def __str__(self):
        return f"{self.track_type} - {self.audio_file.original_filename}"

class ProcessingJob(models.Model):
    """Model for tracking processing jobs"""
    JOB_STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audio_file = models.ForeignKey(AudioFile, on_delete=models.CASCADE, related_name='processing_jobs')
    job_type = models.CharField(max_length=50)  # 'source_separation', 'markov_analysis', etc.
    status = models.CharField(max_length=20, choices=JOB_STATUS_CHOICES, default='queued')
    progress = models.IntegerField(default=0)  # 0-100
    
    # Job details
    parameters = models.JSONField(default=dict)  # Processing parameters
    result = models.JSONField(default=dict)  # Processing results
    error_message = models.TextField(blank=True)
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.job_type} - {self.audio_file.original_filename} ({self.status})"

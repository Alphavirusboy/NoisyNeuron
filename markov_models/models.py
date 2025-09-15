from django.db import models
from django.contrib.auth import get_user_model
import uuid
import numpy as np
import json

User = get_user_model()

class MarkovChain(models.Model):
    """Model for storing Markov chain data and patterns"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=2)  # Order of the Markov chain (n-gram)
    
    # Serialized transition matrix and states
    transition_matrix = models.JSONField(default=dict)
    states = models.JSONField(default=list)
    state_mapping = models.JSONField(default=dict)
    
    # Metadata
    training_samples = models.IntegerField(default=0)
    accuracy_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_trained = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Markov Chain: {self.name} (Order: {self.order})"

class AudioPattern(models.Model):
    """Model for storing audio pattern analysis"""
    PATTERN_TYPE_CHOICES = [
        ('spectral', 'Spectral Pattern'),
        ('temporal', 'Temporal Pattern'),
        ('harmonic', 'Harmonic Pattern'),
        ('rhythmic', 'Rhythmic Pattern'),
        ('timbral', 'Timbral Pattern'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audio_file = models.ForeignKey('audio_processor.AudioFile', on_delete=models.CASCADE, related_name='patterns')
    markov_chain = models.ForeignKey(MarkovChain, on_delete=models.CASCADE, related_name='patterns')
    
    pattern_type = models.CharField(max_length=20, choices=PATTERN_TYPE_CHOICES)
    pattern_data = models.JSONField(default=dict)  # Serialized pattern features
    confidence_score = models.FloatField(default=0.0)
    
    # Pattern statistics
    entropy = models.FloatField(default=0.0)
    complexity = models.FloatField(default=0.0)
    predictability = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['audio_file', 'pattern_type']
    
    def __str__(self):
        return f"{self.pattern_type} pattern for {self.audio_file.original_filename}"

class SeparationModel(models.Model):
    """Model for audio separation using Markov chains"""
    INSTRUMENT_CHOICES = [
        ('vocals', 'Vocals'),
        ('drums', 'Drums'),
        ('bass', 'Bass'),
        ('piano', 'Piano'),
        ('guitar', 'Guitar'),
        ('strings', 'Strings'),
        ('brass', 'Brass'),
        ('woodwinds', 'Woodwinds'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instrument_type = models.CharField(max_length=20, choices=INSTRUMENT_CHOICES)
    markov_chain = models.ForeignKey(MarkovChain, on_delete=models.CASCADE, related_name='separation_models')
    
    # Model parameters
    separation_threshold = models.FloatField(default=0.5)
    noise_reduction_factor = models.FloatField(default=0.1)
    spectral_smoothing = models.FloatField(default=0.2)
    
    # Performance metrics
    separation_accuracy = models.FloatField(default=0.0)
    snr_improvement = models.FloatField(default=0.0)  # Signal-to-noise ratio improvement
    processing_speed = models.FloatField(default=0.0)  # Seconds per minute of audio
    
    # Training data
    training_files_count = models.IntegerField(default=0)
    last_trained = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['instrument_type', 'markov_chain']
    
    def __str__(self):
        return f"Separation Model: {self.instrument_type} (Accuracy: {self.separation_accuracy:.2f})"

class MarkovAnalysis(models.Model):
    """Model for storing Markov analysis results"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audio_file = models.ForeignKey('audio_processor.AudioFile', on_delete=models.CASCADE, related_name='markov_analyses')
    separated_track = models.ForeignKey('audio_processor.SeparatedTrack', on_delete=models.CASCADE, null=True, blank=True)
    
    # Analysis results
    transition_probabilities = models.JSONField(default=dict)
    state_sequence = models.JSONField(default=list)
    pattern_likelihood = models.FloatField(default=0.0)
    anomaly_score = models.FloatField(default=0.0)
    
    # Quality metrics
    separation_quality = models.FloatField(default=0.0)
    confidence_interval = models.JSONField(default=dict)  # [lower, upper] bounds
    statistical_significance = models.FloatField(default=0.0)
    
    # Processing info
    analysis_duration = models.FloatField(default=0.0)  # seconds
    markov_order_used = models.IntegerField(default=2)
    feature_extraction_method = models.CharField(max_length=50, default='mfcc')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        track_info = f" - {self.separated_track.track_type}" if self.separated_track else ""
        return f"Markov Analysis: {self.audio_file.original_filename}{track_info}"

class TrainingData(models.Model):
    """Model for storing training data for Markov models"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    markov_chain = models.ForeignKey(MarkovChain, on_delete=models.CASCADE, related_name='training_data')
    
    # Training sample information
    source_file = models.CharField(max_length=255)
    instrument_label = models.CharField(max_length=50)
    feature_vector = models.JSONField(default=list)
    ground_truth = models.JSONField(default=dict)
    
    # Quality metrics
    sample_quality = models.FloatField(default=0.0)
    noise_level = models.FloatField(default=0.0)
    duration = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_validated = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Training Data: {self.source_file} ({self.instrument_label})"

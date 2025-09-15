from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()


class Instrument(models.Model):
    name = models.CharField(max_length=50)
    category = models.CharField(max_length=30)  # String, Wind, Percussion, etc.
    difficulty_level = models.IntegerField(default=1)  # 1-5 scale
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='instruments/', blank=True)
    
    def __str__(self):
        return self.name


class Chord(models.Model):
    name = models.CharField(max_length=20)  # e.g., "C", "Am", "Dm7"
    root_note = models.CharField(max_length=2)  # C, D, E, F, G, A, B
    chord_type = models.CharField(max_length=20)  # major, minor, 7th, sus4, etc.
    difficulty_level = models.IntegerField(default=1)  # 1-5 scale
    notes = models.JSONField()  # List of notes in the chord
    
    def __str__(self):
        return self.name


class ChordProgression(models.Model):
    name = models.CharField(max_length=100)
    chords = models.JSONField()  # List of chord names
    key = models.CharField(max_length=10)
    time_signature = models.CharField(max_length=10, default="4/4")
    tempo = models.IntegerField(default=120)  # BPM
    difficulty_level = models.IntegerField(default=1)
    
    def __str__(self):
        return f"{self.name} in {self.key}"


class InstrumentChord(models.Model):
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    chord = models.ForeignKey(Chord, on_delete=models.CASCADE)
    fingering = models.JSONField()  # Instrument-specific fingering data
    difficulty_level = models.IntegerField(default=1)
    alternative_fingerings = models.JSONField(default=list)
    audio_sample = models.FileField(upload_to='chord_samples/', blank=True)
    diagram_image = models.ImageField(upload_to='chord_diagrams/', blank=True)
    
    class Meta:
        unique_together = ['instrument', 'chord']
    
    def __str__(self):
        return f"{self.chord.name} on {self.instrument.name}"


class Song(models.Model):
    title = models.CharField(max_length=200)
    artist = models.CharField(max_length=100)
    key = models.CharField(max_length=10)
    tempo = models.IntegerField(default=120)
    time_signature = models.CharField(max_length=10, default="4/4")
    difficulty_level = models.IntegerField(default=1)
    chord_progression = models.ForeignKey(ChordProgression, on_delete=models.SET_NULL, null=True)
    audio_file = models.FileField(upload_to='songs/', blank=True)
    lyrics = models.TextField(blank=True)
    tabs = models.JSONField(default=dict)  # Tabs for different instruments
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} by {self.artist}"


class UserProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE, null=True, blank=True)
    chord = models.ForeignKey(Chord, on_delete=models.CASCADE, null=True, blank=True)
    skill_level = models.IntegerField(default=1)  # 1-5 scale
    practice_time = models.DurationField(default='00:00:00')
    last_practiced = models.DateTimeField(auto_now=True)
    mastery_percentage = models.FloatField(default=0.0)
    
    class Meta:
        unique_together = ['user', 'instrument', 'song', 'chord']


class LearningPath(models.Model):
    name = models.CharField(max_length=100)
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    description = models.TextField()
    target_skill_level = models.IntegerField(default=3)
    estimated_duration = models.DurationField()  # Expected time to complete
    songs = models.ManyToManyField(Song, through='LearningPathSong')
    chords = models.ManyToManyField(Chord, through='LearningPathChord')
    
    def __str__(self):
        return f"{self.name} for {self.instrument.name}"


class LearningPathSong(models.Model):
    learning_path = models.ForeignKey(LearningPath, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    order = models.IntegerField()
    is_required = models.BooleanField(default=True)


class LearningPathChord(models.Model):
    learning_path = models.ForeignKey(LearningPath, on_delete=models.CASCADE)
    chord = models.ForeignKey(Chord, on_delete=models.CASCADE)
    order = models.IntegerField()
    is_required = models.BooleanField(default=True)


class Practice(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE, null=True, blank=True)
    chord = models.ForeignKey(Chord, on_delete=models.CASCADE, null=True, blank=True)
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    duration = models.DurationField()
    accuracy_score = models.FloatField(default=0.0)  # 0-100
    tempo_achieved = models.IntegerField(default=60)
    notes = models.TextField(blank=True)
    recorded_audio = models.FileField(upload_to='practice_recordings/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} practiced {self.song or self.chord} on {self.instrument.name}"

from rest_framework import serializers
from .models import (
    Instrument, Chord, ChordProgression, InstrumentChord,
    Song, UserProgress, LearningPath, Practice
)


class InstrumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instrument
        fields = '__all__'


class ChordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chord
        fields = '__all__'


class ChordProgressionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChordProgression
        fields = '__all__'


class InstrumentChordSerializer(serializers.ModelSerializer):
    chord = ChordSerializer(read_only=True)
    instrument = InstrumentSerializer(read_only=True)
    
    class Meta:
        model = InstrumentChord
        fields = '__all__'


class SongSerializer(serializers.ModelSerializer):
    chord_progression = ChordProgressionSerializer(read_only=True)
    
    class Meta:
        model = Song
        fields = '__all__'


class UserProgressSerializer(serializers.ModelSerializer):
    instrument = InstrumentSerializer(read_only=True)
    song = SongSerializer(read_only=True)
    chord = ChordSerializer(read_only=True)
    
    class Meta:
        model = UserProgress
        fields = '__all__'


class LearningPathSerializer(serializers.ModelSerializer):
    instrument = InstrumentSerializer(read_only=True)
    songs = SongSerializer(many=True, read_only=True)
    chords = ChordSerializer(many=True, read_only=True)
    
    class Meta:
        model = LearningPath
        fields = '__all__'


class PracticeSerializer(serializers.ModelSerializer):
    instrument = InstrumentSerializer(read_only=True)
    song = SongSerializer(read_only=True)
    chord = ChordSerializer(read_only=True)
    
    class Meta:
        model = Practice
        fields = '__all__'

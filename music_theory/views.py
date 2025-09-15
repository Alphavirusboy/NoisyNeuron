from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import os
import tempfile

from .models import (
    Instrument, Chord, ChordProgression, InstrumentChord, 
    Song, UserProgress, LearningPath, Practice
)
from .theory_engine import EnhancedMusicTheoryEngine, PitchDetector, MetronomeEngine
from .serializers import (
    InstrumentSerializer, ChordSerializer, SongSerializer,
    UserProgressSerializer, LearningPathSerializer
)


class InstrumentViewSet(viewsets.ModelViewSet):
    queryset = Instrument.objects.all()
    serializer_class = InstrumentSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def learning_path(self, request, pk=None):
        """Get learning path for specific instrument."""
        instrument = self.get_object()
        skill_level = int(request.query_params.get('skill_level', 1))
        
        theory_engine = EnhancedMusicTheoryEngine()
        path = theory_engine.get_learning_path(instrument.name.lower(), skill_level)
        
        return Response(path)
    
    @action(detail=True, methods=['get'])
    def chord_library(self, request, pk=None):
        """Get chord library for specific instrument."""
        instrument = self.get_object()
        difficulty = request.query_params.get('difficulty')
        
        queryset = InstrumentChord.objects.filter(instrument=instrument)
        if difficulty:
            queryset = queryset.filter(difficulty_level__lte=int(difficulty))
        
        chords = []
        for ic in queryset:
            chords.append({
                'chord': ic.chord.name,
                'difficulty': ic.difficulty_level,
                'fingering': ic.fingering,
                'alternatives': ic.alternative_fingerings,
                'audio_sample': ic.audio_sample.url if ic.audio_sample else None,
                'diagram': ic.diagram_image.url if ic.diagram_image else None
            })
        
        return Response(chords)


class ChordViewSet(viewsets.ModelViewSet):
    queryset = Chord.objects.all()
    serializer_class = ChordSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def substitutions(self, request, pk=None):
        """Get chord substitutions for beginners."""
        chord = self.get_object()
        instrument = request.query_params.get('instrument', 'guitar')
        skill_level = int(request.query_params.get('skill_level', 1))
        
        theory_engine = EnhancedMusicTheoryEngine()
        substitutions = theory_engine.get_chord_substitutions(
            chord.name, instrument, skill_level
        )
        
        return Response(substitutions)


class SongViewSet(viewsets.ModelViewSet):
    queryset = Song.objects.all()
    serializer_class = SongSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def analyze_harmony(self, request):
        """Analyze uploaded song for chord progressions and key."""
        if 'audio_file' not in request.FILES:
            return Response(
                {'error': 'No audio file provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        audio_file = request.FILES['audio_file']
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            for chunk in audio_file.chunks():
                temp_file.write(chunk)
            temp_path = temp_file.name
        
        try:
            theory_engine = EnhancedMusicTheoryEngine()
            analysis = theory_engine.analyze_audio_harmony(temp_path)
            
            # Clean up temp file
            os.unlink(temp_path)
            
            return Response(analysis)
        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def beginner_version(self, request, pk=None):
        """Get beginner-friendly version of song with chord substitutions."""
        song = self.get_object()
        instrument = request.query_params.get('instrument', 'guitar')
        skill_level = int(request.query_params.get('skill_level', 1))
        
        theory_engine = EnhancedMusicTheoryEngine()
        
        # Get original chord progression
        if song.chord_progression and song.chord_progression.chords:
            original_chords = song.chord_progression.chords
        else:
            # Try to extract from song analysis
            return Response({'error': 'No chord progression available for this song'})
        
        beginner_version = {
            'original_song': {
                'title': song.title,
                'artist': song.artist,
                'key': song.key,
                'tempo': song.tempo,
                'chords': original_chords
            },
            'beginner_adaptations': []
        }
        
        # Get substitutions for each chord
        for chord in original_chords:
            substitutions = theory_engine.get_chord_substitutions(
                chord, instrument, skill_level
            )
            
            beginner_version['beginner_adaptations'].append({
                'original_chord': chord,
                'alternatives': substitutions,
                'recommended': substitutions[0] if substitutions else None
            })
        
        return Response(beginner_version)


class PracticeViewSet(viewsets.ModelViewSet):
    serializer_class = UserProgressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Practice.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def start_session(self, request):
        """Start a practice session."""
        song_id = request.data.get('song_id')
        chord_id = request.data.get('chord_id')
        instrument_id = request.data.get('instrument_id')
        
        if not instrument_id:
            return Response(
                {'error': 'Instrument is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session_data = {
            'user_id': request.user.id,
            'instrument_id': instrument_id,
            'song_id': song_id,
            'chord_id': chord_id,
            'start_time': request.data.get('start_time'),
            'tempo': request.data.get('tempo', 120),
            'practice_mode': request.data.get('practice_mode', 'normal')  # normal, slow, loop
        }
        
        # Store session in cache or database
        return Response({
            'session_id': f"practice_{request.user.id}_{song_id or chord_id}",
            'session_data': session_data
        })
    
    @action(detail=False, methods=['post'])
    def pitch_feedback(self, request):
        """Provide real-time pitch feedback."""
        # This would typically receive audio data from the frontend
        # For now, return mock data
        
        pitch_detector = PitchDetector()
        
        # In a real implementation, you'd process the audio buffer here
        feedback = {
            'detected_note': 'A4',
            'target_note': request.data.get('target_note', 'A4'),
            'cents_off': 5,  # How many cents off the target
            'in_tune': True,
            'confidence': 0.85
        }
        
        return Response(feedback)
    
    @action(detail=False, methods=['post'])
    def metronome(self, request):
        """Get metronome settings and click pattern."""
        metronome = MetronomeEngine()
        
        tempo = request.data.get('tempo', 120)
        time_sig_num = request.data.get('time_signature_numerator', 4)
        time_sig_den = request.data.get('time_signature_denominator', 4)
        
        metronome.set_tempo(tempo)
        metronome.set_time_signature(time_sig_num, time_sig_den)
        
        return Response({
            'tempo': metronome.tempo,
            'time_signature': metronome.time_signature,
            'beat_interval': metronome.get_beat_interval(),
            'click_pattern': metronome.generate_click_pattern()
        })


@method_decorator(csrf_exempt, name='dispatch')
class ChordRecommendationView(View):
    """AJAX endpoint for real-time chord recommendations."""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            chord = data.get('chord')
            instrument = data.get('instrument', 'guitar')
            skill_level = int(data.get('skill_level', 1))
            
            theory_engine = EnhancedMusicTheoryEngine()
            recommendations = theory_engine.get_chord_substitutions(
                chord, instrument, skill_level
            )
            
            return JsonResponse({
                'success': True,
                'recommendations': recommendations
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


@method_decorator(csrf_exempt, name='dispatch')
class KeyDetectionView(View):
    """AJAX endpoint for key detection from uploaded audio."""
    
    def post(self, request):
        try:
            if 'audio_file' not in request.FILES:
                return JsonResponse({
                    'success': False,
                    'error': 'No audio file provided'
                })
            
            audio_file = request.FILES['audio_file']
            
            # Process audio file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                for chunk in audio_file.chunks():
                    temp_file.write(chunk)
                temp_path = temp_file.name
            
            theory_engine = EnhancedMusicTheoryEngine()
            analysis = theory_engine.analyze_audio_harmony(temp_path)
            
            # Clean up
            os.unlink(temp_path)
            
            return JsonResponse({
                'success': True,
                'analysis': analysis
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class ProgressTrackingView(View):
    """Track user progress across different instruments and songs."""
    
    def get(self, request):
        progress = UserProgress.objects.filter(user=request.user)
        
        progress_data = {
            'total_practice_time': sum(p.practice_time.total_seconds() for p in progress),
            'instruments': {},
            'achievements': [],
            'current_level': 1
        }
        
        for p in progress:
            instrument_name = p.instrument.name
            if instrument_name not in progress_data['instruments']:
                progress_data['instruments'][instrument_name] = {
                    'skill_level': p.skill_level,
                    'mastery_percentage': 0,
                    'songs_learned': 0,
                    'chords_mastered': 0
                }
            
            progress_data['instruments'][instrument_name]['mastery_percentage'] = max(
                progress_data['instruments'][instrument_name]['mastery_percentage'],
                p.mastery_percentage
            )
        
        return JsonResponse(progress_data)


class LearningPathViewSet(viewsets.ModelViewSet):
    queryset = LearningPath.objects.all()
    serializer_class = LearningPathSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def enroll(self, request, pk=None):
        """Enroll user in a learning path."""
        learning_path = self.get_object()
        
        # Create progress entries for all songs and chords in the path
        for song in learning_path.songs.all():
            UserProgress.objects.get_or_create(
                user=request.user,
                instrument=learning_path.instrument,
                song=song,
                defaults={'skill_level': 1, 'mastery_percentage': 0.0}
            )
        
        for chord in learning_path.chords.all():
            UserProgress.objects.get_or_create(
                user=request.user,
                instrument=learning_path.instrument,
                chord=chord,
                defaults={'skill_level': 1, 'mastery_percentage': 0.0}
            )
        
        return Response({'message': 'Successfully enrolled in learning path'})
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Get user's progress in this learning path."""
        learning_path = self.get_object()
        
        song_progress = UserProgress.objects.filter(
            user=request.user,
            instrument=learning_path.instrument,
            song__in=learning_path.songs.all()
        )
        
        chord_progress = UserProgress.objects.filter(
            user=request.user,
            instrument=learning_path.instrument,
            chord__in=learning_path.chords.all()
        )
        
        total_items = learning_path.songs.count() + learning_path.chords.count()
        completed_items = sum(1 for p in song_progress if p.mastery_percentage >= 80) + \
                        sum(1 for p in chord_progress if p.mastery_percentage >= 80)
        
        progress_percentage = (completed_items / total_items * 100) if total_items > 0 else 0
        
        return Response({
            'progress_percentage': progress_percentage,
            'completed_items': completed_items,
            'total_items': total_items,
            'songs_progress': [
                {
                    'song': p.song.title,
                    'mastery': p.mastery_percentage,
                    'practice_time': str(p.practice_time)
                } for p in song_progress
            ],
            'chords_progress': [
                {
                    'chord': p.chord.name,
                    'mastery': p.mastery_percentage,
                    'practice_time': str(p.practice_time)
                } for p in chord_progress
            ]
        })

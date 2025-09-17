from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import os
import tempfile
import random
import time

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

def learn_view(request):
    """Music theory learning page view."""
    from django.shortcuts import render
    return render(request, 'music_theory/learn.html')

def practice_view(request):
    """Music theory practice page view."""
    from django.shortcuts import render
    return render(request, 'music_theory/practice.html')

# ============ ADVANCED TRAINING FEATURES ============

def interval_training_view(request):
    """Interval training page view."""
    return render(request, 'music_theory/interval_training.html')

def scale_practice_view(request):
    """Scale practice page view."""
    return render(request, 'music_theory/scale_practice.html')

def rhythm_training_view(request):
    """Rhythm training page view."""
    return render(request, 'music_theory/rhythm_training.html')

@api_view(['GET'])
@csrf_exempt
def generate_interval_exercise(request):
    """Generate a random interval exercise."""
    intervals = [
        {'name': 'Perfect Unison', 'semitones': 0, 'difficulty': 1},
        {'name': 'Minor Second', 'semitones': 1, 'difficulty': 3},
        {'name': 'Major Second', 'semitones': 2, 'difficulty': 2},
        {'name': 'Minor Third', 'semitones': 3, 'difficulty': 2},
        {'name': 'Major Third', 'semitones': 4, 'difficulty': 2},
        {'name': 'Perfect Fourth', 'semitones': 5, 'difficulty': 1},
        {'name': 'Tritone', 'semitones': 6, 'difficulty': 4},
        {'name': 'Perfect Fifth', 'semitones': 7, 'difficulty': 1},
        {'name': 'Minor Sixth', 'semitones': 8, 'difficulty': 3},
        {'name': 'Major Sixth', 'semitones': 9, 'difficulty': 3},
        {'name': 'Minor Seventh', 'semitones': 10, 'difficulty': 3},
        {'name': 'Major Seventh', 'semitones': 11, 'difficulty': 4},
        {'name': 'Perfect Octave', 'semitones': 12, 'difficulty': 1},
    ]
    
    difficulty = int(request.GET.get('difficulty', 2))
    filtered_intervals = [i for i in intervals if i['difficulty'] <= difficulty]
    
    interval = random.choice(filtered_intervals)
    root_note = random.choice(['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'])
    
    # Calculate MIDI note numbers (C4 = 60)
    root_midi = 60 + ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'].index(root_note)
    interval_midi = root_midi + interval['semitones']
    
    # Create multiple choice options
    options = [interval['name']]
    while len(options) < 4:
        random_interval = random.choice(intervals)
        if random_interval['name'] not in options:
            options.append(random_interval['name'])
    
    random.shuffle(options)
    correct_answer = interval['name']
    
    return JsonResponse({
        'interval': interval,
        'root_note': root_note,
        'root_midi': root_midi,
        'interval_midi': interval_midi,
        'options': options,
        'correct_answer': correct_answer,
        'exercise_id': int(time.time() * 1000)  # Unique ID
    })

@api_view(['GET'])
@csrf_exempt
def generate_scale_exercise(request):
    """Generate a random scale exercise."""
    scales = {
        'Major': [0, 2, 4, 5, 7, 9, 11],
        'Natural Minor': [0, 2, 3, 5, 7, 8, 10],
        'Harmonic Minor': [0, 2, 3, 5, 7, 8, 11],
        'Melodic Minor': [0, 2, 3, 5, 7, 9, 11],
        'Dorian': [0, 2, 3, 5, 7, 9, 10],
        'Phrygian': [0, 1, 3, 5, 7, 8, 10],
        'Lydian': [0, 2, 4, 6, 7, 9, 11],
        'Mixolydian': [0, 2, 4, 5, 7, 9, 10],
        'Locrian': [0, 1, 3, 5, 6, 8, 10],
        'Pentatonic Major': [0, 2, 4, 7, 9],
        'Pentatonic Minor': [0, 3, 5, 7, 10],
        'Blues': [0, 3, 5, 6, 7, 10],
    }
    
    difficulty = int(request.GET.get('difficulty', 1))
    
    if difficulty == 1:
        available_scales = ['Major', 'Natural Minor', 'Pentatonic Major', 'Pentatonic Minor']
    elif difficulty == 2:
        available_scales = ['Major', 'Natural Minor', 'Harmonic Minor', 'Dorian', 'Mixolydian', 'Pentatonic Major', 'Pentatonic Minor', 'Blues']
    else:
        available_scales = list(scales.keys())
    
    scale_name = random.choice(available_scales)
    scale_intervals = scales[scale_name]
    root_note = random.choice(['C', 'D', 'E', 'F', 'G', 'A', 'B'])
    
    # Calculate the scale notes
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    root_index = note_names.index(root_note)
    
    scale_notes = []
    for interval in scale_intervals:
        note_index = (root_index + interval) % 12
        scale_notes.append(note_names[note_index])
    
    # Create exercise - missing note
    missing_position = random.randint(0, len(scale_notes) - 1)
    correct_note = scale_notes[missing_position]
    
    # Create options
    options = [correct_note]
    while len(options) < 4:
        random_note = random.choice(note_names)
        if random_note not in options:
            options.append(random_note)
    
    random.shuffle(options)
    
    return JsonResponse({
        'scale_name': scale_name,
        'root_note': root_note,
        'scale_notes': scale_notes,
        'missing_position': missing_position,
        'correct_note': correct_note,
        'options': options,
        'exercise_id': int(time.time() * 1000)
    })

@api_view(['GET'])
@csrf_exempt  
def generate_rhythm_exercise(request):
    """Generate a random rhythm exercise."""
    rhythms = {
        'Whole Note': {'duration': 4, 'pattern': '◌', 'difficulty': 1},
        'Half Notes': {'duration': 2, 'pattern': '♩ ♩', 'difficulty': 1},
        'Quarter Notes': {'duration': 1, 'pattern': '♪ ♪ ♪ ♪', 'difficulty': 1},
        'Eighth Notes': {'duration': 0.5, 'pattern': '♫ ♫ ♫ ♫', 'difficulty': 2},
        'Mixed Quarter-Eighth': {'duration': [1, 0.5, 0.5, 1], 'pattern': '♪ ♫ ♪', 'difficulty': 2},
        'Sixteenth Notes': {'duration': 0.25, 'pattern': '♬ ♬ ♬ ♬', 'difficulty': 3},
        'Syncopated': {'duration': [0.5, 1, 0.5, 1], 'pattern': '♫ ♪ ♫ ♪', 'difficulty': 4},
        'Triplets': {'duration': 1/3, 'pattern': '♪♪♪ ♪♪♪', 'difficulty': 4},
    }
    
    difficulty = int(request.GET.get('difficulty', 1))
    time_signature = request.GET.get('time_signature', '4/4')
    
    filtered_rhythms = {k: v for k, v in rhythms.items() if v['difficulty'] <= difficulty}
    
    rhythm_name = random.choice(list(filtered_rhythms.keys()))
    rhythm_data = filtered_rhythms[rhythm_name]
    
    # Generate tempo between 60-120 BPM
    tempo = random.randint(60, 120)
    
    # Create multiple choice options
    options = [rhythm_name]
    while len(options) < 4:
        random_rhythm = random.choice(list(rhythms.keys()))
        if random_rhythm not in options:
            options.append(random_rhythm)
    
    random.shuffle(options)
    
    return JsonResponse({
        'rhythm_name': rhythm_name,
        'rhythm_pattern': rhythm_data['pattern'],
        'tempo': tempo,
        'time_signature': time_signature,
        'options': options,
        'correct_answer': rhythm_name,
        'exercise_id': int(time.time() * 1000)
    })

@api_view(['POST'])
@csrf_exempt
def submit_training_answer(request):
    """Submit and score a training exercise answer."""
    data = json.loads(request.body)
    
    exercise_type = data.get('exercise_type')
    user_answer = data.get('user_answer')
    correct_answer = data.get('correct_answer')
    exercise_id = data.get('exercise_id')
    response_time = data.get('response_time', 0)
    
    is_correct = user_answer == correct_answer
    
    # Calculate score based on correctness and speed
    base_score = 100 if is_correct else 0
    time_bonus = max(0, 50 - response_time) if is_correct else 0
    total_score = min(100, base_score + time_bonus)
    
    response_data = {
        'correct': is_correct,
        'score': total_score,
        'correct_answer': correct_answer,
        'feedback': get_feedback(exercise_type, is_correct, response_time)
    }
    
    return JsonResponse(response_data)

def get_feedback(exercise_type, is_correct, response_time):
    """Generate feedback for training exercises."""
    if is_correct:
        if response_time < 3:
            return "Excellent! Lightning fast recognition!"
        elif response_time < 5:
            return "Great job! Very good timing."
        elif response_time < 10:
            return "Correct! Keep practicing for faster recognition."
        else:
            return "Correct, but try to be quicker next time."
    else:
        feedback_map = {
            'interval': "Not quite right. Listen carefully to the interval size and try again.",
            'scale': "Incorrect. Review the scale pattern and note relationships.", 
            'rhythm': "Wrong rhythm. Try counting along with the beat pattern."
        }
        return feedback_map.get(exercise_type, "Not correct. Keep practicing!")

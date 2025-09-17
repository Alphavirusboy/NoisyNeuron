from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json

# Instrument data structure
INSTRUMENTS_DATA = {
    'piano': {
        'name': 'Piano',
        'icon': 'fas fa-music',
        'color': '#ef4444',
        'description': 'Master the piano with comprehensive lessons from beginner to advanced.',
        'total_lessons': 127,
        'categories': ['Basics', 'Scales', 'Chords', 'Classical', 'Jazz', 'Popular'],
        'lessons': [
            {
                'id': 1,
                'title': 'Piano Fundamentals',
                'category': 'Basics',
                'duration': '15 mins',
                'level': 'Beginner',
                'description': 'Learn proper hand position, posture, and basic key identification.',
                'video_url': None,
                'practice_exercises': ['Hand position practice', 'Key identification', 'Finger independence']
            },
            {
                'id': 2,
                'title': 'Reading Piano Notes',
                'category': 'Basics',
                'duration': '20 mins',
                'level': 'Beginner',
                'description': 'Master treble and bass clef note reading for piano.',
                'video_url': None,
                'practice_exercises': ['Treble clef notes', 'Bass clef notes', 'Both hands together']
            },
            {
                'id': 3,
                'title': 'Major Scales',
                'category': 'Scales',
                'duration': '25 mins',
                'level': 'Intermediate',
                'description': 'Learn all 12 major scales with proper fingering.',
                'video_url': None,
                'practice_exercises': ['C major scale', 'G major scale', 'F major scale']
            }
        ]
    },
    'guitar': {
        'name': 'Guitar',
        'icon': 'fas fa-guitar',
        'color': '#f59e0b',
        'description': 'Learn acoustic and electric guitar with step-by-step lessons.',
        'total_lessons': 98,
        'categories': ['Basics', 'Chords', 'Strumming', 'Fingerpicking', 'Lead', 'Songs'],
        'lessons': [
            {
                'id': 1,
                'title': 'Guitar Basics',
                'category': 'Basics',
                'duration': '12 mins',
                'level': 'Beginner',
                'description': 'Learn how to hold the guitar and basic finger positioning.',
                'video_url': None,
                'practice_exercises': ['Proper posture', 'Fret hand position', 'Pick holding']
            },
            {
                'id': 2,
                'title': 'First Chords',
                'category': 'Chords',
                'duration': '18 mins',
                'level': 'Beginner',
                'description': 'Master your first guitar chords: G, C, D, Em.',
                'video_url': None,
                'practice_exercises': ['G chord', 'C chord', 'D chord', 'Em chord']
            }
        ]
    },
    'drums': {
        'name': 'Drums',
        'icon': 'fas fa-drum',
        'color': '#10b981',
        'description': 'Develop rhythm and coordination with comprehensive drum lessons.',
        'total_lessons': 85,
        'categories': ['Basics', 'Beats', 'Fills', 'Styles', 'Advanced'],
        'lessons': [
            {
                'id': 1,
                'title': 'Drum Kit Setup',
                'category': 'Basics',
                'duration': '10 mins',
                'level': 'Beginner',
                'description': 'Learn about the drum kit components and proper setup.',
                'video_url': None,
                'practice_exercises': ['Kit identification', 'Stick grip', 'Basic posture']
            }
        ]
    },
    'violin': {
        'name': 'Violin',
        'icon': 'fas fa-violin',
        'color': '#3b82f6',
        'description': 'Master the violin with proper technique and beautiful repertoire.',
        'total_lessons': 73,
        'categories': ['Basics', 'Bowing', 'Scales', 'Pieces', 'Advanced'],
        'lessons': []
    },
    'bass': {
        'name': 'Bass Guitar',
        'icon': 'fas fa-guitar',
        'color': '#8b5cf6',
        'description': 'Learn bass guitar fundamentals and advanced techniques.',
        'total_lessons': 64,
        'categories': ['Basics', 'Technique', 'Scales', 'Grooves', 'Styles'],
        'lessons': []
    },
    'saxophone': {
        'name': 'Saxophone',
        'icon': 'fas fa-music',
        'color': '#ec4899',
        'description': 'Develop your saxophone skills from beginner to professional.',
        'total_lessons': 52,
        'categories': ['Basics', 'Technique', 'Scales', 'Jazz', 'Classical'],
        'lessons': []
    }
}

def instrument_list(request):
    """List all available instruments"""
    return render(request, 'instruments/instrument_list.html', {
        'instruments': INSTRUMENTS_DATA
    })

def piano_lessons(request):
    """Piano lessons page"""
    return render(request, 'instruments/instrument_detail.html', {
        'instrument': 'piano',
        'data': INSTRUMENTS_DATA['piano']
    })

def guitar_lessons(request):
    """Guitar lessons page"""
    return render(request, 'instruments/instrument_detail.html', {
        'instrument': 'guitar',
        'data': INSTRUMENTS_DATA['guitar']
    })

def drums_lessons(request):
    """Drums lessons page"""
    return render(request, 'instruments/instrument_detail.html', {
        'instrument': 'drums',
        'data': INSTRUMENTS_DATA['drums']
    })

def violin_lessons(request):
    """Violin lessons page"""
    return render(request, 'instruments/instrument_detail.html', {
        'instrument': 'violin',
        'data': INSTRUMENTS_DATA['violin']
    })

def bass_lessons(request):
    """Bass lessons page"""
    return render(request, 'instruments/instrument_detail.html', {
        'instrument': 'bass',
        'data': INSTRUMENTS_DATA['bass']
    })

def saxophone_lessons(request):
    """Saxophone lessons page"""
    return render(request, 'instruments/instrument_detail.html', {
        'instrument': 'saxophone',
        'data': INSTRUMENTS_DATA['saxophone']
    })

def lesson_detail(request, instrument, lesson_id):
    """Individual lesson page"""
    if instrument not in INSTRUMENTS_DATA:
        return render(request, '404.html', status=404)
    
    instrument_data = INSTRUMENTS_DATA[instrument]
    lesson = None
    
    for lesson_item in instrument_data['lessons']:
        if lesson_item['id'] == lesson_id:
            lesson = lesson_item
            break
    
    if not lesson:
        return render(request, '404.html', status=404)
    
    return render(request, 'instruments/lesson_detail.html', {
        'instrument': instrument,
        'instrument_data': instrument_data,
        'lesson': lesson
    })

@login_required
def practice_session(request, instrument):
    """Practice session for an instrument"""
    if instrument not in INSTRUMENTS_DATA:
        return render(request, '404.html', status=404)
    
    return render(request, 'instruments/practice_session.html', {
        'instrument': instrument,
        'data': INSTRUMENTS_DATA[instrument]
    })

@login_required
def progress_tracking(request, instrument):
    """Progress tracking for an instrument"""
    if instrument not in INSTRUMENTS_DATA:
        return render(request, '404.html', status=404)
    
    # Mock progress data - in real app this would come from database
    progress_data = {
        'lessons_completed': 12,
        'total_lessons': INSTRUMENTS_DATA[instrument]['total_lessons'],
        'practice_time': '45h 30m',
        'skill_level': 'Intermediate',
        'achievements': [
            'First Lesson Complete',
            'Week Streak',
            'Practice Master',
            'Chord Champion'
        ],
        'recent_activity': [
            {'date': '2025-09-16', 'activity': 'Completed Major Scales lesson', 'duration': '25 mins'},
            {'date': '2025-09-15', 'activity': 'Practice session - Chord progressions', 'duration': '30 mins'},
            {'date': '2025-09-14', 'activity': 'Completed Reading Notes lesson', 'duration': '20 mins'},
        ]
    }
    
    return render(request, 'instruments/progress_tracking.html', {
        'instrument': instrument,
        'data': INSTRUMENTS_DATA[instrument],
        'progress': progress_data
    })
import numpy as np
import librosa
from typing import List, Dict, Tuple, Optional, Any
import json
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ScaleType(Enum):
    """Enumeration of musical scales."""
    MAJOR = "major"
    MINOR = "minor"
    DORIAN = "dorian"
    PHRYGIAN = "phrygian"
    LYDIAN = "lydian"
    MIXOLYDIAN = "mixolydian"
    LOCRIAN = "locrian"
    HARMONIC_MINOR = "harmonic_minor"
    MELODIC_MINOR = "melodic_minor"
    PENTATONIC_MAJOR = "pentatonic_major"
    PENTATONIC_MINOR = "pentatonic_minor"
    BLUES = "blues"


@dataclass
class ChordAnalysis:
    """Data class for chord analysis results."""
    root: str
    quality: str
    intervals: List[int]
    notes: List[str]
    inversions: List[str]
    extensions: List[str]
    confidence: float
    difficulty: Dict[str, int]


@dataclass
class KeyAnalysis:
    """Data class for key analysis results."""
    key: str
    mode: str
    confidence: float
    scale_notes: List[str]
    relative_keys: List[str]
    parallel_modes: List[str]
    suggested_chords: List[str]


class EnhancedMusicTheoryEngine:
    """Enhanced music theory analysis engine with comprehensive harmonic analysis."""
    
    def __init__(self):
        """Initialize the enhanced music theory engine."""
        self.note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        self.note_to_number = {note: i for i, note in enumerate(self.note_names)}
        
        # Enhanced chord definitions with extensions and inversions
        self.chord_templates = {
            'major': [0, 4, 7],
            'minor': [0, 3, 7],
            'diminished': [0, 3, 6],
            'augmented': [0, 4, 8],
            'major7': [0, 4, 7, 11],
            'minor7': [0, 3, 7, 10],
            'dominant7': [0, 4, 7, 10],
            'diminished7': [0, 3, 6, 9],
            'minor7b5': [0, 3, 6, 10],
            'major9': [0, 4, 7, 11, 2],
            'minor9': [0, 3, 7, 10, 2],
            'dominant9': [0, 4, 7, 10, 2],
            'major11': [0, 4, 7, 11, 2, 5],
            'minor11': [0, 3, 7, 10, 2, 5],
            'dominant11': [0, 4, 7, 10, 2, 5],
            'major13': [0, 4, 7, 11, 2, 5, 9],
            'minor13': [0, 3, 7, 10, 2, 5, 9],
            'dominant13': [0, 4, 7, 10, 2, 5, 9],
            'sus2': [0, 2, 7],
            'sus4': [0, 5, 7],
            'add9': [0, 4, 7, 2],
            '6': [0, 4, 7, 9],
            'minor6': [0, 3, 7, 9],
        }
        
        # Scale definitions with all modes and variants
        self.scale_templates = {
            ScaleType.MAJOR: [0, 2, 4, 5, 7, 9, 11],
            ScaleType.MINOR: [0, 2, 3, 5, 7, 8, 10],
            ScaleType.DORIAN: [0, 2, 3, 5, 7, 9, 10],
            ScaleType.PHRYGIAN: [0, 1, 3, 5, 7, 8, 10],
            ScaleType.LYDIAN: [0, 2, 4, 6, 7, 9, 11],
            ScaleType.MIXOLYDIAN: [0, 2, 4, 5, 7, 9, 10],
            ScaleType.LOCRIAN: [0, 1, 3, 5, 6, 8, 10],
            ScaleType.HARMONIC_MINOR: [0, 2, 3, 5, 7, 8, 11],
            ScaleType.MELODIC_MINOR: [0, 2, 3, 5, 7, 9, 11],
            ScaleType.PENTATONIC_MAJOR: [0, 2, 4, 7, 9],
            ScaleType.PENTATONIC_MINOR: [0, 3, 5, 7, 10],
            ScaleType.BLUES: [0, 3, 5, 6, 7, 10],
        }
        
        # Enhanced key profiles for better key detection
        self.key_profiles = {
            'C': np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]),
            'C#': np.array([2.88, 6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29]),
            'D': np.array([2.29, 2.88, 6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66]),
            'D#': np.array([3.66, 2.29, 2.88, 6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39]),
            'E': np.array([2.39, 3.66, 2.29, 2.88, 6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19]),
            'F': np.array([5.19, 2.39, 3.66, 2.29, 2.88, 6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52]),
            'F#': np.array([2.52, 5.19, 2.39, 3.66, 2.29, 2.88, 6.35, 2.23, 3.48, 2.33, 4.38, 4.09]),
            'G': np.array([4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88, 6.35, 2.23, 3.48, 2.33, 4.38]),
            'G#': np.array([4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88, 6.35, 2.23, 3.48, 2.33]),
            'A': np.array([2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88, 6.35, 2.23, 3.48]),
            'A#': np.array([3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88, 6.35, 2.23]),
            'B': np.array([2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88, 6.35])
        }
        
        # Minor key profiles
        self.minor_key_profiles = {
            'Am': np.array([5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17, 6.15, 2.39, 2.60]),
            'A#m': np.array([2.60, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17, 6.15, 2.39]),
            'Bbm': np.array([2.60, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17, 6.15, 2.39]),
            'Bm': np.array([2.39, 2.60, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17, 6.15]),
            'Cm': np.array([6.15, 2.39, 2.60, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]),
            'C#m': np.array([3.17, 6.15, 2.39, 2.60, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34]),
            'Dm': np.array([3.34, 3.17, 6.15, 2.39, 2.60, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69]),
            'D#m': np.array([2.69, 3.34, 3.17, 6.15, 2.39, 2.60, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98]),
            'Ebm': np.array([2.69, 3.34, 3.17, 6.15, 2.39, 2.60, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98]),
            'Em': np.array([3.98, 2.69, 3.34, 3.17, 6.15, 2.39, 2.60, 5.38, 2.60, 3.53, 2.54, 4.75]),
            'Fm': np.array([4.75, 3.98, 2.69, 3.34, 3.17, 6.15, 2.39, 2.60, 5.38, 2.60, 3.53, 2.54]),
            'F#m': np.array([2.54, 4.75, 3.98, 2.69, 3.34, 3.17, 6.15, 2.39, 2.60, 5.38, 2.60, 3.53]),
            'Gm': np.array([3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17, 6.15, 2.39, 2.60, 5.38, 2.60]),
            'G#m': np.array([2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17, 6.15, 2.39, 2.60, 5.38])
        }
        
        # Common chord progressions with analysis
        self.common_progressions = {
            'I-V-vi-IV': {'roman': ['I', 'V', 'vi', 'IV'], 'description': 'Pop progression'},
            'vi-IV-I-V': {'roman': ['vi', 'IV', 'I', 'V'], 'description': 'Pop variation'},
            'I-vi-IV-V': {'roman': ['I', 'vi', 'IV', 'V'], 'description': '50s progression'},
            'ii-V-I': {'roman': ['ii', 'V', 'I'], 'description': 'Jazz turnaround'},
            'I-IV-V-I': {'roman': ['I', 'IV', 'V', 'I'], 'description': 'Classical cadence'},
            'vi-ii-V-I': {'roman': ['vi', 'ii', 'V', 'I'], 'description': 'Circle progression'},
            'I-bVII-IV-I': {'roman': ['I', 'bVII', 'IV', 'I'], 'description': 'Mixolydian progression'},
            'i-VI-III-VII': {'roman': ['i', 'VI', 'III', 'VII'], 'description': 'Minor progression'}
        }
        
        # Chord substitution rules for different instruments
        self.chord_substitutions = {
            'guitar': {
                'F': ['Fmaj7', 'Dm', 'C', 'Cadd9'],
                'Bm': ['D', 'G', 'Em', 'B7'],
                'F#m': ['Em', 'Am', 'Dm', 'F#'],
                'C#': ['C', 'D', 'Em', 'Cadd9'],
                'F#': ['G', 'F', 'Em', 'E'],
                'Bb': ['Am', 'C', 'F', 'Gm'],
            },
            'piano': {
                'F#': ['G', 'F', 'Em'],
                'C#': ['C', 'D', 'Db'],
                'Bb': ['Am', 'C', 'Cm'],
                'Db': ['C', 'D', 'Dm'],
                'Eb': ['Em', 'D', 'F'],
            },
            'ukulele': {
                'F': ['C', 'Am', 'Dm', 'G'],
                'Bm': ['Em', 'Am', 'Dm', 'G'],
                'E': ['Em', 'C', 'Am', 'F'],
                'Bb': ['C', 'F', 'Am', 'Gm'],
            }
        }
        
        # Difficulty ratings for chords by instrument (1-10 scale)
        self.chord_difficulty = {
            'guitar': {
                'C': 2, 'Am': 2, 'F': 8, 'G': 3, 'Em': 1, 'Dm': 3,
                'A': 3, 'E': 2, 'B': 6, 'Bm': 7, 'F#m': 6, 'C#': 8,
                'Cm': 4, 'Gm': 4, 'D': 2, 'A7': 3, 'B7': 4, 'E7': 2
            },
            'piano': {
                'C': 1, 'Am': 1, 'F': 2, 'G': 1, 'Em': 2, 'Dm': 2,
                'A': 2, 'E': 3, 'B': 4, 'Bm': 3, 'F#m': 4, 'C#': 5,
                'Cm': 3, 'Gm': 3, 'D': 2, 'Bb': 3, 'Eb': 4, 'Ab': 5
            },
            'ukulele': {
                'C': 1, 'Am': 1, 'F': 2, 'G': 2, 'Em': 3, 'Dm': 2,
                'A': 2, 'E': 4, 'B': 5, 'Bm': 4, 'F#m': 5, 'C#': 6,
                'Cm': 3, 'Gm': 3, 'D': 2, 'A7': 2, 'G7': 1, 'C7': 2
            }
        }
    CHORD_DIFFICULTY = {
        'guitar': {
            'C': 1, 'G': 1, 'Am': 1, 'Em': 1, 'D': 2, 'A': 2,
            'Dm': 2, 'E': 2, 'F': 4, 'Bm': 4, 'B': 3, 'F#m': 4,
            'C#': 5, 'F#': 5, 'Bb': 3, 'Gm': 3
        },
        'piano': {
            'C': 1, 'G': 1, 'F': 1, 'Am': 1, 'Dm': 1, 'Em': 2,
            'D': 2, 'A': 2, 'E': 2, 'Bb': 3, 'F#': 4, 'C#': 4,
            'Bm': 2, 'F#m': 3, 'Gm': 2
        },
        'ukulele': {
            'C': 1, 'F': 1, 'G': 1, 'Am': 1, 'Dm': 2, 'Em': 2,
            'A': 2, 'D': 2, 'E': 3, 'Bm': 4, 'F#m': 4, 'B': 3,
            'F#': 4, 'C#': 5, 'Bb': 3
        }
    }
    
    def __init__(self):
        """Initialize the enhanced music theory engine."""
        self.note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        self.note_to_number = {note: i for i, note in enumerate(self.note_names)}
        
        # Enhanced chord definitions with extensions and inversions
        self.chord_templates = {
            'major': [0, 4, 7],
            'minor': [0, 3, 7],
            'diminished': [0, 3, 6],
            'augmented': [0, 4, 8],
            'major7': [0, 4, 7, 11],
            'minor7': [0, 3, 7, 10],
            'dominant7': [0, 4, 7, 10],
            'diminished7': [0, 3, 6, 9],
            'minor7b5': [0, 3, 6, 10],
            'major9': [0, 4, 7, 11, 2],
            'minor9': [0, 3, 7, 10, 2],
            'dominant9': [0, 4, 7, 10, 2],
            'major11': [0, 4, 7, 11, 2, 5],
            'minor11': [0, 3, 7, 10, 2, 5],
            'dominant11': [0, 4, 7, 10, 2, 5],
            'major13': [0, 4, 7, 11, 2, 5, 9],
            'minor13': [0, 3, 7, 10, 2, 5, 9],
            'dominant13': [0, 4, 7, 10, 2, 5, 9],
            'sus2': [0, 2, 7],
            'sus4': [0, 5, 7],
            'add9': [0, 4, 7, 2],
            '6': [0, 4, 7, 9],
            'minor6': [0, 3, 7, 9],
        }
        
        # Scale definitions with all modes and variants
        self.scale_templates = {
            ScaleType.MAJOR: [0, 2, 4, 5, 7, 9, 11],
            ScaleType.MINOR: [0, 2, 3, 5, 7, 8, 10],
            ScaleType.DORIAN: [0, 2, 3, 5, 7, 9, 10],
            ScaleType.PHRYGIAN: [0, 1, 3, 5, 7, 8, 10],
            ScaleType.LYDIAN: [0, 2, 4, 6, 7, 9, 11],
            ScaleType.MIXOLYDIAN: [0, 2, 4, 5, 7, 9, 10],
            ScaleType.LOCRIAN: [0, 1, 3, 5, 6, 8, 10],
            ScaleType.HARMONIC_MINOR: [0, 2, 3, 5, 7, 8, 11],
            ScaleType.MELODIC_MINOR: [0, 2, 3, 5, 7, 9, 11],
            ScaleType.PENTATONIC_MAJOR: [0, 2, 4, 7, 9],
            ScaleType.PENTATONIC_MINOR: [0, 3, 5, 7, 10],
            ScaleType.BLUES: [0, 3, 5, 6, 7, 10],
        }
        
        # Enhanced key profiles for better key detection
        self.key_profiles = {
            'C': np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]),
            'C#': np.array([2.88, 6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29]),
            'D': np.array([2.29, 2.88, 6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66]),
            'D#': np.array([3.66, 2.29, 2.88, 6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39]),
            'E': np.array([2.39, 3.66, 2.29, 2.88, 6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19]),
            'F': np.array([5.19, 2.39, 3.66, 2.29, 2.88, 6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52]),
            'F#': np.array([2.52, 5.19, 2.39, 3.66, 2.29, 2.88, 6.35, 2.23, 3.48, 2.33, 4.38, 4.09]),
            'G': np.array([4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88, 6.35, 2.23, 3.48, 2.33, 4.38]),
            'G#': np.array([4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88, 6.35, 2.23, 3.48, 2.33]),
            'A': np.array([2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88, 6.35, 2.23, 3.48]),
            'A#': np.array([3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88, 6.35, 2.23]),
            'B': np.array([2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88, 6.35])
        }
        
        # Minor key profiles
        self.minor_key_profiles = {
            'Am': np.array([5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17, 6.15, 2.39, 2.60]),
            'A#m': np.array([2.60, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17, 6.15, 2.39]),
            'Bbm': np.array([2.60, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17, 6.15, 2.39]),
            'Bm': np.array([2.39, 2.60, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17, 6.15]),
            'Cm': np.array([6.15, 2.39, 2.60, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]),
            'C#m': np.array([3.17, 6.15, 2.39, 2.60, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34]),
            'Dm': np.array([3.34, 3.17, 6.15, 2.39, 2.60, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69]),
            'D#m': np.array([2.69, 3.34, 3.17, 6.15, 2.39, 2.60, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98]),
            'Ebm': np.array([2.69, 3.34, 3.17, 6.15, 2.39, 2.60, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98]),
            'Em': np.array([3.98, 2.69, 3.34, 3.17, 6.15, 2.39, 2.60, 5.38, 2.60, 3.53, 2.54, 4.75]),
            'Fm': np.array([4.75, 3.98, 2.69, 3.34, 3.17, 6.15, 2.39, 2.60, 5.38, 2.60, 3.53, 2.54]),
            'F#m': np.array([2.54, 4.75, 3.98, 2.69, 3.34, 3.17, 6.15, 2.39, 2.60, 5.38, 2.60, 3.53]),
            'Gm': np.array([3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17, 6.15, 2.39, 2.60, 5.38, 2.60]),
            'G#m': np.array([2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17, 6.15, 2.39, 2.60, 5.38])
        }
        
        # Common chord progressions with analysis
        self.common_progressions = {
            'I-V-vi-IV': {'roman': ['I', 'V', 'vi', 'IV'], 'description': 'Pop progression'},
            'vi-IV-I-V': {'roman': ['vi', 'IV', 'I', 'V'], 'description': 'Pop variation'},
            'I-vi-IV-V': {'roman': ['I', 'vi', 'IV', 'V'], 'description': '50s progression'},
            'ii-V-I': {'roman': ['ii', 'V', 'I'], 'description': 'Jazz turnaround'},
            'I-IV-V-I': {'roman': ['I', 'IV', 'V', 'I'], 'description': 'Classical cadence'},
            'vi-ii-V-I': {'roman': ['vi', 'ii', 'V', 'I'], 'description': 'Circle progression'},
            'I-bVII-IV-I': {'roman': ['I', 'bVII', 'IV', 'I'], 'description': 'Mixolydian progression'},
            'i-VI-III-VII': {'roman': ['i', 'VI', 'III', 'VII'], 'description': 'Minor progression'}
        }
        
        # Chord substitution rules for different instruments
        self.chord_substitutions = {
            'guitar': {
                'F': ['Fmaj7', 'Dm', 'C', 'Cadd9'],
                'Bm': ['D', 'G', 'Em', 'B7'],
                'F#m': ['Em', 'Am', 'Dm', 'F#'],
                'C#': ['C', 'D', 'Em', 'Cadd9'],
                'F#': ['G', 'F', 'Em', 'E'],
                'Bb': ['Am', 'C', 'F', 'Gm'],
            },
            'piano': {
                'F#': ['G', 'F', 'Em'],
                'C#': ['C', 'D', 'Db'],
                'Bb': ['Am', 'C', 'Cm'],
                'Db': ['C', 'D', 'Dm'],
                'Eb': ['Em', 'D', 'F'],
            },
            'ukulele': {
                'F': ['C', 'Am', 'Dm', 'G'],
                'Bm': ['Em', 'Am', 'Dm', 'G'],
                'E': ['Em', 'C', 'Am', 'F'],
                'Bb': ['C', 'F', 'Am', 'Gm'],
            }
        }
        
        # Difficulty ratings for chords by instrument (1-10 scale)
        self.chord_difficulty = {
            'guitar': {
                'C': 2, 'Am': 2, 'F': 8, 'G': 3, 'Em': 1, 'Dm': 3,
                'A': 3, 'E': 2, 'B': 6, 'Bm': 7, 'F#m': 6, 'C#': 8,
                'Cm': 4, 'Gm': 4, 'D': 2, 'A7': 3, 'B7': 4, 'E7': 2
            },
            'piano': {
                'C': 1, 'Am': 1, 'F': 2, 'G': 1, 'Em': 2, 'Dm': 2,
                'A': 2, 'E': 3, 'B': 4, 'Bm': 3, 'F#m': 4, 'C#': 5,
                'Cm': 3, 'Gm': 3, 'D': 2, 'Bb': 3, 'Eb': 4, 'Ab': 5
            },
            'ukulele': {
                'C': 1, 'Am': 1, 'F': 2, 'G': 2, 'Em': 3, 'Dm': 2,
                'A': 2, 'E': 4, 'B': 5, 'Bm': 4, 'F#m': 5, 'C#': 6,
                'Cm': 3, 'Gm': 3, 'D': 2, 'A7': 2, 'G7': 1, 'C7': 2
            }
        }
    
    def analyze_audio_harmony(self, audio_path: str) -> Dict:
        """
        Analyze audio file to extract harmonic information including
        key, chord progressions, and tempo.
        """
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=22050)
            
            # Extract features
            chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=1024)
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            
            # Analyze key
            key_analysis = self._enhanced_key_detection(chroma)
            
            # Analyze chord progression
            chord_progression = self._analyze_chord_progression(chroma, beats, sr)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(key_analysis, chord_progression)
            
            return {
                'key_analysis': key_analysis.__dict__ if hasattr(key_analysis, '__dict__') else key_analysis,
                'chord_progression': chord_progression,
                'tempo': float(tempo),
                'time_signature': self._estimate_time_signature(y, sr),
                'recommendations': recommendations,
                'harmonic_complexity': self._calculate_harmonic_complexity(chord_progression),
                'mood_analysis': self._analyze_mood(key_analysis, tempo, chord_progression)
            }
            
        except Exception as e:
            logger.error(f"Error in harmonic analysis: {str(e)}")
            return {'error': str(e)}
    
    def _enhanced_key_detection(self, chroma: np.ndarray) -> KeyAnalysis:
        """Enhanced key detection using multiple algorithms."""
        # Average chroma over time
        avg_chroma = np.mean(chroma, axis=1)
        
        # Normalize
        avg_chroma = avg_chroma / (np.sum(avg_chroma) + 1e-8)
        
        # Test against major keys
        major_correlations = {}
        for key, profile in self.key_profiles.items():
            profile_norm = profile / np.sum(profile)
            correlation = np.corrcoef(avg_chroma, profile_norm)[0, 1]
            if not np.isnan(correlation):
                major_correlations[key] = correlation
        
        # Test against minor keys
        minor_correlations = {}
        for key, profile in self.minor_key_profiles.items():
            profile_norm = profile / np.sum(profile)
            correlation = np.corrcoef(avg_chroma, profile_norm)[0, 1]
            if not np.isnan(correlation):
                minor_correlations[key] = correlation
        
        # Find best matches
        best_major = max(major_correlations.items(), key=lambda x: x[1]) if major_correlations else ('C', 0.0)
        best_minor = max(minor_correlations.items(), key=lambda x: x[1]) if minor_correlations else ('Am', 0.0)
        
        # Determine final key
        if best_major[1] > best_minor[1]:
            key, confidence = best_major
            mode = 'major'
            scale_notes = self._get_scale_notes(key, ScaleType.MAJOR)
        else:
            key, confidence = best_minor
            mode = 'minor'
            scale_notes = self._get_scale_notes(key.replace('m', ''), ScaleType.MINOR)
        
        # Generate related keys and chords
        relative_keys = self._find_relative_keys(key, mode)
        parallel_modes = self._find_parallel_modes(key, mode)
        suggested_chords = self._suggest_chords_for_key(key, mode)
        
        return KeyAnalysis(
            key=key,
            mode=mode,
            confidence=float(confidence),
            scale_notes=scale_notes,
            relative_keys=relative_keys,
            parallel_modes=parallel_modes,
            suggested_chords=suggested_chords
        )
    
    def _analyze_chord_progression(self, chroma: np.ndarray, beats: np.ndarray, sr: int) -> List[Dict[str, Any]]:
        """Analyze chord progression over time."""
        chord_progression = []
        
        # Segment audio by beats
        beat_times = librosa.frames_to_time(beats, sr=sr)
        
        for i in range(min(len(beat_times) - 1, 20)):  # Limit to first 20 beats for performance
            start_frame = librosa.time_to_frames(beat_times[i], sr=sr, hop_length=1024)
            end_frame = librosa.time_to_frames(beat_times[i + 1], sr=sr, hop_length=1024)
            
            if end_frame > start_frame:
                # Extract chroma for this segment
                segment_chroma = np.mean(chroma[:, start_frame:end_frame], axis=1)
                
                # Detect chord
                chord_info = self._detect_chord_from_chroma(segment_chroma)
                chord_info['timestamp'] = float(beat_times[i])
                chord_info['duration'] = float(beat_times[i + 1] - beat_times[i])
                
                chord_progression.append(chord_info)
        
        return chord_progression
    
    def _detect_chord_from_chroma(self, chroma: np.ndarray) -> Dict[str, Any]:
        """Detect chord from chroma vector."""
        best_match = {'chord': 'N', 'confidence': 0.0, 'root': '', 'quality': ''}
        
        # Normalize chroma
        chroma_norm = chroma / (np.sum(chroma) + 1e-8)
        
        for root_idx, root in enumerate(self.note_names):
            for quality, intervals in self.chord_templates.items():
                # Create chord template
                template = np.zeros(12)
                for interval in intervals:
                    template[(root_idx + interval) % 12] = 1
                
                # Normalize template
                template = template / (np.sum(template) + 1e-8)
                
                # Calculate correlation
                correlation = np.corrcoef(chroma_norm, template)[0, 1] if np.sum(template) > 0 else 0
                
                if not np.isnan(correlation) and correlation > best_match['confidence']:
                    chord_name = f"{root}{quality}" if quality != 'major' else root
                    best_match = {
                        'chord': chord_name,
                        'confidence': float(correlation),
                        'root': root,
                        'quality': quality,
                        'intervals': intervals
                    }
        
        return best_match
    
    def _get_scale_notes(self, root: str, scale_type: ScaleType) -> List[str]:
        """Get notes in a scale."""
        if root not in self.note_to_number:
            return []
            
        root_idx = self.note_to_number[root]
        intervals = self.scale_templates[scale_type]
        
        return [self.note_names[(root_idx + interval) % 12] for interval in intervals]
    
    def _find_relative_keys(self, key: str, mode: str) -> List[str]:
        """Find relative major/minor keys."""
        try:
            if mode == 'major':
                # Relative minor is 6th degree
                root_idx = self.note_to_number[key]
                relative_minor_idx = (root_idx + 9) % 12  # +9 semitones = -3 semitones
                return [f"{self.note_names[relative_minor_idx]}m"]
            else:
                # Relative major is 3rd degree
                root = key.replace('m', '')
                if root in self.note_to_number:
                    root_idx = self.note_to_number[root]
                    relative_major_idx = (root_idx + 3) % 12
                    return [self.note_names[relative_major_idx]]
        except (KeyError, IndexError):
            pass
        return []
    
    def _find_parallel_modes(self, key: str, mode: str) -> List[str]:
        """Find parallel modes for the key."""
        root = key.replace('m', '') if 'm' in key else key
        modes = []
        
        try:
            for scale_type in list(ScaleType)[:7]:  # Limit to common modes
                if scale_type.value != mode:
                    if scale_type in [ScaleType.MAJOR, ScaleType.MINOR]:
                        mode_key = f"{root}m" if scale_type == ScaleType.MINOR else root
                    else:
                        mode_key = f"{root} {scale_type.value}"
                    modes.append(mode_key)
        except:
            pass
        
        return modes[:5]  # Limit to most common modes
    
    def _suggest_chords_for_key(self, key: str, mode: str) -> List[str]:
        """Suggest diatonic chords for the key."""
        try:
            root = key.replace('m', '') if 'm' in key else key
            if root not in self.note_to_number:
                return []
                
            root_idx = self.note_to_number[root]
            
            if mode == 'major':
                # I, ii, iii, IV, V, vi, vii°
                chord_qualities = ['', 'm', 'm', '', '', 'm', 'dim']
            else:
                # i, ii°, III, iv, v, VI, VII
                chord_qualities = ['m', 'dim', '', 'm', 'm', '', '']
            
            scale_intervals = self.scale_templates[ScaleType.MAJOR if mode == 'major' else ScaleType.MINOR]
            chords = []
            
            for i, quality in enumerate(chord_qualities):
                if i < len(scale_intervals):
                    chord_root_idx = (root_idx + scale_intervals[i]) % 12
                    chord_root = self.note_names[chord_root_idx]
                    chord_name = f"{chord_root}{quality}"
                    chords.append(chord_name)
            
            return chords
        except:
            return []
    
    def _generate_recommendations(self, key_analysis: KeyAnalysis, chord_progression: List[Dict]) -> Dict[str, Any]:
        """Generate educational recommendations."""
        recommendations = {
            'practice_suggestions': [],
            'theory_insights': [],
            'chord_substitutions': {},
            'progression_analysis': {}
        }
        
        try:
            # Analyze progression patterns
            chord_names = [chord['chord'] for chord in chord_progression if chord.get('chord', 'N') != 'N']
            
            if len(chord_names) >= 3:
                # Check for common progressions
                for prog_name, prog_data in self.common_progressions.items():
                    if self._matches_progression_pattern(chord_names, prog_data['roman'], key_analysis.key):
                        recommendations['progression_analysis'][prog_name] = prog_data['description']
            
            # Practice suggestions based on difficulty
            difficult_chords = []
            for chord_info in chord_progression:
                chord = chord_info.get('chord', '')
                if chord in self.chord_difficulty.get('guitar', {}):
                    if self.chord_difficulty['guitar'][chord] > 6:
                        difficult_chords.append(chord)
            
            if difficult_chords:
                recommendations['practice_suggestions'].append(
                    f"Focus on practicing these challenging chords: {', '.join(set(difficult_chords))}"
                )
            
            # Theory insights
            recommendations['theory_insights'].append(
                f"This piece is in {key_analysis.key} {key_analysis.mode}, "
                f"which uses the notes: {', '.join(key_analysis.scale_notes)}"
            )
            
            # Chord substitutions
            for instrument in ['guitar', 'piano', 'ukulele']:
                subs = {}
                for chord_info in chord_progression:
                    chord = chord_info.get('chord', '')
                    if chord in self.chord_substitutions.get(instrument, {}):
                        subs[chord] = self.chord_substitutions[instrument][chord]
                if subs:
                    recommendations['chord_substitutions'][instrument] = subs
                    
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
        
        return recommendations
    
    def _matches_progression_pattern(self, chord_names: List[str], pattern: List[str], key: str) -> bool:
        """Check if chord progression matches a roman numeral pattern."""
        # This is a simplified implementation
        return len(chord_names) >= len(pattern) and len(set(chord_names)) >= 2
    
    def _calculate_harmonic_complexity(self, chord_progression: List[Dict]) -> float:
        """Calculate harmonic complexity score."""
        if not chord_progression:
            return 0.0
        
        unique_chords = set(chord.get('chord', 'N') for chord in chord_progression if chord.get('chord', 'N') != 'N')
        chord_changes = len(chord_progression)
        
        # Factors: number of unique chords, frequency of changes, chord complexity
        complexity_score = len(unique_chords) * 0.3
        complexity_score += min(chord_changes / 10, 3) * 0.2  # Normalize by expected length
        
        # Add points for complex chords (7ths, 9ths, etc.)
        complex_chord_bonus = sum(1 for chord in unique_chords if any(x in chord for x in ['7', '9', '11', '13', 'dim', 'aug']))
        complexity_score += complex_chord_bonus * 0.5
        
        return min(complexity_score, 10.0)  # Cap at 10
    
    def _analyze_mood(self, key_analysis: KeyAnalysis, tempo: float, chord_progression: List[Dict]) -> str:
        """Analyze musical mood based on key, tempo, and harmony."""
        mood_factors = []
        
        # Key-based mood
        if key_analysis.mode == 'minor':
            mood_factors.append('melancholic')
        else:
            mood_factors.append('bright')
        
        # Tempo-based mood
        if tempo < 70:
            mood_factors.append('slow')
        elif tempo < 120:
            mood_factors.append('moderate')
        else:
            mood_factors.append('energetic')
        
        # Harmony-based mood
        try:
            complex_chords = sum(1 for chord in chord_progression if any(x in chord.get('chord', '') for x in ['7', '9', 'dim']))
            if len(chord_progression) > 0 and complex_chords > len(chord_progression) * 0.3:
                mood_factors.append('sophisticated')
        except:
            pass
        
        return ' and '.join(mood_factors) if mood_factors else 'neutral'
    
    def _estimate_time_signature(self, y: np.ndarray, sr: int) -> str:
        """Estimate time signature of the audio."""
        try:
            # Simplified time signature detection
            onset_envelope = librosa.onset.onset_strength(y=y, sr=sr)
            tempo, beats = librosa.beat.beat_track(onset_envelope=onset_envelope, sr=sr)
            
            # Analyze beat patterns to guess time signature
            if len(beats) > 1:
                beat_intervals = np.diff(librosa.frames_to_time(beats, sr=sr))
                avg_beat_interval = np.mean(beat_intervals)
                
                # Simple heuristic based on tempo and beat patterns
                if tempo > 150 and np.std(beat_intervals) < 0.1:
                    return "4/4"
                elif tempo < 100:
                    return "3/4"
                else:
                    return "4/4"  # Default assumption
            else:
                return "4/4"
        except:
            return "4/4"
            timestamp = i / frames_per_second
            
            progression.append({
                'chord': chord,
                'timestamp': timestamp,
                'confidence': self._calculate_chord_confidence(avg_chroma, chord)
            })
        
        return progression
    
    def _match_chord(self, chroma: np.ndarray) -> str:
        """Match chroma vector to closest chord."""
        best_chord = 'C'
        best_score = -1
        
        for root_idx, root in enumerate(self.NOTES):
            for chord_type, intervals in self.CHORD_INTERVALS.items():
                # Create chord template
                template = np.zeros(12)
                for interval in intervals:
                    template[(root_idx + interval) % 12] = 1
                
                # Calculate correlation
                score = np.corrcoef(chroma, template)[0, 1]
                if not np.isnan(score) and score > best_score:
                    best_score = score
                    best_chord = f"{root}{chord_type if chord_type != 'major' else ''}"
        
        return best_chord
    
    def _calculate_chord_confidence(self, chroma: np.ndarray, chord: str) -> float:
        """Calculate confidence score for chord detection."""
        # This is a simplified confidence calculation
        return min(1.0, max(0.0, np.max(chroma) * 0.8))
    
    def get_chord_substitutions(self, chord: str, instrument: str, 
                              skill_level: int = 1) -> List[Dict]:
        """
        Get chord substitutions suitable for beginners or specific skill levels.
        """
        substitutions = []
        
        # Get instrument-specific substitutions
        if instrument in self.BEGINNER_SUBSTITUTIONS:
            if chord in self.BEGINNER_SUBSTITUTIONS[instrument]:
                for sub_chord in self.BEGINNER_SUBSTITUTIONS[instrument][chord]:
                    difficulty = self.CHORD_DIFFICULTY.get(instrument, {}).get(sub_chord, 3)
                    if difficulty <= skill_level + 1:  # Allow slightly harder chords
                        substitutions.append({
                            'chord': sub_chord,
                            'difficulty': difficulty,
                            'reason': f"Easier alternative to {chord}",
                            'confidence': 0.8
                        })
        
        # Add theoretical substitutions based on music theory
        theoretical_subs = self._get_theoretical_substitutions(chord)
        for sub in theoretical_subs:
            difficulty = self.CHORD_DIFFICULTY.get(instrument, {}).get(sub['chord'], 3)
            if difficulty <= skill_level + 2:
                substitutions.append({
                    **sub,
                    'difficulty': difficulty
                })
        
        # Sort by difficulty and confidence
        substitutions.sort(key=lambda x: (x['difficulty'], -x['confidence']))
        return substitutions[:5]  # Return top 5 substitutions
    
    def _get_theoretical_substitutions(self, chord: str) -> List[Dict]:
        """Get chord substitutions based on music theory."""
        substitutions = []
        
        # Parse chord
        root, chord_type = self._parse_chord(chord)
        if not root:
            return substitutions
        
        root_idx = self.NOTES.index(root) if root in self.NOTES else 0
        
        # Common substitutions
        if chord_type == 'major' or chord_type == '':
            # Relative minor
            rel_minor_idx = (root_idx - 3) % 12
            substitutions.append({
                'chord': f"{self.NOTES[rel_minor_idx]}m",
                'reason': "Relative minor",
                'confidence': 0.7
            })
            
            # vi chord (relative minor)
            vi_idx = (root_idx + 9) % 12
            substitutions.append({
                'chord': f"{self.NOTES[vi_idx]}m",
                'reason': "vi chord substitution",
                'confidence': 0.6
            })
        
        elif chord_type == 'minor' or chord_type == 'm':
            # Relative major
            rel_major_idx = (root_idx + 3) % 12
            substitutions.append({
                'chord': self.NOTES[rel_major_idx],
                'reason': "Relative major",
                'confidence': 0.7
            })
        
        return substitutions
    
    def _parse_chord(self, chord: str) -> Tuple[Optional[str], str]:
        """Parse chord name into root note and chord type."""
        if not chord:
            return None, ''
        
        # Handle sharp notes
        if len(chord) > 1 and chord[1] == '#':
            root = chord[:2]
            chord_type = chord[2:]
        else:
            root = chord[0]
            chord_type = chord[1:]
        
        # Normalize chord type
        if chord_type == '' or chord_type.lower() == 'maj':
            chord_type = 'major'
        elif chord_type.lower() == 'm' or chord_type.lower() == 'min':
            chord_type = 'minor'
        
        return root if root in self.NOTES else None, chord_type
    
    def generate_chord_progression(self, key: str, style: str = 'pop') -> List[str]:
        """Generate a chord progression in a given key and style."""
        progressions = {
            'pop': ['I', 'V', 'vi', 'IV'],
            'folk': ['I', 'IV', 'V', 'I'],
            'blues': ['I', 'I', 'I', 'I', 'IV', 'IV', 'I', 'I', 'V', 'IV', 'I', 'V'],
            'jazz': ['I', 'vi', 'ii', 'V'],
            'rock': ['I', 'bVII', 'IV', 'I']
        }
        
        if style not in progressions:
            style = 'pop'
        
        # Convert Roman numerals to actual chords
        root, mode = key.split() if ' ' in key else (key, 'major')
        root_idx = self.NOTES.index(root) if root in self.NOTES else 0
        
        scale_degrees = {
            'I': 0, 'ii': 2, 'iii': 4, 'IV': 5, 'V': 7, 'vi': 9, 'vii': 11,
            'bVII': 10
        }
        
        chord_progression = []
        for numeral in progressions[style]:
            if numeral in scale_degrees:
                chord_idx = (root_idx + scale_degrees[numeral]) % 12
                chord_root = self.NOTES[chord_idx]
                
                # Determine if chord should be major or minor based on key and degree
                if mode == 'major':
                    if numeral.lower() in ['ii', 'iii', 'vi']:
                        chord_progression.append(f"{chord_root}m")
                    else:
                        chord_progression.append(chord_root)
                else:  # minor key
                    if numeral.upper() in ['III', 'VI', 'VII']:
                        chord_progression.append(chord_root)
                    else:
                        chord_progression.append(f"{chord_root}m")
        
        return chord_progression
    
    def get_learning_path(self, instrument: str, skill_level: int = 1) -> Dict:
        """Generate a learning path for an instrument based on skill level."""
        paths = {
            'guitar': {
                1: {
                    'name': 'Beginner Guitar Essentials',
                    'chords': ['Em', 'Am', 'C', 'D', 'G'],
                    'songs': ['Wonderwall - Oasis', 'Horse with No Name - America'],
                    'techniques': ['Basic strumming', 'Chord transitions'],
                    'estimated_weeks': 8
                },
                2: {
                    'name': 'Intermediate Guitar Skills',
                    'chords': ['F', 'Bm', 'A', 'E', 'Dm'],
                    'songs': ['Blackbird - Beatles', 'Tears in Heaven - Clapton'],
                    'techniques': ['Barre chords', 'Fingerpicking basics'],
                    'estimated_weeks': 12
                }
            },
            'piano': {
                1: {
                    'name': 'Piano Fundamentals',
                    'chords': ['C', 'F', 'G', 'Am', 'Dm'],
                    'songs': ['Twinkle Twinkle Little Star', 'Mary Had a Little Lamb'],
                    'techniques': ['Proper posture', 'Basic scales', 'Simple melodies'],
                    'estimated_weeks': 10
                },
                2: {
                    'name': 'Intermediate Piano',
                    'chords': ['A', 'D', 'E', 'Bm', 'Em'],
                    'songs': ['Für Elise - Beethoven', 'Imagine - John Lennon'],
                    'techniques': ['Chord inversions', 'Basic accompaniment patterns'],
                    'estimated_weeks': 16
                }
            }
        }
        
        return paths.get(instrument, {}).get(skill_level, {})


class PitchDetector:
    """Real-time pitch detection for tuning and practice feedback."""
    
    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
        self.note_frequencies = self._generate_note_frequencies()
    
    def _generate_note_frequencies(self) -> Dict[str, float]:
        """Generate frequencies for musical notes."""
        A4_freq = 440.0
        notes = {}
        
        for octave in range(0, 9):
            for i, note in enumerate(['C', 'C#', 'D', 'D#', 'E', 'F', 
                                    'F#', 'G', 'G#', 'A', 'A#', 'B']):
                # Calculate frequency using equal temperament
                semitones_from_A4 = (octave - 4) * 12 + (i - 9)
                frequency = A4_freq * (2 ** (semitones_from_A4 / 12))
                notes[f"{note}{octave}"] = frequency
        
        return notes
    
    def detect_pitch(self, audio_buffer: np.ndarray) -> Dict:
        """Detect pitch from audio buffer."""
        # Use autocorrelation for pitch detection
        correlation = np.correlate(audio_buffer, audio_buffer, mode='full')
        correlation = correlation[len(correlation)//2:]
        
        # Find the peak that corresponds to the fundamental frequency
        d = np.diff(correlation)
        start = np.where(d > 0)[0][0] if len(np.where(d > 0)[0]) > 0 else 1
        peak = np.argmax(correlation[start:]) + start
        
        # Convert to frequency
        frequency = self.sample_rate / peak if peak > 0 else 0
        
        # Find closest note
        closest_note, cents_off = self._frequency_to_note(frequency)
        
        return {
            'frequency': frequency,
            'note': closest_note,
            'cents_off': cents_off,
            'confidence': self._calculate_pitch_confidence(correlation, peak)
        }
    
    def _frequency_to_note(self, frequency: float) -> Tuple[str, float]:
        """Convert frequency to nearest note and cents offset."""
        if frequency <= 0:
            return 'Unknown', 0
        
        # Find the closest note
        min_diff = float('inf')
        closest_note = 'Unknown'
        
        for note, note_freq in self.note_frequencies.items():
            diff = abs(frequency - note_freq)
            if diff < min_diff:
                min_diff = diff
                closest_note = note
        
        # Calculate cents offset
        if closest_note != 'Unknown':
            note_freq = self.note_frequencies[closest_note]
            cents_off = 1200 * np.log2(frequency / note_freq)
        else:
            cents_off = 0
        
        return closest_note, cents_off
    
    def _calculate_pitch_confidence(self, correlation: np.ndarray, peak: int) -> float:
        """Calculate confidence in pitch detection."""
        if peak == 0 or len(correlation) == 0:
            return 0.0
        
        # Confidence based on peak prominence
        peak_value = correlation[peak]
        mean_value = np.mean(correlation)
        
        confidence = min(1.0, (peak_value - mean_value) / peak_value) if peak_value > 0 else 0.0
        return max(0.0, confidence)


class MetronomeEngine:
    """Digital metronome with various time signatures and sounds."""
    
    def __init__(self):
        self.tempo = 120  # BPM
        self.time_signature = (4, 4)
        self.is_running = False
        self.current_beat = 0
    
    def set_tempo(self, bpm: int):
        """Set metronome tempo."""
        self.tempo = max(40, min(300, bpm))  # Limit to reasonable range
    
    def set_time_signature(self, numerator: int, denominator: int):
        """Set time signature."""
        self.time_signature = (numerator, denominator)
    
    def get_beat_interval(self) -> float:
        """Calculate interval between beats in seconds."""
        # Convert BPM to beats per second, then to interval
        beats_per_second = self.tempo / 60.0
        note_value = 4 / self.time_signature[1]  # Quarter note = 1, eighth note = 0.5, etc.
        return note_value / beats_per_second
    
    def generate_click_pattern(self) -> List[Dict]:
        """Generate click pattern for current time signature."""
        pattern = []
        for beat in range(self.time_signature[0]):
            pattern.append({
                'beat_number': beat + 1,
                'is_downbeat': beat == 0,
                'emphasis': 'strong' if beat == 0 else 'weak',
                'sound_type': 'high' if beat == 0 else 'low'
            })
        return pattern

import numpy as np
import librosa
from typing import List, Dict, Tuple, Optional
import json


class MusicTheoryEngine:
    """
    Comprehensive music theory engine for chord analysis, key detection,
    and educational features for musical instruments.
    """
    
    # Musical constants
    NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    CHORD_INTERVALS = {
        'major': [0, 4, 7],
        'minor': [0, 3, 7],
        'dim': [0, 3, 6],
        'aug': [0, 4, 8],
        '7': [0, 4, 7, 10],
        'maj7': [0, 4, 7, 11],
        'm7': [0, 3, 7, 10],
        'dim7': [0, 3, 6, 9],
        'sus2': [0, 2, 7],
        'sus4': [0, 5, 7],
        '6': [0, 4, 7, 9],
        'm6': [0, 3, 7, 9],
        '9': [0, 4, 7, 10, 14],
        'add9': [0, 4, 7, 14],
    }
    
    # Chord substitution rules for beginners
    BEGINNER_SUBSTITUTIONS = {
        'guitar': {
            'F': ['Fmaj7', 'Dm', 'C'],  # F is hard for beginners
            'Bm': ['D', 'G', 'Em'],
            'F#m': ['Em', 'Am', 'Dm'],
            'C#': ['C', 'D', 'Em'],
            'F#': ['G', 'F', 'Em'],
            'Bb': ['Am', 'C', 'F'],
        },
        'piano': {
            'F#': ['G', 'F', 'Em'],
            'C#': ['C', 'D'],
            'Bb': ['Am', 'C'],
        },
        'ukulele': {
            'F': ['C', 'Am', 'Dm'],
            'Bm': ['Em', 'Am', 'Dm'],
            'E': ['Em', 'C', 'Am'],
        }
    }
    
    # Difficulty ratings for chords by instrument
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
        self.chroma_profiles = self._create_chroma_profiles()
    
    def _create_chroma_profiles(self) -> Dict:
        """Create chroma profiles for major and minor keys."""
        # Krumhansl-Schmuckler key profiles
        major_profile = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
        minor_profile = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
        
        profiles = {}
        for i, note in enumerate(self.NOTES):
            # Rotate profiles for each key
            profiles[f"{note}_major"] = np.roll(major_profile, i)
            profiles[f"{note}_minor"] = np.roll(minor_profile, i)
        
        return profiles
    
    def analyze_audio_harmony(self, audio_path: str) -> Dict:
        """
        Analyze audio file to extract harmonic information including
        key, chord progressions, and tempo.
        """
        # Load audio
        y, sr = librosa.load(audio_path)
        
        # Extract features
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        
        # Detect key
        key = self._detect_key(chroma)
        
        # Segment audio and detect chords
        chord_progression = self._detect_chord_progression(chroma, sr)
        
        # Analyze rhythm and structure
        onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
        onset_times = librosa.onset.onset_frames_to_time(onset_frames, sr=sr)
        
        return {
            'key': key,
            'tempo': float(tempo),
            'chord_progression': chord_progression,
            'duration': len(y) / sr,
            'onset_times': onset_times.tolist(),
            'chroma_features': chroma.mean(axis=1).tolist()
        }
    
    def _detect_key(self, chroma: np.ndarray) -> str:
        """Detect the key of the audio using chroma features."""
        # Average chroma over time
        avg_chroma = np.mean(chroma, axis=1)
        
        # Correlate with key profiles
        correlations = {}
        for key, profile in self.chroma_profiles.items():
            correlation = np.corrcoef(avg_chroma, profile)[0, 1]
            correlations[key] = correlation
        
        # Return key with highest correlation
        best_key = max(correlations, key=correlations.get)
        return best_key.replace('_', ' ')
    
    def _detect_chord_progression(self, chroma: np.ndarray, sr: int) -> List[Dict]:
        """Detect chord progression from chroma features."""
        # Segment chroma into chord-length segments
        hop_length = 512
        frames_per_second = sr / hop_length
        segment_length = int(2 * frames_per_second)  # 2-second segments
        
        progression = []
        for i in range(0, chroma.shape[1] - segment_length, segment_length):
            segment_chroma = chroma[:, i:i+segment_length]
            avg_chroma = np.mean(segment_chroma, axis=1)
            
            # Find best matching chord
            chord = self._match_chord(avg_chroma)
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

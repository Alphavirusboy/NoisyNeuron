"""
Audio Processing Service

This module handles audio processing tasks including:
- Audio file analysis and validation
- Source separation using spectral techniques
- Integration with Markov models for improved separation
- Audio format conversion and optimization
"""

import librosa
import numpy as np
import soundfile as sf
from pydub import AudioSegment
import scipy.signal
from sklearn.decomposition import FastICA, NMF
import logging
import os
import tempfile
from typing import Dict, List, Tuple, Optional, Any
import json
import warnings

from markov_models.markov_chain import AudioMarkovChain, AudioSourceSeparator

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

class AudioProcessor:
    """Main class for audio processing and source separation."""
    
    def __init__(self):
        self.separator = AudioSourceSeparator()
        self.supported_formats = ['wav', 'mp3', 'flac', 'ogg', 'm4a', 'aac']
        self.sample_rate = 22050  # Standard sample rate for processing
        self.hop_length = 512
        self.n_fft = 2048
    
    def load_audio(self, file_path: str, normalize: bool = True) -> Tuple[np.ndarray, int]:
        """
        Load audio file and convert to standard format.
        
        Args:
            file_path: Path to audio file
            normalize: Whether to normalize audio amplitude
            
        Returns:
            Tuple of (audio_data, sample_rate)
        """
        try:
            # Load audio using librosa (handles most formats)
            audio, sr = librosa.load(file_path, sr=self.sample_rate, mono=True)
            
            if normalize:
                # Normalize to [-1, 1] range
                max_val = np.max(np.abs(audio))
                if max_val > 0:
                    audio = audio / max_val
            
            logger.info(f"Loaded audio: {file_path}, duration: {len(audio)/sr:.2f}s")
            return audio, sr
            
        except Exception as e:
            logger.error(f"Error loading audio file {file_path}: {str(e)}")
            raise
    
    def analyze_audio(self, audio: np.ndarray, sr: int) -> Dict[str, Any]:
        """
        Analyze audio characteristics.
        
        Args:
            audio: Audio signal
            sr: Sample rate
            
        Returns:
            Dictionary containing audio analysis results
        """
        analysis = {
            'duration': len(audio) / sr,
            'sample_rate': sr,
            'channels': 1,  # We process mono
            'format': 'float32',
            'size_bytes': audio.nbytes
        }
        
        # Spectral analysis
        stft = librosa.stft(audio, hop_length=self.hop_length, n_fft=self.n_fft)
        magnitude = np.abs(stft)
        
        # Basic audio features
        analysis.update({
            'rms_energy': float(np.sqrt(np.mean(audio**2))),
            'zero_crossing_rate': float(np.mean(librosa.feature.zero_crossing_rate(audio))),
            'spectral_centroid': float(np.mean(librosa.feature.spectral_centroid(y=audio, sr=sr))),
            'spectral_bandwidth': float(np.mean(librosa.feature.spectral_bandwidth(y=audio, sr=sr))),
            'spectral_rolloff': float(np.mean(librosa.feature.spectral_rolloff(y=audio, sr=sr))),
        })
        
        # Tempo and rhythm
        try:
            tempo, beats = librosa.beat.beat_track(y=audio, sr=sr)
            analysis['tempo'] = float(tempo)
            analysis['n_beats'] = len(beats)
        except:
            analysis['tempo'] = 0.0
            analysis['n_beats'] = 0
        
        # Harmonic analysis
        try:
            chroma = librosa.feature.chroma_stft(y=audio, sr=sr)
            analysis['key_strength'] = float(np.max(np.mean(chroma, axis=1)))
            analysis['tonal_stability'] = float(np.std(np.mean(chroma, axis=1)))
        except:
            analysis['key_strength'] = 0.0
            analysis['tonal_stability'] = 0.0
        
        return analysis
    
    def spectral_separation(self, audio: np.ndarray, sr: int, 
                          n_components: int = 4) -> Dict[str, np.ndarray]:
        """
        Perform spectral-based source separation using NMF.
        
        Args:
            audio: Input audio signal
            sr: Sample rate
            n_components: Number of components to separate
            
        Returns:
            Dictionary of separated audio components
        """
        logger.info(f"Performing spectral separation with {n_components} components")
        
        # Compute magnitude spectrogram
        stft = librosa.stft(audio, hop_length=self.hop_length, n_fft=self.n_fft)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Apply NMF for source separation
        nmf = NMF(n_components=n_components, random_state=42, max_iter=200)
        W = nmf.fit_transform(magnitude)  # Basis vectors
        H = nmf.components_  # Activation matrix
        
        separated_audio = {}
        
        for i in range(n_components):
            # Reconstruct component
            component_magnitude = np.outer(W[:, i], H[i, :])
            
            # Apply phase and convert back to time domain
            component_stft = component_magnitude * np.exp(1j * phase)
            component_audio = librosa.istft(component_stft, hop_length=self.hop_length)
            
            # Determine component type based on spectral characteristics
            component_name = self._classify_component(component_audio, sr, i)
            separated_audio[component_name] = component_audio
        
        return separated_audio
    
    def _classify_component(self, audio: np.ndarray, sr: int, index: int) -> str:
        """
        Classify separated component based on audio characteristics.
        
        Args:
            audio: Audio component
            sr: Sample rate
            index: Component index
            
        Returns:
            Component classification string
        """
        # Calculate features for classification
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=audio, sr=sr))
        zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(audio))
        rms_energy = np.sqrt(np.mean(audio**2))
        
        # Simple heuristic classification
        if spectral_centroid > 3000 and zero_crossing_rate > 0.1:
            return f"percussion_{index}"
        elif spectral_centroid > 1000:
            return f"vocals_{index}"
        elif spectral_centroid > 500:
            return f"melody_{index}"
        else:
            return f"bass_{index}"
    
    def markov_enhanced_separation(self, audio: np.ndarray, sr: int,
                                 target_instruments: List[str] = None) -> Dict[str, np.ndarray]:
        """
        Perform source separation enhanced with Markov models.
        
        Args:
            audio: Input audio signal
            sr: Sample rate
            target_instruments: List of target instruments
            
        Returns:
            Dictionary of separated audio tracks
        """
        if not target_instruments:
            target_instruments = ['vocals', 'drums', 'bass', 'other']
        
        logger.info(f"Performing Markov-enhanced separation for: {target_instruments}")
        
        # First, perform basic spectral separation
        spectral_components = self.spectral_separation(audio, sr, len(target_instruments))
        
        # If we have trained Markov models, use them to refine separation
        if hasattr(self.separator, 'models') and self.separator.models:
            markov_separated = self.separator.separate_sources(audio, sr, target_instruments)
            
            # Combine spectral and Markov results
            combined_results = {}
            for instrument in target_instruments:
                if instrument in markov_separated:
                    # Use Markov result if available
                    combined_results[instrument] = markov_separated[instrument]
                else:
                    # Fall back to spectral separation
                    spectral_key = self._find_best_spectral_match(instrument, spectral_components)
                    if spectral_key:
                        combined_results[instrument] = spectral_components[spectral_key]
                    else:
                        # Create silent track if no match found
                        combined_results[instrument] = np.zeros_like(audio)
            
            return combined_results
        else:
            # Return spectral separation results with proper naming
            results = {}
            instrument_mapping = {
                0: 'vocals',
                1: 'drums', 
                2: 'bass',
                3: 'other'
            }
            
            for i, instrument in enumerate(target_instruments):
                if i < len(spectral_components):
                    component_name = list(spectral_components.keys())[i]
                    results[instrument] = spectral_components[component_name]
                else:
                    results[instrument] = np.zeros_like(audio)
            
            return results
    
    def _find_best_spectral_match(self, target_instrument: str, 
                                spectral_components: Dict[str, np.ndarray]) -> Optional[str]:
        """Find the best matching spectral component for target instrument."""
        # Simple matching based on naming patterns
        for key in spectral_components.keys():
            if target_instrument.lower() in key.lower():
                return key
            elif target_instrument == 'vocals' and 'melody' in key:
                return key
            elif target_instrument == 'drums' and 'percussion' in key:
                return key
        
        # If no match found, return first available
        return list(spectral_components.keys())[0] if spectral_components else None
    
    def enhance_audio_quality(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """
        Enhance audio quality using signal processing techniques.
        
        Args:
            audio: Input audio
            sr: Sample rate
            
        Returns:
            Enhanced audio signal
        """
        # Noise reduction using spectral gating
        stft = librosa.stft(audio, hop_length=self.hop_length, n_fft=self.n_fft)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Estimate noise floor
        noise_floor = np.percentile(magnitude, 10, axis=1, keepdims=True)
        
        # Apply spectral gating
        gate_threshold = noise_floor * 2.0
        mask = magnitude > gate_threshold
        enhanced_magnitude = magnitude * mask
        
        # Smooth the mask to avoid artifacts
        from scipy import ndimage
        mask_smooth = ndimage.gaussian_filter(mask.astype(float), sigma=1.0)
        enhanced_magnitude = magnitude * mask_smooth
        
        # Reconstruct audio
        enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
        enhanced_audio = librosa.istft(enhanced_stft, hop_length=self.hop_length)
        
        # Apply gentle compression
        enhanced_audio = self._apply_compression(enhanced_audio)
        
        return enhanced_audio
    
    def _apply_compression(self, audio: np.ndarray, threshold: float = 0.5, 
                          ratio: float = 4.0) -> np.ndarray:
        """Apply dynamic range compression."""
        compressed = np.copy(audio)
        
        # Simple compression algorithm
        above_threshold = np.abs(audio) > threshold
        compressed[above_threshold] = np.sign(audio[above_threshold]) * (
            threshold + (np.abs(audio[above_threshold]) - threshold) / ratio
        )
        
        return compressed
    
    def save_audio(self, audio: np.ndarray, sr: int, output_path: str, 
                  format: str = 'wav') -> str:
        """
        Save audio to file.
        
        Args:
            audio: Audio data
            sr: Sample rate
            output_path: Output file path
            format: Output format ('wav', 'mp3', 'flac')
            
        Returns:
            Path to saved file
        """
        try:
            if format.lower() == 'wav':
                sf.write(output_path, audio, sr)
            else:
                # Use pydub for other formats
                # First save as temporary wav
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                    sf.write(temp_wav.name, audio, sr)
                    
                    # Convert using pydub
                    audio_segment = AudioSegment.from_wav(temp_wav.name)
                    audio_segment.export(output_path, format=format)
                    
                    # Clean up temporary file
                    os.unlink(temp_wav.name)
            
            logger.info(f"Audio saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error saving audio to {output_path}: {str(e)}")
            raise
    
    def create_mix(self, tracks: Dict[str, np.ndarray], levels: Dict[str, float] = None) -> np.ndarray:
        """
        Create a mix from separated tracks.
        
        Args:
            tracks: Dictionary of track name -> audio data
            levels: Dictionary of track name -> volume level (0.0 to 1.0)
            
        Returns:
            Mixed audio signal
        """
        if not tracks:
            raise ValueError("No tracks provided for mixing")
        
        if levels is None:
            levels = {name: 1.0 for name in tracks.keys()}
        
        # Ensure all tracks have the same length
        max_length = max(len(track) for track in tracks.values())
        
        mixed_audio = np.zeros(max_length)
        
        for track_name, track_audio in tracks.items():
            level = levels.get(track_name, 1.0)
            
            # Pad track if necessary
            if len(track_audio) < max_length:
                padded_track = np.pad(track_audio, (0, max_length - len(track_audio)))
            else:
                padded_track = track_audio[:max_length]
            
            mixed_audio += padded_track * level
        
        # Normalize to prevent clipping
        max_val = np.max(np.abs(mixed_audio))
        if max_val > 1.0:
            mixed_audio /= max_val
        
        return mixed_audio
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported audio formats."""
        return self.supported_formats.copy()
    
    def validate_audio_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate audio file and return information.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Validation results dictionary
        """
        validation = {
            'is_valid': False,
            'error': None,
            'format': None,
            'duration': 0,
            'file_size': 0
        }
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                validation['error'] = "File not found"
                return validation
            
            # Get file size
            validation['file_size'] = os.path.getsize(file_path)
            
            # Check file extension
            file_ext = os.path.splitext(file_path)[1].lower().lstrip('.')
            if file_ext not in self.supported_formats:
                validation['error'] = f"Unsupported format: {file_ext}"
                return validation
            
            validation['format'] = file_ext
            
            # Try to load and analyze
            audio, sr = self.load_audio(file_path)
            validation['duration'] = len(audio) / sr
            
            # Additional validation checks
            if validation['duration'] > 600:  # 10 minutes max
                validation['error'] = "Audio file too long (max 10 minutes)"
                return validation
            
            if validation['file_size'] > 100 * 1024 * 1024:  # 100MB max
                validation['error'] = "File too large (max 100MB)"
                return validation
            
            validation['is_valid'] = True
            
        except Exception as e:
            validation['error'] = f"Error validating file: {str(e)}"
        
        return validation

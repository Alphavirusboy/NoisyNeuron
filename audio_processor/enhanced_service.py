"""
Enhanced audio processing service with advanced separation algorithms.
This module provides high-quality audio source separation using multiple techniques.
"""

import numpy as np
import librosa
import soundfile as sf
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
from sklearn.decomposition import NMF, FastICA
from scipy.signal import stft, istft
import time
import tempfile
import threading
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class AudioSeparationMethods:
    """Collection of audio separation algorithms."""
    
    @staticmethod
    def separate_with_nmf(y: np.ndarray, sr: int, n_components: int = 4, 
                         progress_callback: Optional[Callable] = None) -> Dict[str, np.ndarray]:
        """
        Separate audio using Non-negative Matrix Factorization.
        
        Args:
            y: Audio signal
            sr: Sample rate
            n_components: Number of components for NMF
            progress_callback: Optional progress callback function
        
        Returns:
            Dictionary with separated stems
        """
        if progress_callback:
            progress_callback(10, "Computing spectrogram...")
            
        # Compute magnitude spectrogram
        D = librosa.stft(y, hop_length=512, n_fft=2048)
        magnitude = np.abs(D)
        phase = np.angle(D)
        
        if progress_callback:
            progress_callback(30, "Applying NMF decomposition...")
        
        # Apply NMF with better initialization
        nmf = NMF(
            n_components=n_components, 
            random_state=42,
            init='nndsvdar',
            max_iter=500,
            beta_loss='frobenius'
        )
        W = nmf.fit_transform(magnitude)
        H = nmf.components_
        
        if progress_callback:
            progress_callback(70, "Reconstructing audio stems...")
        
        # Reconstruct separated sources
        stems = {}
        stem_names = ['vocals', 'drums', 'bass', 'other'][:n_components]
        
        for i, name in enumerate(stem_names):
            # Reconstruct magnitude with improved masking
            source_activation = np.outer(W[:, i], H[i, :])
            
            # Create soft mask
            total_activation = W @ H
            mask = source_activation / (total_activation + 1e-10)
            mask = np.clip(mask, 0.0, 1.0)
            
            # Apply mask to original magnitude
            masked_magnitude = magnitude * mask
            
            # Apply phase
            reconstructed_complex = masked_magnitude * np.exp(1j * phase)
            
            # Convert back to time domain with overlap-add
            stem_audio = librosa.istft(
                reconstructed_complex,
                hop_length=512,
                length=len(y)
            )
            stems[name] = stem_audio
            
            if progress_callback:
                progress_val = 70 + (20 * (i + 1) // len(stem_names))
                progress_callback(progress_val, f"Completed {name} separation")
        
        return stems
    
    @staticmethod
    def separate_with_ica(y: np.ndarray, sr: int, n_components: int = 4,
                         progress_callback: Optional[Callable] = None) -> Dict[str, np.ndarray]:
        """
        Separate audio using Independent Component Analysis.
        
        Args:
            y: Audio signal
            sr: Sample rate
            n_components: Number of components
            progress_callback: Optional progress callback function
        
        Returns:
            Dictionary with separated stems
        """
        if progress_callback:
            progress_callback(10, "Preparing audio for ICA...")
        
        # Convert to spectrogram
        D = librosa.stft(y, hop_length=512, n_fft=2048)
        magnitude = np.abs(D)
        phase = np.angle(D)
        
        if progress_callback:
            progress_callback(30, "Applying ICA decomposition...")
        
        # Apply ICA to magnitude spectrogram
        ica = FastICA(n_components=n_components, random_state=42, max_iter=1000)
        
        # Reshape for ICA (flatten frequency bins)
        magnitude_reshaped = magnitude.reshape(magnitude.shape[0], -1)
        sources = ica.fit_transform(magnitude_reshaped.T).T
        
        if progress_callback:
            progress_callback(70, "Reconstructing audio stems...")
        
        # Reconstruct sources
        stems = {}
        stem_names = ['vocals', 'drums', 'bass', 'other'][:n_components]
        
        for i, name in enumerate(stem_names):
            # Reshape back to spectrogram shape
            source_mag = sources[i].reshape(magnitude.shape)
            source_mag = np.abs(source_mag)  # Ensure positive
            
            # Apply original phase
            reconstructed_complex = source_mag * np.exp(1j * phase)
            
            # Convert back to time domain
            stem_audio = librosa.istft(
                reconstructed_complex,
                hop_length=512,
                length=len(y)
            )
            stems[name] = stem_audio
            
            if progress_callback:
                progress_val = 70 + (25 * (i + 1) // len(stem_names))
                progress_callback(progress_val, f"Completed {name} separation")
        
        return stems
    
    @staticmethod
    def separate_with_median_filter(y: np.ndarray, sr: int,
                                  progress_callback: Optional[Callable] = None) -> Dict[str, np.ndarray]:
        """
        Separate vocals using median filtering (simple vocal isolation).
        
        Args:
            y: Audio signal (should be stereo)
            sr: Sample rate
            progress_callback: Optional progress callback function
        
        Returns:
            Dictionary with separated stems
        """
        if progress_callback:
            progress_callback(20, "Analyzing stereo channels...")
        
        if len(y.shape) == 1:
            # Convert mono to fake stereo
            y = np.stack([y, y])
        
        # Ensure we have stereo
        if y.shape[0] != 2:
            y = y[:2]  # Take first two channels
        
        if progress_callback:
            progress_callback(50, "Isolating vocals...")
        
        # Simple vocal isolation (center channel extraction)
        vocals = y[0] - y[1]  # Subtract right from left
        accompaniment = (y[0] + y[1]) / 2  # Average of both channels
        
        if progress_callback:
            progress_callback(80, "Finalizing separation...")
        
        stems = {
            'vocals': vocals,
            'accompaniment': accompaniment,
            'original_left': y[0],
            'original_right': y[1]
        }
        
        return stems

import numpy as np
import librosa
import soundfile as sf
from typing import Dict, List, Tuple, Optional, Any
import logging
import tempfile
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class AudioSeparationMethods:
    """Collection of audio separation techniques."""
    
    @staticmethod
    def separate_with_nmf(audio: np.ndarray, sr: int, n_components: int = 4) -> Dict[str, np.ndarray]:
        """Separate audio using Non-negative Matrix Factorization."""
        try:
            # Compute magnitude spectrogram
            stft = librosa.stft(audio, hop_length=512, n_fft=2048)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # Apply NMF
            from sklearn.decomposition import NMF
            nmf = NMF(n_components=n_components, random_state=42, max_iter=200)
            W = nmf.fit_transform(magnitude.T).T
            H = nmf.components_
            
            separated_stems = {}
            stem_names = ['vocals', 'drums', 'bass', 'other']
            
            for i, stem_name in enumerate(stem_names[:n_components]):
                # Reconstruct component
                component_magnitude = np.outer(W[:, i], H[i, :])
                
                # Apply original phase
                component_stft = component_magnitude * np.exp(1j * phase)
                
                # Convert back to time domain
                component_audio = librosa.istft(component_stft, hop_length=512)
                separated_stems[stem_name] = component_audio
            
            logger.info(f"NMF separation completed with {n_components} components")
            return separated_stems
            
        except Exception as e:
            logger.error(f"Error in NMF separation: {e}")
            raise
    
    @staticmethod
    def separate_with_ica(audio: np.ndarray, sr: int, n_components: int = 2) -> Dict[str, np.ndarray]:
        """Separate audio using Independent Component Analysis."""
        try:
            # Create artificial stereo for ICA if mono
            if audio.ndim == 1:
                # Create delayed version for pseudo-stereo
                delayed = np.roll(audio, int(sr * 0.01))  # 10ms delay
                stereo_audio = np.array([audio, delayed])
            else:
                stereo_audio = audio
            
            # Apply ICA
            from sklearn.decomposition import FastICA
            ica = FastICA(n_components=n_components, random_state=42)
            components = ica.fit_transform(stereo_audio.T).T
            
            separated_stems = {}
            stem_names = ['component_1', 'component_2', 'component_3', 'component_4']
            
            for i, component in enumerate(components):
                if i < len(stem_names):
                    separated_stems[stem_names[i]] = component
            
            logger.info(f"ICA separation completed with {n_components} components")
            return separated_stems
            
        except Exception as e:
            logger.error(f"Error in ICA separation: {e}")
            raise
    
    @staticmethod
    def harmonic_percussive_separation(audio: np.ndarray, sr: int) -> Dict[str, np.ndarray]:
        """Separate harmonic and percussive components."""
        try:
            # Perform harmonic-percussive separation
            harmonic, percussive = librosa.effects.hpss(audio)
            
            # Extract vocals using spectral subtraction
            stft_harmonic = librosa.stft(harmonic)
            stft_original = librosa.stft(audio)
            
            # Simple vocal extraction (center channel extraction simulation)
            magnitude_harmonic = np.abs(stft_harmonic)
            magnitude_original = np.abs(stft_original)
            
            # Create vocal mask (simplified approach)
            vocal_mask = magnitude_harmonic / (magnitude_original + 1e-10)
            vocal_mask = np.clip(vocal_mask, 0, 1)
            
            # Apply mask
            vocal_stft = stft_original * vocal_mask
            vocals = librosa.istft(vocal_stft)
            
            # Create instrumental track
            instrumental = audio - vocals * 0.5  # Simple subtraction
            
            return {
                'harmonic': harmonic,
                'percussive': percussive,
                'vocals': vocals,
                'instrumental': instrumental
            }
            
        except Exception as e:
            logger.error(f"Error in harmonic-percussive separation: {e}")
            raise


class AudioEffectsProcessor:
    """Audio effects and enhancement processor."""
    
    @staticmethod
    def apply_noise_reduction(audio: np.ndarray, sr: int, noise_factor: float = 0.1) -> np.ndarray:
        """Apply basic noise reduction using spectral gating."""
        try:
            # Compute spectrogram
            stft = librosa.stft(audio)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # Estimate noise floor
            noise_floor = np.percentile(magnitude, 10, axis=1, keepdims=True)
            
            # Create noise gate
            gate = magnitude / (noise_floor + 1e-10)
            gate = np.clip(gate, 0, 1)
            
            # Apply smoothing to gate
            from scipy.ndimage import gaussian_filter1d
            gate = gaussian_filter1d(gate, sigma=1, axis=1)
            
            # Apply gate
            cleaned_magnitude = magnitude * gate
            cleaned_stft = cleaned_magnitude * np.exp(1j * phase)
            
            # Convert back to time domain
            cleaned_audio = librosa.istft(cleaned_stft)
            
            return cleaned_audio
            
        except Exception as e:
            logger.error(f"Error in noise reduction: {e}")
            return audio
    
    @staticmethod
    def apply_dynamic_range_compression(audio: np.ndarray, threshold: float = 0.5, 
                                      ratio: float = 4.0) -> np.ndarray:
        """Apply dynamic range compression."""
        try:
            # Convert to dB
            audio_db = librosa.amplitude_to_db(np.abs(audio) + 1e-10)
            
            # Apply compression above threshold
            compressed_db = np.where(
                audio_db > threshold,
                threshold + (audio_db - threshold) / ratio,
                audio_db
            )
            
            # Convert back to linear scale
            compressed_amplitude = librosa.db_to_amplitude(compressed_db)
            
            # Preserve original sign
            compressed_audio = compressed_amplitude * np.sign(audio)
            
            return compressed_audio
            
        except Exception as e:
            logger.error(f"Error in compression: {e}")
            return audio
    
    @staticmethod
    def apply_eq(audio: np.ndarray, sr: int, eq_params: Dict[str, float]) -> np.ndarray:
        """Apply parametric EQ."""
        try:
            # Simple EQ implementation using filtering
            from scipy.signal import butter, filtfilt
            
            processed_audio = audio.copy()
            
            # Low shelf (bass)
            if 'bass' in eq_params and eq_params['bass'] != 0:
                sos = butter(2, 200, btype='low', fs=sr, output='sos')
                bass_component = filtfilt(sos, processed_audio)
                processed_audio += bass_component * eq_params['bass'] * 0.1
            
            # High shelf (treble)
            if 'treble' in eq_params and eq_params['treble'] != 0:
                sos = butter(2, 5000, btype='high', fs=sr, output='sos')
                treble_component = filtfilt(sos, processed_audio)
                processed_audio += treble_component * eq_params['treble'] * 0.1
            
            # Mid frequencies
            if 'mid' in eq_params and eq_params['mid'] != 0:
                sos = butter(2, [800, 3000], btype='band', fs=sr, output='sos')
                mid_component = filtfilt(sos, processed_audio)
                processed_audio += mid_component * eq_params['mid'] * 0.1
            
            # Normalize to prevent clipping
            processed_audio = np.clip(processed_audio, -1, 1)
            
            return processed_audio
            
        except Exception as e:
            logger.error(f"Error in EQ: {e}")
            return audio


class AudioAnalyzer:
    """Advanced audio analysis tools."""
    
    @staticmethod
    def detect_key_and_tempo(audio: np.ndarray, sr: int) -> Dict[str, Any]:
        """Detect musical key and tempo."""
        try:
            # Tempo detection
            tempo, beats = librosa.beat.beat_track(y=audio, sr=sr)
            
            # Chroma analysis for key detection
            chroma = librosa.feature.chroma_stft(y=audio, sr=sr)
            chroma_mean = np.mean(chroma, axis=1)
            
            # Key mapping
            keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            detected_key = keys[np.argmax(chroma_mean)]
            key_confidence = float(np.max(chroma_mean))
            
            return {
                'tempo': float(tempo),
                'key': detected_key,
                'key_confidence': key_confidence,
                'beats': beats.tolist() if len(beats) < 1000 else beats[:1000].tolist()
            }
            
        except Exception as e:
            logger.error(f"Error in key/tempo detection: {e}")
            return {'tempo': 0, 'key': 'Unknown', 'key_confidence': 0, 'beats': []}
    
    @staticmethod
    def analyze_frequency_spectrum(audio: np.ndarray, sr: int) -> Dict[str, Any]:
        """Analyze frequency spectrum characteristics."""
        try:
            # Compute FFT
            fft = np.fft.fft(audio)
            magnitude = np.abs(fft)
            frequencies = np.fft.fftfreq(len(audio), 1/sr)
            
            # Take only positive frequencies
            positive_freq_idx = frequencies >= 0
            frequencies = frequencies[positive_freq_idx]
            magnitude = magnitude[positive_freq_idx]
            
            # Find dominant frequencies
            peaks_idx = np.argsort(magnitude)[-10:]  # Top 10 peaks
            dominant_frequencies = frequencies[peaks_idx].tolist()
            
            # Frequency band analysis
            freq_bands = {
                'sub_bass': (20, 60),
                'bass': (60, 250),
                'low_mid': (250, 500),
                'mid': (500, 2000),
                'high_mid': (2000, 4000),
                'presence': (4000, 6000),
                'brilliance': (6000, 20000)
            }
            
            band_energy = {}
            for band_name, (low, high) in freq_bands.items():
                band_mask = (frequencies >= low) & (frequencies <= high)
                band_energy[band_name] = float(np.sum(magnitude[band_mask]))
            
            return {
                'dominant_frequencies': dominant_frequencies,
                'frequency_bands': band_energy,
                'spectral_centroid': float(np.sum(frequencies * magnitude) / np.sum(magnitude)),
                'spectral_bandwidth': float(np.sqrt(np.sum(((frequencies - np.sum(frequencies * magnitude) / np.sum(magnitude)) ** 2) * magnitude) / np.sum(magnitude)))
            }
            
        except Exception as e:
            logger.error(f"Error in frequency analysis: {e}")
            return {}


class AudioExporter:
    """Audio export and format conversion utilities."""
    
    @staticmethod
    def export_stems(stems: Dict[str, np.ndarray], sr: int, output_dir: str, 
                    format: str = 'wav', quality: str = 'high') -> Dict[str, str]:
        """Export separated stems to files."""
        try:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            exported_files = {}
            
            # Quality settings
            quality_settings = {
                'wav': {'subtype': 'PCM_24' if quality == 'high' else 'PCM_16'},
                'flac': {'subtype': 'PCM_24' if quality == 'high' else 'PCM_16'},
                'mp3': {'format': 'MP3', 'bitrate': '320k' if quality == 'high' else '192k'}
            }
            
            for stem_name, stem_audio in stems.items():
                # Normalize audio
                if np.max(np.abs(stem_audio)) > 0:
                    stem_audio = stem_audio / np.max(np.abs(stem_audio)) * 0.95
                
                filename = f"{stem_name}.{format}"
                filepath = output_dir / filename
                
                if format in ['wav', 'flac']:
                    sf.write(str(filepath), stem_audio, sr, **quality_settings[format])
                else:
                    # For MP3 and other formats, use temporary WAV then convert
                    temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                    sf.write(temp_wav.name, stem_audio, sr)
                    
                    # Convert using pydub
                    from pydub import AudioSegment
                    audio_segment = AudioSegment.from_wav(temp_wav.name)
                    
                    if format == 'mp3':
                        bitrate = quality_settings['mp3']['bitrate']
                        audio_segment.export(str(filepath), format="mp3", bitrate=bitrate)
                    
                    # Clean up temp file
                    Path(temp_wav.name).unlink()
                
                exported_files[stem_name] = str(filepath)
                logger.info(f"Exported {stem_name} to {filepath}")
            
            return exported_files
            
        except Exception as e:
            logger.error(f"Error exporting stems: {e}")
            raise
    
    @staticmethod
    def create_mix_preview(stems: Dict[str, np.ndarray], sr: int, 
                          mix_settings: Dict[str, float]) -> np.ndarray:
        """Create a preview mix with adjustable stem volumes."""
        try:
            if not stems:
                raise ValueError("No stems provided for mixing")
            
            # Get the length of the longest stem
            max_length = max(len(stem) for stem in stems.values())
            
            # Initialize mix
            mix = np.zeros(max_length)
            
            for stem_name, stem_audio in stems.items():
                # Get volume setting (default to 1.0)
                volume = mix_settings.get(stem_name, 1.0)
                
                # Pad shorter stems with zeros
                if len(stem_audio) < max_length:
                    padded_stem = np.pad(stem_audio, (0, max_length - len(stem_audio)))
                else:
                    padded_stem = stem_audio[:max_length]
                
                # Add to mix with volume scaling
                mix += padded_stem * volume
            
            # Normalize to prevent clipping
            if np.max(np.abs(mix)) > 0:
                mix = mix / np.max(np.abs(mix)) * 0.95
            
            return mix
            
        except Exception as e:
            logger.error(f"Error creating mix preview: {e}")
            raise
    
    def separate_audio(self, input_path: str, output_dir: str, 
                      stems: List[str] = None, quality: str = 'balanced',
                      progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Main audio separation method for task processing.
        
        Args:
            input_path: Path to input audio file
            output_dir: Directory to save separated stems
            stems: List of stem types to extract
            quality: Quality setting ('fast', 'balanced', 'high')
            progress_callback: Progress callback function
        
        Returns:
            Dictionary with separation results
        """
        start_time = time.time()
        
        try:
            if progress_callback:
                progress_callback(0, "Validating audio file...")
            
            # Validate input
            validation = self.validate_audio_file(input_path)
            if not validation['valid']:
                return {'success': False, 'error': validation['error']}
            
            if progress_callback:
                progress_callback(5, "Loading audio...")
            
            # Load audio
            y, sr = librosa.load(input_path, sr=22050, mono=True)
            original_audio = y.copy()
            
            if progress_callback:
                progress_callback(15, "Selecting separation algorithm...")
            
            # Choose algorithm based on quality setting
            if quality == 'fast':
                if len(y.shape) == 1:
                    # For mono, use simple NMF
                    separated_stems = AudioSeparationMethods.separate_with_nmf(
                        y, sr, n_components=2, progress_callback=progress_callback
                    )
                else:
                    separated_stems = AudioSeparationMethods.separate_with_median_filter(
                        y, sr, progress_callback=progress_callback
                    )
            elif quality == 'high':
                separated_stems = AudioSeparationMethods.separate_with_ica(
                    y, sr, n_components=4, progress_callback=progress_callback
                )
            else:  # balanced
                separated_stems = AudioSeparationMethods.separate_with_nmf(
                    y, sr, n_components=4, progress_callback=progress_callback
                )
            
            if progress_callback:
                progress_callback(85, "Assessing quality...")
            
            # Assess quality
            quality_scores = QualityAssessment.assess_separation_quality(
                separated_stems, original_audio, sr
            )
            
            if progress_callback:
                progress_callback(90, "Saving separated stems...")
            
            # Save stems
            os.makedirs(output_dir, exist_ok=True)
            saved_stems = []
            
            # Filter stems if specific ones requested
            if stems:
                filtered_stems = {k: v for k, v in separated_stems.items() if k in stems}
                separated_stems = filtered_stems
            
            for stem_name, stem_audio in separated_stems.items():
                if len(stem_audio) == 0:
                    continue
                    
                output_path = os.path.join(output_dir, f"{stem_name}.wav")
                
                # Normalize audio
                if np.max(np.abs(stem_audio)) > 0:
                    stem_audio = stem_audio / np.max(np.abs(stem_audio)) * 0.95
                
                # Save as WAV
                sf.write(output_path, stem_audio, sr, subtype='PCM_16')
                
                file_size = os.path.getsize(output_path)
                saved_stems.append({
                    'stem_type': stem_name,
                    'file_path': output_path,
                    'file_size': file_size,
                    'duration': len(stem_audio) / sr
                })
            
            processing_time = time.time() - start_time
            
            if progress_callback:
                progress_callback(100, "Separation completed!")
            
            return {
                'success': True,
                'stems': saved_stems,
                'quality_scores': quality_scores,
                'processing_time': processing_time,
                'original_duration': validation['duration'],
                'algorithm_used': quality,
                'metadata': {
                    'sample_rate': sr,
                    'input_format': validation['format'],
                    'output_format': 'wav'
                }
            }
            
        except Exception as e:
            logger.error(f"Audio separation error: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
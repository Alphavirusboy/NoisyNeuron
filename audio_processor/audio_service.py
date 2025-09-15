"""
Enhanced Audio Processing Service for NoisyNeuron

This module provides professional-grade audio processing capabilities including:
- Advanced source separation using multiple AI models (Demucs, Spleeter)
- Real-time progress tracking and WebSocket updates
- Comprehensive audio analysis and quality metrics
- Professional audio effects and enhancement
- Support for multiple audio formats and high-quality output
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
import json
import warnings
import asyncio
from typing import Dict, List, Tuple, Optional, Any, Callable
from pathlib import Path
import time
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

# Import AI models for source separation (with fallbacks)
try:
    import torch
    import torchaudio
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("PyTorch not available. GPU acceleration disabled.")

try:
    import demucs.separate
    from demucs.pretrained import get_model
    DEMUCS_AVAILABLE = True
except ImportError:
    DEMUCS_AVAILABLE = False
    logging.warning("Demucs not available. Install with: pip install demucs")

try:
    from spleeter.separator import Separator
    SPLEETER_AVAILABLE = True
except ImportError:
    SPLEETER_AVAILABLE = False
    logging.warning("Spleeter not available. Install with: pip install spleeter")

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


class ProcessingStatus(Enum):
    """Enum for processing status tracking."""
    PENDING = "pending"
    PREPROCESSING = "preprocessing"
    ANALYZING = "analyzing"
    SEPARATING = "separating"
    POSTPROCESSING = "postprocessing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProcessingProgress:
    """Data class for tracking processing progress."""
    status: ProcessingStatus
    progress: float  # 0.0 to 1.0
    message: str
    current_step: str
    total_steps: int
    current_step_num: int
    estimated_time_remaining: Optional[float] = None
    error: Optional[str] = None


class EnhancedAudioProcessor:
    """Professional audio processor with AI-powered source separation."""
    
    def __init__(self, use_gpu: bool = True, progress_callback: Optional[Callable] = None):
        """Initialize the enhanced audio processor."""
        self.use_gpu = use_gpu and TORCH_AVAILABLE and torch.cuda.is_available()
        self.device = torch.device('cuda' if self.use_gpu else 'cpu') if TORCH_AVAILABLE else None
        self.progress_callback = progress_callback
        
        # Audio processing parameters
        self.supported_formats = [
            'wav', 'mp3', 'flac', 'ogg', 'm4a', 'aac', 'wma', 'aiff', 'au'
        ]
        self.sample_rate = 44100  # Professional sample rate
        self.hop_length = 512
        self.n_fft = 2048
        
        # Initialize models
        self.demucs_model = None
        self.spleeter_separator = None
        
        logger.info(f"Enhanced Audio Processor initialized (GPU: {self.use_gpu})")
    
    def validate_audio_file_upload(self, audio_file):
        """Validate uploaded audio file."""
        try:
            # Check file size (500MB limit)
            max_size = 500 * 1024 * 1024
            if audio_file.size > max_size:
                return {'valid': False, 'error': f'File too large. Maximum size is {max_size//1024//1024}MB'}
            
            # Check file format
            file_ext = os.path.splitext(audio_file.name)[1].lower().strip('.')
            if file_ext not in self.supported_formats:
                return {'valid': False, 'error': f'Unsupported format. Supported: {", ".join(self.supported_formats)}'}
            
            return {
                'valid': True,
                'format': file_ext,
                'size': audio_file.size,
                'name': audio_file.name
            }
            
        except Exception as e:
            return {'valid': False, 'error': f'Validation error: {str(e)}'}
    
    def quick_analyze(self, file_path: str):
        """Quick audio analysis without full processing."""
        try:
            # Use librosa for basic info
            duration = librosa.get_duration(path=file_path)
            y, sr = librosa.load(file_path, sr=None, duration=1)  # Load just 1 second
            
            return {
                'duration': duration,
                'sample_rate': sr,
                'channels': 1 if len(y.shape) == 1 else y.shape[0]
            }
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return {'duration': 0, 'sample_rate': 44100, 'channels': 2}
    
    def _update_progress(self, progress: ProcessingProgress):
        """Update processing progress."""
        if self.progress_callback:
            self.progress_callback(progress)
        logger.info(f"Progress: {progress.message} ({progress.progress:.1%})")
    
    def load_audio(self, file_path: str, normalize: bool = True) -> Tuple[np.ndarray, int]:
        """
        Load audio file with enhanced format support and error handling.
        
        Args:
            file_path: Path to audio file
            normalize: Whether to normalize audio amplitude
            
        Returns:
            Tuple of (audio_data, sample_rate)
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"Audio file not found: {file_path}")
            
            # Get file format
            file_ext = file_path.suffix.lower().lstrip('.')
            
            if file_ext not in self.supported_formats:
                raise ValueError(f"Unsupported audio format: {file_ext}")
            
            # Load audio based on format
            if file_ext in ['wav', 'flac', 'aiff']:
                # Use soundfile for lossless formats
                audio, sr = sf.read(str(file_path))
            else:
                # Use librosa for other formats (includes ffmpeg)
                audio, sr = librosa.load(str(file_path), sr=None)
            
            # Convert to mono if stereo
            if audio.ndim > 1:
                audio = librosa.to_mono(audio.T)
            
            # Resample to standard rate if needed
            if sr != self.sample_rate:
                audio = librosa.resample(audio, orig_sr=sr, target_sr=self.sample_rate)
                sr = self.sample_rate
            
            # Normalize if requested
            if normalize:
                audio = librosa.util.normalize(audio)
            
            # Remove silence from beginning and end
            audio, _ = librosa.effects.trim(audio, top_db=20)
            
            logger.info(f"Loaded audio: {file_path.name} ({len(audio)/sr:.1f}s, {sr}Hz)")
            return audio, sr
            
        except Exception as e:
            logger.error(f"Error loading audio {file_path}: {e}")
            raise
    
    def analyze_audio_quality(self, audio: np.ndarray, sr: int) -> Dict[str, Any]:
        """Analyze various quality metrics of audio."""
        quality_metrics = {}
        
        try:
            # Dynamic range
            rms = librosa.feature.rms(y=audio)[0]
            quality_metrics['dynamic_range'] = float(np.max(rms) - np.min(rms))
            
            # Spectral centroid (brightness)
            spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
            quality_metrics['spectral_centroid_mean'] = float(np.mean(spectral_centroids))
            
            # Zero crossing rate (roughness)
            zcr = librosa.feature.zero_crossing_rate(audio)[0]
            quality_metrics['zero_crossing_rate'] = float(np.mean(zcr))
            
            # Spectral rolloff
            rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)[0]
            quality_metrics['spectral_rolloff'] = float(np.mean(rolloff))
            
            # MFCC features
            mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
            quality_metrics['mfcc_features'] = [float(np.mean(mfcc)) for mfcc in mfccs]
            
            # Tempo detection
            tempo, _ = librosa.beat.beat_track(y=audio, sr=sr)
            quality_metrics['tempo'] = float(tempo)
            
            # Key detection
            chroma = librosa.feature.chroma_stft(y=audio, sr=sr)
            quality_metrics['key_strength'] = float(np.max(np.mean(chroma, axis=1)))
            
        except Exception as e:
            logger.warning(f"Error in quality analysis: {e}")
            quality_metrics['error'] = str(e)
        
        return quality_metrics
    
    def separate_with_nmf(self, audio: np.ndarray, sr: int, n_components: int = 4) -> Dict[str, np.ndarray]:
        """Separate audio using Non-negative Matrix Factorization."""
        try:
            # Compute magnitude spectrogram
            stft = librosa.stft(audio, hop_length=self.hop_length, n_fft=self.n_fft)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # Apply NMF
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
                component_audio = librosa.istft(component_stft, hop_length=self.hop_length)
                separated_stems[stem_name] = component_audio
            
            logger.info(f"NMF separation completed with {n_components} components")
            return separated_stems
            
        except Exception as e:
            logger.error(f"Error in NMF separation: {e}")
            raise
    
    def harmonic_percussive_separation(self, audio: np.ndarray, sr: int) -> Dict[str, np.ndarray]:
        """Separate harmonic and percussive components."""
        try:
            # Perform harmonic-percussive separation
            harmonic, percussive = librosa.effects.hpss(audio)
            
            # Simple vocal extraction using spectral subtraction
            stft_harmonic = librosa.stft(harmonic)
            stft_original = librosa.stft(audio)
            
            # Create vocal mask (simplified approach)
            magnitude_harmonic = np.abs(stft_harmonic)
            magnitude_original = np.abs(stft_original)
            
            vocal_mask = magnitude_harmonic / (magnitude_original + 1e-10)
            vocal_mask = np.clip(vocal_mask, 0, 1)
            
            # Apply mask
            vocal_stft = stft_original * vocal_mask
            vocals = librosa.istft(vocal_stft)
            
            # Create instrumental track
            instrumental = audio - vocals * 0.5
            
            return {
                'harmonic': harmonic,
                'percussive': percussive,
                'vocals': vocals,
                'instrumental': instrumental
            }
            
        except Exception as e:
            logger.error(f"Error in harmonic-percussive separation: {e}")
            raise
    
    async def separate_audio_advanced(self, file_path: str, method: str = 'auto', 
                                    options: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Perform advanced audio source separation.
        
        Args:
            file_path: Path to input audio file
            method: Separation method ('demucs', 'spleeter', 'nmf', 'hpss', 'auto')
            options: Additional options for separation
            
        Returns:
            Dictionary containing separated stems and metadata
        """
        options = options or {}
        start_time = time.time()
        
        try:
            # Initialize progress tracking
            progress = ProcessingProgress(
                status=ProcessingStatus.PREPROCESSING,
                progress=0.0,
                message="Loading audio file...",
                current_step="loading",
                total_steps=5,
                current_step_num=1
            )
            self._update_progress(progress)
            
            # Load audio
            audio, sr = self.load_audio(file_path, normalize=True)
            
            progress.progress = 0.2
            progress.message = "Analyzing audio characteristics..."
            progress.current_step = "analyzing"
            progress.current_step_num = 2
            progress.status = ProcessingStatus.ANALYZING
            self._update_progress(progress)
            
            # Analyze audio quality
            quality_metrics = self.analyze_audio_quality(audio, sr)
            
            # Choose separation method
            if method == 'auto':
                method = self._choose_best_method(audio, sr, quality_metrics)
                logger.info(f"Auto-selected separation method: {method}")
            
            progress.progress = 0.4
            progress.message = f"Separating audio using {method.upper()}..."
            progress.current_step = "separating"
            progress.current_step_num = 3
            progress.status = ProcessingStatus.SEPARATING
            self._update_progress(progress)
            
            # Perform separation based on method
            if method == 'demucs' and DEMUCS_AVAILABLE:
                separated_stems = await self.separate_with_demucs(file_path, options)
            elif method == 'spleeter' and SPLEETER_AVAILABLE:
                separated_stems = await self.separate_with_spleeter(file_path, options)
            elif method == 'nmf':
                n_components = options.get('n_components', 4)
                separated_stems = self.separate_with_nmf(audio, sr, n_components)
            elif method == 'hpss':
                separated_stems = self.harmonic_percussive_separation(audio, sr)
            else:
                # Fallback to available method
                if DEMUCS_AVAILABLE:
                    separated_stems = await self.separate_with_demucs(file_path, options)
                elif SPLEETER_AVAILABLE:
                    separated_stems = await self.separate_with_spleeter(file_path, options)
                else:
                    separated_stems = self.harmonic_percussive_separation(audio, sr)
            
            progress.progress = 0.8
            progress.message = "Post-processing stems..."
            progress.current_step = "postprocessing"
            progress.current_step_num = 4
            progress.status = ProcessingStatus.POSTPROCESSING
            self._update_progress(progress)
            
            # Post-process stems
            processed_stems = self._post_process_stems(separated_stems, sr, options)
            
            progress.progress = 1.0
            progress.message = "Separation completed successfully!"
            progress.current_step = "completed"
            progress.current_step_num = 5
            progress.status = ProcessingStatus.COMPLETED
            self._update_progress(progress)
            
            processing_time = time.time() - start_time
            
            # Prepare result
            result = {
                'success': True,
                'stems': processed_stems,
                'metadata': {
                    'method_used': method,
                    'processing_time': processing_time,
                    'sample_rate': sr,
                    'original_duration': len(audio) / sr,
                    'quality_metrics': quality_metrics,
                    'options_used': options
                }
            }
            
            logger.info(f"Audio separation completed in {processing_time:.2f}s using {method}")
            return result
            
        except Exception as e:
            error_msg = f"Error in audio separation: {str(e)}"
            logger.error(error_msg)
            
            progress = ProcessingProgress(
                status=ProcessingStatus.FAILED,
                progress=0.0,
                message="Separation failed",
                current_step="error",
                total_steps=5,
                current_step_num=0,
                error=error_msg
            )
            self._update_progress(progress)
            
            return {
                'success': False,
                'error': error_msg,
                'stems': {},
                'metadata': {}
            }
    
    async def separate_with_demucs(self, file_path: str, options: Dict = None) -> Dict[str, np.ndarray]:
        """Separate audio using Facebook's Demucs model."""
        if not DEMUCS_AVAILABLE:
            raise RuntimeError("Demucs not available. Install with: pip install demucs")
        
        options = options or {}
        model_name = options.get('model', 'htdemucs')  # Use latest model by default
        
        try:
            # Initialize model if not already loaded
            if self.demucs_model is None or self.demucs_model.name != model_name:
                logger.info(f"Loading Demucs model: {model_name}")
                self.demucs_model = get_model(model_name)
                if self.use_gpu and self.device:
                    self.demucs_model.to(self.device)
            
            # Create temporary output directory
            with tempfile.TemporaryDirectory() as temp_dir:
                output_dir = Path(temp_dir) / 'separated'
                
                # Run Demucs separation
                await asyncio.get_event_loop().run_in_executor(
                    None, 
                    demucs.separate.separate,
                    [str(file_path)],
                    model_name,
                    self.device,
                    str(output_dir)
                )
                
                # Load separated stems
                stems = {}
                stem_names = ['drums', 'bass', 'other', 'vocals']
                
                for stem_name in stem_names:
                    stem_file = output_dir / model_name / Path(file_path).stem / f"{stem_name}.wav"
                    if stem_file.exists():
                        stem_audio, _ = librosa.load(str(stem_file), sr=self.sample_rate)
                        stems[stem_name] = stem_audio
                
                logger.info(f"Demucs separation completed with {len(stems)} stems")
                return stems
                
        except Exception as e:
            logger.error(f"Error in Demucs separation: {e}")
            raise
    
    async def separate_with_spleeter(self, file_path: str, options: Dict = None) -> Dict[str, np.ndarray]:
        """Separate audio using Deezer's Spleeter model."""
        if not SPLEETER_AVAILABLE:
            raise RuntimeError("Spleeter not available. Install with: pip install spleeter")
        
        options = options or {}
        config = options.get('config', '5stems-config')  # Use 5-stem model by default
        
        try:
            # Initialize Spleeter if not already loaded
            if self.spleeter_separator is None or self.spleeter_separator._params['audio']['sample_rate'] != self.sample_rate:
                logger.info(f"Loading Spleeter model: {config}")
                self.spleeter_separator = Separator(
                    config,
                    stft_backend='tensorflow',
                    multiprocess=False
                )
            
            # Load audio in Spleeter format
            audio, sr = librosa.load(file_path, sr=self.sample_rate, mono=False)
            if audio.ndim == 1:
                audio = np.expand_dims(audio, axis=1)
            else:
                audio = audio.T
            
            # Perform separation
            separation_result = await asyncio.get_event_loop().run_in_executor(
                None,
                self.spleeter_separator.separate,
                audio
            )
            
            # Convert results to our format
            stems = {}
            for stem_name, stem_audio in separation_result.items():
                # Convert to mono if stereo
                if stem_audio.ndim > 1:
                    stem_audio = librosa.to_mono(stem_audio.T)
                stems[stem_name] = stem_audio
            
            logger.info(f"Spleeter separation completed with {len(stems)} stems")
            return stems
            
        except Exception as e:
            logger.error(f"Error in Spleeter separation: {e}")
            raise
    
    def _choose_best_method(self, audio: np.ndarray, sr: int, quality_metrics: Dict) -> str:
        """Choose the best separation method based on audio characteristics and available models."""
        try:
            duration = len(audio) / sr
            dynamic_range = quality_metrics.get('dynamic_range', 0)
            tempo = quality_metrics.get('tempo', 120)
            
            # Prioritize AI models if available
            if DEMUCS_AVAILABLE and duration > 30:  # Demucs works best on longer tracks
                return 'demucs'
            elif SPLEETER_AVAILABLE:  # Spleeter is fast and reliable
                return 'spleeter'
            elif dynamic_range > 0.5:  # Complex mixes benefit from NMF
                return 'nmf'
            else:
                return 'hpss'  # Fallback method
                
        except Exception as e:
            logger.warning(f"Error choosing method, defaulting to best available: {e}")
            # Return best available method
            if DEMUCS_AVAILABLE:
                return 'demucs'
            elif SPLEETER_AVAILABLE:
                return 'spleeter'
            else:
                return 'hpss'
    
    def _post_process_stems(self, stems: Dict[str, np.ndarray], sr: int, 
                           options: Dict) -> Dict[str, np.ndarray]:
        """Post-process separated stems."""
        processed_stems = {}
        
        for stem_name, stem_audio in stems.items():
            try:
                processed_audio = stem_audio.copy()
                
                # Normalize
                if np.max(np.abs(processed_audio)) > 0:
                    processed_audio = librosa.util.normalize(processed_audio)
                
                processed_stems[stem_name] = processed_audio
                
            except Exception as e:
                logger.warning(f"Error post-processing {stem_name}: {e}")
                processed_stems[stem_name] = stem_audio
        
        return processed_stems
    
    def reduce_noise(self, audio: np.ndarray, sr: int, noise_level: float = 0.1) -> np.ndarray:
        """Apply spectral gating noise reduction."""
        try:
            # Compute spectral magnitude
            stft = librosa.stft(audio, hop_length=self.hop_length, n_fft=self.n_fft)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # Estimate noise floor from quiet sections
            rms = librosa.feature.rms(y=audio, hop_length=self.hop_length)[0]
            noise_threshold = np.percentile(rms, 20) * (1 + noise_level)
            
            # Create noise gate mask
            gate_mask = np.where(rms > noise_threshold, 1.0, noise_level)
            gate_mask = np.repeat(gate_mask[np.newaxis, :], magnitude.shape[0], axis=0)
            
            # Apply gate to magnitude
            gated_magnitude = magnitude * gate_mask
            
            # Reconstruct audio
            gated_stft = gated_magnitude * np.exp(1j * phase)
            cleaned_audio = librosa.istft(gated_stft, hop_length=self.hop_length)
            
            logger.info("Noise reduction applied successfully")
            return cleaned_audio
            
        except Exception as e:
            logger.error(f"Error in noise reduction: {e}")
            return audio
    
    def enhance_audio(self, audio: np.ndarray, sr: int, options: Dict = None) -> np.ndarray:
        """Apply professional audio enhancement."""
        options = options or {}
        enhanced = audio.copy()
        
        try:
            # Apply compression if requested
            if options.get('compression', False):
                enhanced = self._apply_compression(enhanced, sr, options.get('compression_ratio', 3.0))
            
            # Apply EQ if requested
            if options.get('eq', False):
                enhanced = self._apply_eq(enhanced, sr, options.get('eq_settings', {}))
            
            # Apply stereo widening for stereo content
            if enhanced.ndim > 1 and options.get('stereo_widening', False):
                enhanced = self._apply_stereo_widening(enhanced, options.get('width_factor', 1.5))
            
            # Apply harmonic enhancement
            if options.get('harmonic_enhancement', False):
                enhanced = self._apply_harmonic_enhancement(enhanced, sr)
            
            logger.info("Audio enhancement applied successfully")
            return enhanced
            
        except Exception as e:
            logger.error(f"Error in audio enhancement: {e}")
            return audio
    
    def _apply_compression(self, audio: np.ndarray, sr: int, ratio: float = 3.0) -> np.ndarray:
        """Apply dynamic range compression."""
        try:
            # Simple compression using envelope following
            envelope = np.abs(audio)
            threshold = np.percentile(envelope, 70)
            
            # Apply compression
            compressed = np.where(
                envelope > threshold,
                threshold + (envelope - threshold) / ratio,
                envelope
            )
            
            # Maintain original sign
            return compressed * np.sign(audio)
            
        except Exception as e:
            logger.warning(f"Error in compression: {e}")
            return audio
    
    def _apply_eq(self, audio: np.ndarray, sr: int, eq_settings: Dict) -> np.ndarray:
        """Apply equalizer with frequency band adjustments."""
        try:
            # Define frequency bands (Hz)
            bands = {
                'low': (80, 250),
                'low_mid': (250, 1000),
                'mid': (1000, 4000),
                'high_mid': (4000, 8000),
                'high': (8000, sr//2)
            }
            
            # Apply filtering for each band
            equalized = audio.copy()
            
            for band_name, (low_freq, high_freq) in bands.items():
                gain_db = eq_settings.get(band_name, 0.0)
                if abs(gain_db) > 0.1:  # Only apply if significant gain
                    gain_linear = 10 ** (gain_db / 20)
                    
                    # Create bandpass filter
                    nyquist = sr / 2
                    low = low_freq / nyquist
                    high = min(high_freq / nyquist, 0.99)
                    
                    if low < high:
                        b, a = scipy.signal.butter(4, [low, high], btype='band')
                        band_signal = scipy.signal.filtfilt(b, a, audio)
                        equalized += band_signal * (gain_linear - 1)
            
            return equalized
            
        except Exception as e:
            logger.warning(f"Error in EQ: {e}")
            return audio
    
    def _apply_harmonic_enhancement(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Apply subtle harmonic enhancement."""
        try:
            # Generate harmonics
            harmonics = np.zeros_like(audio)
            
            # Add second harmonic (octave)
            harmonic_2 = librosa.effects.pitch_shift(audio, sr=sr, n_steps=12, bins_per_octave=12)
            harmonics += harmonic_2 * 0.1
            
            # Add third harmonic (fifth + octave)
            harmonic_3 = librosa.effects.pitch_shift(audio, sr=sr, n_steps=19, bins_per_octave=12)
            harmonics += harmonic_3 * 0.05
            
            # Blend with original
            enhanced = audio + harmonics
            
            # Normalize to prevent clipping
            if np.max(np.abs(enhanced)) > 1.0:
                enhanced = enhanced / np.max(np.abs(enhanced)) * 0.95
            
            return enhanced
            
        except Exception as e:
            logger.warning(f"Error in harmonic enhancement: {e}")
            return audio
    
    def validate_audio_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate audio file for processing.
        
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
            'file_size': 0,
            'channels': 0,
            'sample_rate': 0
        }
        
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                validation['error'] = "File not found"
                return validation
            
            validation['file_size'] = file_path.stat().st_size
            
            file_ext = file_path.suffix.lower().lstrip('.')
            if file_ext not in self.supported_formats:
                validation['error'] = f"Unsupported format: {file_ext}"
                return validation
            
            validation['format'] = file_ext
            
            # Try to get audio info
            try:
                info = sf.info(str(file_path))
                validation['duration'] = info.duration
                validation['channels'] = info.channels
                validation['sample_rate'] = info.samplerate
            except:
                # Fallback to librosa
                audio, sr = librosa.load(str(file_path), sr=None, duration=1)
                validation['duration'] = len(audio) / sr
                validation['sample_rate'] = sr
                validation['channels'] = 1 if audio.ndim == 1 else audio.shape[0]
            
            # Validation checks
            if validation['duration'] > 600:  # 10 minutes max
                validation['error'] = "Audio file too long (max 10 minutes)"
                return validation
            
            if validation['file_size'] > 100 * 1024 * 1024:  # 100MB max
                validation['error'] = "File too large (max 100MB)"
                return validation
            
            if validation['duration'] < 1:
                validation['error'] = "Audio file too short (minimum 1 second)"
                return validation
            
            validation['is_valid'] = True
            
        except Exception as e:
            validation['error'] = f"Error validating file: {str(e)}"
        
        return validation
    
    def export_stems(self, stems: Dict[str, np.ndarray], sr: int, output_dir: str, 
                    format: str = 'wav') -> Dict[str, str]:
        """Export separated stems to files."""
        try:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            exported_files = {}
            
            for stem_name, stem_audio in stems.items():
                # Normalize audio
                if np.max(np.abs(stem_audio)) > 0:
                    stem_audio = stem_audio / np.max(np.abs(stem_audio)) * 0.95
                
                filename = f"{stem_name}.{format}"
                filepath = output_dir / filename
                
                if format == 'wav':
                    sf.write(str(filepath), stem_audio, sr)
                else:
                    # Use temporary WAV then convert
                    temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                    sf.write(temp_wav.name, stem_audio, sr)
                    
                    from pydub import AudioSegment
                    audio_segment = AudioSegment.from_wav(temp_wav.name)
                    audio_segment.export(str(filepath), format=format)
                    
                    Path(temp_wav.name).unlink()
                
                exported_files[stem_name] = str(filepath)
                logger.info(f"Exported {stem_name} to {filepath}")
            
            return exported_files
            
        except Exception as e:
            logger.error(f"Error exporting stems: {e}")
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
            
            # Load audio
            if progress_callback:
                progress_callback(5, "Loading audio...")
            
            y, sr = self.load_audio(input_path)
            original_audio = y.copy()
            
            if progress_callback:
                progress_callback(15, "Starting separation...")
            
            # Perform separation using existing methods
            if quality == 'fast':
                # Use simple NMF-based separation
                stems_data = self._separate_with_nmf(y, sr, progress_callback)
            elif quality == 'high':
                # Use advanced separation
                stems_data = self._separate_with_advanced_method(y, sr, progress_callback)
            else:  # balanced
                # Use harmonic-percussive separation + NMF
                stems_data = self._separate_balanced(y, sr, progress_callback)
            
            if progress_callback:
                progress_callback(85, "Assessing quality...")
            
            # Calculate quality scores
            quality_scores = self._assess_quality(stems_data, original_audio, sr)
            
            if progress_callback:
                progress_callback(90, "Saving separated stems...")
            
            # Save stems to files
            os.makedirs(output_dir, exist_ok=True)
            saved_stems = []
            
            # Filter stems if specific ones requested
            if stems:
                filtered_stems = {k: v for k, v in stems_data.items() if k in stems}
                stems_data = filtered_stems
            
            for stem_name, stem_audio in stems_data.items():
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
                'algorithm_used': quality,
                'metadata': {
                    'sample_rate': sr,
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
    
    def _separate_with_nmf(self, y: np.ndarray, sr: int, progress_callback=None) -> Dict[str, np.ndarray]:
        """Simple NMF-based separation."""
        if progress_callback:
            progress_callback(20, "Computing spectrogram...")
        
        # Compute magnitude spectrogram
        D = librosa.stft(y, hop_length=512, n_fft=2048)
        magnitude = np.abs(D)
        phase = np.angle(D)
        
        if progress_callback:
            progress_callback(40, "Applying NMF decomposition...")
        
        # Apply NMF
        from sklearn.decomposition import NMF
        nmf = NMF(n_components=4, random_state=42, max_iter=100)
        W = nmf.fit_transform(magnitude)
        H = nmf.components_
        
        if progress_callback:
            progress_callback(70, "Reconstructing audio stems...")
        
        # Reconstruct separated sources
        stems = {}
        stem_names = ['vocals', 'drums', 'bass', 'other']
        
        for i, name in enumerate(stem_names):
            # Reconstruct magnitude
            source_activation = np.outer(W[:, i], H[i, :])
            
            # Create soft mask
            total_activation = W @ H
            mask = source_activation / (total_activation + 1e-10)
            mask = np.clip(mask, 0.0, 1.0)
            
            # Apply mask to original magnitude
            masked_magnitude = magnitude * mask
            
            # Apply phase
            reconstructed_complex = masked_magnitude * np.exp(1j * phase)
            
            # Convert back to time domain
            stem_audio = librosa.istft(
                reconstructed_complex,
                hop_length=512,
                length=len(y)
            )
            stems[name] = stem_audio
        
        return stems
    
    def _separate_with_advanced_method(self, y: np.ndarray, sr: int, progress_callback=None) -> Dict[str, np.ndarray]:
        """Advanced separation using ICA."""
        if progress_callback:
            progress_callback(20, "Computing spectrogram...")
        
        # Convert to spectrogram
        D = librosa.stft(y, hop_length=512, n_fft=2048)
        magnitude = np.abs(D)
        phase = np.angle(D)
        
        if progress_callback:
            progress_callback(40, "Applying ICA decomposition...")
        
        # Apply ICA to magnitude spectrogram
        from sklearn.decomposition import FastICA
        ica = FastICA(n_components=4, random_state=42, max_iter=500)
        
        # Reshape for ICA
        magnitude_reshaped = magnitude.reshape(magnitude.shape[0], -1)
        sources = ica.fit_transform(magnitude_reshaped.T).T
        
        if progress_callback:
            progress_callback(70, "Reconstructing audio stems...")
        
        # Reconstruct sources
        stems = {}
        stem_names = ['vocals', 'drums', 'bass', 'other']
        
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
        
        return stems
    
    def _separate_balanced(self, y: np.ndarray, sr: int, progress_callback=None) -> Dict[str, np.ndarray]:
        """Balanced separation using harmonic-percussive separation + NMF."""
        if progress_callback:
            progress_callback(20, "Separating harmonic and percussive components...")
        
        # Harmonic-percussive separation
        y_harmonic, y_percussive = librosa.effects.hpss(y, margin=3.0)
        
        if progress_callback:
            progress_callback(50, "Applying NMF to harmonic component...")
        
        # Apply NMF to harmonic component for vocals and instruments
        D_harmonic = librosa.stft(y_harmonic)
        magnitude_harmonic = np.abs(D_harmonic)
        phase_harmonic = np.angle(D_harmonic)
        
        from sklearn.decomposition import NMF
        nmf = NMF(n_components=3, random_state=42, max_iter=100)
        W_harmonic = nmf.fit_transform(magnitude_harmonic)
        H_harmonic = nmf.components_
        
        if progress_callback:
            progress_callback(75, "Reconstructing stems...")
        
        stems = {}
        
        # Reconstruct harmonic components
        harmonic_names = ['vocals', 'bass', 'other']
        for i, name in enumerate(harmonic_names):
            source_activation = np.outer(W_harmonic[:, i], H_harmonic[i, :])
            total_activation = W_harmonic @ H_harmonic
            mask = source_activation / (total_activation + 1e-10)
            mask = np.clip(mask, 0.0, 1.0)
            
            masked_magnitude = magnitude_harmonic * mask
            reconstructed_complex = masked_magnitude * np.exp(1j * phase_harmonic)
            
            stem_audio = librosa.istft(reconstructed_complex, length=len(y))
            stems[name] = stem_audio
        
        # Drums from percussive component
        stems['drums'] = y_percussive
        
        return stems
    
    def _assess_quality(self, stems: Dict[str, np.ndarray], original: np.ndarray, sr: int) -> Dict[str, float]:
        """Assess quality of separated stems."""
        quality_scores = {}
        
        for stem_name, stem_audio in stems.items():
            if len(stem_audio) == 0:
                quality_scores[stem_name] = 0.0
                continue
            
            # Ensure same length
            min_len = min(len(original), len(stem_audio))
            orig_trim = original[:min_len]
            stem_trim = stem_audio[:min_len]
            
            # Calculate simple quality metrics
            # Signal-to-noise ratio estimation
            stem_power = np.mean(stem_trim ** 2)
            if stem_power > 0:
                quality_score = min(100, stem_power * 100)  # Simple power-based score
            else:
                quality_score = 0.0
            
            quality_scores[stem_name] = quality_score
        
        return quality_scores


# Create backwards-compatible alias
AudioProcessor = EnhancedAudioProcessor
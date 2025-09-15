"""
Markov Chain Implementation for Audio Source Separation

This module implements Markov chains for analyzing audio patterns and improving
source separation quality. The implementation uses spectral features and 
temporal patterns to model instrument characteristics.
"""

import numpy as np
import librosa
import scipy.signal
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from collections import defaultdict, Counter
import json
import pickle
from typing import List, Dict, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)

class AudioMarkovChain:
    """
    Markov Chain implementation for audio source separation.
    
    This class implements a Hidden Markov Model-like approach where:
    - States represent different spectral/timbral characteristics
    - Transitions model how these characteristics change over time
    - The model helps identify and separate different instruments
    """
    
    def __init__(self, order: int = 2, n_states: int = 16, feature_type: str = 'mfcc'):
        """
        Initialize the Markov chain.
        
        Args:
            order: Order of the Markov chain (memory length)
            n_states: Number of discrete states
            feature_type: Type of features to extract ('mfcc', 'spectral', 'chroma')
        """
        self.order = order
        self.n_states = n_states
        self.feature_type = feature_type
        
        # Markov chain components
        self.transition_matrix = np.zeros((n_states ** order, n_states))
        self.state_counts = np.zeros(n_states ** order)
        self.emission_matrix = None
        
        # Feature extraction
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=n_states, random_state=42)
        
        # State mapping
        self.state_mapping = {}
        self.reverse_mapping = {}
        
        # Training status
        self.is_trained = False
        self.training_samples = 0
    
    def extract_features(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """
        Extract features from audio signal.
        
        Args:
            audio: Audio signal
            sr: Sample rate
            
        Returns:
            Feature matrix of shape (n_frames, n_features)
        """
        if self.feature_type == 'mfcc':
            # Extract MFCC features
            mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
            delta_mfccs = librosa.feature.delta(mfccs)
            delta2_mfccs = librosa.feature.delta(mfccs, order=2)
            features = np.vstack([mfccs, delta_mfccs, delta2_mfccs])
            
        elif self.feature_type == 'spectral':
            # Extract spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sr)
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=sr)
            zero_crossing_rate = librosa.feature.zero_crossing_rate(audio)
            features = np.vstack([spectral_centroids, spectral_rolloff, 
                                spectral_bandwidth, zero_crossing_rate])
            
        elif self.feature_type == 'chroma':
            # Extract chroma features
            chroma = librosa.feature.chroma_stft(y=audio, sr=sr)
            tonnetz = librosa.feature.tonnetz(y=audio, sr=sr)
            features = np.vstack([chroma, tonnetz])
            
        else:
            raise ValueError(f"Unknown feature type: {self.feature_type}")
        
        return features.T  # Transpose to (n_frames, n_features)
    
    def _quantize_features(self, features: np.ndarray) -> np.ndarray:
        """
        Quantize continuous features into discrete states.
        
        Args:
            features: Feature matrix
            
        Returns:
            State sequence
        """
        if not self.is_trained:
            # First time: fit the scaler and k-means
            normalized_features = self.scaler.fit_transform(features)
            states = self.kmeans.fit_predict(normalized_features)
        else:
            # Use pre-trained models
            normalized_features = self.scaler.transform(features)
            states = self.kmeans.predict(normalized_features)
        
        return states
    
    def _build_transition_matrix(self, state_sequence: np.ndarray):
        """
        Build transition matrix from state sequence.
        
        Args:
            state_sequence: Sequence of states
        """
        n_frames = len(state_sequence)
        
        for i in range(self.order, n_frames):
            # Get current state and history
            current_state = state_sequence[i]
            history = tuple(state_sequence[i-self.order:i])
            
            # Convert history tuple to index
            history_idx = self._history_to_index(history)
            
            # Update transition counts
            self.transition_matrix[history_idx, current_state] += 1
            self.state_counts[history_idx] += 1
    
    def _history_to_index(self, history: Tuple) -> int:
        """Convert state history to matrix index."""
        index = 0
        for i, state in enumerate(history):
            index += state * (self.n_states ** (self.order - 1 - i))
        return index
    
    def _index_to_history(self, index: int) -> Tuple:
        """Convert matrix index to state history."""
        history = []
        for i in range(self.order):
            history.append(index % self.n_states)
            index //= self.n_states
        return tuple(reversed(history))
    
    def train(self, audio_files: List[Tuple[np.ndarray, int]], instrument_type: str):
        """
        Train the Markov chain on audio data.
        
        Args:
            audio_files: List of (audio, sample_rate) tuples
            instrument_type: Type of instrument being modeled
        """
        logger.info(f"Training Markov chain for {instrument_type} with {len(audio_files)} files")
        
        all_features = []
        all_states = []
        
        # Extract features from all files
        for audio, sr in audio_files:
            features = self.extract_features(audio, sr)
            all_features.append(features)
        
        # Concatenate all features for clustering
        combined_features = np.vstack(all_features)
        
        # Quantize features into states
        all_state_sequences = []
        for features in all_features:
            states = self._quantize_features(features)
            all_state_sequences.append(states)
            all_states.extend(states)
        
        # Build transition matrix
        for state_sequence in all_state_sequences:
            self._build_transition_matrix(state_sequence)
        
        # Normalize transition matrix
        for i in range(len(self.transition_matrix)):
            if self.state_counts[i] > 0:
                self.transition_matrix[i] /= self.state_counts[i]
        
        self.is_trained = True
        self.training_samples = len(audio_files)
        
        logger.info(f"Training completed. Processed {len(combined_features)} frames.")
    
    def predict_probability(self, audio: np.ndarray, sr: int) -> float:
        """
        Calculate the probability that an audio segment belongs to this model.
        
        Args:
            audio: Audio signal
            sr: Sample rate
            
        Returns:
            Log probability of the sequence
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        features = self.extract_features(audio, sr)
        states = self._quantize_features(features)
        
        log_prob = 0.0
        smoothing = 1e-10  # Laplace smoothing
        
        for i in range(self.order, len(states)):
            history = tuple(states[i-self.order:i])
            current_state = states[i]
            history_idx = self._history_to_index(history)
            
            # Get transition probability with smoothing
            prob = (self.transition_matrix[history_idx, current_state] + smoothing) / \
                   (self.state_counts[history_idx] + smoothing * self.n_states)
            
            log_prob += np.log(prob)
        
        return log_prob
    
    def generate_mask(self, audio: np.ndarray, sr: int, threshold: float = 0.5) -> np.ndarray:
        """
        Generate a separation mask based on Markov model predictions.
        
        Args:
            audio: Audio signal
            sr: Sample rate
            threshold: Threshold for mask generation
            
        Returns:
            Binary mask for source separation
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before mask generation")
        
        # Compute STFT
        stft = librosa.stft(audio)
        magnitude = np.abs(stft)
        
        # Extract features frame by frame
        features = self.extract_features(audio, sr)
        states = self._quantize_features(features)
        
        # Calculate frame-wise probabilities
        frame_probs = []
        for i in range(self.order, len(states)):
            history = tuple(states[i-self.order:i])
            history_idx = self._history_to_index(history)
            
            # Average probability across all possible next states
            prob = np.mean(self.transition_matrix[history_idx])
            frame_probs.append(prob)
        
        # Pad probabilities to match STFT frames
        frame_probs = np.array(frame_probs)
        if len(frame_probs) < magnitude.shape[1]:
            # Pad with mean probability
            padding = np.full(magnitude.shape[1] - len(frame_probs), np.mean(frame_probs))
            frame_probs = np.concatenate([frame_probs, padding])
        elif len(frame_probs) > magnitude.shape[1]:
            # Truncate
            frame_probs = frame_probs[:magnitude.shape[1]]
        
        # Create mask
        mask = (frame_probs > threshold).astype(float)
        
        # Apply smoothing to mask
        mask = scipy.signal.medfilt(mask, kernel_size=5)
        
        # Expand mask to frequency dimension
        mask = np.tile(mask, (magnitude.shape[0], 1))
        
        return mask
    
    def analyze_patterns(self, audio: np.ndarray, sr: int) -> Dict[str, Any]:
        """
        Analyze patterns in the audio using the Markov model.
        
        Args:
            audio: Audio signal
            sr: Sample rate
            
        Returns:
            Dictionary containing pattern analysis results
        """
        features = self.extract_features(audio, sr)
        states = self._quantize_features(features)
        
        # Calculate pattern statistics
        state_distribution = Counter(states)
        entropy = -sum(p * np.log2(p) for p in 
                      [count/len(states) for count in state_distribution.values()])
        
        # Calculate transition entropy
        transition_entropy = 0.0
        for i in range(self.order, len(states)):
            history = tuple(states[i-self.order:i])
            history_idx = self._history_to_index(history)
            
            if self.state_counts[history_idx] > 0:
                probs = self.transition_matrix[history_idx]
                probs = probs[probs > 0]  # Remove zero probabilities
                transition_entropy -= np.sum(probs * np.log2(probs))
        
        # Calculate complexity and predictability
        complexity = entropy / np.log2(self.n_states)  # Normalized entropy
        predictability = 1.0 - (transition_entropy / len(states))
        
        return {
            'entropy': entropy,
            'complexity': complexity,
            'predictability': max(0.0, predictability),
            'state_distribution': dict(state_distribution),
            'transition_entropy': transition_entropy,
            'n_unique_states': len(state_distribution),
            'avg_state_duration': len(states) / len(state_distribution)
        }
    
    def save_model(self, filepath: str):
        """Save the trained model to disk."""
        model_data = {
            'order': self.order,
            'n_states': self.n_states,
            'feature_type': self.feature_type,
            'transition_matrix': self.transition_matrix.tolist(),
            'state_counts': self.state_counts.tolist(),
            'is_trained': self.is_trained,
            'training_samples': self.training_samples,
            'scaler_mean': self.scaler.mean_.tolist() if hasattr(self.scaler, 'mean_') else None,
            'scaler_scale': self.scaler.scale_.tolist() if hasattr(self.scaler, 'scale_') else None,
            'kmeans_centers': self.kmeans.cluster_centers_.tolist() if hasattr(self.kmeans, 'cluster_centers_') else None
        }
        
        with open(filepath, 'w') as f:
            json.dump(model_data, f, indent=2)
    
    def load_model(self, filepath: str):
        """Load a trained model from disk."""
        with open(filepath, 'r') as f:
            model_data = json.load(f)
        
        self.order = model_data['order']
        self.n_states = model_data['n_states']
        self.feature_type = model_data['feature_type']
        self.transition_matrix = np.array(model_data['transition_matrix'])
        self.state_counts = np.array(model_data['state_counts'])
        self.is_trained = model_data['is_trained']
        self.training_samples = model_data['training_samples']
        
        # Restore scaler
        if model_data.get('scaler_mean') and model_data.get('scaler_scale'):
            self.scaler.mean_ = np.array(model_data['scaler_mean'])
            self.scaler.scale_ = np.array(model_data['scaler_scale'])
        
        # Restore k-means
        if model_data.get('kmeans_centers'):
            self.kmeans.cluster_centers_ = np.array(model_data['kmeans_centers'])

class AudioSourceSeparator:
    """
    Audio source separation using multiple Markov chains.
    """
    
    def __init__(self):
        self.models = {}  # instrument_type -> AudioMarkovChain
    
    def add_model(self, instrument_type: str, model: AudioMarkovChain):
        """Add a trained model for an instrument type."""
        self.models[instrument_type] = model
    
    def separate_sources(self, audio: np.ndarray, sr: int, 
                        target_instruments: List[str] = None) -> Dict[str, np.ndarray]:
        """
        Separate audio sources using trained Markov models.
        
        Args:
            audio: Input audio signal
            sr: Sample rate
            target_instruments: List of instruments to separate (None for all)
            
        Returns:
            Dictionary mapping instrument names to separated audio
        """
        if target_instruments is None:
            target_instruments = list(self.models.keys())
        
        # Compute STFT
        stft = librosa.stft(audio)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        separated_audio = {}
        
        for instrument in target_instruments:
            if instrument not in self.models:
                logger.warning(f"No model available for {instrument}")
                continue
            
            model = self.models[instrument]
            
            # Generate separation mask
            mask = model.generate_mask(audio, sr)
            
            # Apply mask to magnitude spectrogram
            separated_magnitude = magnitude * mask
            
            # Reconstruct audio
            separated_stft = separated_magnitude * np.exp(1j * phase)
            separated_audio[instrument] = librosa.istft(separated_stft)
        
        return separated_audio

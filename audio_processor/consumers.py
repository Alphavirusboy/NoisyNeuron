"""
WebSocket consumers for real-time audio processing updates.
"""

import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from audio_processor.audio_service import EnhancedAudioProcessor
from music_theory.theory_engine import EnhancedMusicTheoryEngine
import logging

logger = logging.getLogger(__name__)


class AudioProcessingConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time audio processing updates."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_group_name = None
        self.user_id = None
        self.audio_processor = EnhancedAudioProcessor()
        self.theory_engine = EnhancedMusicTheoryEngine()
    
    async def connect(self):
        """Handle WebSocket connection."""
        # Get user from session
        user = self.scope.get("user", AnonymousUser())
        
        # For demo purposes, allow anonymous users with a session ID
        if user.is_anonymous:
            # Use session key as user identifier for anonymous users
            session_key = self.scope.get('session', {}).get('session_key')
            if not session_key:
                # Generate a temporary session ID for the connection
                import uuid
                session_key = f"anon_{uuid.uuid4().hex[:8]}"
            self.user_id = f"anonymous_{session_key}"
        else:
            self.user_id = user.id
        
        self.room_group_name = f"audio_processing_{self.user_id}"
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to audio processing channel',
            'user_id': str(self.user_id),
            'is_anonymous': user.is_anonymous
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave room group
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle messages from WebSocket."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'start_processing':
                await self.handle_start_processing(data)
            elif message_type == 'request_progress':
                await self.handle_progress_request(data)
            elif message_type == 'cancel_processing':
                await self.handle_cancel_processing(data)
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error in WebSocket receive: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))
    
    async def handle_start_processing(self, data):
        """Handle start processing request."""
        try:
            processing_type = data.get('processing_type', 'source_separation')
            file_path = data.get('file_path')
            options = data.get('options', {})
            
            if not file_path:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'File path is required'
                }))
                return
            
            # Send processing started notification
            await self.send(text_data=json.dumps({
                'type': 'processing_started',
                'processing_type': processing_type,
                'file_path': file_path,
                'message': 'Audio processing started'
            }))
            
            # Start async processing
            if processing_type == 'source_separation':
                await self.process_source_separation(file_path, options)
            elif processing_type == 'harmony_analysis':
                await self.process_harmony_analysis(file_path, options)
            elif processing_type == 'noise_reduction':
                await self.process_noise_reduction(file_path, options)
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown processing type: {processing_type}'
                }))
                
        except Exception as e:
            logger.error(f"Error starting processing: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'processing_error',
                'message': f'Failed to start processing: {str(e)}'
            }))
    
    async def process_source_separation(self, file_path: str, options: dict):
        """Process audio source separation with progress updates."""
        try:
            method = options.get('method', 'demucs')
            
            # Send progress updates during processing
            await self.send_progress_update(10, "Initializing separation model...")
            
            # Simulate processing steps with progress updates
            if method == 'demucs':
                await self.send_progress_update(25, "Loading Demucs model...")
                await asyncio.sleep(1)  # Simulate model loading
                
                await self.send_progress_update(50, "Separating audio sources...")
                # Here you would call the actual separation method
                # For now, we'll simulate the process
                await asyncio.sleep(2)
                
                await self.send_progress_update(75, "Processing separated tracks...")
                await asyncio.sleep(1)
                
                await self.send_progress_update(90, "Finalizing output...")
                await asyncio.sleep(0.5)
                
                # Simulate successful completion
                result = {
                    'vocals': f"{file_path}_vocals.wav",
                    'drums': f"{file_path}_drums.wav", 
                    'bass': f"{file_path}_bass.wav",
                    'other': f"{file_path}_other.wav"
                }
                
                await self.send(text_data=json.dumps({
                    'type': 'processing_complete',
                    'processing_type': 'source_separation',
                    'method': method,
                    'result': result,
                    'message': 'Source separation completed successfully'
                }))
                
            elif method == 'spleeter':
                await self.send_progress_update(25, "Loading Spleeter model...")
                await asyncio.sleep(1)
                
                await self.send_progress_update(60, "Separating with Spleeter...")
                await asyncio.sleep(2)
                
                await self.send_progress_update(85, "Processing output files...")
                await asyncio.sleep(1)
                
                result = {
                    'vocals': f"{file_path}_vocals.wav",
                    'accompaniment': f"{file_path}_accompaniment.wav"
                }
                
                await self.send(text_data=json.dumps({
                    'type': 'processing_complete',
                    'processing_type': 'source_separation',
                    'method': method,
                    'result': result,
                    'message': 'Spleeter separation completed successfully'
                }))
            
        except Exception as e:
            logger.error(f"Error in source separation: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'processing_error',
                'message': f'Source separation failed: {str(e)}'
            }))
    
    async def process_harmony_analysis(self, file_path: str, options: dict):
        """Process harmony analysis with progress updates."""
        try:
            await self.send_progress_update(15, "Loading audio file...")
            await asyncio.sleep(0.5)
            
            await self.send_progress_update(30, "Extracting audio features...")
            await asyncio.sleep(1)
            
            await self.send_progress_update(50, "Analyzing harmonic content...")
            await asyncio.sleep(1)
            
            await self.send_progress_update(70, "Detecting key and chords...")
            await asyncio.sleep(1)
            
            await self.send_progress_update(85, "Generating recommendations...")
            await asyncio.sleep(0.5)
            
            # Simulate analysis result
            result = {
                'key_analysis': {
                    'key': 'C',
                    'mode': 'major',
                    'confidence': 0.85,
                    'scale_notes': ['C', 'D', 'E', 'F', 'G', 'A', 'B']
                },
                'chord_progression': [
                    {'chord': 'C', 'confidence': 0.92, 'timestamp': 0.0},
                    {'chord': 'Am', 'confidence': 0.88, 'timestamp': 2.0},
                    {'chord': 'F', 'confidence': 0.91, 'timestamp': 4.0},
                    {'chord': 'G', 'confidence': 0.89, 'timestamp': 6.0}
                ],
                'tempo': 120,
                'time_signature': '4/4',
                'mood_analysis': 'bright and energetic'
            }
            
            await self.send(text_data=json.dumps({
                'type': 'processing_complete',
                'processing_type': 'harmony_analysis',
                'result': result,
                'message': 'Harmony analysis completed successfully'
            }))
            
        except Exception as e:
            logger.error(f"Error in harmony analysis: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'processing_error',
                'message': f'Harmony analysis failed: {str(e)}'
            }))
    
    async def process_noise_reduction(self, file_path: str, options: dict):
        """Process noise reduction with progress updates."""
        try:
            strength = options.get('strength', 0.5)
            
            await self.send_progress_update(20, "Analyzing noise profile...")
            await asyncio.sleep(1)
            
            await self.send_progress_update(50, "Applying noise reduction...")
            await asyncio.sleep(2)
            
            await self.send_progress_update(80, "Enhancing audio quality...")
            await asyncio.sleep(1)
            
            result = {
                'output_file': f"{file_path}_cleaned.wav",
                'noise_reduction_db': -12,
                'quality_improvement': 15
            }
            
            await self.send(text_data=json.dumps({
                'type': 'processing_complete',
                'processing_type': 'noise_reduction',
                'result': result,
                'message': 'Noise reduction completed successfully'
            }))
            
        except Exception as e:
            logger.error(f"Error in noise reduction: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'processing_error',
                'message': f'Noise reduction failed: {str(e)}'
            }))
    
    async def send_progress_update(self, percentage: int, message: str):
        """Send progress update to client."""
        await self.send(text_data=json.dumps({
            'type': 'progress_update',
            'percentage': percentage,
            'message': message,
            'timestamp': asyncio.get_event_loop().time()
        }))
    
    async def handle_progress_request(self, data):
        """Handle progress request."""
        # In a real implementation, you would track processing status
        await self.send(text_data=json.dumps({
            'type': 'progress_response',
            'message': 'Progress tracking not yet implemented'
        }))
    
    async def handle_cancel_processing(self, data):
        """Handle cancel processing request."""
        # In a real implementation, you would cancel ongoing processing
        await self.send(text_data=json.dumps({
            'type': 'processing_cancelled',
            'message': 'Processing cancellation not yet implemented'
        }))
    
    # Group message handlers
    async def processing_update(self, event):
        """Handle processing update from group."""
        await self.send(text_data=json.dumps({
            'type': 'processing_update',
            'message': event['message'],
            'data': event.get('data', {})
        }))


class MusicTheoryConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time music theory interactions."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_group_name = None
        self.user_id = None
        self.theory_engine = EnhancedMusicTheoryEngine()
    
    async def connect(self):
        """Handle WebSocket connection."""
        user = self.scope.get("user", AnonymousUser())
        
        if user.is_anonymous:
            await self.close()
            return
        
        self.user_id = user.id
        self.room_group_name = f"music_theory_{self.user_id}"
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send welcome message with available features
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to music theory channel',
            'features': [
                'chord_analysis',
                'scale_generation',
                'key_detection',
                'chord_progressions',
                'substitutions',
                'practice_exercises'
            ]
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle messages from WebSocket."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'analyze_chord':
                await self.handle_chord_analysis(data)
            elif message_type == 'generate_scale':
                await self.handle_scale_generation(data)
            elif message_type == 'detect_key':
                await self.handle_key_detection(data)
            elif message_type == 'get_substitutions':
                await self.handle_chord_substitutions(data)
            elif message_type == 'practice_exercise':
                await self.handle_practice_exercise(data)
            elif message_type == 'chord_progression':
                await self.handle_chord_progression(data)
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error in music theory WebSocket: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))
    
    async def handle_chord_analysis(self, data):
        """Handle chord analysis request."""
        try:
            notes = data.get('notes', [])
            if not notes:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Notes array is required'
                }))
                return
            
            # Analyze chord
            chord_analysis = await asyncio.get_event_loop().run_in_executor(
                None, self.theory_engine.analyze_chord, notes
            )
            
            await self.send(text_data=json.dumps({
                'type': 'chord_analysis_result',
                'chord': chord_analysis.chord_name,
                'confidence': chord_analysis.confidence,
                'quality': chord_analysis.quality,
                'inversion': chord_analysis.inversion,
                'tensions': chord_analysis.tensions,
                'difficulty': chord_analysis.difficulty,
                'substitutions': chord_analysis.substitutions[:5],  # Limit results
                'message': f'Analyzed chord: {chord_analysis.chord_name}'
            }))
            
        except Exception as e:
            logger.error(f"Error in chord analysis: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Chord analysis failed: {str(e)}'
            }))
    
    async def handle_scale_generation(self, data):
        """Handle scale generation request."""
        try:
            root = data.get('root', 'C')
            scale_type = data.get('scale_type', 'major')
            
            # Generate scale
            scale_notes = await asyncio.get_event_loop().run_in_executor(
                None, self.theory_engine.generate_scale, root, scale_type
            )
            
            # Get scale information
            scale_info = {
                'notes': scale_notes,
                'intervals': self.theory_engine.scale_templates.get(scale_type, {}).get('intervals', []),
                'characteristic': self.theory_engine.scale_templates.get(scale_type, {}).get('characteristic', ''),
                'difficulty': self.theory_engine.scale_templates.get(scale_type, {}).get('difficulty', 1)
            }
            
            await self.send(text_data=json.dumps({
                'type': 'scale_generation_result',
                'root': root,
                'scale_type': scale_type,
                'scale_info': scale_info,
                'message': f'Generated {root} {scale_type} scale'
            }))
            
        except Exception as e:
            logger.error(f"Error in scale generation: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Scale generation failed: {str(e)}'
            }))
    
    async def handle_key_detection(self, data):
        """Handle key detection request."""
        try:
            chroma_vector = data.get('chroma_vector')
            if not chroma_vector or len(chroma_vector) != 12:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Valid 12-dimensional chroma vector is required'
                }))
                return
            
            # Detect key
            key_analysis = await asyncio.get_event_loop().run_in_executor(
                None, self.theory_engine.detect_key, chroma_vector
            )
            
            await self.send(text_data=json.dumps({
                'type': 'key_detection_result',
                'key': key_analysis.key,
                'mode': key_analysis.mode,
                'confidence': key_analysis.confidence,
                'scale_notes': key_analysis.scale_notes,
                'related_keys': key_analysis.related_keys,
                'message': f'Detected key: {key_analysis.key} {key_analysis.mode}'
            }))
            
        except Exception as e:
            logger.error(f"Error in key detection: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Key detection failed: {str(e)}'
            }))
    
    async def handle_chord_substitutions(self, data):
        """Handle chord substitution request."""
        try:
            chord = data.get('chord', 'C')
            instrument = data.get('instrument', 'guitar')
            max_results = data.get('max_results', 5)
            
            # Get substitutions
            substitutions = await asyncio.get_event_loop().run_in_executor(
                None, self.theory_engine.get_chord_substitutions, chord, instrument
            )
            
            # Limit results
            limited_substitutions = substitutions[:max_results]
            
            await self.send(text_data=json.dumps({
                'type': 'chord_substitutions_result',
                'original_chord': chord,
                'instrument': instrument,
                'substitutions': [
                    {
                        'chord': sub['chord'],
                        'type': sub['type'],
                        'difficulty': sub.get('difficulty', 1),
                        'notes': sub.get('notes', [])
                    }
                    for sub in limited_substitutions
                ],
                'message': f'Found {len(limited_substitutions)} substitutions for {chord}'
            }))
            
        except Exception as e:
            logger.error(f"Error getting substitutions: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Substitution lookup failed: {str(e)}'
            }))
    
    async def handle_practice_exercise(self, data):
        """Handle practice exercise generation."""
        try:
            exercise_type = data.get('exercise_type', 'chord_recognition')
            difficulty = data.get('difficulty', 1)
            
            if exercise_type == 'chord_recognition':
                # Generate random chord for recognition
                import random
                chord_templates = list(self.theory_engine.chord_templates.keys())
                random_chord = random.choice(chord_templates)
                root_notes = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
                root = random.choice(root_notes)
                
                chord_info = self.theory_engine.chord_templates[random_chord]
                exercise = {
                    'type': 'chord_recognition',
                    'chord': f"{root}{random_chord}",
                    'notes': [root] + chord_info['intervals'][:3],  # Simplified
                    'difficulty': chord_info.get('difficulty', 1),
                    'question': f"What chord is formed by these notes?",
                    'answer': f"{root}{random_chord}"
                }
                
            elif exercise_type == 'scale_practice':
                import random
                scales = list(self.theory_engine.scale_templates.keys())
                scale_type = random.choice(scales)
                root_notes = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
                root = random.choice(root_notes)
                
                scale_notes = self.theory_engine.generate_scale(root, scale_type)
                exercise = {
                    'type': 'scale_practice',
                    'scale': f"{root} {scale_type}",
                    'notes': scale_notes,
                    'difficulty': self.theory_engine.scale_templates[scale_type].get('difficulty', 1),
                    'question': f"Play the {root} {scale_type} scale",
                    'answer': scale_notes
                }
            
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown exercise type: {exercise_type}'
                }))
                return
            
            await self.send(text_data=json.dumps({
                'type': 'practice_exercise_result',
                'exercise': exercise,
                'message': f'Generated {exercise_type} exercise'
            }))
            
        except Exception as e:
            logger.error(f"Error generating exercise: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Exercise generation failed: {str(e)}'
            }))
    
    async def handle_chord_progression(self, data):
        """Handle chord progression analysis/generation."""
        try:
            key = data.get('key', 'C')
            mode = data.get('mode', 'major')
            length = data.get('length', 4)
            
            # Generate a simple chord progression
            if mode == 'major':
                # Common major progressions
                progressions = [
                    ['I', 'V', 'vi', 'IV'],  # Pop progression
                    ['I', 'vi', 'IV', 'V'],  # Classic progression
                    ['vi', 'IV', 'I', 'V'],  # Variation
                    ['I', 'IV', 'V', 'I']    # Simple cadence
                ]
            else:
                # Common minor progressions
                progressions = [
                    ['i', 'VII', 'VI', 'VII'],
                    ['i', 'iv', 'V', 'i'],
                    ['i', 'VI', 'III', 'VII']
                ]
            
            import random
            chosen_progression = random.choice(progressions)[:length]
            
            # Convert roman numerals to actual chords (simplified)
            scale_notes = self.theory_engine.generate_scale(key, mode)
            chord_mapping = {
                'I': scale_notes[0], 'i': scale_notes[0] + 'm',
                'ii': scale_notes[1] + 'm', 'II': scale_notes[1],
                'iii': scale_notes[2] + 'm', 'III': scale_notes[2],
                'IV': scale_notes[3], 'iv': scale_notes[3] + 'm',
                'V': scale_notes[4], 'v': scale_notes[4] + 'm',
                'vi': scale_notes[5] + 'm', 'VI': scale_notes[5],
                'vii': scale_notes[6] + 'dim', 'VII': scale_notes[6]
            }
            
            actual_chords = [chord_mapping.get(roman, roman) for roman in chosen_progression]
            
            await self.send(text_data=json.dumps({
                'type': 'chord_progression_result',
                'key': key,
                'mode': mode,
                'roman_numerals': chosen_progression,
                'chords': actual_chords,
                'scale_notes': scale_notes,
                'message': f'Generated chord progression in {key} {mode}'
            }))
            
        except Exception as e:
            logger.error(f"Error generating progression: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Chord progression generation failed: {str(e)}'
            }))
    
    # Group message handlers
    async def theory_update(self, event):
        """Handle theory update from group."""
        await self.send(text_data=json.dumps({
            'type': 'theory_update',
            'message': event['message'],
            'data': event.get('data', {})
        }))

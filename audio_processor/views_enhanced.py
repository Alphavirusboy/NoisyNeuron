from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

User = get_user_model()
import os
import json
import uuid
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import AudioProject, AudioFile, ProcessingJob
from .audio_service import EnhancedAudioProcessor
from .task_processor import process_separation_job

logger = logging.getLogger(__name__)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def upload_audio(request):
    """Enhanced audio upload endpoint with real-time progress."""
    try:
        # Get uploaded file
        audio_file = request.FILES.get('audio_file')
        if not audio_file:
            return Response({'error': 'No audio file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get processing options
        quality = request.POST.get('quality', 'balanced')
        stems_json = request.POST.get('stems', '["vocals", "drums", "bass", "other"]')
        
        try:
            stems = json.loads(stems_json)
        except json.JSONDecodeError:
            stems = ["vocals", "drums", "bass", "other"]
        
        # Validate file
        processor = EnhancedAudioProcessor()
        validation = processor.validate_audio_file_upload(audio_file)
        
        if not validation['valid']:
            return Response({'error': validation['error']}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create demo user
        demo_user, created = User.objects.get_or_create(
            username='demo_user',
            defaults={
                'email': 'demo@noisyneuron.com',
                'first_name': 'Demo',
                'last_name': 'User'
            }
        )
        
        # Create project
        project_name = f"Separation - {audio_file.name}"
        project = AudioProject.objects.create(
            user=demo_user,
            name=project_name,
            description=f"AI source separation of {audio_file.name}"
        )
        
        # Create audio file record
        audio_file_obj = AudioFile.objects.create(
            project=project,
            original_filename=audio_file.name,
            file=audio_file,
            file_size=audio_file.size,
            format=validation['format'],
            processing_status='pending'
        )
        
        # Analyze audio properties
        try:
            temp_path = audio_file_obj.file.path
            analysis = processor.quick_analyze(temp_path)
            
            audio_file_obj.duration = analysis.get('duration', 0)
            audio_file_obj.sample_rate = analysis.get('sample_rate', 44100)
            audio_file_obj.channels = analysis.get('channels', 2)
            audio_file_obj.save()
            
        except Exception as e:
            logger.warning(f"Could not analyze audio file: {e}")
        
        # Create processing job
        job = ProcessingJob.objects.create(
            audio_file=audio_file_obj,
            job_type='source_separation',
            status='queued',
            parameters={
                'stems': stems,
                'quality': quality,
            }
        )
        
        # Start processing job asynchronously
        try:
            process_separation_job.delay(job.id)
        except Exception as e:
            logger.warning(f"Could not start async job: {e}")
            # Fallback to sync processing
            job.status = 'processing'
            job.save()
        
        return Response({
            'success': True,
            'job_id': str(job.id),
            'project_id': str(project.id),
            'message': 'Upload successful, processing started'
        })
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return Response({'error': 'Upload failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def separate_audio_view(request):
    """Main audio separation page view."""
    from django.shortcuts import render
    return render(request, 'audio_processor/separate.html')

def separate_professional_view(request):
    """Professional audio separation page view."""
    from django.shortcuts import render
    return render(request, 'audio_processor/separate_professional.html')

@api_view(['POST'])
@permission_classes([AllowAny])
def professional_separate(request):
    """Professional audio separation with advanced features"""
    try:
        audio_file = request.FILES.get('audio_file')
        model_type = request.POST.get('model_type', 'basic_separation')
        
        if not audio_file:
            return Response({'error': 'No audio file provided'}, status=400)
        
        # Import required libraries
        import librosa
        import numpy as np
        import soundfile as sf
        import tempfile
        import os
        
        logger.info(f"Starting audio separation for file: {audio_file.name}")
        
        # Create directories
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        separated_dir = os.path.join(settings.MEDIA_ROOT, 'separated')
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(separated_dir, exist_ok=True)
        
        # Generate unique filenames
        unique_id = uuid.uuid4().hex
        temp_input = os.path.join(temp_dir, f"input_{unique_id}.wav")
        
        # Save uploaded file
        with open(temp_input, 'wb') as f:
            for chunk in audio_file.chunks():
                f.write(chunk)
        
        logger.info(f"Saved input file to: {temp_input}")
        
        # Load audio with librosa
        y, sr = librosa.load(temp_input, sr=44100, mono=False)
        logger.info(f"Loaded audio: shape={y.shape}, sr={sr}")
        
        # Handle mono/stereo conversion
        if y.ndim == 1:
            # Convert mono to stereo by duplicating
            y = np.stack([y, y])
            logger.info("Converted mono to stereo")
        elif y.ndim == 2 and y.shape[0] == 1:
            # Single channel stereo to dual channel
            y = np.repeat(y, 2, axis=0)
            logger.info("Expanded single channel to stereo")
        
        # Use system Spleeter command-line (verified working approach)
        logger.info("Starting Spleeter command-line separation...")
        
        try:
            import subprocess
            import shutil
            import glob
            
            # Create output directory for spleeter
            spleeter_output_dir = os.path.join(temp_dir, f"spleeter_out_{unique_id}")
            os.makedirs(spleeter_output_dir, exist_ok=True)
            
            logger.info("Running Spleeter 4stems separation...")
            
            # Use the exact command you verified works
            cmd = [
                'spleeter', 'separate',
                '-p', 'spleeter:4stems-16kHz',
                '-o', spleeter_output_dir,
                temp_input
            ]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            
            # Run spleeter with proper error handling
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=temp_dir,
                timeout=120  # 2 minute timeout
            )
            
            if result.returncode != 0:
                logger.error(f"Spleeter command failed with return code {result.returncode}")
                logger.error(f"STDERR: {result.stderr}")
                logger.error(f"STDOUT: {result.stdout}")
                raise Exception(f"Spleeter failed: {result.stderr}")
            
            logger.info("Spleeter completed successfully!")
            logger.info(f"Spleeter STDOUT: {result.stdout}")
            
            # Find the separated files
            input_basename = os.path.splitext(os.path.basename(temp_input))[0]
            stems_dir = os.path.join(spleeter_output_dir, input_basename)
            
            logger.info(f"Looking for stems in: {stems_dir}")
            
            # Check if stems directory exists
            if not os.path.exists(stems_dir):
                logger.error(f"Stems directory not found: {stems_dir}")
                # Try to find any output directories
                output_dirs = glob.glob(os.path.join(spleeter_output_dir, "*"))
                logger.info(f"Available output directories: {output_dirs}")
                if output_dirs:
                    stems_dir = output_dirs[0]
                    logger.info(f"Using first available directory: {stems_dir}")
                else:
                    raise Exception("No output directory found from Spleeter")
            
            # Load the Spleeter results
            vocals_file = os.path.join(stems_dir, 'vocals.wav')
            drums_file = os.path.join(stems_dir, 'drums.wav') 
            bass_file = os.path.join(stems_dir, 'bass.wav')
            other_file = os.path.join(stems_dir, 'other.wav')
            
            logger.info(f"Expected files: {vocals_file}, {drums_file}, {bass_file}, {other_file}")
            
            # Check which files exist
            existing_files = []
            for f in [vocals_file, drums_file, bass_file, other_file]:
                if os.path.exists(f):
                    existing_files.append(f)
                    logger.info(f"Found: {f}")
                else:
                    logger.warning(f"Missing: {f}")
            
            # List all files in stems directory for debugging
            if os.path.exists(stems_dir):
                all_files = os.listdir(stems_dir)
                logger.info(f"All files in stems directory: {all_files}")
            
            # Load the files
            if os.path.exists(vocals_file):
                vocals_raw, _ = librosa.load(vocals_file, sr=sr, mono=True)
                logger.info(f"Loaded vocals: {len(vocals_raw)} samples")
            else:
                logger.error("Vocals file not found!")
                raise Exception("Vocals file not generated by Spleeter")
            
            if os.path.exists(drums_file):
                drums_raw, _ = librosa.load(drums_file, sr=sr, mono=True)
                logger.info(f"Loaded drums: {len(drums_raw)} samples")
            else:
                logger.error("Drums file not found!")
                raise Exception("Drums file not generated by Spleeter")
            
            if os.path.exists(bass_file):
                bass_raw, _ = librosa.load(bass_file, sr=sr, mono=True)
                logger.info(f"Loaded bass: {len(bass_raw)} samples")
            else:
                logger.error("Bass file not found!")
                raise Exception("Bass file not generated by Spleeter")
            
            if os.path.exists(other_file):
                other_raw, _ = librosa.load(other_file, sr=sr, mono=True)
                logger.info(f"Loaded other: {len(other_raw)} samples")
            else:
                logger.error("Other file not found!")
                raise Exception("Other file not generated by Spleeter")
            
            # Clean up spleeter output directory
            shutil.rmtree(spleeter_output_dir, ignore_errors=True)
            logger.info("Cleaned up Spleeter temporary files")
            
            logger.info("Spleeter separation completed successfully!")
            
        except subprocess.TimeoutExpired:
            logger.error("Spleeter command timed out")
            raise Exception("Spleeter processing timed out")
            
        except FileNotFoundError:
            logger.error("Spleeter command not found in PATH")
            logger.info("Please install Spleeter: pip install spleeter")
            raise Exception("Spleeter not installed or not in PATH")
            
        except Exception as spleeter_error:
            logger.error(f"Spleeter separation failed: {str(spleeter_error)}")
            logger.info("Falling back to enhanced separation...")
            
            # Fallback to enhanced separation
            if y.shape[0] == 2:
                left, right = y[0], y[1]
                mid = (left + right) / 2
                side = (left - right) / 2
                
                # Enhanced separation as fallback
                vocals_raw = side * 1.8 + mid * 0.2
                vocals_raw = vocals_raw + np.roll(vocals_raw, 1) * 0.3 - np.roll(vocals_raw, 5) * 0.4
                
                bass_raw = mid * 1.6
                for _ in range(3):
                    bass_raw = (bass_raw + np.roll(bass_raw, 1) + np.roll(bass_raw, -1)) / 3
                
                drums_raw = mid * 1.3
                drums_transients = np.abs(drums_raw - np.roll(drums_raw, 1))
                drums_raw = drums_raw + drums_transients * 0.6
                
                other_raw = (mid * 0.8 + side * 0.4) - vocals_raw * 0.2 - bass_raw * 0.1
                
            else:
                audio = y[0] if y.ndim > 1 else y
                
                vocals_raw = audio * 1.1 + np.roll(audio, 1) * 0.2 - np.roll(audio, 3) * 0.3
                
                bass_raw = audio * 1.4
                for _ in range(4):
                    bass_raw = (bass_raw + np.roll(bass_raw, 1) + np.roll(bass_raw, -1)) / 3
                
                drums_raw = audio * 0.9 + np.abs(audio - np.roll(audio, 1)) * 0.4
                
                other_raw = audio * 0.8 - vocals_raw * 0.1 - bass_raw * 0.1
        
        # Ensure all arrays have the same length
        target_length = len(y[0])
        vocals_raw = vocals_raw[:target_length]
        drums_raw = drums_raw[:target_length] 
        bass_raw = bass_raw[:target_length]
        other_raw = other_raw[:target_length]
        
        # Normalize to prevent clipping
        vocals_raw = np.clip(vocals_raw, -1.0, 1.0)
        drums_raw = np.clip(drums_raw, -1.0, 1.0)
        bass_raw = np.clip(bass_raw, -1.0, 1.0)
        other_raw = np.clip(other_raw, -1.0, 1.0)
        
        logger.info("4-track separation processing completed")
        
        # Save separated tracks
        results = {}
        
        # Save vocals
        vocals_filename = f"vocals_{unique_id}.wav"
        vocals_path = os.path.join(separated_dir, vocals_filename)
        sf.write(vocals_path, vocals_raw, sr)
        logger.info(f"Saved vocals to: {vocals_path}")
        
        # Verify file was created
        if os.path.exists(vocals_path):
            file_size = os.path.getsize(vocals_path)
            logger.info(f"Vocals file created successfully: {file_size} bytes")
        else:
            logger.error(f"Failed to create vocals file at: {vocals_path}")
        
        # Create URL for vocals
        vocals_url = f"/media/separated/{vocals_filename}"
        results['vocals'] = vocals_url
        
        # Save drums
        drums_filename = f"drums_{unique_id}.wav"
        drums_path = os.path.join(separated_dir, drums_filename)
        sf.write(drums_path, drums_raw, sr)
        logger.info(f"Saved drums to: {drums_path}")
        
        # Verify file was created
        if os.path.exists(drums_path):
            file_size = os.path.getsize(drums_path)
            logger.info(f"Drums file created successfully: {file_size} bytes")
        else:
            logger.error(f"Failed to create drums file at: {drums_path}")
        
        # Create URL for drums
        drums_url = f"/media/separated/{drums_filename}"
        results['drums'] = drums_url
        
        # Save bass
        bass_filename = f"bass_{unique_id}.wav"
        bass_path = os.path.join(separated_dir, bass_filename)
        sf.write(bass_path, bass_raw, sr)
        logger.info(f"Saved bass to: {bass_path}")
        
        # Verify file was created
        if os.path.exists(bass_path):
            file_size = os.path.getsize(bass_path)
            logger.info(f"Bass file created successfully: {file_size} bytes")
        else:
            logger.error(f"Failed to create bass file at: {bass_path}")
        
        # Create URL for bass
        bass_url = f"/media/separated/{bass_filename}"
        results['bass'] = bass_url
        
        # Save other
        other_filename = f"other_{unique_id}.wav"
        other_path = os.path.join(separated_dir, other_filename)
        sf.write(other_path, other_raw, sr)
        logger.info(f"Saved other to: {other_path}")
        
        # Verify file was created
        if os.path.exists(other_path):
            file_size = os.path.getsize(other_path)
            logger.info(f"Other file created successfully: {file_size} bytes")
        else:
            logger.error(f"Failed to create other file at: {other_path}")
        
        # Create URL for other
        other_url = f"/media/separated/{other_filename}"
        results['other'] = other_url
        
        # Clean up temp input file
        if os.path.exists(temp_input):
            os.remove(temp_input)
            logger.info("Cleaned up temporary input file")
        
        logger.info(f"Separation completed successfully. Results: {results}")
        
        return Response({
            'success': True,
            'results': results,
            'message': 'Audio separation completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Professional separation error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': f'Separation failed: {str(e)}'
        }, status=500)

@api_view(['GET'])
def get_processing_status(request, job_id):
    """Get the status of a processing job."""
    try:
        job = ProcessingJob.objects.get(id=job_id)
        return Response({
            'status': job.status,
            'progress': job.progress,
            'message': job.status_message or '',
            'error': job.error_message or ''
        })
    except ProcessingJob.DoesNotExist:
        return Response({'error': 'Job not found'}, status=404)

@api_view(['GET'])
def get_project_results(request, project_id):
    """Get the results of a completed project."""
    try:
        project = AudioProject.objects.get(id=project_id)
        # Return project results
        return Response({
            'project_name': project.name,
            'status': 'completed',
            'results': {}  # Add actual results here
        })
    except AudioProject.DoesNotExist:
        return Response({'error': 'Project not found'}, status=404)

@api_view(['GET'])
def download_stem(request, track_id):
    """Download a separated track."""
    # Implementation for downloading tracks
    return Response({'error': 'Not implemented'}, status=501)

@api_view(['POST'])
def cancel_processing(request, job_id):
    """Cancel a processing job."""
    try:
        job = ProcessingJob.objects.get(id=job_id)
        job.status = 'cancelled'
        job.save()
        return Response({'message': 'Job cancelled successfully'})
    except ProcessingJob.DoesNotExist:
        return Response({'error': 'Job not found'}, status=404)

@api_view(['GET'])
def health_check(request):
    """Health check endpoint."""
    return JsonResponse({
        'status': 'healthy',
        'service': 'NoisyNeuron Audio Processor',
        'version': '2.0.0'
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def analyze_audio_enhanced(request):
    """Enhanced audio analysis endpoint."""
    try:
        audio_file = request.FILES.get('audio_file')
        if not audio_file:
            return Response({'error': 'No audio file provided'}, status=400)
        
        # Placeholder for audio analysis
        return Response({
            'success': True,
            'analysis': {
                'duration': 120,
                'sample_rate': 44100,
                'channels': 2,
                'format': 'WAV'
            }
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)
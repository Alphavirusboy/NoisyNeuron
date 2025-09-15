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
                'quality': quality,
                'stems': stems,
                'model': 'htdemucs' if quality == 'high' else 'mdx_extra',
                'device': 'auto'
            }
        )
        
        # Send WebSocket notification
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"audio_processing_{demo_user.id}",
                {
                    'type': 'processing_started',
                    'job_id': str(job.id),
                    'project_id': str(project.id),
                    'filename': audio_file.name
                }
            )
        
        # Start processing (in production, this would be a Celery task)
        if hasattr(settings, 'USE_CELERY') and settings.USE_CELERY:
            # For Celery: process_audio_separation_enhanced.delay(job.id)
            process_audio_separation_sync(job.id)
        else:
            # For development, process synchronously (not recommended for production)
            process_audio_separation_sync(job.id)
        
        return Response({
            'status': 'success',
            'project_id': str(project.id),
            'job_id': str(job.id),
            'audio_file_id': str(audio_file_obj.id),
            'filename': audio_file.name,
            'size': audio_file.size,
            'duration': audio_file_obj.duration,
            'message': 'File uploaded successfully. Processing will begin shortly.'
        })
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return Response(
            {'error': f'Upload failed: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def process_audio_separation_sync(job_id):
    """Synchronous processing for development."""
    import threading
    thread = threading.Thread(target=_process_job_background, args=(job_id,))
    thread.daemon = True
    thread.start()

def _process_job_background(job_id):
    """Background processing function."""
    try:
        from .task_processor import process_separation_job
        process_separation_job(job_id)
    except Exception as e:
        logger.error(f"Background processing error: {e}")

@api_view(['GET'])
@permission_classes([AllowAny])
def get_processing_status(request, job_id):
    """Get processing status for a job."""
    try:
        job = ProcessingJob.objects.get(id=job_id)
        
        return Response({
            'status': job.status,
            'progress': job.progress,
            'stage': job.current_stage,
            'error': job.error_message,
            'estimated_time': job.estimated_completion_time,
            'created_at': job.created_at,
            'updated_at': job.updated_at
        })
        
    except ProcessingJob.DoesNotExist:
        return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_project_results(request, project_id):
    """Get separation results for a project."""
    try:
        project = AudioProject.objects.get(id=project_id)
        
        results = []
        for audio_file in project.audio_files.all():
            file_data = {
                'id': str(audio_file.id),
                'filename': audio_file.original_filename,
                'status': audio_file.processing_status,
                'separated_tracks': []
            }
            
            for track in audio_file.separated_tracks.all():
                track_data = {
                    'id': str(track.id),
                    'stem_type': track.stem_type,
                    'file_url': track.file.url if track.file else None,
                    'file_size': track.file_size,
                    'quality_score': track.quality_score,
                    'created_at': track.created_at
                }
                file_data['separated_tracks'].append(track_data)
            
            results.append(file_data)
        
        return Response({
            'project_id': str(project.id),
            'name': project.name,
            'results': results
        })
        
    except AudioProject.DoesNotExist:
        return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([AllowAny])
def download_stem(request, track_id):
    """Download a separated stem."""
    try:
        from .models import SeparatedTrack
        track = SeparatedTrack.objects.get(id=track_id)
        
        if not track.file:
            return Response({'error': 'File not available'}, status=status.HTTP_404_NOT_FOUND)
        
        response = FileResponse(
            track.file.open('rb'),
            as_attachment=True,
            filename=f"{track.stem_type}_{track.audio_file.original_filename}"
        )
        
        return response
        
    except SeparatedTrack.DoesNotExist:
        return Response({'error': 'Track not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([AllowAny])
def cancel_processing(request, job_id):
    """Cancel a processing job."""
    try:
        job = ProcessingJob.objects.get(id=job_id)
        
        if job.status in ['completed', 'failed', 'cancelled']:
            return Response({'error': 'Job cannot be cancelled'}, status=status.HTTP_400_BAD_REQUEST)
        
        job.status = 'cancelled'
        job.save()
        
        # Send WebSocket notification
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"audio_processing_{job.audio_file.project.user.id}",
                {
                    'type': 'processing_cancelled',
                    'job_id': str(job.id)
                }
            )
        
        return Response({'status': 'cancelled'})
        
    except ProcessingJob.DoesNotExist:
        return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint."""
    return JsonResponse({
        'status': 'healthy',
        'service': 'NoisyNeuron Audio Processor',
        'version': '2.0.0'
    })
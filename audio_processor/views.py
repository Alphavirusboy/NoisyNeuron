from rest_framework import status, viewsets
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import os
import json
import uuid
import logging
from typing import Dict, Any

from .models import AudioProject, AudioFile, SeparatedTrack, ProcessingJob
from .serializers import (
    AudioProjectSerializer, AudioFileSerializer, SeparatedTrackSerializer,
    ProcessingJobSerializer, AudioUploadSerializer, ProcessingOptionsSerializer
)
from .audio_service import AudioProcessor
from .tasks import process_audio_separation

logger = logging.getLogger(__name__)

class AudioProjectViewSet(viewsets.ModelViewSet):
    serializer_class = AudioProjectSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return AudioProject.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@csrf_exempt
@api_view(['POST'])
def analyze_audio(request):
    """Analyze uploaded audio file and return characteristics."""
    try:
        serializer = AudioUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        audio_file = serializer.validated_data['audio_file']
        
        # Save temporary file
        temp_path = default_storage.save(f'temp/{uuid.uuid4()}.tmp', audio_file)
        full_path = os.path.join(settings.MEDIA_ROOT, temp_path)
        
        try:
            # Analyze audio
            processor = AudioProcessor()
            validation = processor.validate_audio_file(full_path)
            
            if not validation['is_valid']:
                return Response(
                    {'error': validation['error']}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Load and analyze
            audio_data, sample_rate = processor.load_audio(full_path)
            analysis = processor.analyze_audio(audio_data, sample_rate)
            
            return Response({
                'status': 'success',
                'analysis': analysis,
                'validation': validation
            })
            
        finally:
            # Clean up temporary file
            if os.path.exists(full_path):
                os.remove(full_path)
                
    except Exception as e:
        logger.error(f"Audio analysis error: {str(e)}")
        return Response(
            {'error': 'Failed to analyze audio file'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@csrf_exempt
@api_view(['POST'])
def process_audio(request):
    """Start audio source separation processing."""
    try:
        # Parse form data
        audio_file = request.FILES.get('audio_file')
        options_json = request.POST.get('options', '{}')
        
        if not audio_file:
            return Response({'error': 'No audio file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate options
        try:
            options = json.loads(options_json)
            options_serializer = ProcessingOptionsSerializer(data=options)
            if not options_serializer.is_valid():
                return Response(options_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            validated_options = options_serializer.validated_data
        except json.JSONDecodeError:
            return Response({'error': 'Invalid options format'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create project and audio file (use anonymous user for now)
        from django.contrib.auth.models import User
        
        # Get or create a test user for demo purposes
        test_user, created = User.objects.get_or_create(
            username='demo_user',
            defaults={'email': 'demo@example.com'}
        )
        
        project_name = f"Separation {uuid.uuid4().hex[:8]}"
        project = AudioProject.objects.create(
            user=test_user,
            name=project_name,
            description="Audio source separation project"
        )
        
        # Save audio file
        audio_file_obj = AudioFile.objects.create(
            project=project,
            original_filename=audio_file.name,
            file=audio_file,
            file_size=audio_file.size,
            format=os.path.splitext(audio_file.name)[1].lower().lstrip('.'),
            processing_status='pending'
        )
        
        # Create processing job
        job = ProcessingJob.objects.create(
            audio_file=audio_file_obj,
            job_type='source_separation',
            status='queued',
            parameters=validated_options
        )
        
        # Start background processing
        process_audio_separation.delay(job.id)
        
        return Response({
            'status': 'success',
            'job_id': str(job.id),
            'project_id': str(project.id),
            'audio_file_id': str(audio_file_obj.id),
            'message': 'Processing started'
        })
        
    except Exception as e:
        logger.error(f"Processing start error: {str(e)}")
        return Response(
            {'error': 'Failed to start processing'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@csrf_exempt
@api_view(['GET'])
def processing_status(request, job_id):
    """Get processing status for a job."""
    try:
        job = get_object_or_404(ProcessingJob, id=job_id)
        
        # For demo purposes, allow access without authentication
        
        # Get separated tracks if completed
        separated_tracks = []
        if job.status == 'completed':
            tracks = SeparatedTrack.objects.filter(audio_file=job.audio_file)
            separated_tracks = SeparatedTrackSerializer(tracks, many=True).data
        
        return Response({
            'job_id': str(job.id),
            'status': job.status,
            'progress': job.progress,
            'current_step': job.result.get('current_step', ''),
            'step_number': job.result.get('step_number', 1),
            'markov_status': job.result.get('markov_status', 'Pending'),
            'spectral_status': job.result.get('spectral_status', 'Pending'),
            'enhancement_status': job.result.get('enhancement_status', 'Pending'),
            'error_message': job.error_message,
            'separated_tracks': separated_tracks,
            'created_at': job.created_at,
            'completed_at': job.completed_at
        })
        
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        return Response(
            {'error': 'Failed to get status'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@csrf_exempt
@api_view(['POST'])
def cancel_processing(request, job_id):
    """Cancel a processing job."""
    try:
        job = get_object_or_404(ProcessingJob, id=job_id)
        
        # Check if user has access
        if not request.user.is_authenticated or job.audio_file.project.user != request.user:
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        if job.status in ['queued', 'running']:
            job.status = 'cancelled'
            job.save()
            
            return Response({
                'status': 'success',
                'message': 'Processing cancelled'
            })
        else:
            return Response({
                'error': 'Cannot cancel job in current status'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Cancel processing error: {str(e)}")
        return Response(
            {'error': 'Failed to cancel processing'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def download_track(request, track_id):
    """Download a separated track."""
    try:
        track = get_object_or_404(SeparatedTrack, id=track_id)
        
        # Check if user has access
        if not request.user.is_authenticated or track.audio_file.project.user != request.user:
            raise Http404()
        
        file_path = track.file.path
        if not os.path.exists(file_path):
            raise Http404()
        
        response = FileResponse(
            open(file_path, 'rb'),
            content_type='audio/wav',
            as_attachment=True,
            filename=f"{track.track_type}_{track.audio_file.original_filename}"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Download track error: {str(e)}")
        raise Http404()

@api_view(['GET'])
def download_all_stems(request, job_id):
    """Download all separated tracks as a ZIP file."""
    try:
        job = get_object_or_404(ProcessingJob, id=job_id)
        
        # Check if user has access
        if not request.user.is_authenticated or job.audio_file.project.user != request.user:
            raise Http404()
        
        if job.status != 'completed':
            return Response(
                {'error': 'Processing not completed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create ZIP file with all tracks
        import zipfile
        import tempfile
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
            with zipfile.ZipFile(temp_zip.name, 'w') as zip_file:
                tracks = SeparatedTrack.objects.filter(audio_file=job.audio_file)
                
                for track in tracks:
                    if os.path.exists(track.file.path):
                        zip_file.write(
                            track.file.path,
                            f"{track.track_type}_{job.audio_file.original_filename}"
                        )
            
            response = FileResponse(
                open(temp_zip.name, 'rb'),
                content_type='application/zip',
                as_attachment=True,
                filename=f"stems_{job.audio_file.original_filename}.zip"
            )
            
            # Schedule cleanup of temp file
            # In production, use a background task for this
            import threading
            import time
            
            def cleanup():
                time.sleep(60)  # Wait 1 minute before cleanup
                try:
                    os.unlink(temp_zip.name)
                except:
                    pass
            
            threading.Thread(target=cleanup).start()
            
            return response
            
    except Exception as e:
        logger.error(f"Download all stems error: {str(e)}")
        raise Http404()

class AudioFileViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AudioFileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return AudioFile.objects.filter(project__user=self.request.user)

class SeparatedTrackViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SeparatedTrackSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return SeparatedTrack.objects.filter(audio_file__project__user=self.request.user)

class ProcessingJobViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProcessingJobSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ProcessingJob.objects.filter(audio_file__project__user=self.request.user)

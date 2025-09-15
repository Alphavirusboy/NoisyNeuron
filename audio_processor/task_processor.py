"""
Background tasks for audio processing
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

def process_separation_job(job_id: str):
    """Process audio separation job."""
    try:
        from .models import ProcessingJob, SeparatedTrack
        from .audio_service import EnhancedAudioProcessor
        
        # Get job
        job = ProcessingJob.objects.get(id=job_id)
        audio_file = job.audio_file
        
        # Update status
        job.status = 'processing'
        job.started_at = datetime.now()
        job.progress = 0
        job.current_stage = 'Initializing...'
        job.save()
        
        # Send WebSocket update
        send_progress_update(job, 0, 'Initializing separation...')
        
        # Initialize processor
        processor = EnhancedAudioProcessor()
        
        # Get processing parameters
        params = job.parameters or {}
        quality = params.get('quality', 'balanced')
        stems = params.get('stems', ['vocals', 'drums', 'bass', 'other'])
        
        # Create output directory
        output_dir = Path(settings.MEDIA_ROOT) / 'separated' / str(job.id)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Progress callback
        def progress_callback(progress: int, stage: str):
            job.progress = progress
            job.current_stage = stage
            job.save()
            send_progress_update(job, progress, stage)
        
        # Perform separation
        result = processor.separate_audio(
            input_path=audio_file.file.path,
            output_dir=str(output_dir),
            stems=stems,
            quality=quality,
            progress_callback=progress_callback
        )
        
        if result['success']:
            # Save separated tracks
            for stem_data in result['stems']:
                SeparatedTrack.objects.create(
                    audio_file=audio_file,
                    processing_job=job,
                    stem_type=stem_data['stem_type'],
                    file=stem_data['file_path'],
                    file_size=stem_data['file_size'],
                    quality_score=result['quality_scores'].get(stem_data['stem_type'], 0.0)
                )
            
            # Update job status
            job.status = 'completed'
            job.completed_at = datetime.now()
            job.progress = 100
            job.current_stage = 'Completed'
            job.processing_time = result['processing_time']
            job.save()
            
            # Update audio file status
            audio_file.processing_status = 'completed'
            audio_file.processing_completed_at = datetime.now()
            audio_file.save()
            
            # Send completion notification
            send_completion_notification(job, result)
            
            logger.info(f"Job {job_id} completed successfully")
            
        else:
            # Handle failure
            job.status = 'failed'
            job.error_message = result.get('error', 'Unknown error')
            job.save()
            
            audio_file.processing_status = 'failed'
            audio_file.processing_error = job.error_message
            audio_file.save()
            
            send_error_notification(job, result.get('error', 'Unknown error'))
            
            logger.error(f"Job {job_id} failed: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Job processing error for {job_id}: {e}")
        
        try:
            job = ProcessingJob.objects.get(id=job_id)
            job.status = 'failed'
            job.error_message = str(e)
            job.save()
            
            audio_file = job.audio_file
            audio_file.processing_status = 'failed'
            audio_file.processing_error = str(e)
            audio_file.save()
            
            send_error_notification(job, str(e))
            
        except Exception as inner_e:
            logger.error(f"Failed to update job status: {inner_e}")

def send_progress_update(job, progress: int, stage: str):
    """Send progress update via WebSocket."""
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            user_id = job.audio_file.project.user.id
            
            async_to_sync(channel_layer.group_send)(
                f"audio_processing_{user_id}",
                {
                    'type': 'processing_progress',
                    'job_id': str(job.id),
                    'progress': progress,
                    'stage': stage,
                    'project_id': str(job.audio_file.project.id)
                }
            )
    except Exception as e:
        logger.error(f"Failed to send progress update: {e}")

def send_completion_notification(job, result: Dict[str, Any]):
    """Send completion notification via WebSocket."""
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            user_id = job.audio_file.project.user.id
            
            # Prepare stem information
            stems_info = []
            for stem_data in result['stems']:
                stems_info.append({
                    'type': stem_data['stem_type'],
                    'size': stem_data['file_size'],
                    'quality': result['quality_scores'].get(stem_data['stem_type'], 0.0)
                })
            
            async_to_sync(channel_layer.group_send)(
                f"audio_processing_{user_id}",
                {
                    'type': 'processing_complete',
                    'job_id': str(job.id),
                    'project_id': str(job.audio_file.project.id),
                    'stems': stems_info,
                    'processing_time': result['processing_time'],
                    'filename': job.audio_file.original_filename
                }
            )
    except Exception as e:
        logger.error(f"Failed to send completion notification: {e}")

def send_error_notification(job, error_message: str):
    """Send error notification via WebSocket."""
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            user_id = job.audio_file.project.user.id
            
            async_to_sync(channel_layer.group_send)(
                f"audio_processing_{user_id}",
                {
                    'type': 'processing_error',
                    'job_id': str(job.id),
                    'project_id': str(job.audio_file.project.id),
                    'error': error_message,
                    'filename': job.audio_file.original_filename
                }
            )
    except Exception as e:
        logger.error(f"Failed to send error notification: {e}")

# Celery tasks (if using Celery)
try:
    from celery import shared_task
    
    @shared_task
    def process_audio_separation_enhanced(job_id: str):
        """Celery task for audio separation."""
        return process_separation_job(job_id)
        
except ImportError:
    # Celery not available
    pass

def cleanup_old_files():
    """Clean up old temporary and processed files."""
    try:
        from .models import ProcessingJob
        from datetime import timedelta
        
        # Delete files older than 7 days
        cutoff_date = datetime.now() - timedelta(days=7)
        old_jobs = ProcessingJob.objects.filter(
            created_at__lt=cutoff_date,
            status__in=['completed', 'failed', 'cancelled']
        )
        
        for job in old_jobs:
            try:
                # Delete separated tracks
                for track in job.separated_tracks.all():
                    if track.file and os.path.exists(track.file.path):
                        os.remove(track.file.path)
                        logger.info(f"Deleted old track file: {track.file.path}")
                
                # Delete job output directory
                output_dir = Path(settings.MEDIA_ROOT) / 'separated' / str(job.id)
                if output_dir.exists():
                    import shutil
                    shutil.rmtree(output_dir)
                    logger.info(f"Deleted old job directory: {output_dir}")
                
                # Delete the job record
                job.delete()
                logger.info(f"Deleted old job: {job.id}")
                
            except Exception as e:
                logger.error(f"Failed to clean up job {job.id}: {e}")
                
    except Exception as e:
        logger.error(f"Cleanup error: {e}")

def get_processing_statistics():
    """Get processing statistics."""
    try:
        from .models import ProcessingJob, AudioFile
        from django.db.models import Count, Avg, Sum
        
        stats = {
            'total_jobs': ProcessingJob.objects.count(),
            'completed_jobs': ProcessingJob.objects.filter(status='completed').count(),
            'failed_jobs': ProcessingJob.objects.filter(status='failed').count(),
            'processing_jobs': ProcessingJob.objects.filter(status='processing').count(),
            'queued_jobs': ProcessingJob.objects.filter(status='queued').count(),
        }
        
        # Average processing time for completed jobs
        avg_time = ProcessingJob.objects.filter(
            status='completed',
            processing_time__isnull=False
        ).aggregate(avg_time=Avg('processing_time'))
        
        stats['average_processing_time'] = avg_time['avg_time'] or 0
        
        # Total files processed
        stats['total_files_processed'] = AudioFile.objects.filter(
            processing_status='completed'
        ).count()
        
        # Total file size processed
        total_size = AudioFile.objects.filter(
            processing_status='completed'
        ).aggregate(total_size=Sum('file_size'))
        
        stats['total_size_processed'] = total_size['total_size'] or 0
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        return {}

def estimate_queue_time():
    """Estimate queue waiting time."""
    try:
        from .models import ProcessingJob
        
        # Count jobs in queue
        queued_count = ProcessingJob.objects.filter(status='queued').count()
        processing_count = ProcessingJob.objects.filter(status='processing').count()
        
        # Rough estimate: 5 minutes per job
        estimated_minutes = (queued_count + processing_count) * 5
        
        return {
            'queued_jobs': queued_count,
            'processing_jobs': processing_count,
            'estimated_wait_minutes': estimated_minutes
        }
        
    except Exception as e:
        logger.error(f"Failed to estimate queue time: {e}")
        return {'estimated_wait_minutes': 0}
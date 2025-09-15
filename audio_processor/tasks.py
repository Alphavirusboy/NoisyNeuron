"""
Celery tasks for audio processing
"""

from celery import shared_task
from django.utils import timezone
import logging
import os
import traceback
from .models import ProcessingJob, AudioFile, SeparatedTrack
from .audio_service import AudioProcessor
from markov_models.markov_chain import AudioMarkovChain

logger = logging.getLogger(__name__)

@shared_task
def process_audio_separation(job_id):
    """
    Background task for audio source separation processing.
    """
    try:
        job = ProcessingJob.objects.get(id=job_id)
        audio_file = job.audio_file
        
        # Update job status
        job.status = 'running'
        job.started_at = timezone.now()
        job.progress = 0
        job.result = {'current_step': 'Initializing...', 'step_number': 1}
        job.save()
        
        # Initialize audio processor
        processor = AudioProcessor()
        
        # Step 1: Load and validate audio
        job.progress = 10
        job.result.update({
            'current_step': 'Loading audio file...',
            'step_number': 1,
            'markov_status': 'Pending'
        })
        job.save()
        
        audio_path = audio_file.file.path
        audio_data, sample_rate = processor.load_audio(audio_path)
        
        # Update audio file metadata
        analysis = processor.analyze_audio(audio_data, sample_rate)
        audio_file.duration = analysis['duration']
        audio_file.sample_rate = sample_rate
        audio_file.channels = 1  # We process mono
        audio_file.save()
        
        # Step 2: Markov chain analysis
        job.progress = 30
        job.result.update({
            'current_step': 'Performing Markov chain analysis...',
            'step_number': 2,
            'markov_status': 'Running'
        })
        job.save()
        
        # Get processing options
        options = job.parameters
        target_instruments = []
        if options.get('separate_vocals', True):
            target_instruments.append('vocals')
        if options.get('separate_drums', True):
            target_instruments.append('drums')
        if options.get('separate_bass', True):
            target_instruments.append('bass')
        if options.get('separate_other', True):
            target_instruments.append('other')
        
        # Step 3: Source separation
        job.progress = 50
        job.result.update({
            'current_step': 'Separating audio sources...',
            'step_number': 3,
            'markov_status': 'Completed',
            'spectral_status': 'Running'
        })
        job.save()
        
        # Perform separation
        separated_audio = processor.markov_enhanced_separation(
            audio_data, sample_rate, target_instruments
        )
        
        # Step 4: Enhancement and saving
        job.progress = 80
        job.result.update({
            'current_step': 'Enhancing and saving tracks...',
            'step_number': 4,
            'spectral_status': 'Completed',
            'enhancement_status': 'Running'
        })
        job.save()
        
        # Save separated tracks
        output_format = options.get('output_format', 'wav')
        
        for instrument, audio in separated_audio.items():
            if len(audio) > 0:  # Skip empty tracks
                # Enhance audio quality
                enhanced_audio = processor.enhance_audio_quality(audio, sample_rate)
                
                # Save to file
                output_filename = f"{instrument}_{audio_file.original_filename}.{output_format}"
                output_path = os.path.join('audio', 'outputs', str(audio_file.project.id), output_filename)
                output_full_path = os.path.join('media', output_path)
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(output_full_path), exist_ok=True)
                
                processor.save_audio(enhanced_audio, sample_rate, output_full_path, output_format)
                
                # Calculate quality score (mock implementation)
                quality_score = min(0.95, max(0.6, len(audio) / len(audio_data) + 0.2))
                
                # Create SeparatedTrack record
                SeparatedTrack.objects.create(
                    audio_file=audio_file,
                    track_type=instrument,
                    file=output_path,
                    confidence_score=quality_score,
                    file_size=os.path.getsize(output_full_path),
                    separation_quality=quality_score,
                    markov_patterns={}  # Would contain actual pattern analysis
                )
        
        # Complete the job
        job.progress = 100
        job.status = 'completed'
        job.completed_at = timezone.now()
        job.result.update({
            'current_step': 'Processing completed!',
            'step_number': 4,
            'enhancement_status': 'Completed'
        })
        job.save()
        
        # Update audio file status
        audio_file.processing_status = 'completed'
        audio_file.processing_completed_at = timezone.now()
        audio_file.save()
        
        logger.info(f"Audio separation completed for job {job_id}")
        
    except Exception as e:
        logger.error(f"Audio separation failed for job {job_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        try:
            job = ProcessingJob.objects.get(id=job_id)
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = timezone.now()
            job.save()
            
            # Update audio file status
            audio_file = job.audio_file
            audio_file.processing_status = 'failed'
            audio_file.processing_error = str(e)
            audio_file.save()
            
        except Exception as save_error:
            logger.error(f"Failed to update job status: {str(save_error)}")

@shared_task
def train_markov_model(instrument_type, audio_files_paths):
    """
    Background task for training Markov models on audio data.
    """
    try:
        logger.info(f"Starting Markov model training for {instrument_type}")
        
        # Load audio files
        audio_data_list = []
        processor = AudioProcessor()
        
        for file_path in audio_files_paths:
            try:
                audio, sr = processor.load_audio(file_path)
                audio_data_list.append((audio, sr))
            except Exception as e:
                logger.warning(f"Failed to load {file_path}: {str(e)}")
                continue
        
        if not audio_data_list:
            raise ValueError("No valid audio files found for training")
        
        # Create and train Markov chain
        markov_chain = AudioMarkovChain(order=2, n_states=16, feature_type='mfcc')
        markov_chain.train(audio_data_list, instrument_type)
        
        # Save trained model
        model_path = f"markov_models/{instrument_type}_model.json"
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        markov_chain.save_model(model_path)
        
        logger.info(f"Markov model training completed for {instrument_type}")
        
        return {
            'status': 'success',
            'instrument_type': instrument_type,
            'training_samples': len(audio_data_list),
            'model_path': model_path
        }
        
    except Exception as e:
        logger.error(f"Markov model training failed for {instrument_type}: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            'status': 'failed',
            'error': str(e)
        }

@shared_task
def cleanup_old_files():
    """
    Cleanup old temporary and processed files.
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        # Remove temporary files older than 1 hour
        temp_dir = os.path.join('media', 'temp')
        if os.path.exists(temp_dir):
            cutoff_time = timezone.now() - timedelta(hours=1)
            
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                if os.path.isfile(file_path):
                    file_time = timezone.datetime.fromtimestamp(
                        os.path.getctime(file_path), tz=timezone.utc
                    )
                    if file_time < cutoff_time:
                        try:
                            os.remove(file_path)
                            logger.info(f"Removed old temp file: {filename}")
                        except Exception as e:
                            logger.warning(f"Failed to remove {filename}: {str(e)}")
        
        # Remove old processing jobs (older than 30 days)
        cutoff_date = timezone.now() - timedelta(days=30)
        old_jobs = ProcessingJob.objects.filter(created_at__lt=cutoff_date)
        
        for job in old_jobs:
            try:
                # Remove associated files
                tracks = SeparatedTrack.objects.filter(audio_file=job.audio_file)
                for track in tracks:
                    if track.file and os.path.exists(track.file.path):
                        os.remove(track.file.path)
                
                # Remove audio file
                if job.audio_file.file and os.path.exists(job.audio_file.file.path):
                    os.remove(job.audio_file.file.path)
                
                # Delete database records
                job.audio_file.project.delete()  # Cascades to delete everything
                
                logger.info(f"Cleaned up old job: {job.id}")
                
            except Exception as e:
                logger.warning(f"Failed to cleanup job {job.id}: {str(e)}")
        
        logger.info("File cleanup completed")
        
    except Exception as e:
        logger.error(f"File cleanup failed: {str(e)}")
        logger.error(traceback.format_exc())

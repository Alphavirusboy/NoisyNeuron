from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import views_enhanced

app_name = 'audio_processor'

router = DefaultRouter()
router.register(r'projects', views.AudioProjectViewSet, basename='audioproject')

urlpatterns = [
    path('', include(router.urls)),
    
    # Main separation page
    path('separate/', views_enhanced.separate_audio_view, name='separate'),
    path('professional/', views_enhanced.separate_professional_view, name='separate_professional'),
    
    # Enhanced endpoints
    path('upload/', views_enhanced.upload_audio, name='upload_audio'),
    path('professional-separate/', views_enhanced.professional_separate, name='professional_separate'),
    path('analyze-enhanced/', views_enhanced.analyze_audio_enhanced, name='analyze_audio_enhanced'),
    path('status/<uuid:job_id>/', views_enhanced.get_processing_status, name='processing_status'),
    path('results/<uuid:project_id>/', views_enhanced.get_project_results, name='project_results'),
    path('download/<uuid:track_id>/', views_enhanced.download_stem, name='download_stem'),
    path('cancel/<uuid:job_id>/', views_enhanced.cancel_processing, name='cancel_processing'),
    path('health/', views_enhanced.health_check, name='health_check'),
    
    # Legacy endpoints
    path('analyze/', views.analyze_audio, name='analyze_audio'),
    path('process/', views.process_audio, name='process_audio'),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import views_enhanced

router = DefaultRouter()
router.register(r'projects', views.AudioProjectViewSet, basename='audioproject')

urlpatterns = [
    path('', include(router.urls)),
    
    # Enhanced endpoints
    path('upload/', views_enhanced.upload_audio, name='upload_audio'),
    path('status/<uuid:job_id>/', views_enhanced.get_processing_status, name='processing_status'),
    path('results/<uuid:project_id>/', views_enhanced.get_project_results, name='project_results'),
    path('download/<uuid:track_id>/', views_enhanced.download_stem, name='download_stem'),
    path('cancel/<uuid:job_id>/', views_enhanced.cancel_processing, name='cancel_processing'),
    path('health/', views_enhanced.health_check, name='health_check'),
    
    # Legacy endpoints
    path('analyze/', views.analyze_audio, name='analyze_audio'),
    path('process/', views.process_audio, name='process_audio'),
]

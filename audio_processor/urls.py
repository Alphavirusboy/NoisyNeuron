from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'projects', views.AudioProjectViewSet, basename='audioproject')
router.register(r'files', views.AudioFileViewSet, basename='audiofile')
router.register(r'tracks', views.SeparatedTrackViewSet, basename='separatedtrack')
router.register(r'jobs', views.ProcessingJobViewSet, basename='processingjob')

urlpatterns = [
    path('', include(router.urls)),
    path('analyze/', views.analyze_audio, name='analyze_audio'),
    path('process/', views.process_audio, name='process_audio'),
    path('status/<uuid:job_id>/', views.processing_status, name='processing_status'),
    path('cancel/<uuid:job_id>/', views.cancel_processing, name='cancel_processing'),
    path('download/<uuid:track_id>/', views.download_track, name='download_track'),
    path('download-all/<uuid:job_id>/', views.download_all_stems, name='download_all_stems'),
]

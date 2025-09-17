from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'music_theory'

router = DefaultRouter()
router.register(r'instruments', views.InstrumentViewSet)
router.register(r'chords', views.ChordViewSet)
router.register(r'songs', views.SongViewSet)
router.register(r'practice', views.PracticeViewSet, basename='practice')
router.register(r'learning-paths', views.LearningPathViewSet)

urlpatterns = [
    # Main pages
    path('learn/', views.learn_view, name='learn'),
    path('practice/', views.practice_view, name='practice'),
    
    # Advanced Training Features
    path('interval-training/', views.interval_training_view, name='interval_training'),
    path('scale-practice/', views.scale_practice_view, name='scale_practice'),
    path('rhythm-training/', views.rhythm_training_view, name='rhythm_training'),
    
    # Training API endpoints
    path('api/generate-interval/', views.generate_interval_exercise, name='generate_interval'),
    path('api/generate-scale/', views.generate_scale_exercise, name='generate_scale'),
    path('api/generate-rhythm/', views.generate_rhythm_exercise, name='generate_rhythm'),
    path('api/submit-answer/', views.submit_training_answer, name='submit_answer'),
    
    # API endpoints
    path('api/', include(router.urls)),
    path('chord-recommendations/', views.ChordRecommendationView.as_view(), name='chord-recommendations'),
    path('key-detection/', views.KeyDetectionView.as_view(), name='key-detection'),
    path('progress/', views.ProgressTrackingView.as_view(), name='progress-tracking'),
]
